from flask import Blueprint
from flask import request, jsonify
from app.adapter import get_result, get_stats, get_clients, get_settings, change_settings, change_instagram_client, \
    delete_instagram_client
from app.insta_client import check_info, parse
from .. import socketio
from flask_login import login_required
import logging

log = logging.getLogger("flaskapp.main_router")
main_bp = Blueprint('main', __name__)


@main_bp.route("/api/account", methods=["GET", "POST"])
@login_required
def account_get_route():
    if request.method == "GET":
        page_num = request.args.get('p')
        result = get_clients(page_num)
        return jsonify(result["json"]), result["status"]
    elif request.method == "POST":
        result = change_instagram_client(request.json)
        return jsonify(result["json"]), result["status"]


@main_bp.route("/api/account/<account_id>/check", methods=["GET"])
@login_required
def account_check_route(account_id):
    result = change_instagram_client({"id": account_id})
    return jsonify(result["json"]), result["status"]


@main_bp.route("/api/account/<account_id>/remove", methods=["GET"])
@login_required
def account_del_route(account_id):
    result = delete_instagram_client(account_id)
    return jsonify(result["json"]), result["status"]


@main_bp.route("/api/stats", strict_slashes=False, methods=["GET"])
@login_required
def stats_route():
    page_num = request.args.get('p')
    search_query = request.args.get("search", default="")
    result = get_stats(page_num, search_query)
    return jsonify(result["json"]), result["status"]


@main_bp.route("/api/stats/<stats_id>/commonfollowers", methods=["GET"])
def stats_id_route(stats_id):
    page_num = request.args.get("p")
    search_query = request.args.get("search", default="")
    result = get_result(stats_id, page_num, search_query)
    return jsonify(result["json"]), result["status"]


@main_bp.route("/api/settings", methods=["GET", "POST"])
@login_required
def settings_get_route():
    if request.method == "GET":
        result = get_settings()
        return jsonify(result["json"]), result["status"]
    elif request.method == "POST":
        max_followers = request.json.get("max_followers")
        result = change_settings(max_followers)
        return jsonify(result["json"]), result["status"]


@main_bp.route("/api/compare", methods=["GET"])
def compare_route():
    users = [request.args.get("0"), request.args.get("1")]
    if None in users:
        return jsonify({"error": "EmptyUser"}), 400
    check_result = check_info(users)
    if not "error" in check_result["json"]:
        if not any(x["error"] for x in check_result["json"]["users"]):
            socketio.start_background_task(parse, users, socketio, check_result["json"]["id"])
    return jsonify(check_result["json"]), check_result["status"]
