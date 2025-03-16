import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db import db


class FlashCardModel(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Ensure UUID type consistency
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    user = db.relationship(
        "UserModel",
        back_populates="flashcards",
        single_parent=True,
    )
    tags = db.relationship(
        'TagModel',
        secondary="flashcards_tags",
        backref=db.backref('flashcards', lazy='dynamic'),
        lazy='joined'
    )

    __table_args__ = (db.UniqueConstraint("question", "user_id", name="uq_question_user"),)

    def __repr__(self):
        return f"<FlashCard(id={self.id}, question='{self.question[:20]}', user_id={self.user_id})>"
