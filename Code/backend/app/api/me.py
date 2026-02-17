from fastapi import APIRouter, Depends
from app.utils.auth.auth import get_current_user
from app.utils.auth.user_service import ensure_user_exists

router = APIRouter(prefix="/auth_test")

@router.get("/me")
async def test_auth(user=Depends(get_current_user)):

    uid = await ensure_user_exists(user)

    return {
        "user_id": uid,
        "email": user.get("email")
    }
