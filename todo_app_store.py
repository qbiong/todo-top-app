"""数据层 — 待办事项 JSON 持久化"""

import json
import os
from datetime import datetime


class TodoStore:
    def __init__(self, filepath):
        self.filepath = filepath
        self.todos = []  # [{id, text, done, created_at}]
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.todos = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.todos = []

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"保存失败: {e}")

    def add(self, text):
        text = text.strip()
        if not text:
            return None
        todo = {
            "id": datetime.now().strftime("%y%m%d%H%M%S%f"),
            "text": text,
            "done": False,
            "created_at": datetime.now().isoformat(),
        }
        self.todos.append(todo)
        self._save()
        return todo

    def toggle(self, todo_id):
        for t in self.todos:
            if t["id"] == todo_id:
                t["done"] = not t["done"]
                self._save()
                return True
        return False

    def delete(self, todo_id):
        self.todos = [t for t in self.todos if t["id"] != todo_id]
        self._save()

    def clear_done(self):
        self.todos = [t for t in self.todos if not t["done"]]
        self._save()

    def get_pending(self):
        return [t for t in self.todos if not t["done"]]

    def get_done(self):
        return [t for t in self.todos if t["done"]]
