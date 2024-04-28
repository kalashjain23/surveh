from flask import Flask, render_template, url_for, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
import pathlib
import textwrap
import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyBVDNwLyrVx1sTUSTnwCy2_lkXZV_ImUZY"

genai.configure(api_key=GOOGLE_API_KEY)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'surveh'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///surveys.db'
db = SQLAlchemy(app)
app.app_context().push()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    surveys = db.relationship('Survey', backref='user', lazy=True)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='survey', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    responses = db.relationship('Response', backref='question', lazy=True)
    
    def get_summary(self):
        responses = [response.text for response in self.responses]
        prompt = "Provide summary of the following responses as a brief paragraph:\n"
        if responses:
            all_responses = " ".join(responses)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt+all_responses)
            
            return response.text
        else:
            return None

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

db.create_all()

@app.route('/create_survey', methods=['GET', 'POST'])
def create_survey():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            user_id = session['user_id']
            survey = Survey(title=title, user_id=user_id)
            db.session.add(survey)
            db.session.commit()

            questions = request.form.getlist('question')
            for question_text in questions:
                question = Question(text=question_text, survey_id=survey.id)
                db.session.add(question)
            db.session.commit()

            return redirect(url_for('index'))

        return render_template('create_survey.html')
    return render_template('landing.html')

@app.route("/survey/fill/<int:survey_id>", methods=['GET', 'POST'])
def survey_form(survey_id):
    if 'user_id' in session:
        survey = Survey.query.get_or_404(survey_id)
        if request.method == 'POST':
            for question in survey.questions:
                answer_text = request.form.get(f"answer_{question.id}")
                if answer_text:
                    response = Response(text=answer_text, question_id=question.id)
                    db.session.add(response)

            db.session.commit()
            flash('Survey submitted successfully!', 'success')
            return redirect(url_for('index'))
        return render_template("survey_form.html", survey=survey)
    return render_template('landing.html')

@app.route("/survey/<int:survey_id>")
def survey_responses(survey_id):
    if 'user_id' in session:
        survey = Survey.query.get(survey_id)
        return render_template("survey_responses.html", survey=survey)
    return render_template('landing.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            print('Please fill in all fields.')
            return redirect(url_for('signup'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print('Username already exists!')
            return 'Username already exists!'

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id

        return redirect(url_for('index'))
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.clear()
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and password == user.password:
            session['user_id'] = user.id
            print('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            print('Invalid username or password. Please try again.')
            return redirect(url_for('login'))

    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            user_surveys = Survey.query.filter_by(user_id=user_id).all()
            return render_template('index.html', user_name=user.name, surveys=user_surveys)
    return render_template('landing.html')

if __name__ == "__main__":
    app.run(debug=True)
    