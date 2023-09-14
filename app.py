from flask import Flask, redirect, url_for
from flask import Flask, render_template, request, jsonify, session, g
import random
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.sql.expression import func

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maindatabase.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db1': 'sqlite:///mydatabase.db',
    'db2': 'sqlite:///answerdata.db'
}
db = SQLAlchemy(app)


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

def get_latest_answers_subquery(user_id, book_id, chapter_id):
    print("get_latest_answers_subquery",user_id, book_id, chapter_id)
    sub = AnswerHistory.query.with_entities(
    AnswerHistory.quiz_id, func.max(
        AnswerHistory.timestamp).label('latest')
    ).filter(
    AnswerHistory.user_id == user_id, 
    AnswerHistory.book_id == book_id, 
    AnswerHistory.chapter_id == chapter_id
    ).group_by(AnswerHistory.quiz_id).all()
    
    print(sub)

    sub = AnswerHistory.query.with_entities(
        AnswerHistory.quiz_id,func.max(
            AnswerHistory.timestamp).label('latest')).filter(
                AnswerHistory.user_id == user_id, 
                AnswerHistory.book_id == book_id, 
                AnswerHistory.chapter_id == chapter_id).group_by(AnswerHistory.quiz_id).subquery()
    return sub

def get_latest_incorrect_answers(user_id, book_id, chapter_id):
    print("get_latest_incorrect_answers",user_id, book_id, chapter_id)

    subquery = get_latest_answers_subquery(user_id, book_id, chapter_id)
    
    answers = db.session.query(AnswerHistory).join(
        subquery, 
        db.and_(
            AnswerHistory.quiz_id == subquery.c.quiz_id, 
            AnswerHistory.timestamp == subquery.c.latest, 
            AnswerHistory.is_correct == False
        )
    ).order_by(
        func.random()
    ).all()

    quiz_ids = [answer.quiz_id for answer in answers]
    questions = FourChoice.query.filter(
        FourChoice.book_id == book_id, 
        FourChoice.chapter_id == chapter_id, 
        FourChoice.quiz_id.in_(quiz_ids)
    ).limit(10).all()

    return questions

def get_unanswered_questions(user_id, book_id, chapter_id):
    # すべての問題を取得します
    all_questions = FourChoice.query.filter(
        FourChoice.book_id == book_id, 
        FourChoice.chapter_id == chapter_id
    ).all()
    
    # ユーザーの回答履歴を取得します
    answered_quiz_ids = [ah.quiz_id for ah in AnswerHistory.query.filter_by(
        user_id=user_id, 
        book_id=book_id, 
        chapter_id=chapter_id
    ).all()]

    # 回答されていない質問をフィルタリングします
    unanswered_questions = [q for q in all_questions if q.quiz_id not in answered_quiz_ids]

    return unanswered_questions[:10]
    

def get_question(user_id, book_id, chapter_id):
    print("get_latest_correct_answers",user_id, book_id, chapter_id)

    questions = FourChoice.query.filter(
        FourChoice.book_id == book_id, 
        FourChoice.chapter_id == chapter_id, 
    ).order_by(
        func.random()
    ).limit(10).all()

    return questions

def load_quiz_data():
    with app.app_context():
        if not Book.query.first():
            book1 = Book(book_id=99, name="Book 1")
            db.session.add(book1)
            db.session.commit()
        db.create_all()
        books = [b.to_dict() for b in Book.query.all()]
    return books

def get_quiz_questions(book_id, chapter_id, mode):
    # この部分でデータベースから問題を取得し、モードに基づいてフィルタリングします。
    user_id=1
    print("get_quiz_questions",book_id, chapter_id, mode)

    if mode == 'review':
        questions = get_latest_incorrect_answers(user_id, book_id, chapter_id)
    elif mode == 'unanswered':
        questions = get_unanswered_questions(user_id, book_id, chapter_id)
    else :
        questions = get_question(user_id, book_id, chapter_id)
    return questions

def get_question_counts(user_id, book_id, chapter_id):
    review_count = len(get_latest_incorrect_answers(user_id, book_id, chapter_id))
    unanswered_count = len(get_unanswered_questions(user_id, book_id, chapter_id))
    return review_count, unanswered_count


books = load_quiz_data()

@app.before_request
def before_request():
    if not hasattr(g, 'quiz_data_loaded'):
        g.quiz_data_loaded = True

@app.route('/')
def select_book():
    print("select_book",books)
    return render_template('select_book.html', books=books)

@app.route('/quiz/<book_id>')
def select_chapter(book_id):
    user_id = 1  # ここで適切なユーザーIDを取得します
    
    questions = [q.to_dict() for q in FourChoice.query.filter_by(book_id=book_id).all()]
    book = next((b for b in books if b['book_id'] == int(book_id)), None)

    chapters = []
    chapter_ids = list(set(q['chapter_id'] for q in questions if q['book_id'] == int(book_id)))

    for chapter_id in chapter_ids:
        total_questions = len([q for q in questions if q['chapter_id'] == chapter_id])
        recent_correct_answers = len([ah for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=book_id, chapter_id=chapter_id, is_correct=True).all()])
        
        chapters.append({
            "id": chapter_id,
            "total_questions": total_questions,
            "recent_correct_answers": recent_correct_answers
        })
        
    return render_template('select_chapter.html', chapters=chapters, book=book, book_id=book_id)


@app.route('/quiz/<book_id>/<chapter_id>/quiz_mode_selection/', methods=['GET', 'POST'])
def quiz_mode_selection(book_id, chapter_id):
    user_id = 1
    review_count, unanswered_count = get_question_counts(user_id, book_id, chapter_id)
    print("review_count unanswered_count:",review_count, unanswered_count)
          
    if request.method == 'POST':
        session['quiz_mode'] = request.form['quiz_mode']
        return redirect(url_for('quiz', book_id=book_id, chapter_id=chapter_id))
    return render_template('quiz_mode_selection.html', book_id=book_id, chapter_id=chapter_id, review_count=review_count, unanswered_count=unanswered_count)


@app.route('/quiz/<book_id>/<chapter_id>/<mode>')
def quiz(book_id, chapter_id, mode):
    user_id = 1  
    print("quiz",book_id, chapter_id, mode)
    questions = get_quiz_questions(int(book_id), int(chapter_id), mode)
    
    if not questions:
        return "No questions found for this book and chapter", 404
    print("quiz2",book_id, chapter_id, mode, questions)
    answer_history = [ah.to_dict() for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=str(book_id), chapter_id=str(chapter_id)).all()]
    return render_template('quiz.html', questions=[q.to_dict() for q in questions], answer_history=answer_history, questionCount=0)



@app.route('/score_page/<int:book_id>/<int:chapter_id>')
def score_page(book_id, chapter_id):
    return render_template('score_page.html', book_id=book_id, chapter_id=chapter_id)



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
    with app.app_context():
        db.create_all()
    app.run(debug=True)
