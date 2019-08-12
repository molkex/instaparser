import datetime
import logging

from flask_login import UserMixin, LoginManager
from flask_mongoengine import MongoEngine
from mongoengine import queryset_manager, IntField, StringField, DateTimeField, ListField, BooleanField, EmbeddedDocumentListField, EmbeddedDocument

db = MongoEngine()
login_manager = LoginManager()
log = logging.getLogger("flaskapp.models")


class ComparedUserField(EmbeddedDocument):
    username = StringField()
    total_followers = IntField()


class Statistics(db.Document):
    creation_time = DateTimeField()
    compared_users = EmbeddedDocumentListField(ComparedUserField)
    common_followers = ListField()

    def save(self, *args, **kwargs):
        self.creation_time = datetime.datetime.now()
        return super(Statistics, self).save(*args, **kwargs)


class InstaClients(db.Document):
    username = StringField()
    password = StringField()
    settings = StringField(default="")
    checkpoint = StringField(default="")
    error = StringField(default="")
    last_used = DateTimeField()
    __last_used_id = 0

    def save(self, *args, **kwargs):
        self.last_used = datetime.datetime.now()
        return super(InstaClients, self).save(*args, **kwargs)

    @queryset_manager
    def client_update_settings(self, queryset, __id, settings):
        self.update(id=__id, set__settings=settings)
        return

    @queryset_manager
    def get_oldest_client(self, queryset):
        log.debug(f"Requested oldest client")
        if any(False if str(x.error) else True for x in self.objects):
            log.debug(f"At least one client is valid")
            valid_flag = False
            while not valid_flag:
                oldest = self.objects.order_by("last_used").first()
                oldest.update(last_used=datetime.datetime.now())
                log.debug(f"{oldest.username} is valid: {not bool(oldest.error)}")
                if str(oldest.error) == "":
                    valid_flag = True
        else:
            log.debug(f"No valid clients")
            oldest = None
        return oldest

    @queryset_manager
    def settings_exist(self, queryset, __id):
        client = self.objects.get(id=__id)
        if client.settings != "":
            return True
        return False


class User(db.Document, UserMixin):
    username = StringField()
    password = StringField()


class Settings(db.Document):
    max_followers = IntField()


class ComparedUsers(db.Document):
    username = StringField(primary_key=True)
    uses = IntField(defaul=1)

    @queryset_manager
    def increment(self, queryset, user):
        query = self.objects(pk=user).first()
        if query:
            query.update(uses=(query.uses+1))
        else:
            self(username=user, uses=1).save()
        return


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()
