from flask import render_template, request, jsonify, session, g, redirect, url_for
from utils import load_quiz_data, get_quiz_questions, get_question_counts
from models import Book, AnswerHistory, FourChoice,Chapter,Like,Dislike,db
from collections import Counter

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

        # book変数の定義をBookモデルを使って取得するよう更新
        book = Book.query.filter_by(book_id=book_id).first()
        if book:
            book = book.to_dict()

        questions = [q.to_dict() for q in FourChoice.query.filter_by(book_id=book_id).all()]
        
        chapters = []
        chapter_ids = list(set(q['chapter_id'] for q in questions if q['book_id'] == int(book_id)))

        for chapter_id in chapter_ids:
            total_questions = len([q for q in questions if q['chapter_id'] == chapter_id])
            recent_correct_answers = len([ah for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=book_id, chapter_id=chapter_id, is_correct=True).all()])
            
            # ここで章の名前を取得します
            chapter = Chapter.query.filter_by(book_id=book_id, chapter_id=chapter_id).first()
            if chapter:
                chapter_name = chapter.name
            else:
                chapter_name = None

            chapters.append({
                "id": chapter_id,
                "name": chapter_name,
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
    
    @app.route('/save-feedback', methods=['POST'])
    def save_feedback():
        data = request.get_json()
        print("save_feedback", data)
        
        quiz_id = data.get('quiz_id')
        user_id = data.get('user_id')
        reaction_type_id = data.get('reaction_type_id')
        like_dislike = data.get('like_dislike')  # 'like' または 'dislike' の値を持つ
        book_id = data.get('book_id')
        chapter_id = data.get('chapter_id')

        ModelClass = Like if like_dislike == 'like' else Dislike
        feedback = ModelClass(
            quiz_id=quiz_id, 
            user_id=user_id, 
            reaction_type_id=reaction_type_id, 
            book_id=book_id, 
            chapter_id=chapter_id
        )
        
        print("save_feedback", quiz_id, user_id, reaction_type_id, like_dislike, book_id, chapter_id)
        db.session.add(feedback)
        db.session.commit()
        return jsonify(message='Feedback saved successfully'), 200

    @app.route('/management/user-reactions')
    def user_feedback():
        # データベースからlikesとdislikesを取得
        likes = Like.query.all()
        dislikes = Dislike.query.all()

        # 各属性による集計
        likes_summary = Counter([(like.quiz_id, like.book_id, like.chapter_id) for like in likes])
        dislikes_summary = Counter([(dislike.quiz_id, dislike.book_id, dislike.chapter_id) for dislike in dislikes])
        print("user_reactions",likes_summary, dislikes_summary)

        return render_template('user_reactions.html', likes_summary=likes_summary, dislikes_summary=dislikes_summary)


    if __name__ == "__main__":
        with app.app_context():
            db.create_all()
        app.run(debug=True)
