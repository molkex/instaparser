from gevent import monkey
monkey.patch_all()
from app import create_app, socketio
import logging, sys
from logging import handlers

conf = 'dev'

app = create_app(conf)


if __name__ == "__main__":
    handler = handlers.RotatingFileHandler("main.log", maxBytes=1000000, backupCount=1)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logging.getLogger("socketio").setLevel(logging.INFO)
    logging.getLogger("engineio").setLevel(logging.INFO)

    if conf == "dev":
        app.logger.setLevel(logging.DEBUG)
    elif conf == "prod":
        app.logger.setLevel(logging.INFO)

    logging.root.handlers = [handler]

    socketio.run(host='0.0.0.0', port=5000, app=app)
