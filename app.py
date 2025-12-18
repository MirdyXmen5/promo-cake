from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.sql import func # func добавлен для отчетов
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
# Импортируем UUID для генерации сложных ключей
import uuid

# --- КОНФИГУРАЦИЯ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid.uuid4()) # Генерируем новый секретный ключ при каждом старте (для продакшена лучше задать один раз)

# ПОДКЛЮЧЕНИЕ К POSTGRESQL (ЛОКАЛЬНО)
# ВАЖНО: При деплое в Docker-Compose нужно будет заменить 'localhost' на 'db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:147852@localhost:5432/promodb'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- МОДЕЛИ БАЗЫ ДАННЫХ ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, index=True) 
    prize_amount = db.Column(db.Integer, default=0) 
    is_used = db.Column(db.Boolean, default=False) 
    used_at = db.Column(db.DateTime, nullable=True) 
    used_by = db.Column(db.String(100), nullable=True) 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- МОДЕЛЬ ЛОГОВ (ОТЧЕТОВ) ---
class ScanLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    username = db.Column(db.String(100)) 
    code_input = db.Column(db.String(100)) 
    status = db.Column(db.String(50)) 
    details = db.Column(db.String(200)) 

# --- РОУТЫ (Без изменений) ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (код логина без изменений) ...
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/check', methods=['POST'])
@login_required
def check_code():
    # ... (логика проверки и записи логов ScanLog, которую мы финализировали) ...
    code_input = request.form.get('code').strip()
    
    status_log = ""
    details_log = ""
    promo = PromoCode.query.filter_by(code=code_input).first()
    template_response = None

    if not promo:
        status_log = "ERROR"
        details_log = "Код не найден"
        template_response = render_template('result.html', status='error', message="Код не найден в системе!")
        
    elif promo.is_used:
        status_log = "USED_AGAIN"
        details_log = f"Попытка повтора. Использован: {promo.used_by}"
        template_response = render_template('result.html', status='warning', message=f"ВНИМАНИЕ! Код УЖЕ использован {promo.used_at} пользователем {promo.used_by}")
        
    else:
        # УСПЕШНАЯ АКТИВАЦИЯ
        promo.is_used = True
        promo.used_at = datetime.datetime.now()
        promo.used_by = current_user.username
        
        if promo.prize_amount > 0:
            status_log = "WIN"
            details_log = f"Выигрыш: {promo.prize_amount}"
            template_response = render_template('result.html', status='win', amount=promo.prize_amount, code=promo.code)
        else:
            status_log = "LOSE"
            details_log = "Без выигрыша"
            template_response = render_template('result.html', status='lose', message="К сожалению, в этом коде нет выигрыша.")
        
        db.session.commit()

    # Запись в историю (Сработает всегда)
    new_log = ScanLog(username=current_user.username, code_input=code_input, status=status_log, details=details_log)
    db.session.add(new_log)
    db.session.commit()

    return template_response

@app.route('/admin_stats')
@login_required
def admin_stats():
    # ... (логика отчетов) ...
    total_scans = ScanLog.query.count()
    total_wins = ScanLog.query.filter_by(status='WIN').count()
    total_money = db.session.query(func.sum(PromoCode.prize_amount)).filter_by(is_used=True).scalar() or 0
    
    logs = ScanLog.query.order_by(ScanLog.timestamp.desc()).limit(50).all()
    
    suspicious = db.session.query(
        ScanLog.username, func.count(ScanLog.id)
    ).filter(ScanLog.status.in_(['ERROR', 'USED_AGAIN'])).group_by(ScanLog.username).order_by(func.count(ScanLog.id).desc()).all()

    return render_template('admin_stats.html', 
                        total_scans=total_scans, 
                        total_wins=total_wins, 
                        total_money=total_money,
                        logs=logs,
                        suspicious=suspicious)

# --- ЗАПУСК (ГЛАВНЫЙ БЛОК) ---
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() теперь создаст все 3 таблицы: User, PromoCode, ScanLog
        db.create_all()
        
        # Создаем тестового админа только если он не существует.
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            print("База создана. Тестовый админ (admin/admin123) добавлен.")
            
    app.run(debug=True, host='0.0.0.0', port=5000)