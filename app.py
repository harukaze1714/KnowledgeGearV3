from flask import Flask
from models import db
from views.views import init_views

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some_secret_key'  # こちらを使用します
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maindatabase.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///mydatabase.db',
    'db2': 'sqlite:///answerdata.db'
}

db.init_app(app)
with app.app_context():
    db.create_all()
init_views(app)

if __name__ == "__main__":
    with app.app_context():
        # DB関連の初期化処理やマイグレーションはここに記述されるでしょう
        pass  # この行は仮のもので、必要に応じて変更・削除してください

    app.run()
