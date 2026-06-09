import os
import json
import hashlib
from datetime import datetime
from typing import Any


class VectorMemory:
    def __init__(self, storage_path: str = "memory/vectors"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _file_path(self) -> str:
        return os.path.join(self.storage_path, "vectors.json")

    def _load_all(self) -> list[dict]:
        path = self._file_path()
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return json.load(f)

    def _save_all(self, items: list[dict]):
        path = self._file_path()
        with open(path, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def _simple_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def store(self, text: str, metadata: dict | None = None):
        items = self._load_all()
        entry = {
            "id": self._simple_hash(text),
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        for i, item in enumerate(items):
            if item["id"] == entry["id"]:
                items[i] = entry
                break
        else:
            items.append(entry)
        self._save_all(items)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        items = self._load_all()
        query_lower = query.lower()
        scored = []
        for item in items:
            score = sum(
                1 for word in query_lower.split()
                if word in item["text"].lower()
            )
            if score > 0 or query_lower in item["text"].lower():
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def delete(self, text_id: str):
        items = self._load_all()
        items = [item for item in items if item["id"] != text_id]
        self._save_all(items)
