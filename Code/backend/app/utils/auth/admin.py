import os
from fastapi import Header, HTTPException
from app.core.config import settings

async def verify_admin(x_admin_key: str = Header(...)):

    if x_admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail=f'Unauthorized')

    return True
