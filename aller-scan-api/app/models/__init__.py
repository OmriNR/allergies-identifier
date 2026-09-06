from app.models.allergen_profile import AllergenProfile, DetectedAllergen
from app.models.product import Product, ProductSource
from app.models.user import User
from app.models.user_properties import AllergyPreference, ScanHistory, ScanStatus

DOCUMENT_MODELS = [User, ScanHistory, AllergyPreference, Product, AllergenProfile]

__all__ = [
    "AllergenProfile",
    "AllergyPreference",
    "DetectedAllergen",
    "DOCUMENT_MODELS",
    "Product",
    "ProductSource",
    "ScanHistory",
    "ScanStatus",
    "User",
]
