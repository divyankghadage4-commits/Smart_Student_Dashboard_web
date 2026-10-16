# Student Dashboard — deployment and cloud integration setup

This package preserves the existing Flask dashboard and adds optional server-side integration APIs for Supabase private Storage and Firebase Firestore. Cloud APIs require credentials and Firebase/Supabase project setup before they work. Existing local upload routes remain unchanged for backward compatibility.

## 1. Install locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in values. Do not commit `.env`.

## 2. Supabase Storage

- Project URL: `https://pfxltaamgkzidtjalscw.supabase.co`
- Bucket: `student-files`
- Keep the bucket private.
- `SUPABASE_KEY`/`sb_publishable_...` is not sufficient for this Flask server to bypass private-bucket RLS. Set `SUPABASE_SECRET_KEY` using a server-side secret from Supabase API settings (never expose it to the browser or commit it). If your project only shows a newer `sb_secret_...` key, use that server-only key.
- Restrict access to this key in your hosting environment and rotate it if exposed.

Added endpoints:
- `POST /api/cloud-files/upload` — authenticated user uploads a permitted file into a namespaced private path. Multipart field: `file`.
- `POST /api/cloud-files/signed-url` — JSON `{ "object_path": "student/<your-session-id>/<file>" }`; returns a 120-second signed URL after a basic ownership check. Admin sessions can access paths.

These are additive APIs; the existing dashboard UI has not yet been rewired to use them, so current legacy upload controls still use their existing local paths. Integrate the APIs into the UI after verifying them in your deployment.

## 3. Firebase Firestore

Use the Firebase project you created for the dashboard. Set `FIREBASE_PROJECT_ID` to the actual project ID shown in Firebase Console. Create Firestore in Production mode. For server access, configure a service account in your host's secret manager as `FIREBASE_SERVICE_ACCOUNT_JSON` (the entire JSON value) or set `GOOGLE_APPLICATION_CREDENTIALS` to a secure file path. Never put service-account credentials in frontend code or Git.

Added endpoint: `GET/POST /api/messages`. It uses Firestore collection `conversations/{conversation_id}/messages`; request body for POST: `{ "conversation_id": "general", "message": "Hello" }`. This is a basic authenticated messaging API, not yet connected to the dashboard UI. Add and test conversation-level authorization/rules before using it with real student data; do not assume any conversation ID is private.

## 4. Production deployment

- Set `SECRET_KEY` to a unique long random value in hosting secrets.
- Configure `DATABASE_URL` to a persistent production database if the host filesystem is ephemeral. The bundled SQLite file is for local use and is not reliable persistence on many hosting platforms.
- Start command: `gunicorn app:app` (Procfile is included).
- Do not deploy real student data until role checks, database persistence, backup/restore, and cloud API tests are complete.

## 5. Verification

Run `python -m py_compile app.py cloud_integrations.py` and `pip install -r requirements.txt`. Then test login, existing routes, upload size/type checks, private bucket access, signed URL expiration, Firestore messages, and separate student/admin permissions. Real cloud connectivity cannot be verified until your secret keys and new Firebase service-account credentials are configured.
