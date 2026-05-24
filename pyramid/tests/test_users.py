def test_create_user(testapp):
    resp = testapp.post_json("/users", {"name": "Ada", "email": "ada@example.com"})
    assert resp.status_code == 201
    assert resp.json["id"] > 0
    assert resp.json["name"] == "Ada"
    assert resp.json["email"] == "ada@example.com"


def test_get_user(testapp):
    created = testapp.post_json(
        "/users", {"name": "Bob", "email": "bob@example.com"}
    ).json
    resp = testapp.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json["email"] == "bob@example.com"


def test_get_user_not_found(testapp):
    testapp.get("/users/999", status=404)


def test_list_users(testapp):
    testapp.post_json("/users", {"name": "A", "email": "a@example.com"})
    testapp.post_json("/users", {"name": "B", "email": "b@example.com"})
    resp = testapp.get("/users")
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_update_user(testapp):
    created = testapp.post_json(
        "/users", {"name": "C", "email": "c@example.com"}
    ).json
    resp = testapp.put_json(
        f"/users/{created['id']}", {"name": "C2", "email": "c2@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json["name"] == "C2"


def test_update_user_not_found(testapp):
    testapp.put_json(
        "/users/999", {"name": "X", "email": "x@example.com"}, status=404
    )


def test_delete_user(testapp):
    created = testapp.post_json(
        "/users", {"name": "D", "email": "d@example.com"}
    ).json
    testapp.delete(f"/users/{created['id']}", status=204)
    testapp.get(f"/users/{created['id']}", status=404)


def test_delete_user_not_found(testapp):
    testapp.delete("/users/999", status=404)


def test_index_page(testapp):
    resp = testapp.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.content_type
    assert "userSelect" in resp.text
