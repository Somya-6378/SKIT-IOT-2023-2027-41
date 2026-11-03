
from flask import Flask
from app.routes.routes import api_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)

    @app.get("/")
    def home():
        return {
            "message": "Finding Missing Person Using AI API is running"
        }, 200

    return app
