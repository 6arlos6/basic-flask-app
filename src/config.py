class Config:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'


class DevelopmentConfig(Config):
    DEBUG = True
    #SESSION_COOKIE_DOMAIN = False
    #SESSION_COOKIE_SECURE = False 
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'flask_login'
    UPLOAD_FOLDER = 'src\data' # Carpeta de carga de datos.


config = {
    'development': DevelopmentConfig
}
