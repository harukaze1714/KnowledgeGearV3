from models import AnswerHistory, FourChoice,Book, db
from datetime import datetime
from sqlalchemy import desc, func


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

def load_quiz_data(app):
    with app.app_context():
        if not Book.query.first():
            db.session.commit()
        db.create_all()
        books = [b.to_dict() for b in Book.query.all()]
    return books

def get_quiz_questions(book_id, chapter_id, mode,user_id):
    # この部分でデータベースから問題を取得し、モードに基づいてフィルタリングします。

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

