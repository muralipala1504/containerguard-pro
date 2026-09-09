import os
import sys
import gradio as gr
from flask import Flask, redirect, session, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import threading
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# ---------- Flask Auth App ----------
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
    redirect_uri='http://192.168.217.167:7860/oauth2/callback'
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

@app.route('/login')
def login():
    return github.authorize_redirect()

@app.route('/oauth2/callback')
def callback():
    token = github.authorize_access_token()
    resp = github.get('user', token=token)
    user_info = resp.json()
    user = User(str(user_info['id']), user_info['login'], user_info.get('email', ''))
    login_user(user)
    return redirect('/dashboard')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/user')
@login_required
def get_user():
    return jsonify({"username": current_user.username, "email": current_user.email})

# ---------- Gradio Dashboard ----------
def get_user_info():
    """Get current user info from Flask session"""
    try:
        # In a real integration, we'd share the session
        # For now, return a placeholder
        return {"username": "user", "email": "user@example.com"}
    except:
        return {"username": "guest", "email": ""}

def refresh():
    user = get_user_info()
    return f"## 🖥️ Nodes\n\nminikube: Ready", f"## 📦 Pods\n\ntest-pod: Running", f"## 📜 Recent Actions\n\nNo actions recorded yet."

def manual_restart_pod(name):
    return f"✅ Restarted {name}"

def build_dashboard():
    with gr.Blocks(theme=gr.themes.Soft(), title="ContainerGuard") as dashboard:
        gr.Markdown("# 🔐 ContainerGuard Dashboard")
        gr.Markdown("Auto-heal · Monitor · Optimize")
        
        with gr.Row():
            user_status = gr.Markdown("**User**: Guest")
            license_status = gr.Markdown("**License**: Free")
        
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh")
        
        with gr.Row():
            with gr.Column(scale=1):
                nodes_output = gr.Markdown("Loading...")
            with gr.Column(scale=2):
                pods_output = gr.Markdown("Loading...")
        
        with gr.Row():
            history_output = gr.Markdown("Loading...")
        
        with gr.Row():
            pod_name = gr.Textbox(label="Pod Name", placeholder="e.g., test-pod")
            restart_btn = gr.Button("🔄 Restart Pod")
            restart_result = gr.Textbox(label="Result", interactive=False)
        
        refresh_btn.click(refresh, outputs=[nodes_output, pods_output, history_output])
        restart_btn.click(manual_restart_pod, inputs=[pod_name], outputs=[restart_result])
        dashboard.load(refresh, outputs=[nodes_output, pods_output, history_output])
    
    return dashboard

# ---------- Run Combined App ----------
if __name__ == "__main__":
    # Create dashboard
    dashboard = build_dashboard()
    
    # Mount Gradio app on Flask
    app = gr.mount_gradio_app(app, dashboard, path="/dashboard")
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=7860)
