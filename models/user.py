import uuid

from werkzeug.security import check_password_hash, generate_password_hash

from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), unique=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationship for flashcards
    flashcards = db.relationship(
        "FlashCardModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Relationship for tags (newly added)
    tags = db.relationship("TagModel", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<UserModel username={self.username}>"

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
