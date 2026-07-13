"""Ponto de entrada e application factory do Carona Alegre."""
from __future__ import annotations

from datetime import date, datetime, time

from flask import Flask, render_template

from config import Config
from database.extensions import csrf, db, login_manager


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    import models  # noqa: F401

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        with app.app_context():
            db.create_all()

    from models import ContaUsuario
    from routes.auth import auth_bp
    from routes.driver import driver_bp
    from routes.main import main_bp
    from routes.passenger import passenger_bp
    from routes.profile import profile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(passenger_bp)
    app.register_blueprint(profile_bp)

    from database.healthcheck import register_commands
    register_commands(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(ContaUsuario, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.template_filter("data_br")
    def data_br(value: date | None) -> str:
        return value.strftime("%d/%m/%Y") if value else "—"

    @app.template_filter("hora_br")
    def hora_br(value: time | None) -> str:
        return value.strftime("%H:%M") if value else "—"

    @app.template_filter("datahora_br")
    def datahora_br(value: datetime | None) -> str:
        return value.strftime("%d/%m/%Y %H:%M") if value else "—"

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
