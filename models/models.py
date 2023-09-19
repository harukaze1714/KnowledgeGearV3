from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FourChoice(db.Model):
    __bind_key__ = 'db1'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    chapter_id = db.Column(db.Integer, nullable=False)
    quiz_id = db.Column(db.Integer, nullable=False)
    question = db.Column(db.String(255), nullable=False)
    option_A = db.Column(db.String(255), nullable=False)
    option_B = db.Column(db.String(255), nullable=False)
    option_C = db.Column(db.String(255), nullable=False)
    option_D = db.Column(db.String(255), nullable=False)
    ans = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "chapter_id": self.chapter_id,
            "quiz_id": self.quiz_id,
            "question": self.question,
            "option_A": self.option_A,
            "option_B": self.option_B,
            "option_C": self.option_C,
            "option_D": self.option_D,
            "answer": self.ans,
            "explanation": self.explanation
        }

class Book(db.Model):
    __bind_key__ = 'db1'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "name": self.name
        }
    
class Chapter(db.Model):
    __bind_key__ = 'db1'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    chapter_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "chapter_id": self.chapter_id,
            "name": self.name,
        }


class AnswerHistory(db.Model):
    __bind_key__ = 'db2'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    chapter_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    quiz_id = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "chapter_id": self.chapter_id,
            "user_id": self.user_id,
            "quiz_id": self.quiz_id,
            "answer": self.answer,
            "is_correct": self.is_correct,
            "timestamp": self.timestamp.isoformat()
        }
    
class Like(db.Model):
    __bind_key__ = 'db2'
    lid = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    reaction_type_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=True)  # 新しい列を追加
    chapter_id = db.Column(db.Integer, nullable=True)  # 新しい列を追加

class Dislike(db.Model):
    __bind_key__ = 'db2'
    did = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    reaction_type_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=True)  # 新しい列を追加
    chapter_id = db.Column(db.Integer, nullable=True)  # 新しい列を追加

