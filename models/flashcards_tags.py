import uuid

from sqlalchemy.dialects.postgresql import UUID

from db import db


class FlashCardsTags(db.Model):
    __tablename__ = "flashcards_tags"

    # Composite Primary Key - Flashcard and Tag IDs together form the primary key
    flashcard_id = db.Column(UUID(as_uuid=True), db.ForeignKey("flashcards.id", ondelete="CASCADE"), primary_key=True)
    tag_id = db.Column(UUID(as_uuid=True), db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    # Optionally, you can add an id field if you still want a unique identifier for each record
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
