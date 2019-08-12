from flask import request
from flask_socketio import join_room, leave_room
from .. import socketio
from app.insta_client import check_info, parse


@socketio.on("connect")
def connect():
    room_id = request.args.get("room_id")
    if room_id:
        join_room(room_id)


# @socketio.on("disconnect")
# def disconnect():
#     room_id = request.args.get("id")
#     if room_id:
#         leave_room(room_id)
