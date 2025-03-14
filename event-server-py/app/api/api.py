from fastapi import APIRouter

from app.api.endpoints import character

api_router = APIRouter()


@api_router.get("/", include_in_schema=False)
async def root():
    return {"message": "Yo! Check /docs for API documentation"}


api_router.include_router(character.router, prefix="/character", tags=["Character"])
