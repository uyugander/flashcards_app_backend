from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from db import db
from models import FlashCardModel, TagModel
from schemas import (FlashCardRequestSchema, FlashCardResponseSchema,
                     FlashCardSchema, FlashCardUpdateSchema)

blp = Blueprint("flashcards", __name__, description="Operations on flashcards")

# Helper function for admin check
def check_admin():
    jwt = get_jwt()
    if not jwt.get("is_admin"):
        abort(401, message="Admin privilege required. You do not have permission to delete flashcards.")

# FlashCard specific routes
@blp.route("/flashcard/<string:flashcard_id>")
class FlashCard(MethodView):
    
    @jwt_required()
    @blp.response(200, FlashCardSchema)
    def get(self, flashcard_id):
        """Get a specific flashcard by ID"""
        flashcard = FlashCardModel.query.get_or_404(flashcard_id)
        return flashcard

    @jwt_required()
    @blp.arguments(FlashCardUpdateSchema)
    @blp.response(200, FlashCardSchema)
    def put(self, flashcard_data, flashcard_id):
        """Update an existing flashcard by ID"""

        flashcard = FlashCardModel.query.get(flashcard_id)

        if flashcard is None:
            abort(404, message="Flashcard not found.")  # Return 404 instead of inserting

        flashcard.question = flashcard_data.get("question", flashcard.question)
        flashcard.answer = flashcard_data.get("answer", flashcard.answer)

        db.session.commit()
        return flashcard

    @jwt_required()
    def delete(self, flashcard_id):
        """Delete a flashcard by ID"""
        # check_admin()  # Reusable admin check for deletion

        flashcard = FlashCardModel.query.get_or_404(flashcard_id)
        
        db.session.delete(flashcard)
        db.session.commit()
        return {"message": "Flashcard deleted successfully."}
    

# FlashCard list routes
@blp.route("/flashcard")
class FlashCardList(MethodView):
    
    @jwt_required()
    @blp.response(200, FlashCardSchema(many=True))
    def get(self):
        """Get a list of all flashcards for the currently logged-in user"""
        user_id = get_jwt_identity()

        # Fetch flashcards with tags loaded eagerly
        flashcards = FlashCardModel.query.filter_by(user_id=user_id).options(joinedload(FlashCardModel.tags)).all()

        return flashcards

    @jwt_required()
    @blp.arguments(FlashCardRequestSchema)
    @blp.response(201, FlashCardResponseSchema)
    def post(self, flashcard_data):
        """Create a new flashcard and link tags in a single API call"""
        user_id = get_jwt_identity()

        # Check if the user already has a flashcard with the same question
        existing_flashcard = FlashCardModel.query.filter_by(
            user_id=user_id, 
            question=flashcard_data["question"]
        ).first()
        
        if existing_flashcard:
            abort(400, message="A flashcard with the same question already exists for this user.")

        # Extract tags from the request data (if provided)
        tag_names = flashcard_data.pop("tags", [])

        # Create the flashcard with the authenticated user's ID
        flashcard = FlashCardModel(user_id=user_id, **flashcard_data)

        # If no tags provided, assign a default tag
        if not tag_names:
            default_tag_name = "default"  # You can change this to whatever default you want
            tag = TagModel.query.filter_by(name=default_tag_name, user_id=user_id).first()
            if not tag:
                # Create the default tag if it doesn’t exist
                tag = TagModel(name=default_tag_name, user_id=user_id)
                db.session.add(tag)
            flashcard.tags.append(tag)
        else:
            # Add tags to the flashcard
            for tag_name in tag_names:
                # Check if the tag already exists for the user
                tag = TagModel.query.filter_by(name=tag_name, user_id=user_id).first()
                if not tag:
                    # Create a new tag if it doesn't exist
                    tag = TagModel(name=tag_name, user_id=user_id)
                    db.session.add(tag)
                flashcard.tags.append(tag)

        try:
            db.session.add(flashcard)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(400, message="A flashcard with the same question or answer already exists.")
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, message="An error occurred while saving the flashcard to the database.")

        return flashcard
