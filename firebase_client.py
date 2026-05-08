import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

_db = None

def get_db() -> firestore.Client:
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cert_path = os.getenv("FIREBASE_CREDENTIALS")
            if not cert_path:
                raise RuntimeError("FIREBASE_CREDENTIALS 환경변수가 설정되지 않았습니다")
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db
