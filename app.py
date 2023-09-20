from flask import Flask
from models import  db
from views.views import init_views
#from flask_migrate import Migrate, upgrade

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maindatabase.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///mydatabase.db',
    'db2': 'sqlite:///answerdata.db'
}

db.init_app(app)
#migrate = Migrate(app, db)
init_views(app)

if __name__ == "__main__":
    with app.app_context():
        print()
        #db.create_all()
        #upgrade()

    #init_views(app)
    app.run()
