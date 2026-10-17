import json
import os
from datetime import datetime, timezone

import firebase_admin
from fastapi import HTTPException
from firebase_admin import credentials, firestore


def db():
    try:
        firebase_admin.get_app()
    except ValueError:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        try:
            if raw:
                credential = credentials.Certificate(json.loads(raw))
            elif path:
                credential = credentials.Certificate(path)
            else:
                raise HTTPException(503, "Firestore 자격 증명이 설정되지 않았습니다")
            firebase_admin.initialize_app(credential)
        except HTTPException:
            raise
        except (ValueError, TypeError, OSError, KeyError) as exc:
            raise HTTPException(503, "Firestore 자격 증명을 확인해 주세요") from exc
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
    client = db()
    collection = client.collection("data")
    ref = collection.document(id)
    if not ref.get().exists:
        return None
    if id != item.date.isoformat() and collection.document(item.date.isoformat()).get().exists:
        raise ValueError("date already exists")
    payload = item.model_dump(mode="json")
    target = collection.document(item.date.isoformat())
    batch = client.batch()
    batch.set(target, payload)
    if id != target.id:
        batch.delete(ref)
    batch.commit()
    return {**payload, "id": target.id}


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
