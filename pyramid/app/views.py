from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from app.models import User
from app.ui import INDEX_HTML


@view_config(route_name="home")
def home(request):
    return Response(INDEX_HTML.encode("utf-8"), content_type="text/html; charset=utf-8")


def _serialize(user):
    return {"id": user.id, "name": user.name, "email": user.email}


@view_config(route_name="health", renderer="json")
def health(request):
    return {"status": "ok"}


@view_config(route_name="users_collection", request_method="POST", renderer="json")
def create_user(request):
    data = request.json_body
    user = User(name=data["name"], email=data["email"])
    request.db.add(user)
    request.db.commit()
    request.db.refresh(user)
    request.response.status = 201
    return _serialize(user)


@view_config(route_name="users_collection", request_method="GET", renderer="json")
def list_users(request):
    return [_serialize(u) for u in request.db.query(User).all()]


@view_config(route_name="users_item", request_method="GET", renderer="json")
def get_user(request):
    user = request.db.get(User, int(request.matchdict["id"]))
    if user is None:
        raise HTTPNotFound(json_body={"detail": "User not found"})
    return _serialize(user)


@view_config(route_name="users_item", request_method="PUT", renderer="json")
def update_user(request):
    user = request.db.get(User, int(request.matchdict["id"]))
    if user is None:
        raise HTTPNotFound(json_body={"detail": "User not found"})
    data = request.json_body
    user.name = data["name"]
    user.email = data["email"]
    request.db.commit()
    request.db.refresh(user)
    return _serialize(user)


@view_config(route_name="users_item", request_method="DELETE", renderer="json")
def delete_user(request):
    user = request.db.get(User, int(request.matchdict["id"]))
    if user is None:
        raise HTTPNotFound(json_body={"detail": "User not found"})
    request.db.delete(user)
    request.db.commit()
    return Response(status=204)
