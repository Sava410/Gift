from peewee import *

db = SqliteDatabase("stars.db")

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = IntegerField(unique=True)
    stars = IntegerField(default=0)

db.connect()
db.create_tables([User], safe=True)

def add_user_if_not_exists(user_id):
    user, created = User.get_or_create(user_id=user_id)
    return user

def get_stars(user_id):
    user = add_user_if_not_exists(user_id)
    return user.stars

def add_stars(user_id, amount):
    user = add_user_if_not_exists(user_id)
    user.stars += amount
    user.save()

def deduct_stars(user_id, amount):
    user = add_user_if_not_exists(user_id)
    if user.stars >= amount:
        user.stars -= amount
        user.save()
        return True
    return False
