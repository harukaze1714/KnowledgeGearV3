from flask import Flask, redirect, url_for, render_template, request, jsonify, session, g
import random
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.sql.expression import func
from models import Book, FourChoice, AnswerHistory,db
from views.views import init_views


app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maindatabase.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///mydatabase.db',
    'db2': 'sqlite:///answerdata.db'
}

db.init_app(app)
init_views(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
