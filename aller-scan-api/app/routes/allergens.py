from fastapi import APIRouter

from .. import models, schemas
from ..services.allergen_detection import DETECTION_SOURCE, detect_allergens

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
        matches = detect_allergens(check_in.ingredients)
        profile = models.AllergenProfile(
            barcode=check_in.barcode,
            detected_allergens=[
                models.DetectedAllergen(
                    allergen=match.allergen,
                    display_name=match.display_name,
                    triggered_by=match.triggered_by,
                )
                for match in matches
            ],
            detection_source=DETECTION_SOURCE,
        )
        await profile.create()

    matched_user_allergens: list[str] = []
    if check_in.user_id is not None:
        preference = await models.AllergyPreference.find_one({"user_id": check_in.user_id})
        if preference is not None:
            user_allergen_keys = {match.allergen for match in detect_allergens(preference.allergies)}
            matched_user_allergens = [
                detected.display_name
                for detected in profile.detected_allergens
                if detected.allergen in user_allergen_keys
            ]

    return schemas.AllergenCheckResponse(
        profile=profile,
        from_cache=from_cache,
        matched_user_allergens=matched_user_allergens,
        warning=bool(matched_user_allergens),
    )
