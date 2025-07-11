from flask import Blueprint, request, jsonify, session
from models import User
from utils.decorators import login_required

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route("/api/signup", methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    if User.objects(username=username).first():
        return jsonify({"success": False, "error": "Username already exists"}), 400

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    new_user.save()

    return jsonify({"success": True, "message": "Account created successfully! Please sign in."}), 201

@auth_bp.route("/api/signin", methods=['POST'])
def api_signin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    user = User.objects(username=username).first()

    if user and user.check_password(password):
        session['user_id'] = str(user.id)
        session['username'] = user.username
        return jsonify({"success": True, "message": "Login successful!", "username": user.username}), 200
    else:
        return jsonify({"success": False, "error": "Invalid username or password"}), 401

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "You have been logged out."}), 200
