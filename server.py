from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura' # Necessária para gerir sessões de login

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
USERS_FILE = os.path.join(UPLOAD_FOLDER, 'users.json')

# Funções auxiliares para gerir utilizadores
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# HTML para Login e Registo
AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - LocalServer</title>
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --accent: #3b82f6; --accent-hover: #2563eb; --text-main: #f8fafc; --text-muted: #94a3b8; --border-color: #334155; --danger: #ef4444; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .auth-card { background-color: var(--card-bg); border: 1px solid var(--border-color); padding: 32px; border-radius: 12px; width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 20px; }
        h2 { text-align: center; color: var(--accent); }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        label { font-size: 0.9rem; color: var(--text-muted); }
        input { background: var(--bg-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 6px; color: var(--text-main); outline: none; }
        input:focus { border-color: var(--accent); }
        button { background-color: var(--accent); color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { background-color: var(--accent-hover); }
        .error { color: var(--danger); font-size: 0.85rem; text-align: center; }
        .switch-link { text-align: center; font-size: 0.9rem; color: var(--text-muted); }
        .switch-link a { color: var(--accent); text-decoration: none; }
    </style>
</head>
<body>
    <div class="auth-card">
        <h2>{{ title }}</h2>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Utilizador</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group" style="margin-top: 15px;">
                <label>Palavra-passe</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" style="margin-top: 20px; width: 100%;">{{ btn_text }}</button>
        </form>
        <div class="switch-link">
            {{ switch_text | safe }}
        </div>
    </div>
</body>
</html>
"""

# HTML do Gestor de Ficheiros (Com botão de Logout)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestor de Ficheiros Local</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --accent: #3b82f6; --accent-hover: #2563eb; --text-main: #f8fafc; --text-muted: #94a3b8; --border-color: #334155; --danger: #ef4444; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); display: flex; min-height: 100vh; }
        aside { width: 260px; background-color: var(--card-bg); border-right: 1px solid var(--border-color); padding: 24px; display: flex; flex-direction: column; justify-content: space-between; }
        .top-side { display: flex; flex-direction: column; gap: 24px; }
        .logo { display: flex; align-items: center; gap: 12px; font-size: 1.25rem; font-weight: bold; color: var(--accent); }
        .nav-menu { list-style: none; display: flex; flex-direction: column; gap: 8px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; color: var(--text-muted); text-decoration: none; cursor: pointer; transition: 0.2s; }
        .nav-item:hover, .nav-item.active { background-color: rgba(59, 130, 246, 0.1); color: var(--accent); }
        .logout-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; color: var(--danger); text-decoration: none; background: rgba(239, 68, 68, 0.1); font-weight: 600; transition: 0.2s; }
        .logout-btn:hover { background: rgba(239, 68, 68, 0.2); }
        main { flex: 1; padding: 32px; overflow-y: auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .search-bar { display: flex; align-items: center; gap: 8px; background-color: var(--card-bg); border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 8px; width: 300px; }
        .search-bar input { background: none; border: none; color: var(--text-main); outline: none; width: 100%; }
        .upload-wrapper { position: relative; overflow: hidden; display: inline-block; }
        .btn-upload { background-color: var(--accent); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; }
        .upload-wrapper input[type=file] { position: absolute; left: 0; top: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
        .section-title { font-size: 1.1rem; margin-bottom: 16px; color: var(--text-muted); }
        .files-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
        .file-card { background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px; transition: 0.2s; text-decoration: none; color: inherit; }
        .file-card:hover { transform: translateY(-2px); border-color: var(--accent); }
        .file-icon { width: 40px; height: 40px; background-color: rgba(59, 130, 246, 0.1); color: var(--accent); border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        .file-info { display: flex; flex-direction: column; }
        .file-name { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .file-meta { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
    </style>
</head>
<body>
    <aside>
        <div class="top-side">
            <div class="logo">
                <i data-lucide="hard-drive"></i>
                <span>LocalServer</span>
            </div>
            <ul class="nav-menu">
                <li class="nav-item active" onclick="filterCategory('all')">
                    <i data-lucide="folder"></i>
                    <span>Todos os Ficheiros</span>
                </li>
                <li class="nav-item" onclick="filterCategory('doc')">
                    <i data-lucide="file-text"></i>
                    <span>Documentos</span>
                </li>
                <li class="nav-item" onclick="filterCategory('img')">
                    <i data-lucide="image"></i>
                    <span>Imagens</span>
                </li>
            </ul>
        </div>
        <a href="/logout" class="logout-btn">
            <i data-lucide="log-out"></i>
            <span>Terminar Sessão ({{ user }})</span>
        </a>
    </aside>

    <main>
        <header>
            <div class="search-bar">
                <i data-lucide="search" style="color: var(--text-muted);"></i>
                <input type="text" id="searchInput" onkeyup="filterFiles()" placeholder="Pesquisar ficheiros...">
            </div>
            <form action="/upload" method="post" enctype="multipart/form-data" id="uploadForm">
                <div class="upload-wrapper">
                    <button type="button" class="btn-upload">
                        <i data-lucide="upload"></i>
                        Carregar Ficheiro
                    </button>
                    <input type="file" name="file" onchange="document.getElementById('uploadForm').submit();">
                </div>
            </form>
        </header>

        <h2 class="section-title">Ficheiros Disponíveis</h2>

        <div class="files-grid" id="filesGrid">
            {% for file in files %}
            <a href="/files/{{ file.name }}" target="_blank" class="file-card" data-name="{{ file.name.lower() }}" data-type="{{ file.type }}">
                <div class="file-icon">
                    <i data-lucide="{{ file.icon }}"></i>
                </div>
                <div class="file-info">
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-meta">{{ file.size }}</span>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>

    <script>
        lucide.createIcons();
        function filterFiles() {
            let input = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.file-card').forEach(card => {
                let name = card.getAttribute('data-name');
                card.style.display = name.includes(input) ? 'flex' : 'none';
            });
        }
        function filterCategory(cat) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.querySelectorAll('.file-card').forEach(card => {
                let type = card.getAttribute('data-type');
                if (cat === 'all') card.style.display = 'flex';
                else if (cat === 'doc' && ['txt', 'pdf', 'docx', 'py', 'html'].includes(type)) card.style.display = 'flex';
                else if (cat === 'img' && ['png', 'jpg', 'jpeg', 'gif'].includes(type)) card.style.display = 'flex';
                else card.style.display = 'none';
            });
        }
    </script>
</body>
</html>
"""

def get_file_info(filename):
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    icon = 'file'
    if ext in ['png', 'jpg', 'jpeg', 'gif']: icon = 'image'
    elif ext in ['txt', 'pdf', 'doc', 'docx']: icon = 'file-text'
    elif ext in ['py', 'html', 'js', 'css']: icon = 'code'
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    size_kb = f"{round(size_bytes / 1024, 1)} KB" if size_bytes > 0 else "0 KB"
    
    return {'name': filename, 'icon': icon, 'type': ext, 'size': size_kb}

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        
        if username in users and check_password_hash(users[username], password):
            session['user'] = username
            return redirect(url_for('index'))
        error = 'Utilizador ou palavra-passe incorretos.'
        
    return render_template_string(AUTH_TEMPLATE, title='Iniciar Sessão', btn_text='Entrar', switch_text='Não tens conta? <a href="/register">Regista-te</a>', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        
        if username in users:
            error = 'Esse nome de utilizador já existe.'
        else:
            users[username] = generate_password_hash(password)
            save_users(users)
            session['user'] = username
            return redirect(url_for('index'))
            
    return render_template_string(AUTH_TEMPLATE, title='Criar Conta', btn_text='Registar', switch_text='Já tens conta? <a href="/login">Entra aqui</a>', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    ignored = ['server.py', 'index.html', 'users.json', '__pycache__']
    all_files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and f not in ignored]
    files_data = [get_file_info(f) for f in all_files]
    return render_template_string(DASHBOARD_TEMPLATE, files=files_data, user=session['user'])

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return redirect(url_for('index'))

@app.route('/files/<filename>')
def download_file(filename):
    if 'user' not in session:
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)