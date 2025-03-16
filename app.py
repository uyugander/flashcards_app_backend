import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from resources.flashcard import blp as FlashCardBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint


def create_app(db_url=None, debug=False):
    app = Flask(__name__)
    load_dotenv()

    # Enables Flask to propagate exceptions from extensions to the main app for easier debugging.
    app.config["PROPAGATE_EXCEPTION"] = True

    # Setting the API title and version for OpenAPI documentation
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Use environment variables for database and JWT configurations
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["DEBUG"] = debug

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default-secret")  # Load from env var
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize API
    api = Api(app)

    # Initialize JWT Manager
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in BLOCKLIST
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has been revoked.", "error": "token_revoked"}), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token is not fresh.", "error": "fresh_token_required"}), 401

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        # Query user to check if they are admin dynamically
        user = UserModel.query.get(identity)  # Fetch user by identity (id)
        if user and user.is_admin:  # assuming 'is_admin' is an attribute on your UserModel
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Signature verification failed.", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Request does not contain an access token.", "error": "authorization_required"}), 401

    # Initialize database with the app context
    # with app.app_context():
    #     db.create_all()

    # Register blueprints
    api.register_blueprint(FlashCardBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app

if __name__ == "__main__":
    app = create_app(debug=True)  # Enable debug mode
    app.run(debug=True)

