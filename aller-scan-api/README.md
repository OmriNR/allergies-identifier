# aller-scan-api

FastAPI + MongoDB (Beanie ODM) backend for aller-scan: user accounts, a
product catalog, allergy preferences/scan history, and ingredient-based
allergen detection. Pairs with the `aller-scan` React frontend; see the repo
root `docker-compose.yaml` to run both together with Mongo.

## Stack

- FastAPI, Pydantic v2 / pydantic-settings
- Beanie (async ODM) over `pymongo`'s `AsyncMongoClient`, MongoDB
- JWT auth (`python-jose`) with OAuth2 password flow
- `uv` for dependency management, `pytest` + `pytest-asyncio` + `httpx` for tests
- `mongomock-motor` to fake Mongo in tests (no real database needed)

## Project layout

```
app/
  auth/auth.py          password hashing, JWT create/decode, get_current_active_user
  config/config.py       Settings (env-driven), loaded from ../.env
  data/allergen_reference.json   allergen -> synonym list used by detection
  db.py                  Mongo client + init_beanie()
  main.py                FastAPI app, CORS, seeds a superuser on startup
  models/                Beanie Documents: User, Product, AllergyPreference,
                          ScanHistory, AllergenProfile
  routes/                one router module per resource, wired in routes/api.py
  schemas/                Pydantic request/response models (never expose password)
  services/allergen_detection.py   ingredient/text -> allergen matching
tests/
  test_models/           direct model tests (no HTTP)
  test_api/               black-box tests through the FastAPI app
  test_services/          unit tests for allergen_detection
  conftest.py             in-memory Mongo + app/client fixtures
  README.md               assumed API contract test_api/ was written against
```

## Setup & running

```
uv sync
cp .env.example .env   # or set env vars directly; all Settings fields are required except the SSO/mongo-auth ones
uv run fastapi dev app/main.py
```

Requires a reachable MongoDB (`MONGO_HOST`/`MONGO_PORT`/...). The root
`docker-compose.yaml` runs Mongo + this API + the frontend together.

On startup, `main.py`'s lifespan hook creates a superuser
(`FIRST_SUPERUSER`/`FIRST_SUPERUSER_PASSWORD`) if one doesn't exist yet.

## Testing

```
uv run pytest
```

Tests use `mongomock-motor` (see `tests/conftest.py`) — no real MongoDB
required. Ran the full suite: **123 passed, 9 failed** (pre-existing, in
`tests/test_api/test_products.py` — see "Known issues" below; unrelated to
the allergen feature, all of whose tests pass).

## API

All paths are prefixed with `/api/v1`.

### Auth / users
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/users/` | none | Register `{name, email, password}`. 201, 409 on duplicate email. |
| POST | `/login/access-token` | none | OAuth2 password form (`username`=email). Returns `{access_token, token_type}`. |
| GET | `/users/me` | bearer | Current user. |
| PATCH | `/users/me` | bearer | Update `name`/`avatar_url`. |
| DELETE | `/users/me` | bearer | Delete current user. |
| GET | `/users` | none | List users (`limit`, `offset`). |
| GET/PUT/DELETE | `/users/{userid}` | none | Fetch/replace/delete a user by uuid. |

### Products
| Method | Path | Notes |
|---|---|---|
| POST | `/products/` | Create manual product. 409 on duplicate barcode. |
| POST | `/products/list_of_products` | Filtered list; body `{brand?, product_name?, allergens?}`, query `limit`/`offset`. |
| GET | `/products/brands` | Distinct brand list. **Currently broken** — see below. |
| GET | `/products/get_by_id/{product_id}` | 404 if missing. |
| GET | `/products/get_by_barcode/{product_barcode}` | 404 if missing. |

### User properties
| Method | Path | Notes |
|---|---|---|
| GET/PUT | `/user-properties/allergies/{userid}` | Fetch/replace a user's allergy list. |
| POST | `/user-properties/allergies` | Create (400 if one already exists for that user). |
| GET | `/user-properties/scan-history/users/{userid}` | All scans for a user. |
| POST | `/user-properties/scan-history` | Record a scan. |
| GET | `/user-properties/scan-history/products/{product_id}` | Scans for a product (`limit`, default 20, max 100). |

### Allergens (new)
| Method | Path | Notes |
|---|---|---|
| POST | `/allergens/check` | Body `{barcode, ingredients: [str], user_id?}`. See below. |

**What it does:** looks up a cached `AllergenProfile` by barcode; if none
exists, runs `ingredients` through `services/allergen_detection.py` (matches
free-text terms against `app/data/allergen_reference.json` by substring, e.g.
"whey" -> milk, "wheat flour" -> gluten) and saves the result. If `user_id`
is given, the user's `AllergyPreference.allergies` are matched through the
same detector, and any overlap with the product's detected allergens is
returned as `matched_user_allergens` with `warning: true`.

Response: `{profile: {id, barcode, detected_allergens: [{allergen,
display_name, triggered_by}], detection_source, created_at, updated_at},
from_cache, matched_user_allergens, warning}`.

Covered by `tests/test_services/test_allergen_detection.py` (matcher logic:
synonym matching, multi-trigger collection, embedded-substring matches,
blank input) and `tests/test_api/test_allergens.py` (cache reuse, user
allergy cross-check, no-warning path) — 9 tests, all passing.

## Known issues (pre-existing, not part of the allergen feature)

- **`GET /products/brands` is broken**: calls
  `models.Product.find_all().distinct("brand")`, but the installed Beanie
  version's `FindMany` has no `.distinct()`. Raises `AttributeError` at
  request time. Needs `.distinct(key)` from the underlying pymongo
  collection, or a manual `{x async for x in ...}` fallback.
- **`tests/test_api/test_products.py` assumes a different route contract**
  than what's implemented (e.g. `GET /products/{barcode}` vs the actual
  `GET /products/get_by_barcode/{product_barcode}`, and query-param search
  vs the actual `POST /products/list_of_products`). 8 of its 9 failures are
  this mismatch, not bugs; the 9th (`GetBrands`) is the `.distinct()` bug
  above. See `tests/README.md` for the originally-assumed contract.
