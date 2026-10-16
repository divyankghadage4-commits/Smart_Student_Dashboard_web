"""Server-side helpers for private Supabase Storage and Firebase Firestore.

Credentials are read only from environment variables. This module deliberately does
not embed service keys. Supabase server-side access requires SUPABASE_SECRET_KEY.
"""
import json
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_supabase_client():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    if not url or not key or key.startswith("replace-with"):
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SECRET_KEY in environment secrets.")
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("Install dependencies with pip install -r requirements.txt") from exc
    return create_client(url, key)

@lru_cache(maxsize=1)
def get_firestore_client():
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
    if not project_id or project_id.startswith("replace-with"):
        raise RuntimeError("Set FIREBASE_PROJECT_ID to the new Firebase project ID.")
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise RuntimeError("firebase-admin is missing; install requirements.txt") from exc
    try:
        app = firebase_admin.get_app()
    except ValueError:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if raw:
            try:
                info = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON must be valid JSON.") from exc
            cred = credentials.Certificate(info)
        elif path:
            cred = credentials.Certificate(path)
        else:
            raise RuntimeError("Set Firebase service-account credentials in your hosting secret manager.")
        app = firebase_admin.initialize_app(cred, {"projectId": project_id})
    return firestore.client(app=app)


def upload_private_file(file_obj, object_path, content_type=None):
    """Upload a file-like object to the configured private Supabase bucket."""
    bucket = os.environ.get("SUPABASE_BUCKET", "student-files")
    options = {"upsert": "true"}
    if content_type:
        options["content-type"] = content_type
    response = get_supabase_client().storage.from_(bucket).upload(object_path, file_obj, options)
    return response


def create_private_download_url(object_path, expires_in=120):
    """Create a short-lived signed URL. Caller must authorize access first."""
    bucket = os.environ.get("SUPABASE_BUCKET", "student-files")
    result = get_supabase_client().storage.from_(bucket).create_signed_url(object_path, expires_in)
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url")
    return getattr(result, "signed_url", None)
