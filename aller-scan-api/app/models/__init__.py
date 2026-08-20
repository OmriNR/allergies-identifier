from app.models.product import Product, ProductSource
from app.models.user import User
from app.models.user_properties import AllergyPreference, ScanHistory, ScanStatus

DOCUMENT_MODELS = [User, ScanHistory, AllergyPreference, Product]

__all__ = [
    "AllergyPreference",
    "DOCUMENT_MODELS",
    "Product",
    "ProductSource",
    "ScanHistory",
    "ScanStatus",
    "User",
]
