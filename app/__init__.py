import logging
import os
from flask import Flask, render_template
from config import Config
from app.models import db
from app.routes.main import main_bp
from app.routes.api import api_bp
from app.utils.helpers import format_date_human


def create_app(config_class=Config):
    """
    Flask Application Factory.
    Initializes Flask, configuration, database, blueprints, error handlers, and logging.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize SQLAlchemy database extension
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Custom Jinja filters and context processors
    app.jinja_env.filters["format_date"] = format_date_human

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config.get("APPLICATION_NAME", "Train Booking Date Reminder System"),
            "booking_window": app.config.get("BOOKING_WINDOW_DAYS", 60),
        }

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html", error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html", error=error), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template("404.html", error="Bad request"), 400

    # Configure Application Logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    # Initialize database tables automatically within app context
    with app.app_context():
        db.create_all()

    return app
