import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import database
from app.models import User
from app.ui import INDEX_HTML

USER_RE = re.compile(r"^/users/(\d+)$")


def serialize(user):
    return {"id": user.id, "name": user.name, "email": user.email}


class Handler(BaseHTTPRequestHandler):
    # --- helpers (all hand-written; a framework would provide these) ---
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw or b"{}")

    # --- routing ---
    def do_GET(self):
        if self.path == "/":
            return self._send_html(INDEX_HTML)
        if self.path == "/health":
            return self._send_json(200, {"status": "ok"})
        if self.path == "/users":
            session = database.SessionLocal()
            try:
                users = session.query(User).all()
                return self._send_json(200, [serialize(u) for u in users])
            finally:
                session.close()
        m = USER_RE.match(self.path)
        if m:
            session = database.SessionLocal()
            try:
                user = session.get(User, int(m.group(1)))
                if user is None:
                    return self._send_json(404, {"detail": "User not found"})
                return self._send_json(200, serialize(user))
            finally:
                session.close()
        self._send_json(404, {"detail": "Not found"})

    def do_POST(self):
        if self.path == "/users":
            try:
                data = self._read_json()
            except json.JSONDecodeError:
                return self._send_json(400, {"detail": "Invalid JSON"})
            if not isinstance(data, dict) or "name" not in data or "email" not in data:
                return self._send_json(400, {"detail": "name and email are required"})
            session = database.SessionLocal()
            try:
                user = User(name=data["name"], email=data["email"])
                session.add(user)
                session.commit()
                session.refresh(user)
                payload = serialize(user)
            finally:
                session.close()
            return self._send_json(201, payload)
        self._send_json(404, {"detail": "Not found"})

    def do_PUT(self):
        m = USER_RE.match(self.path)
        if m:
            try:
                data = self._read_json()
            except json.JSONDecodeError:
                return self._send_json(400, {"detail": "Invalid JSON"})
            if not isinstance(data, dict) or "name" not in data or "email" not in data:
                return self._send_json(400, {"detail": "name and email are required"})
            session = database.SessionLocal()
            try:
                user = session.get(User, int(m.group(1)))
                if user is None:
                    return self._send_json(404, {"detail": "User not found"})
                user.name = data["name"]
                user.email = data["email"]
                session.commit()
                session.refresh(user)
                payload = serialize(user)
            finally:
                session.close()
            return self._send_json(200, payload)
        self._send_json(404, {"detail": "Not found"})

    def do_DELETE(self):
        m = USER_RE.match(self.path)
        if m:
            session = database.SessionLocal()
            try:
                user = session.get(User, int(m.group(1)))
                if user is None:
                    return self._send_json(404, {"detail": "User not found"})
                session.delete(user)
                session.commit()
            finally:
                session.close()
            return self._send_empty(204)
        self._send_json(404, {"detail": "Not found"})

    def log_message(self, *args):  # silence default stderr logging
        pass


def run(host="0.0.0.0", port=8080):
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run()
