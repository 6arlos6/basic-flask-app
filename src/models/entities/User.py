from werkzeug.security import check_password_hash
from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, id, username, password, fullname="", rol="",fecha_mod = "") -> None:
        self.id = id
        self.username = username
        self.password = password
        self.fullname = fullname
        self.rol = rol
        self.fecha_mod = fecha_mod 

    @classmethod
    def check_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)
