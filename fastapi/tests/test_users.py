def test_create_user(client):
    resp = client.post("/users", json={"name": "Ada", "email": "ada@example.com"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["name"] == "Ada"
    assert body["email"] == "ada@example.com"


def test_get_user(client):
    created = client.post(
        "/users", json={"name": "Bob", "email": "bob@example.com"}
    ).json()
    resp = client.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "bob@example.com"


def test_get_user_not_found(client):
    assert client.get("/users/999").status_code == 404


def test_list_users(client):
    client.post("/users", json={"name": "A", "email": "a@example.com"})
    client.post("/users", json={"name": "B", "email": "b@example.com"})
    resp = client.get("/users")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_user(client):
    created = client.post(
        "/users", json={"name": "C", "email": "c@example.com"}
    ).json()
    resp = client.put(
        f"/users/{created['id']}", json={"name": "C2", "email": "c2@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "C2"


def test_update_user_not_found(client):
    resp = client.put("/users/999", json={"name": "X", "email": "x@example.com"})
    assert resp.status_code == 404


def test_delete_user(client):
    created = client.post(
        "/users", json={"name": "D", "email": "d@example.com"}
    ).json()
    assert client.delete(f"/users/{created['id']}").status_code == 204
    assert client.get(f"/users/{created['id']}").status_code == 404


def test_delete_user_not_found(client):
    assert client.delete("/users/999").status_code == 404


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "userSelect" in resp.text
