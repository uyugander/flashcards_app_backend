from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import FlashCardModel
from schemas import FlashCardSchema, FlashCardUpdateSchema

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
    
    @jwt_required(fresh=False)
    @blp.response(200, FlashCardSchema(many=True))
    def get(self):
        """Get a list of all flashcards"""
        return FlashCardModel.query.all()

    @jwt_required(fresh=False)
    @blp.arguments(FlashCardSchema)
    @blp.response(201, FlashCardSchema)
    def post(self, flashcard_data):
        """Create a new flashcard"""
        # Check if the user already has a flashcard with the same question
        existing_flashcard = FlashCardModel.query.filter_by(
            user_id=flashcard_data["user_id"], 
            question=flashcard_data["question"]
        ).first()
        
        if existing_flashcard:
            abort(400, message="A flashcard with the same question already exists for this user.")

        flashcard = FlashCardModel(**flashcard_data)

        try:
            db.session.add(flashcard)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()  # Rollback in case of error
            abort(400, message="A flash card with the same question or answer already exists.")
        except SQLAlchemyError:
            db.session.rollback()  # Rollback in case of error
            abort(500, message="An error occurred while saving the flash card to the database.")

        return flashcard
