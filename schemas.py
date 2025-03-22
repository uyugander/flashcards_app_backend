from marshmallow import Schema, fields


class PlainFlashCardSchema(Schema):
    id = fields.Str(dump_only=True)
    question = fields.Str(required=True)
    answer = fields.Str(required=True)

class PlainTagSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)

class PlainUserSchema(Schema):
    id = fields.Str(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)

class FlashCardUpdateSchema(Schema):
    question = fields.Str()
    answer = fields.Str()
    user_id = fields.Str()

# Request schema (for input)
class FlashCardRequestSchema(PlainFlashCardSchema):
    user = fields.Nested(PlainUserSchema(), dump_only=True)   # Include user details
    tags = fields.List(fields.Str(), required=False)  # Tags as strings for input

# Response schema (for output)
class FlashCardResponseSchema(PlainFlashCardSchema):
    user = fields.Nested(PlainUserSchema(), dump_only=True)   # User details in response
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)  # Tags as objects in response

class FlashCardSchema(PlainFlashCardSchema):
    user = fields.Nested(PlainUserSchema(), dump_only=True)   # Include user details
    tags = fields.List(fields.Str(), required=False, load_only=True)  # Allow tags in request
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)  # Directly use 'tags'

class TagSchema(PlainTagSchema):
    flashcards = fields.List(fields.Nested(PlainFlashCardSchema()), dump_only=True)
    users = fields.List(fields.Nested(PlainUserSchema(), many=True, load_only=True))

class FlashCardAndTagSchema(Schema):
    message = fields.Str()
    flashcard = fields.Nested(FlashCardSchema)
    tag = fields.Nested(TagSchema)

class UserSchema(PlainUserSchema):
    flashcards = fields.Nested(PlainFlashCardSchema(), dump_only=True)
    tags = fields.Nested(PlainTagSchema(), many=True, dump_only=True)  # Relationship with tags
