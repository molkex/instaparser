from flask import request
from flask_socketio import join_room

from .. import socketio


@socketio.on("connect")
def connect():
    room_id = request.args.get("room_id")
    if room_id:
        join_room(room_id)
    return
