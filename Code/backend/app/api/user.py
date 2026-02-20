import time
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth.auth import get_current_user
from app.core.db import users as users_collection
from app.models.user import UserModel


router = APIRouter(prefix="/user", tags=["user"])


@router.post("/create", response_model=UserModel)
async def create_user(
    full_name: str,
    user=Depends(get_current_user)
):

    uid = user["uid"]
    email = user.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    existing = await users_collection.find_one({"_id": uid})

    if existing:
        return UserModel(
            uid=existing["_id"],
            email=existing["email"],
            full_name=existing["full_name"],
            created_at=existing["created_at"]
        )

    user_doc = {
        "_id": uid,
        "email": email,
        "full_name": full_name,
        "created_at": int(time.time() * 1000)
    }

    await users_collection.insert_one(user_doc)

    return UserModel(
        uid=uid,
        email=email,
        full_name=full_name,
        created_at=user_doc["created_at"]
    )

@router.get("/me", response_model=UserModel)
async def get_user(
    user=Depends(get_current_user)
):
    uid = user["uid"]

    existing = await users_collection.find_one({"_id": uid})

    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    return UserModel(
        uid=existing["_id"],
        email=existing["email"],
        full_name=existing["full_name"],
        created_at=existing["created_at"]
    )