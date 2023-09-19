from flask import render_template, request, jsonify, session, g, redirect, url_for
from utils import load_quiz_data, get_quiz_questions, get_question_counts
from models import Book, AnswerHistory, FourChoice

def init_views(app):
    books = load_quiz_data(app)
    
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
