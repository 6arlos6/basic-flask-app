import sys

sys.path.insert(0, '/home/Analisis/basic-flask-app')

activate_this = '/home/Analisis/.local/share/virtualenvs/home-x9zZxZME/bin/activate_this.py'
# /home/Analisis/.local/share/virtualenvs/basic-flask-app-joBq_XcM

with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from src.app import app as application

if __name__ == '__main__':
    # Aquí puedes configurar la app si es necesario
    application.run(host='localhost', port=5000)


