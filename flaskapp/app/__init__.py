from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from app.adapter import Settings, User

socketio = SocketIO()
config = {
    "dev": "app.flask_config.DevelopmentConfig",
    "prod": "app.flask_config.ProductionConfig"
}


def create_app(conf="dev"):
    app = Flask('flaskapp')
    app.config.from_object(config[conf])

    from .routes import main_bp as main_blueprint
    app.register_blueprint(main_blueprint)

    from .routes import auth_bp as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.adapter import login_manager
    login_manager.init_app(app)

    from app.adapter import db
    db.init_app(app)
    # cors = CORS(app)
    socketio.init_app(app, async_mode="gevent", engineio_logger=False,
                      cors_allowed_origins='*')

    if not Settings.objects.first():
        Settings(max_followers=500000).save()

    if not User.objects.first():
        User(username='admin', password='CuaZwT49uHe').save()

    return app
