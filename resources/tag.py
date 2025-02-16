from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import FlashCardModel, FlashCardsTags, TagModel
from schemas import FlashCardAndTagSchema, TagSchema

blp = Blueprint("tags", __name__, description="Operations on tags")

# Helper function to handle database commits
def commit_to_db():
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()  # Always rollback on error
        abort(500, message=f"An error occurred while processing your request: {str(e)}")

# Tag-specific routes
@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):

    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        """Get tag by ID"""
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required()
    @blp.response(202, description="Deletes a tag if no flashcard is tagged with it.")
    @blp.response(404, description="Tag not found.")
    @blp.response(400, description="Tag is associated with one or more flashcards, deletion prevented.")
    def delete(self, tag_id):
        """Delete tag if it's not associated with any flashcards"""
        tag = TagModel.query.get_or_404(tag_id)
        print(f"Tag: {tag}")
        print(f"Tag flashcards: {tag.flashcards}")  # Debugging: Check the value of flashcards

        # Check if flashcards is empty
        if db.session.query(FlashCardsTags).filter_by(tag_id=tag_id).count() == 0:
            db.session.delete(tag)
            commit_to_db()
            return {"message": "Tag deleted successfully."}

        abort(400, message="Could not delete tag. Make sure tag is not associated with any flashcard.")

@blp.route("/flashcard/<string:flashcard_id>/tag/<string:tag_id>")
class LinkTagsToFlashCards(MethodView):

    @jwt_required()
    @blp.response(200, TagSchema)
    def post(self, flashcard_id, tag_id):
        """Link a tag to a flashcard"""
        flashcard = FlashCardModel.query.get_or_404(flashcard_id)
        tag = TagModel.query.get_or_404(tag_id)

        if tag in flashcard.tags:
            abort(400, message="Tag is already linked to this flashcard.")

        flashcard.tags.append(tag)
        commit_to_db()
        return tag

    @jwt_required()
    @blp.response(200, FlashCardAndTagSchema)
    def delete(self, flashcard_id, tag_id):
        """Unlink a tag from a flashcard"""
        flashcard = FlashCardModel.query.get_or_404(flashcard_id)
        tag = TagModel.query.get_or_404(tag_id)

        if tag not in flashcard.tags:
            abort(400, message="Tag is not linked to this flashcard.")

        flashcard.tags.remove(tag)
        commit_to_db()
        return {"message": "Flashcard removed from the tag", "flashcard": flashcard, "tag": tag}

@blp.route("/flashcard/<string:flashcard_id>/tag")
class TagInFlashCard(MethodView):

    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, flashcard_id):
        """Get all tags associated with a flashcard"""
        flashcard = FlashCardModel.query.get_or_404(flashcard_id)
        return flashcard.tags

    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, flashcard_id):
        """Assign a tag to a flashcard, reusing existing tags if available"""

        flashcard = FlashCardModel.query.get_or_404(flashcard_id)

        # Check if the tag already exists
        tag = TagModel.query.filter_by(name=tag_data["name"]).first()
        if not tag:
            tag = TagModel(name=tag_data["name"])
            db.session.add(tag)

        # Associate the tag with the flashcard (prevent duplicates)
        if tag not in flashcard.tags:
            flashcard.tags.append(tag)
            db.session.commit()
        else:
            abort(400, message="Tag already exists for this flashcard.")

        return tag


@blp.route("/tag")
class TagList(MethodView):

    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self):
        """Get a list of all tags"""
        user_id = get_jwt_identity()  # Get the current user ID from the JWT token
        return TagModel.query.filter_by(user_id=user_id).all()

    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data):
        """Create a new tag"""
        user_id = get_jwt_identity()  # Get the current user ID from the JWT token
        tag = TagModel(name=tag_data["name"], user_id=user_id)

        if TagModel.query.filter_by(name=tag_data["name"], user_id=user_id).first():
            abort(400, message="A tag with this name already exists for this user.")

        db.session.add(tag)
        commit_to_db()
        return tag
