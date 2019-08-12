from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user

from app.adapter import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    req_json = dict(request.get_json())
    if req_json.get("username") and req_json.get("password"):
        if current_user.is_authenticated == True:
            return jsonify({"success": True}), 200
        try:
            check_user = User.objects(username=req_json.get("username")).first()
        except Exception:
            return jsonify({"success": False}), 500
        check_user = User.objects(username=req_json.get("username")).first()
        if check_user:
            if str(check_user.password) == req_json.get("password"):
                try:
                    login_user(check_user)
                except Exception:
                    return jsonify({"success": False}), 500
                login_user(check_user)
                return jsonify({"success": True}), 200
        return jsonify({"success": False}), 401
    return jsonify({"success": False}), 401


@auth_bp.route("/api/auth")
def auth():
    if current_user.is_authenticated == True:
        return jsonify(None), 200
    return jsonify(None), 401
