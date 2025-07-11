from flask import Blueprint, jsonify, session, request, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from utils.decorators import login_required
from utils.file_utils import allowed_file, process_git_repo , limit_object_depth
from models import User
from flask import current_app
from bson import json_util
import json
import pymongo

# Adding .<ext> to certain endpoints confuses bots and enumeration tools, making it harder for them to determine our backend stack.

main_bp = Blueprint('main_bp', __name__)


@main_bp.route("/")
def home():
    return send_from_directory("templates", "index.html")

@main_bp.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@main_bp.route("/<page>")
def serve_page(page):
    # Ensure the page is one of the allowed html files
    if page in ['signin', 'signup', 'profile', 'why']:
        return send_from_directory("templates", page+'.html')
    return send_from_directory("templates", "index.html") # Default fallback


@main_bp.route('/api/profile')
@main_bp.route('/api/profile.<ext>')
@login_required
def api_profile(ext=None):
    # The decorator handles the auth check
    print(session.get('user_id'))
    return jsonify({"success": True, "username": session.get('username')})

@main_bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    # Check file size (1MB = 1024 * 1024 bytes)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  
    
    if file_size > 1024 * 1024:  # 1MB limit
        return jsonify({"success": False, "error": "File size exceeds 1MB limit"}), 400
    
    if file and allowed_file(file.filename):
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session['user_id'])
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Create temporary file path
        file_path = os.path.join(user_upload_dir, secure_filename(file.filename))
        
        try:
            # Save the uploaded file
            file.save(file_path)
            
            # Process the ZIP file
            result = process_git_repo(file_path, user_upload_dir)
            
            # Clean up the ZIP file
            os.remove(file_path)
            
            if result['success']:
                return jsonify({"success": True, "message": result['message']})
            else:
                return jsonify({"success": False, "error": result['error']})
                
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"success": False, "error": f"Upload failed: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "error": "Invalid file type. Only ZIP files are allowed."}), 400


@main_bp.route('/api/search', methods=['GET'])
@main_bp.route('/api/search.<ext>', methods=['GET'])
def search(ext=None):
    try:
        # Check if this is a GET request with debug parameter from localhost
        if request.method == 'GET':
            # Check for debug parameter
            debug = request.args.get('debug', '').lower()
            if debug != 'true':
                return jsonify({"message": "Debug mode required"}), 400
            
        
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                client_ip = forwarded_for.strip()
            else:
                client_ip = request.remote_addr
            current_app.logger.debug(f"client_ip: {client_ip}, X-Forwarded-For: {forwarded_for}")
            if client_ip not in ['127.0.0.1', 'localhost', '::1']:
                return jsonify({"message": "Access denied - localhost only"}), 403
            
            # Get filter from URL parameter
            filter_param = request.args.get('filter')
            if not filter_param:
                return jsonify({"message": "Missing filter parameter"}), 400
            
            try:
               
                filter_obj = json.loads(filter_param)
            except json.JSONDecodeError:
                return jsonify({"message": "Invalid JSON in filter parameter"}), 400
        
        
        if not filter_obj or not isinstance(filter_obj, dict):
            return jsonify({"message": "Missing filter"}), 400
        
        if isinstance(filter_obj, list):
            return jsonify({"message": "Invalid filter"}), 400
        
        filter_keys = list(filter_obj.keys())
        
        if len(filter_keys) > 5:
            return jsonify({"message": "Too many filter options"}), 400
        
        found_disabled_key = any(key in current_app.config['DISABLED_OPERATION_MONGO'] for key in filter_keys)
        
        if found_disabled_key:
            return jsonify({"message": "Invalid Filter found"}), 400
        
        updated_filter = limit_object_depth(filter_obj, 2, 0)
        
        if updated_filter is None:
            return jsonify({"message": "Filter too deep or invalid"}), 400
        
        try:
           
            pipeline = [updated_filter, {"$limit": 2}] 
            with pymongo.timeout(4):
                result = list(User.objects.aggregate(pipeline))
            json_result = json.loads(json_util.dumps(result))
            
            return jsonify(json_result)
                
        except TimeoutError:
            return jsonify({"message": "Query timeout - operation too slow"}), 400
        except Exception as db_err:
            current_app.logger.error(f"Database error: {db_err}")
            return jsonify({"message": "Something went wrong"}), 500
        
    except Exception as err:
        current_app.logger.error(f"General error: {err}")
        return jsonify({"message": "Something went wrong"}), 500
