import os

from flask import Flask
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    if not app.config.get("DATABASE_URL"):
        db_path = os.path.join(app.instance_path, "emailapp.db")
        app.config["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"

    from app import db
    from app.models import Base
    db.init_app(app)
    Base.metadata.create_all(app.extensions["database"].engine)

    from app import routes
    app.register_blueprint(routes.bp)

    return app
