# Tests

These are black-box tests written against models that already exist
(`app/models/*`) and route files that are currently empty stubs
(`app/routes/*`). Since there's no existing API contract to test against,
the API-level tests (`tests/test_api/`) encode an **assumed** contract —
implement the routes to make them pass. The model-level tests
(`tests/test_models/`) test `app/models/*` directly and don't depend on any
route implementation.

Run with:

```
uv run pytest
```

No real MongoDB is required — tests use an in-memory mock
(`mongomock-motor`) wired into Beanie via the `mongo_db` fixture in
`conftest.py`.

## Known pre-existing issues (unrelated to missing routes)

These will block tests from passing (some even from collecting/running)
independent of any route implementation work, and should probably be
resolved first:

1. **`app/config.py` vs `app/config/` package collision.** Both
   `app/config.py` (empty) and `app/config/` (a package with its own
   `config.py`) exist. Python resolves `app.config` to the package, so
   `app/db.py`'s `from app.config import settings` currently can't find
   `settings` (since `app/config/__init__.py` is empty). Looks like a
   mid-migration leftover — `app/config.py` was probably meant to be
   deleted once `app/config/config.py` replaced it, and `app/db.py`
   updated to `from app.config.config import settings`.
2. **`app/auth/auth.py`: `ALGORITHM = "H256"`** is not a valid JWT
   algorithm name (`python-jose` will reject it) — this looks like a typo
   for `"HS256"`.
3. **`User` model has no `password` field**, but `app/auth/auth.py`'s
   `authenticate_user()` already reads `user.password`. The tests assume a
   required, hashed `password` field will be added to the model, and that
   it is never included in any API response.

## Assumed route contract

All paths are prefixed with `settings.API_V1_STR` (`/api/v1`).

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/users/` | none | Register. Body: `{name, email, password}`. 201, never returns the password. 409 on duplicate email. |
| POST | `/login/access-token` | none | OAuth2 password flow (form body: `username`=email, `password`). 200 `{access_token, token_type}`. 401 on bad credentials, 400 if user inactive. |
| GET | `/users/me` | required | Current user's profile. |
| PATCH | `/users/me` | required | Partial update of `name`/`avatar_url`. `email` not editable here. |
| POST | `/products/` | required | Create a manual product. Body matches `Product` fields (minus `id`/`source`/`created_at`). 409 on duplicate barcode. |
| GET | `/products/{barcode}` | none | Lookup by barcode. 404 if not found. |
| GET | `/products/` | none | List/search. Query params: `q` (name substring), `limit`, `skip`. |
| GET | `/user-properties/allergies` | required | Current user's `AllergyPreference`. Auto-vivifies to `{allergies: []}` if none saved yet. |
| PUT | `/user-properties/allergies` | required | Replaces (not merges) the allergy list. Body: `{allergies: [str]}`. |
| GET | `/user-properties/scan-history` | required | Current user's `ScanHistory` entries only. |
| POST | `/user-properties/scan-history` | required | Record a scan. Body matches `ScanHistory` fields (minus `id`/`user_id`/`created_at`); `user_id` comes from the auth token, not the client. |
| GET | `/user-properties/scan-history/{id}` | required | Single scan. 404/403 if it belongs to another user. |

Status codes and exact paths are reasonable defaults, not hard requirements
from the models — if you'd rather use different (but still sensible)
conventions, feel free to adjust the tests to match as you build.
