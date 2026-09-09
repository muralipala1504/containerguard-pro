import os
from flask import Flask, redirect, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
    redirect_uri='http://192.168.217.167:7861/oauth2/callback'
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, 'user', 'user@example.com')

@app.route('/')
def home():
    if current_user.is_authenticated:
        return f'Hello, {current_user.username}! <a href="/logout">Logout</a> | <a href="/dashboard">Dashboard</a>'
    return '<a href="/login">Login with GitHub</a>'

@app.route('/login')
def login():
    return github.authorize_redirect(redirect_uri='http://192.168.217.167:7861/oauth2/callback')

@app.route('/oauth2/callback')
def callback():
    token = github.authorize_access_token()
    resp = github.get('user', token=token)
    user_info = resp.json()
    user = User(str(user_info['id']), user_info['login'], user_info.get('email', ''))
    login_user(user)
    return redirect('/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/user')
@login_required
def get_user():
    return jsonify({"username": current_user.username, "email": current_user.email})

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect('http://192.168.217.167:7860/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7861)
