from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, BooleanField, TextField
from flask import Flask, render_template, redirect, url_for, request, jsonify, json
from wtforms.validators import InputRequired, Email, Length
from flask_wtf import FlaskForm, RecaptchaField
from flask_admin.contrib.sqla import ModelView
from kubernetes.client.apis import core_v1_api
from flask_admin import Admin, AdminIndexView
from flask_sqlalchemy  import SQLAlchemy
from kubernetes  import client, config
from flask_bootstrap import Bootstrap
from os import path
import subprocess
import smtplib
import pusher
import random
import yaml
import time

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
config.load_kube_config()
kube = client.ExtensionsV1beta1Api()
api = core_v1_api.CoreV1Api()


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

pusher_client = pusher.Pusher(
  app_id='562264',
  key='0e8bc0c64581e29ed721',
  secret='3b9c25c29e5d3e7d0adc',
  cluster='us2',
  ssl=True
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    message = db.Column(db.String(500))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(15))
    lastname = db.Column(db.String(15))
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    status = db.Column(db.String(5))
    role = db.Column(db.String(5))
    def __repr__(self):
        return '<User %r>' % self.username

class Pynote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    pynotelink = db.Column(db.String(50), unique=True)
    port = db.Column(db.Integer, unique=True)


class myModelView(ModelView):
    def is_accessible(self):
        if current_user.role == "Admin":
            return True
        else:
            return False
    def inaccessible_callback(self, name, **kwargs):
        return "<h2>Sorry you do not have permission for this page <h2>"


class MyAdminIndex(AdminIndexView):
    def is_accessible(self):
        if current_user.role == "Admin":
            return True
        else:
            return False
    def inaccessible_callback(self, name, **kwargs):
        return "<h2>Sorry you do not have permission for this page<h2>"


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')
    recaptcha = RecaptchaField()

class RegisterForm(FlaskForm):
    firstname = StringField('Firstname', validators=[InputRequired(), Length(min=4, max=15)])
    lastname = StringField('Lastname', validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

class QuestionForm(FlaskForm):
    first = StringField('firstname', validators=[InputRequired(),  Length(max=50)])
    last = StringField('lastname', validators=[InputRequired(), Length(min=4, max=15)])
    phone = StringField('phone', validators=[InputRequired(), Length(min=8, max=80)])


def getExternalIp(name):
    while True:
        services = api.list_namespaced_service('students')
        for service in services.items:
            if service.status.load_balancer.ingress:
                return service.status.load_balancer.ingress[0].ip
                break


#Menu for chat
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    messages = Message.query.all()
    return render_template('chat.html', messages=messages, fname=current_user.firstname, lname=current_user.lastname)

@app.route('/message', methods=['POST'])
def message():
    try:
        username = request.form.get('username')
        message = request.form.get('message')

        new_message = Message(username=username, message=message)
        db.session.add(new_message)
        db.session.commit()

        pusher_client.trigger('chat-channel', 'new-message', {'username' : username, 'message': message})
        return jsonify({'result' : 'success'})
    except:
        return jsonify({'result' : 'failure'})


# pynote
@app.route('/pynote', methods=['GET', 'POST'])
@login_required
def pynote():
    servers  = Pynote.query.all()
    if request.form:
        server_name = request.form.get('server-name')
        password = request.form.get('password')

        if Pynote.query.filter_by(username=current_user.username).first():
            return "<h1>Sorry you already requested a server.</h1>"

        with open('kubernetes/pynote-pod.yaml' ) as file:
            deployment = yaml.load(file)

            ## Rename by username
            deployment['metadata']['name'] = current_user.username
            deployment['metadata']['labels']['run'] = current_user.username
            deployment['spec']['containers'][0]['name'] = current_user.username

            ## Set the password for Jupyter pynote
            deployment['spec']['containers'][0]['args'] = [ "/jupyter-runner.py", f"--username={current_user.username}", f"--password={password}"]

            ## Create Pod on Cluster
            pod = api.create_namespaced_pod(body=deployment, namespace="students")

        ## Create a Service
        with open('kubernetes/pynote-service.yaml') as file:
            service = yaml.load(file)
            service['metadata']['labels']['run'] = current_user.username
            service['spec']['selector']['run'] = current_user.username
            service['metadata']['name'] = current_user.username

            object = api.create_namespaced_service(body=service, namespace="students")
            pynotelink = f'http://{getExternalIp(current_user.username)}'

        ## Store request to the DataBase
        new_user = Pynote(username=current_user.username, password=password, server_name=server_name,  pynotelink=pynotelink, port=service['spec']['ports'][0]['port'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(pynotelink)

    return render_template('pynote.html', name=current_user.username, servers=servers)

# Welcome Page
@app.route('/')
def index():
    return render_template('index.html')

#Menu for Videos
@app.route('/videos', methods=['GET', 'POST'])
@login_required
def videos():
    return render_template('videos.html', name=current_user.username)

# Vidoe classes
@app.route('/linux', methods=['GET', 'POST'])
@login_required
def linux():
    return render_template('linux.html', name=current_user.username)

# Docker classes
@app.route('/docker', methods=['GET', 'POST'])
@login_required
def docker():
    return render_template('docker.html', name=current_user.username)

# Scripting classes
@app.route('/script', methods=['GET', 'POST'])
@login_required
def script():
    return render_template('script.html', name=current_user.username)

# Raiting of the user
@app.route('/raiting', methods=['GET', 'POST'])
@login_required
def raiting():
    return render_template('raiting.html', name=current_user.username)

@app.route('/work', methods=['GET', 'POST'])
@login_required
def work():
    return render_template('work.html', name=current_user.username)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', fname=current_user.firstname, lname=current_user.lastname, users=users )

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'firstname' in request.form:
        question = request.form['question']
        phone = request.form['phone']
        with open('question.txt', 'w') as the_file:
            the_file.write(question + '\n' + "This is test")
        subprocess.call(["python", "mail.py"])
        return "<h1>Your QUESTION is submited</h1>"
    return render_template('contact.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, firstname=form.firstname.data, lastname=form.lastname.data,  email=form.email.data, password=hashed_password, status='False')
        if user:
            if user.username == form.username.data:
                return '<h1>This user name is exist</h1>'
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.status == "True":
                if check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('dashboard'))
            elif user.status == "False":
                return render_template('disabled-user.html')
        return '<h1>Invalid username or password</h1>'
    return render_template('login.html', form=form)

@app.route('/disabled-user')
def disabled_user():
    return render_template('disabled-user.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

### Api Block starts from here ####

@app.route('/api/example-users', methods=['GET', 'POST'])
@login_required
def example():
    with open('api/examples/example.json') as file:
        data = json.load(file)
    return jsonify(data)

@app.route('/api/users', methods=['GET'])
def api_users():
    with open('api/examples/example.json') as file:
        data = json.load(file)
    return jsonify(data)


### Api Block ends from here ####

admin = Admin(app, index_view=MyAdminIndex())
admin.add_view(myModelView(User, db.session))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
