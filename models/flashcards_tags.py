import uuid

from db import db


class FlashCardsTags(db.Model):
    __tablename__ = "flashcards_tags"

    # Composite Primary Key - Flashcard and Tag IDs together form the primary key
    flashcard_id = db.Column(db.String(36), db.ForeignKey("flashcards.id"), primary_key=True)
    tag_id = db.Column(db.String(36), db.ForeignKey("tags.id"), primary_key=True)
    
    # Optionally, you can add an id field if you still want a unique identifier for each record
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
