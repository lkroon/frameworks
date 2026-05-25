import json
import urllib.error
import urllib.request


def _req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        body = resp.read()
        return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, (json.loads(body) if body else None)


def test_create_user(base_url):
    status, body = _req("POST", base_url + "/users", {"name": "Ada", "email": "ada@example.com"})
    assert status == 201
    assert body["id"] > 0
    assert body["name"] == "Ada"
    assert body["email"] == "ada@example.com"


def test_get_user(base_url):
    _, created = _req("POST", base_url + "/users", {"name": "Bob", "email": "bob@example.com"})
    status, body = _req("GET", base_url + f"/users/{created['id']}")
    assert status == 200
    assert body["email"] == "bob@example.com"


def test_get_user_not_found(base_url):
    status, _ = _req("GET", base_url + "/users/999")
    assert status == 404


def test_list_users(base_url):
    _req("POST", base_url + "/users", {"name": "A", "email": "a@example.com"})
    _req("POST", base_url + "/users", {"name": "B", "email": "b@example.com"})
    status, body = _req("GET", base_url + "/users")
    assert status == 200
    assert len(body) == 2


def test_update_user(base_url):
    _, created = _req("POST", base_url + "/users", {"name": "C", "email": "c@example.com"})
    status, body = _req("PUT", base_url + f"/users/{created['id']}", {"name": "C2", "email": "c2@example.com"})
    assert status == 200
    assert body["name"] == "C2"


def test_update_user_not_found(base_url):
    status, _ = _req("PUT", base_url + "/users/999", {"name": "X", "email": "x@example.com"})
    assert status == 404


def test_delete_user(base_url):
    _, created = _req("POST", base_url + "/users", {"name": "D", "email": "d@example.com"})
    status, _ = _req("DELETE", base_url + f"/users/{created['id']}")
    assert status == 204
    status, _ = _req("GET", base_url + f"/users/{created['id']}")
    assert status == 404


def test_delete_user_not_found(base_url):
    status, _ = _req("DELETE", base_url + "/users/999")
    assert status == 404


def test_index_page(base_url):
    req = urllib.request.Request(base_url + "/", method="GET")
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    assert "text/html" in resp.headers["Content-Type"]
    assert "userSelect" in resp.read().decode()
