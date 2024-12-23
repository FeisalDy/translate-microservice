from flask import Flask
from app.routes.translate_routes import translate_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(translate_bp, url_prefix='/api')
    return app
