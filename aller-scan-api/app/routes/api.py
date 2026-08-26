from fastapi import APIRouter

from . import login, products, userProperties, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(
    userProperties.router, prefix="/user-properties", tags=["user-properties"]
)
api_router.include_router(products.router, prefix="/products", tags=["products"])


@api_router.get("/")
async def root():
    return {"message": "Backend API for FARM-docker operational !"}