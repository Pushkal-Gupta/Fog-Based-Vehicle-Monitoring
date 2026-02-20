import json
import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings

def initialize_firebase():

    if firebase_admin._apps:
        return

    firebase_credentials = settings.FIREBASE

    if not firebase_credentials:
        raise Exception("FIREBASE environment variable not set")

    try:
        cred_dict = json.loads(firebase_credentials)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")

    except Exception as e:
        raise Exception(f"Firebase initialization failed: {e}")


initialize_firebase()


def verify_firebase_token(id_token: str):
    return auth.verify_id_token(id_token)