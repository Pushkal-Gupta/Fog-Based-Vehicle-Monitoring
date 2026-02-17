import firebase_admin
from firebase_admin import credentials, auth
try:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
    print('Firebase initialized successfully.')
except FileNotFoundError:
    print('Could not find the json file...')


def verify_firebase_token(id_token: str):
    decoded_token = auth.verify_id_token(id_token)
    return decoded_token
