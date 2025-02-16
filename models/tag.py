import uuid

from db import db


class TagModel(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)  # Foreign key to users

    # Composite unique constraint for name and user_id
    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='_name_user_uc'),
    )

    # Relationship with UserModel (many tags to one user)
    user = db.relationship("UserModel", back_populates="tags")

    def __repr__(self):
        return f"<TagModel name={self.name}>"
