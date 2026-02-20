from fastapi import Header, HTTPException
from app.core.firebase import verify_firebase_token


async def get_current_user(authorization: str = Header(...)):

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]

    try:
        decoded = verify_firebase_token(token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
