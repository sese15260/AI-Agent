import json
import os
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore


def db():
    if not firebase_admin._apps:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if raw:
            credential = credentials.Certificate(json.loads(raw))
        elif path:
            credential = credentials.Certificate(path)
        else:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH is required")
        firebase_admin.initialize_app(credential)
    return firestore.client()


def data_list():
    return sorted(({**doc.to_dict(), "id": doc.id} for doc in db().collection("data").stream()), key=lambda x: x["date"])


def data_create(item):
    payload = item.model_dump(mode="json")
    ref = db().collection("data").document(item.date.isoformat())
    if ref.get().exists:
        return None
    ref.set(payload)
    return {**payload, "id": ref.id}


def data_update(id, item):
    ref = db().collection("data").document(id)
    if not ref.get().exists:
        return None
    if id != item.date.isoformat() and db().collection("data").document(item.date.isoformat()).get().exists:
        raise ValueError("date already exists")
    if id != item.date.isoformat():
        ref.delete()
        ref = db().collection("data").document(item.date.isoformat())
    payload = item.model_dump(mode="json")
    ref.set(payload)
    return {**payload, "id": ref.id}


def data_delete(id):
    ref = db().collection("data").document(id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True


def conversations_list():
    rows = [{**doc.to_dict(), "id": doc.id} for doc in db().collection("conversations").stream()]
    return sorted(rows, key=lambda x: x.get("updated_at", ""), reverse=True)


def conversation_get(id):
    doc = db().collection("conversations").document(id).get()
    return {**doc.to_dict(), "id": doc.id} if doc.exists else None


def conversation_save(title, messages, id=None):
    ref = db().collection("conversations").document(id) if id else db().collection("conversations").document()
    payload = {"title": title, "messages": messages, "updated_at": datetime.now(timezone.utc).isoformat()}
    ref.set(payload)
    return {**payload, "id": ref.id}


def conversation_delete(id):
    ref = db().collection("conversations").document(id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
