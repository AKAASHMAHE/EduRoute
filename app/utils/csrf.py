import secrets
from functools import wraps
from flask import session, request, abort, current_app


class CSRFProtect:
    """
    Lightweight, robust CSRF protection extension for Flask.
    Compatible with Flask-WTF token patterns and Jinja helpers.
    """

    def __init__(self, app=None):
        self._exempt_views = set()
        self._exempt_blueprints = set()
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.extensions = getattr(app, "extensions", {})
        app.extensions["csrf"] = self

        @app.before_request
        def csrf_protect():
            if not current_app.config.get("WTF_CSRF_ENABLED", True):
                return

            if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
                return

            # Exemption checks
            view_func = current_app.view_functions.get(request.endpoint)
            if view_func and view_func in self._exempt_views:
                return

            if request.blueprint and request.blueprint in self._exempt_blueprints:
                return

            # Check token from form or header
            expected_token = session.get("_csrf_token")
            received_token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")

            if not expected_token or not received_token or not secrets.compare_digest(expected_token, received_token):
                abort(400, description="CSRF token missing or invalid.")

        @app.context_processor
        def inject_csrf_token():
            return {"csrf_token": self.generate_csrf}

        app.jinja_env.globals["csrf_token"] = self.generate_csrf

    def generate_csrf(self):
        """Generate or retrieve the session CSRF token."""
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_hex(32)
        return session["_csrf_token"]

    def exempt(self, view_or_bp):
        """Exempt a view function or Blueprint from CSRF validation."""
        if hasattr(view_or_bp, "name"):
            self._exempt_blueprints.add(view_or_bp.name)
        else:
            self._exempt_views.add(view_or_bp)
        return view_or_bp


csrf = CSRFProtect()
