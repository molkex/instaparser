class BaseConfig(object):
    DEBUG = False
    MONGODB_DB = "instaparser"
    MONGODB_HOST = "mongo"
    MONGODB_PORT = 27017
    SECRET_KEY = "AD9awd*hawd12_=+#!$"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOGIN_DISABLED = True


class ProductionConfig(BaseConfig):
    pass
