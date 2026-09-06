from fastapi import APIRouter

from .. import models, schemas
from ..services.allergen_detection import get_or_create_profile, matched_user_allergens

router = APIRouter()


@router.post("/check", response_model=schemas.AllergenCheckResponse)
async def check_allergens(check_in: schemas.AllergenCheckRequest):
    """Look up the cached allergen profile for a barcode, or detect and
    save one from the given ingredients. Then, if a user_id is given,
    cross-check the detected allergens against that user's allergy
    preferences and flag a warning on any match.
    """
    profile = await models.AllergenProfile.find_one({"barcode": check_in.barcode})
    from_cache = profile is not None
    if profile is None:
        profile = await get_or_create_profile(check_in.barcode, check_in.ingredients)

    matched = await matched_user_allergens(profile, check_in.user_id)

    return schemas.AllergenCheckResponse(
        profile=profile,
        from_cache=from_cache,
        matched_user_allergens=matched,
        warning=bool(matched),
    )
