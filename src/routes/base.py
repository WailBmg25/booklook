from fastapi import FastAPI, APIRouter, Depends
from helpers import get_settings, Settings
base_router = APIRouter(
    prefix="/api/v1",
    tags=["base"]
)

@base_router.get("/")
async def test_message(app_settings: Settings = Depends(get_settings)):
    
    app_name = app_settings.APP_NAME
    app_version = app_settings.VERSION
    return {"message": f"Welcome to {app_name} v{app_version}!"}
