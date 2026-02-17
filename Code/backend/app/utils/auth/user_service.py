import time
from app.core.db import users


async def ensure_user_exists(decoded_token):

    uid = decoded_token["uid"]
    email = decoded_token.get("email")

    existing = await users.find_one({"_id": uid})

    if not existing:
        await users.insert_one({
            "_id": uid,
            "email": email,
            "created_at": int(time.time() * 1000)
        })

    return uid
