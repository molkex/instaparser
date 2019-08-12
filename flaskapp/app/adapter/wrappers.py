import logging

from mongoengine import ValidationError

import app.insta_client as ic
from .models import Statistics, InstaClients, Settings, ComparedUsers

per_page = 15
log = logging.getLogger("flaskapp.wrappers")


def check_page(number):
    if not number:
        number = 1
    elif number.isdigit():
        number = int(number)
    else:
        number = 0
    return number


def get_result(id, page_n, query):
    try:
        stats = Statistics.objects.get(id=id)
    except ValidationError:
        return {"json": None, "status": 400}
    common_followers_count = len(stats.common_followers)
    output_json = {"compared_users": list(stats.compared_users)}

    page_n = check_page(page_n)

    search_result = [x for x in stats.common_followers if query in x]
    search_result_count = len(search_result)
    output_json["count"] = search_result_count

    if 0 < page_n * per_page < search_result_count + per_page:
        search_result = search_result[(page_n - 1) * per_page:page_n * per_page]
        output_json["common_followers"] = search_result
    else:
        output_json["common_followers"] = []
    return {"json": output_json, "status": 200}


def get_stats(page_n, query):
    page_n = check_page(page_n)
    output_json = {}

    stats = Statistics.objects.order_by('-creation_time')
    search_result = []
    for each in stats:
        if any(query in usr.username for usr in each.compared_users):
            search_result.append({
                "id": str(each.id),
                "compared_users": [
                    {
                        "username": x,
                        "count": int(ComparedUsers.objects(pk=x).first().uses) if len(ComparedUsers.objects(pk=x)) else 0
                    }
                    for x in [str(y.username) for y in each.compared_users]],
                "count": len(each.common_followers),
                "creation_time": str(each.creation_time)
            })

    search_result_count = len(search_result)
    output_json["count"] = search_result_count

    if 0 < page_n * per_page < search_result_count + per_page:
        search_result = search_result[(page_n - 1) * per_page:page_n * per_page]
        output_json["stats"] = search_result
    else:
        output_json["stats"] = []

    return {"json": output_json, "status": 200}


def get_clients(page_n):
    page_n = check_page(page_n)
    output_json = {}

    clients = InstaClients.objects
    output_json["count"] = len(clients)
    clients_arr = [{
        "id": str(x.id),
        "username": str(x.username),
        "password": str(x.password),
        "error": str(x.error),
        "checkpoint": str(x.checkpoint)
    } for x in clients]
    if 0 < page_n * per_page < output_json["count"] + per_page:
        search_result = clients_arr[(page_n - 1) * per_page:page_n * per_page]
        output_json["accounts"] = search_result
    else:
        output_json["accounts"] = []
    return {"json": output_json, "status": 200}


def get_settings():
    try:
        settings = Settings.objects.first()
        return {"json": {"error": "", "max_followers": settings.max_followers}, "status": 200}
    except Exception as e:
        return {"json": {"error": str(e)}, "status": 400}


def change_settings(max_followers):
    try:
        if max_followers:
            if len(Settings.objects):
                settings = Settings.objects.first()
                settings.update(max_followers=max_followers)
            else:
                Settings(max_followers=max_followers).save()
            return {"json": {"error": ""}, "status": 200}
        else:
            return {"json": {"error": "EmptySetting"}, "status": 400}
    except Exception as e:
        return {"json": {"error": str(e)}, "status": 400}


def change_instagram_client(new_data):
    log.debug(f"Change request: {new_data}")
    return ic.init_client(new_data)


def delete_instagram_client(id):
    client = InstaClients.objects.get(id=id)
    if client:
        client.delete()
        return {"json": {"error": ""}, "status": 200}
    else:
        return {"json": {"error": "WrongID"}, "status": 400}
