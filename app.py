from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# --- КОНФИГУРАЦИЯ ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me' # Поменяй на что-то сложное!
# СТАЛО (PostgreSQL):
# Формат: postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
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
    code = db.Column(db.String(50), unique=True, index=True) # Сам QR-код (строка)
    prize_amount = db.Column(db.Integer, default=0) # Сумма выигрыша (0 если нет приза)
    is_used = db.Column(db.Boolean, default=False) # Использован ли?
    used_at = db.Column(db.DateTime, nullable=True) # Когда использовали
    used_by = db.Column(db.String(100), nullable=True) # Кто активировал (имя директора)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- МАРШРУТЫ (РОУТЫ) ---

@app.route('/')
@login_required
def index():
    # Главная страница - поле для ввода кода
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    code_input = request.form.get('code').strip()
    
    # Ищем код в базе
    promo = PromoCode.query.filter_by(code=code_input).first()

    if not promo:
        return render_template('result.html', status='error', message="Код не найден в системе!")

    if promo.is_used:
        return render_template('result.html', status='warning', message=f"ВНИМАНИЕ! Код УЖЕ использован {promo.used_at} пользователем {promo.used_by}")

    # Если код найден и не использован - АКТИВИРУЕМ
    promo.is_used = True
    promo.used_at = datetime.datetime.now()
    promo.used_by = current_user.username
    db.session.commit()

    if promo.prize_amount > 0:
        return render_template('result.html', status='win', amount=promo.prize_amount, code=promo.code)
    else:
        return render_template('result.html', status='lose', message="К сожалению, в этом коде нет выигрыша.")

# --- ЗАПУСК И СОЗДАНИЕ БД ---
# В продакшене эту часть нужно убрать и делать через init_db
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создадим тестового директора, если нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            # Создадим пару тестовых кодов
            db.session.add(PromoCode(code='WIN1000', prize_amount=1000))
            db.session.add(PromoCode(code='LOSE001', prize_amount=0))
            db.session.commit()
            print("База создана, админ добавлен (admin/admin123)")
            
    app.run(debug=True, host='0.0.0.0', port=5000)