from app.models.product import Product, ProductSource
from app.models.user import User
from app.models.user_properties import AllergyPreference, ScanHistory, ScanStatus
from app.models.resteraunt import Resteraunt, Location, MenuItem

DOCUMENT_MODELS = [User, ScanHistory, AllergyPreference, Product, Resteraunt]

__all__ = [
    "AllergyPreference",
    "DOCUMENT_MODELS",
    "Location",
    "MenuItem",
    "Product",
    "ProductSource",
    "Resteraunt",
    "ScanHistory",
    "ScanStatus",
    "User",
]
