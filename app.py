import threading
from flask import Flask
import os
import subprocess
import time
from database import init_db
from models import Config , User
from routes.auth import auth_bp
from routes.main import main_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.secret_key = os.urandom(24)
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["ALLOWED_EXTENSIONS"] = {"zip"}
    app.config["DISABLED_OPERATION_MONGO"] = [
        "$listLocalSessions",
        "$listSessions",
        "$listSearchIndexes",
        "$listSampledQueries",
        "$indexStats",
        "$limit",
        "$documents",
        "$regex",
        "$func",
        "$lookup",
        "$where",
        "$currentOp",
        "$changeStream",
        "$vectorSearch",
        "$unwind",
        "$unset",
        "$setWindowFields",
        "$search",
        "$searchMeta",
        "$queryStats",
        "$planCacheStats",
        "$collStats",
        "$graphLookup",
        "$replaceRoot",
        "$mergeObjects",
        "$setUnion",
        "$setIntersection",
        "$meta",
        "$zip",
        "$unionWith",
        "$match",
        "$out",
        "$merge",
        "$accumulator",
        "$function",
        "$set",
        "$javascript",    
        "$code",        
        "$eval" 
    ]

    # Initialize the database
    init_db()



    def insert_flag():
        flag_config = Config(value=f"{os.environ.get('Flag')}", type="flag")
        flag_config.save()
          
    def cleanup_users():
        while True:
            try:
                deleted_count = User.objects.delete()
                app.logger.debug(f"Deleted {deleted_count} users from the database.")
                res = subprocess.run(["rm", "-rf", "./uploads/*"], shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    app.logger.debug("Successfully deleted all files and subdirectories in ./uploads/")
                else:
                    app.logger.error(f"Error during cleanup: {res.stderr}")
            except Exception as e:
                app.logger.error(f"Error during cleanup: {e}")
            time.sleep(600)  


    time.sleep(30)
    insert_flag()
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_users, daemon=True)
    cleanup_thread.start()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)
