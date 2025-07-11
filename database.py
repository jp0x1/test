from mongoengine import connect 
import mongoengine
import os

def init_db():
    """Initializes the database connection."""
    mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/gitbad')
    connect(host=mongodb_uri)


