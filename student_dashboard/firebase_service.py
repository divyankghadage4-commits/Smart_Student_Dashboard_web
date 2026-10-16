"""Lazy Firebase Admin SDK integration.

Uses environment-provided service-account credentials. Never store private keys in source.
The web Firebase config is not a substitute for server credentials.
"""
import json
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_firebase_services():
    """Return (Firestore client, Storage bucket); raises a useful error if not configured."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
    except ImportError as exc:
        raise RuntimeError("firebase-admin is not installed; install requirements.txt") from exc

    project_id = os.environ.get("FIREBASE_PROJECT_ID", "aihack-71875")
    bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET", "aihack-71875.firebasestorage.app")
    app = None
    try:
        app = firebase_admin.get_app()
    except ValueError:
        raw_credentials = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if raw_credentials:
            try:
                service_account_info = json.loads(raw_credentials)
            except json.JSONDecodeError as exc:
                raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON must contain valid JSON") from exc
            cred = credentials.Certificate(service_account_info)
        elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        else:
            raise RuntimeError(
                "Firebase server credentials are not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON "
                "in your hosting secrets or configure GOOGLE_APPLICATION_CREDENTIALS."
            )
        options = {"projectId": project_id}
        if bucket_name:
            options["storageBucket"] = bucket_name
        app = firebase_admin.initialize_app(cred, options)

    return firestore.client(app=app), storage.bucket(name=bucket_name, app=app)
