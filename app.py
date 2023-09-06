from flask import Flask, render_template, request, jsonify,g
import random
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
db = SQLAlchemy(app)

class AnswerHistory(db.Model):
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

class FourChoice(db.Model):
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

def load_quiz_data():
    with app.app_context():
        db.create_all()
        questions = [q.to_dict() for q in FourChoice.query.all()]
        print(f"Loaded {len(questions)} questions from database")
    return questions

@app.before_request
def before_request():
    if not hasattr(g, 'quiz_data_loaded'):
        g.quiz_data_loaded = True

questions = load_quiz_data()


@app.route('/')
def select_book():
    book_ids = list(set(q['book_id'] for q in questions))
    return render_template('select_book.html', book_ids=book_ids)


@app.route('/select_chapter/<book_id>')
def select_chapter(book_id):
    chapter_ids = list(set(q['chapter_id'] for q in questions if q['book_id'] == int(book_id)))
    return render_template('select_chapter.html', chapter_ids=chapter_ids, book_id=book_id)


@app.route('/quiz/<book_id>/<chapter_id>')
def quiz(book_id, chapter_id):
    user_id = 1  
    
    selected_questions = [q for q in questions if q['book_id'] == int(book_id) and q['chapter_id'] == int(chapter_id)]
    
    if not selected_questions:
        return "No questions found for this book and chapter", 404

    question = random.choice(selected_questions)

    answer_history = [ah.to_dict() for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=str(book_id), chapter_id=str(chapter_id)).all()]
    return render_template('quiz.html', question=question, answer_history=answer_history)

@app.route('/save-answer', methods=['POST'])
def save_answer():
    data = request.json
    answer = AnswerHistory(
        user_id=data['user_id'],
        book_id=data['book_id'],
        chapter_id=data['chapter_id'],
        quiz_id=data['quiz_id'],
        answer=data['answer'],
        is_correct=data['is_correct']
    )
    db.session.add(answer)
    db.session.commit()

    # 現在のユーザーの回答履歴を取得
    answer_history = [ah.to_dict() for ah in AnswerHistory.query.filter_by(user_id=data['user_id'], book_id=data['book_id'], chapter_id=data['chapter_id']).all()]
    return jsonify({'message': 'Answer saved successfully', 'answer_history': answer_history}), 201

@app.route('/get-answer-history', methods=['POST'])
def get_answer_history():
    data = request.json
    user_id = data['user_id']
    book_id = data['book_id']
    chapter_id = data['chapter_id']

    answer_history = [ah.to_dict() for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=book_id, chapter_id=chapter_id).all()]
    return jsonify({'answer_history': answer_history}), 200

if __name__ == "__main__":
    app.run(debug=True)
