import app.database as database
from pyramid.config import Configurator


def db(request):
    session = database.SessionLocal()

    def cleanup(request):
        session.close()

    request.add_finished_callback(cleanup)
    return session


def main(global_config=None, **settings):
    config = Configurator(settings=settings)
    config.add_request_method(db, reify=True)
    config.add_route("health", "/health")
    config.add_route("users_collection", "/users")
    config.add_route("users_item", "/users/{id}")
    config.add_route("home", "/")
    config.scan("app.views")
    return config.make_wsgi_app()
