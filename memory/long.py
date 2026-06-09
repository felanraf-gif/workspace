import os
import json
from datetime import datetime
from typing import Any


class LongMemory:
    def __init__(self, storage_path: str = "memory/long_term"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _file_path(self, key: str) -> str:
        safe = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_path, f"{safe}.json")

    def save(self, key: str, data: Any):
        path = self._file_path(key)
        entry = {"key": key, "data": data, "updated": datetime.now().isoformat()}
        with open(path, "w") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)

    def load(self, key: str) -> Any | None:
        path = self._file_path(key)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            entry = json.load(f)
        return entry["data"]

    def delete(self, key: str):
        path = self._file_path(key)
        if os.path.exists(path):
            os.remove(path)

    def list_keys(self) -> list[str]:
        files = os.listdir(self.storage_path)
        return [f.replace(".json", "") for f in files if f.endswith(".json")]
