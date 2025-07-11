from mongoengine import Document, StringField 
from werkzeug.security import generate_password_hash, check_password_hash


class User(Document):
    """
    User model for storing user data with a defined schema.
    """
    username = StringField(required=True, unique=True, max_length=80)
    email = StringField(required=True, max_length=120)
    password = StringField(required=True)

    def set_password(self, password_text):
        """Hashes the provided password and stores it."""
        self.password = generate_password_hash(password_text)

    def check_password(self, password_text):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password, password_text)

class Config(Document):
    """
    Configuration model for storing app settings and flags
    """
    value = StringField(required=True)
    type = StringField(required=True)
    description = StringField()
    
    meta = {
        'collection': 'config'  # Explicitly set collection name to 'config'
    }