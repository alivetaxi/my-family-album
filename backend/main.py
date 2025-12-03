import os
import json
from datetime import timedelta

from google.cloud import storage, secretmanager
from google.cloud.firestore_v1 import SERVER_TIMESTAMP, Query
from firebase_admin import auth, firestore, initialize_app, credentials
import firebase_admin


def init_firebase():
    # Initialize firebase_admin. Prefer using Secret Manager if FIREBASE_ADMIN_SECRET_NAME provided.
    if len(firebase_admin._apps) > 0:
        return
    secret_name = os.environ.get("FIREBASE_ADMIN_SECRET_NAME")
    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if secret_name and project:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project}/secrets/{secret_name}/versions/latest"
            resp = client.access_secret_version(request={"name": name})
            key_json = resp.payload.data.decode("utf-8")
            cred = credentials.Certificate(json.loads(key_json))
            initialize_app(cred)
            return
        except Exception:
            # fallback to default credentials if secret access fails
            pass
    initialize_app()

def init_service_account_info():
    secret_name = os.environ.get("SERVICE_ACCOUNT_SECRET_NAME")
    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if secret_name and project:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project}/secrets/{secret_name}/versions/latest"
            resp = client.access_secret_version(request={"name": name})
            key_json = resp.payload.data.decode("utf-8")
            return json.loads(key_json)
        except Exception:
            pass
    return None


init_firebase()
db = firestore.client()
# Initialize storage client
sa_info = init_service_account_info()
storage_client = storage.Client.from_service_account_info(sa_info)


def _get_cors_origin(request):
    """Get the appropriate CORS origin to return based on request origin."""
    allowed = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    allowed = [o.strip() for o in allowed]
    origin = request.headers.get("Origin", "")
    if origin in allowed or "*" in allowed:
        return origin or allowed[0]
    return allowed[0] if allowed else "*"


def _cors_headers(request):
    """Return standard CORS headers for the request."""
    return {"Access-Control-Allow-Origin": _get_cors_origin(request)}


def _unauthorized(msg="Unauthorized"):
    return (json.dumps({"error": msg}), 401, {"Content-Type": "application/json"})


def _bad_request(msg="Bad request"):
    return (json.dumps({"error": msg}), 400, {"Content-Type": "application/json"})


def verify_id_token_from_request(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    id_token = auth_header.split(" ", 1)[1]
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None


def api(request):
    """
    Single HTTP function to handle a small REST API for albums and photos.

    Endpoints:
      GET  /albums
      POST /albums   (admin only) JSON: {"title": "...", "description": "..."}
      GET  /albums/{album_id}/photos
      POST /generate_upload_url  JSON: {"album_id":"...", "filename":"..."}
      POST /photos  JSON: {"album_id":"...", "filename":"...","public_url":"...","metadata":{}}

    Authentication: send Firebase ID token in `Authorization: Bearer <idToken>` header.
    """
    path = request.path or "/"
    # normalize path to remove optional /api prefix used by frontend
    if path.startswith("/api"):
        path = path[4:]
    method = request.method

    # simple auth check for endpoints that need a user
    user = verify_id_token_from_request(request)

    # CORS preflight
    if request.method == "OPTIONS":
        headers = _cors_headers(request)
        headers.update({
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
        })
        return ("", 204, headers)

    # Runtime config endpoint for frontend (non-sensitive)
    if method == "GET" and path.endswith("/config"):
        # Return firebase client config from env vars or JSON
        client_config = os.environ.get("FIREBASE_CLIENT_CONFIG")
        if client_config:
            try:
                cfg = json.loads(client_config)
                headers = {"Content-Type": "application/json"}
                headers.update(_cors_headers(request))
                return (json.dumps(cfg), 200, headers)
            except Exception:
                pass
        # fallback to individual env vars
        cfg = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps(cfg), 200, headers)

    # List albums
    if method == "GET" and path.endswith("/albums"):
        albums_ref = db.collection("albums").order_by("created_at", direction=Query.DESCENDING)
        docs = albums_ref.stream()
        items = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            data["created_at"] = data["created_at"].isoformat()
            # try to include a cover photo (first photo)
            photos = db.collection("albums").document(d.id).collection("photos").order_by("created_at", direction=Query.DESCENDING).limit(1).stream()
            cover = None
            for p in photos:
                pd = p.to_dict()
                cover = pd.get("public_url")
            data["cover_url"] = cover
            items.append(data)
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"albums": items}), 200, headers)

    # Create album (require admin custom claim)
    if method == "POST" and path.endswith("/albums"):
        if not user:
            return _unauthorized()
        # require admin claim
        if not user.get("admin"):
            return _unauthorized("Admin only")
        payload = request.get_json(silent=True)
        if not payload or "title" not in payload:
            return _bad_request("Missing title")
        doc = db.collection("albums").document()
        payload.setdefault("description", "")
        payload["created_by"] = user.get("uid")
        payload["created_at"] = SERVER_TIMESTAMP
        doc.set(payload)
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"id": doc.id}), 201, headers)

    # List photos for album
    if method == "GET" and "/albums/" in path and path.endswith("/photos"):
        parts = path.split("/")
        # path like /albums/{id}/photos
        try:
            album_id = parts[2]
        except Exception:
            return _bad_request("Invalid path")
        photos_ref = db.collection("albums").document(album_id).collection("photos").order_by("created_at", direction=Query.DESCENDING)
        docs = photos_ref.stream()
        items = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            items.append(data)
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"photos": items}), 200, headers)

    # Generate signed upload URL (authenticated users)
    # generate signed URLs for single or multiple files
    if method == "POST" and path.endswith("/generate_upload_urls"):
        if not user:
            return _unauthorized()
        payload = request.get_json(silent=True)
        if not payload or "album_id" not in payload or ("filenames" not in payload and "filename" not in payload):
            return _bad_request("Missing album_id or filenames")
        bucket_name = os.environ.get("IMAGES_BUCKET")
        if not bucket_name:
            return _bad_request("Server not configured: IMAGES_BUCKET")
        bucket = storage_client.bucket(bucket_name)
        results = []
        filenames = []
        if "filenames" in payload:
            filenames = payload["filenames"]
        else:
            filenames = [payload["filename"]]
        for fname in filenames:
            blob_path = f"albums/{payload['album_id']}/{user.get('uid')}/{fname}"
            blob = bucket.blob(blob_path)
            url = blob.generate_signed_url(expiration=timedelta(minutes=15), method="PUT", version="v4", content_type=payload.get("content_type", "application/octet-stream"))
            results.append({"filename": fname, "upload_url": url, "blob_path": blob_path})
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"results": results}), 200, headers)

    # Register photo metadata after upload
    if method == "POST" and path.endswith("/photos"):
        if not user:
            return _unauthorized()
        payload = request.get_json(silent=True)
        if not payload or "album_id" not in payload or "blob_path" not in payload:
            return _bad_request("Missing album_id or blob_path")
        album_id = payload["album_id"]
        photo_doc = db.collection("albums").document(album_id).collection("photos").document()
        data = {
            "filename": payload.get("filename"),
            "blob_path": payload.get("blob_path"),
            "public_url": payload.get("public_url"),
            "created_by": user.get("uid"),
            "created_at": SERVER_TIMESTAMP,
        }
        if "metadata" in payload:
            data["metadata"] = payload["metadata"]
        photo_doc.set(data)
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"id": photo_doc.id}), 201, headers)

    # Get album metadata
    if method == "GET" and path.startswith("/albums/") and path.count("/") == 2:
        # /albums/{id}
        parts = path.split("/")
        album_id = parts[2]
        doc = db.collection("albums").document(album_id).get()
        if not doc.exists:
            headers = {"Content-Type": "application/json"}
            headers.update(_cors_headers(request))
            return (json.dumps({"error": "Not found"}), 404, headers)
        data = doc.to_dict()
        data["id"] = doc.id
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps(data), 200, headers)

    # Delete album (admin only): only if no photos
    if method == "DELETE" and path.startswith("/albums/") and path.count("/") == 2:
        if not user:
            return _unauthorized()
        if not user.get("admin"):
            return _unauthorized("Admin only")
        parts = path.split("/")
        album_id = parts[2]
        photos_ref = db.collection("albums").document(album_id).collection("photos").limit(1).stream()
        for _ in photos_ref:
            headers = {"Content-Type": "application/json"}
            headers.update(_cors_headers(request))
            return (json.dumps({"error": "Album has photos and cannot be deleted"}), 400, headers)
        # safe to delete
        db.collection("albums").document(album_id).delete()
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"ok": True}), 200, headers)

    # Photo detail
    if method == "GET" and path.startswith("/photos/"):
        # /photos/{album_id}/{photo_id}
        parts = path.split("/")
        if len(parts) < 4:
            return _bad_request("Invalid path")
        album_id = parts[2]
        photo_id = parts[3]
        doc = db.collection("albums").document(album_id).collection("photos").document(photo_id).get()
        if not doc.exists:
            headers = {"Content-Type": "application/json"}
            headers.update(_cors_headers(request))
            return (json.dumps({"error": "Not found"}), 404, headers)
        data = doc.to_dict()
        data["id"] = doc.id
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps(data), 200, headers)

    # Update photo description (admin only)
    if method in ("PUT", "PATCH") and path.startswith("/photos/") and path.endswith("/description"):
        if not user:
            return _unauthorized()
        if not user.get("admin"):
            return _unauthorized("Admin only")
        # /photos/{album_id}/{photo_id}/description
        parts = path.split("/")
        if len(parts) < 5:
            return _bad_request("Invalid path")
        album_id = parts[2]
        photo_id = parts[3]
        payload = request.get_json(silent=True)
        if not payload or "description" not in payload:
            return _bad_request("Missing description")
        db.collection("albums").document(album_id).collection("photos").document(photo_id).update({"description": payload["description"]})
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"ok": True}), 200, headers)

    # Delete photo (admin only)
    if method == "DELETE" and path.startswith("/photos/"):
        if not user:
            return _unauthorized()
        if not user.get("admin"):
            return _unauthorized("Admin only")
        # /photos/{album_id}/{photo_id}
        parts = path.split("/")
        if len(parts) < 4:
            return _bad_request("Invalid path")
        album_id = parts[2]
        photo_id = parts[3]
        doc_ref = db.collection("albums").document(album_id).collection("photos").document(photo_id)
        doc = doc_ref.get()
        if not doc.exists:
            headers = {"Content-Type": "application/json"}
            headers.update(_cors_headers(request))
            return (json.dumps({"error": "Not found"}), 404, headers)
        data = doc.to_dict()
        # delete blob if exists
        bucket_name = os.environ.get("IMAGES_BUCKET")
        if bucket_name and data.get("blob_path"):
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(data.get("blob_path"))
            try:
                blob.delete()
            except Exception:
                pass
        doc_ref.delete()
        headers = {"Content-Type": "application/json"}
        headers.update(_cors_headers(request))
        return (json.dumps({"ok": True}), 200, headers)

    headers = {"Content-Type": "application/json"}
    headers.update(_cors_headers(request))
    return (json.dumps({"error": "Not found"}), 404, headers)


# For Google Cloud Functions entrypoint compatibility
def main(request):
    return api(request)

