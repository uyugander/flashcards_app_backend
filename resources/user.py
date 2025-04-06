from flask.views import MethodView
from flask_bcrypt import Bcrypt  # Optionally use Bcrypt for stronger hashing
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt, get_jwt_identity, jwt_required)
from flask_smorest import Blueprint, abort

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import PlainUserSchema, UserSchema

blp = Blueprint("Users", "users", description="Operations on users.")
bcrypt = Bcrypt()

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(PlainUserSchema)
    def post(self, user_data):
        # Check if the username already exists
        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="A user with that username already exists.")
        
        # Hash the password using bcrypt (more secure than pbkdf2_sha256)
        hashed_password = bcrypt.generate_password_hash(user_data["password"]).decode('utf-8')
        
        # Create the new user
        user = UserModel(
            username=user_data["username"],
            password=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()

        return {"message": "User created successfully.", "user_id": str(user.id)}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        # Retrieve user from the database
        user = UserModel.query.filter(UserModel.username == user_data["username"]).first()

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password, user_data["password"]):
            # Create JWT tokens
            access_token = create_access_token(identity=str(user.id), fresh=True)
            refresh_token = create_refresh_token(identity=str(user.id))
            return {"access_token": access_token, "refresh_token": refresh_token, "user_id": str(user.id)}
        
        abort(401, message="Invalid credentials.")


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        # Create a new access token
        new_token = create_access_token(identity=current_user, fresh=False)
        jti = get_jwt()["jti"]
        
        # Add the JWT ID to the blocklist
        BLOCKLIST.add(jti)
        return {"access_token": new_token}


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        # Add the JWT ID to the blocklist to invalidate the token
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}


@blp.route("/user/<string:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    @jwt_required()
    def get(self, user_id):
        # Ensure user can only view their own profile or admins can view other profiles
        current_user = get_jwt_identity()
        if current_user != user_id:  # Check if the user is requesting their own data
            abort(403, message="You can only view your own profile.")
        
        user = UserModel.query.get_or_404(user_id)
        return user

    @jwt_required()
    def delete(self, user_id):
        # Ensure user can only delete their own profile or admins can delete other profiles
        current_user = get_jwt_identity()
        if current_user != user_id:
            abort(403, message="You can only delete your own account.")
        
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200
