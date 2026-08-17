"""
Hate Speech Detection backend -- Flask application factory.

This module used to be a single ~950 line file holding routes, SQL, pandas
aggregation, model loading and formatting all at once.  Those concerns now live
in:

    src/api/v1/       HTTP layer (one module per resource)
    src/api/          cross-cutting: auth, errors, pagination, schemas
    src/services/     business logic (classifier, analytics, survey, training)
    src/repositories/ SQL
    src/utils/        config, paths, labels, db

Run with:  python -m backend.app          (development)
           python -m backend.wsgi         (waitress, production-ish)
"""

from flask import Flask, jsonify, redirect
from flask_cors import CORS

from backend.src.api.errors import register_error_handlers
from backend.src.api.v1 import create_v1_blueprint
from backend.src.repositories import training_jobs as training_jobs_repo
from backend.src.services.classifier import classifier
from backend.src.utils import config, db, paths


def create_app(load_model=True):
    app = Flask(__name__)

    # --- app config --------------------------------------------------------
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES
    app.config["JSON_SORT_KEYS"] = False
    # Emit Devanagari as-is rather than \uXXXX escapes.
    app.json.ensure_ascii = False
    # Treat /predictions and /predictions/ as the same route.
    app.url_map.strict_slashes = False

    # --- CORS --------------------------------------------------------------
    # The old app called CORS(app) with no arguments, allowing every origin.
    CORS(
        app,
        resources={r"/*": {"origins": config.CORS_ORIGINS}},
        allow_headers=["Content-Type", "X-API-KEY", "X-ADMIN-KEY", "Authorization"],
        expose_headers=["Location", "Deprecation", "Link", "X-API-Deprecation-Notice"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # --- JSON errors everywhere -------------------------------------------
    register_error_handlers(app)

    # --- storage -----------------------------------------------------------
    paths.ensure_dirs()
    db.init_db(verbose=True)
    # A job left 'running' by a killed process would block every future retrain.
    released = training_jobs_repo.release_stale_jobs()
    if released:
        print(f"  [App] Marked {released} interrupted training job(s).")

    # --- routes ------------------------------------------------------------
    app.register_blueprint(create_v1_blueprint())

    if config.ENABLE_LEGACY_ROUTES:
        from backend.src.api.legacy import bp as legacy_bp

        app.register_blueprint(legacy_bp)

    @app.route("/", methods=["GET"])
    def root():
        """Service banner pointing at the versioned API."""
        return jsonify(
            {
                "status": "Hate Speech Detection backend running",
                "name": config.API_TITLE,
                "version": config.API_VERSION,
                "api": config.API_PREFIX,
                "health": f"{config.API_PREFIX}/health",
                "legacy_routes_enabled": config.ENABLE_LEGACY_ROUTES,
            }
        )

    @app.route("/api", methods=["GET"])
    @app.route("/api/", methods=["GET"])
    def api_root():
        return redirect(config.API_PREFIX, code=302)

    # --- model -------------------------------------------------------------
    if load_model:
        print("  [App] Initializing inference engine...")
        classifier.load()

    config.warn_about_insecure_defaults()

    return app


app = create_app()


if __name__ == "__main__":
    print(f"  [App] Listening on http://{config.HOST}:{config.PORT}")
    print(f"  [App] API index: http://{config.HOST}:{config.PORT}{config.API_PREFIX}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
