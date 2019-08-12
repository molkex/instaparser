import json
import logging
from http.client import IncompleteRead

from gevent import sleep
from instagram_private_api import (ClientThrottledError, ClientCookieExpiredError, ClientLoginError,
                                   Client, ClientError, ClientCheckpointRequiredError, ClientSentryBlockError)

from app.adapter import InstaClients, Statistics, Settings, ComparedUsers
from app.utils import to_json, from_json, Constants

log = logging.getLogger('flaskapp.parser')


def on_login_callback(bd_client, inst_client):
    bd_client.settings = str(json.dumps(inst_client.settings, default=to_json))
    bd_client.save()
    return


def init_client(new_data=None):
    client = None
    while not client:
        log.debug("Initializing client")

        if new_data:
            if new_data.get("id"):
                client_params = InstaClients.objects.get(id=new_data.get("id"))
                if not client_params:
                    return {"json": {"error": "ClientDoesNotExist"}, "status": 200}
            elif new_data.get("username") or new_data.get("password"):
                if len(InstaClients.objects(username=new_data.get("username"))):
                    return {"json": {"error": "ClientExists"}, "status": 200}
                client_params = InstaClients()
                client_params.username = new_data["username"] if new_data.get("username") else ""
                client_params.password = new_data["password"] if new_data.get("password") else ""
            else:
                return {"json": {"error": "WrongRequest"}, "status": 400}
        else:
            client_params = InstaClients.get_oldest_client
            if not client_params:
                return None
        log.debug("Got client, checking settings")
        device_id = None

        try:
            if str(client_params.settings) == "":
                client = Client(username=client_params.username,
                                password=client_params.password,
                                on_login=lambda x: on_login_callback(client_params, x))
                log.info(f"Logged in using {client_params.username} and generated cookies")
            else:
                client = Client(username=client_params.username,
                                password=client_params.password,
                                settings=json.loads(str(client_params.settings), object_hook=from_json))
                log.info(f"Logged in using {client_params.username}")
            if str(client_params.error) != "":
                client_params.update(error="", checkpoint="")

        except ClientError as e:
            if isinstance(e, ClientThrottledError):
                sleep(Constants.api_throttle_delay)
            elif isinstance(e, ClientLoginError):
                if str(e) == Constants.bad_password or str(e) == Constants.invalid_user:
                    if str(e) == Constants.invalid_user:
                        if new_data:
                            return {"json": {"error": Constants.error_wrong_username}, "status": 200}
                        client_params.error = Constants.error_wrong_username
                    elif str(e) == Constants.bad_password:
                        if new_data:
                            return {"json": {"error": Constants.error_wrong_password}, "status": 200}
                        client_params.error = Constants.error_wrong_password
                    else:
                        if new_data:
                            return {"json": {"error": str(e)}, "status": 200}
                        client_params.error = str(e)
                    client_params.save()
                    client_params = InstaClients.get_oldest_client
                    if not client_params:
                        return None
            elif isinstance(e, ClientCookieExpiredError):
                client_params.update(settings="")
            elif isinstance(e, ClientCheckpointRequiredError):
                if new_data:
                    return {"json": {"error": Constants.error_checkpoint_required, "checkpoint": e.challenge_url},
                            "status": 200}
                client_params.update(error=Constants.error_checkpoint_required, checkpoint=str(e.challenge_url))
                client_params = InstaClients.get_oldest_client
                if not client_params:
                    return None
            elif isinstance(e, ClientSentryBlockError):
                if new_data:
                    return {"json": {"error": Constants.error_flagged_for_spam}, "status": 200}
                client_params.update(error=Constants.error_flagged_for_spam)
                client_params = InstaClients.get_oldest_client
                if not client_params:
                    return None
            log.debug(e)
    if new_data:
        return {"json": {"error": "", "id": str(client_params.id)}, "status": 200}
    return client


def check_info(usernames):
    MAX_FOLLOWER_COUNT = int(Settings.objects.first().max_followers)

    def form_response(name, error="", follower_count=0):
        return {"username": name, "error": error, "total_followers": follower_count, "limit": MAX_FOLLOWER_COUNT}

    client = init_client()
    if not client:
        return {"json": {"error": "InternalError"}, "status": 200}

    user_infos = []
    user_responses = []
    for user in usernames:
        user_info = None
        try:
            user_info = client.username_info(user)
            if user_info["user"]["is_private"]:
                user_responses.append(form_response(user, "UserIsPrivate"))
            elif user_info["user"]["follower_count"] > MAX_FOLLOWER_COUNT:
                user_responses.append(form_response(user, "UserTooManyFollowers"))
            else:
                user_responses.append(form_response(user, "", user_info["user"]["follower_count"]))
        except ClientError as e:
            user_responses.append(form_response(user, "UserNotFound"))
        log.info(f"Checked info for {user} using {client.username}")
    if any(x["error"] for x in user_responses):
        return {"json": {"id": "", "users": user_responses}, "status": 200}

    compared_users_db = [{"username": x["username"], "total_followers": x["total_followers"]} for x in user_responses]
    saved_stat = Statistics(compared_users=compared_users_db).save()
    return {"json": {"id": str(saved_stat.id), "users": user_responses}, "status": 200}


def parse(usernames, socketio, room_id):
    threads = []
    temporary_storage = {}

    saved_document = Statistics.objects(pk=room_id).first()

    def parse_user(username, room_id):
        log = logging.getLogger('flaskapp.parser')
        success_string = "Parsed for {} using {}"
        error_string = "Error parsing for {} using {}: {}"
        client = init_client()
        if not client:
            socketio.emit("error", {"error", "InternalError"}, room=room_id)
            return
        rank_token = client.generate_uuid()
        user_id = None
        while not user_id:
            try:
                user_id = client.username_info(username)["user"]["pk"]
                results = client.user_followers(user_id, rank_token)
                log.debug(f"Started parsing for {username} using {client.username}")
            except ClientError as e:
                log.debug(type(e))
                if isinstance(e, ClientThrottledError):
                    log.info(error_string.format(username, client.username, e))
                    sleep(20)
        followers = []
        followers.extend((x["username"] for x in results.get('users', [])))
        next_max_id = results.get('next_max_id')
        socketio.emit('progress', {"name": username, "followers_progress": len(followers)},
                      room=room_id)
        while next_max_id:
            try:
                results = client.user_followers(user_id, rank_token, max_id=next_max_id)
                followers.extend((x["username"] for x in results.get('users', [])))
                socketio.emit('progress', {"name": username, "followers_progress": len(followers)},
                              room=room_id)
                next_max_id = results.get('next_max_id')
                log.info(success_string.format(username, client.username))
            except (ClientError, ConnectionResetError) as e:
                log.info(error_string.format(username, client.username, e))
                sleep(20)
            except ClientCookieExpiredError as e:
                log.info(error_string.format(username, client.username, e))
                client = init_client()
                if not client:
                    socketio.emit("error", {"error", "InternalError"}, room=room_id)
                    return
            except IncompleteRead as e:
                log.warning(f"Incomplete read of stream: {e}")
                sleep(5)
        temporary_storage[username] = followers

    def start():
        for user in usernames:
            sleep(1)
            threads.append(socketio.start_background_task(parse_user, user, room_id))

    def wait_and_emit():
        for each in threads:
            each.join()
        tmpset1 = set(temporary_storage[usernames[0]])
        tmpset2 = set(temporary_storage[usernames[1]])
        outlist = list(tmpset1.intersection(tmpset2))
        outlist.sort()

        saved_document.update(common_followers=outlist)
        result_id = str(saved_document.id)
        ComparedUsers.increment(usernames[0])
        ComparedUsers.increment(usernames[1])
        socketio.emit("end", result_id, room=room_id)

    start()
    wait_and_emit()
    return
