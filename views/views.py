# Flask関連のインポート
from flask import render_template, request, jsonify, session, g, redirect, url_for, flash, Response
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# その他のライブラリ・モジュールのインポート
from utils import load_quiz_data, get_quiz_questions, get_question_counts
from models import Book, AnswerHistory, FourChoice, Chapter, Like, Dislike, User, db
from collections import Counter
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import io


login_manager = LoginManager()
login_manager.login_view = "login"


class LoginForm(FlaskForm):
    username = StringField('ユーザーネーム', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

def dump_databases_to_sql(db_paths):
    output = io.StringIO()

    for db_path in db_paths:
        db_path_clean = db_path.replace('sqlite:///', '')
        with sqlite3.connect(db_path_clean) as con:
            # 変更を確定させる
            con.commit()
            for line in con.iterdump():
                output.write('%s\n' % line)

    output.seek(0)
    return output




def init_views(app):
    login_manager.init_app(app)
    books = load_quiz_data(app)

    @login_manager.user_loader
    def load_user(user_id):
        print("user_id", User.query.get(int(user_id)))
        return User.query.get(int(user_id))
    
    @app.before_request
    def before_request():
        if not hasattr(g, 'quiz_data_loaded'):
            g.quiz_data_loaded = True

    @app.before_request
    def require_login():
        if not current_user.is_authenticated and request.endpoint not in ['login', 'signup', 'static']:
            return redirect(url_for('login'))

        
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        print("login")
        print("current_user.is_authenticated", current_user.is_authenticated)
        print("current_user", current_user)
        
        if current_user.is_authenticated:
            return redirect(url_for('select_book'))
        
        form = LoginForm()
        if request.method == "POST":
            print("form username:", form.username.data)
            print("form password:", form.password.data)

        print(form.validate_on_submit())
        if form.validate_on_submit():
            print("form validate_on_submit")
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                print("login_user(user)")
                return redirect(url_for('select_book'))
            flash('ログイン情報が間違っています。')
        else:
            print("Form Validation Failed:", form.errors)  # This line will print the errors

        
        print("login_error")
        
        return render_template('login.html', form=form)

    

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        print("signup")
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm-password')
            
            # 既に存在するユーザーネームかどうかをチェック
            user = User.query.filter_by(username=username).first()
            if user:
                flash('そのユーザーネームは既に存在しています。')
                return render_template('login.html')  
            
            # パスワードと確認用パスワードが一致しているかを確認
            if password != confirm_password:
                flash('パスワードと確認用パスワードが一致しません。')
                return render_template('login.html')

            # 新しいユーザーアカウントをデータベースに保存
            hashed_password = generate_password_hash(password, method='scrypt')
            new_user = User(username=username, password=hashed_password)
            try:
                db.session.add(new_user)
                db.session.commit()
                print("新しいユーザーID:", new_user.user_id) 
                login_user(new_user)
                flash('アカウントの作成に成功しました！')
                return redirect(url_for('select_book'))
            except Exception as e:
                print("Error during account creation:", e)
                flash('アカウントの作成中にエラーが発生しました。再試行してください。')
                return render_template('login.html')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('ログアウトしました。')
        return redirect(url_for('login'))

    
    @app.route('/')
    def select_book():
        print("select_book",books)
        return render_template('select_book.html', books=books)

    @app.route('/quiz/<book_id>')
    def select_chapter(book_id):
        user_id = current_user.user_id

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
        user_id = current_user.user_id

        review_count, unanswered_count = get_question_counts(user_id, book_id, chapter_id)
        print("review_count unanswered_count:",review_count, unanswered_count)
            
        if request.method == 'POST':
            session['quiz_mode'] = request.form['quiz_mode']
            return redirect(url_for('quiz', book_id=book_id, chapter_id=chapter_id))
        return render_template('quiz_mode_selection.html', book_id=book_id, chapter_id=chapter_id, review_count=review_count, unanswered_count=unanswered_count)


    @app.route('/quiz/<book_id>/<chapter_id>/<mode>')
    def quiz(book_id, chapter_id, mode):
        user_id = current_user.user_id

        questions = get_quiz_questions(int(book_id), int(chapter_id), mode, user_id)
        
        if not questions:
            return "No questions found for this book and chapter", 404

        answer_history = [ah.to_dict() for ah in AnswerHistory.query.filter_by(user_id=user_id, book_id=str(book_id), chapter_id=str(chapter_id)).all()]
        return render_template('quiz.html', questions=[q.to_dict() for q in questions], answer_history=answer_history, questionCount=0, user_id=user_id)



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
    
    @app.route('/download_sql')
    def download_sql():
        # データベースの設定を辞書で持つ

        #/download_sql?db=db1 で mydatabase.db の内容をダウンロード
        #/download_sql?db=db2 で answerdata.db の内容をダウンロード
        database_options = {
            'db1': {
                'path': ['sqlite:///instance/mydatabase.db'],
                'filename': "mydatabase.sql"
            },
            'db2': {
                'path': ['sqlite:///instance/answerdata.db'],
                'filename': "answerdata.sql"
            },
            'combined': {
                'path': ['sqlite:///instance/maindatabase.db', 'sqlite:///instance/mydatabase.db', 'sqlite:///instance/answerdata.db'],
                'filename': "combined_databases.sql"
            }
        }

        # クエリパラメータからdb_nameを取得し、デフォルトとして'combined'を設定
        db_name = request.args.get('db', 'combined')

        # db_nameがdatabase_optionsに存在しない場合はエラーメッセージを返す
        if db_name not in database_options:
            return "Invalid db option provided.", 400

        # 選択されたデータベースの設定を取得
        db_option = database_options[db_name]
        output = dump_databases_to_sql(db_option['path'])

        return Response(
            output.getvalue(),  # StringIOオブジェクトの内容を取得
            mimetype="application/sql",
            headers={"Content-Disposition": f"attachment;filename={db_option['filename']}"}
        )




