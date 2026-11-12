
from pathlib import Path
from flask import Flask, render_template

from app.routes.routes import api_bp

# Project root ke frontend folders ka path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def create_app():
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
        static_url_path="/static"
    )

    # API routes
    app.register_blueprint(api_bp)

    # Frontend pages
    @app.get("/")
    def login_page():
        return render_template("login.html")

    @app.get("/register-case")
    def register_page():
        return render_template("register_case.html")

    @app.get("/search")
    def search_page():
        return render_template("search.html")

    @app.get("/review-matches")
    def review_page():
        return render_template("review_matches.html")

    return app
