import csv
from werkzeug.security import generate_password_hash
from app import app, db, User

FILENAME = 'users.csv'

def import_users():
    with app.app_context():
        # Сначала создадим таблицы, если их нет
        db.create_all()
        
        try:
            with open(FILENAME, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                count = 0
                for row in csv_reader:
                    username = row['username'].strip()
                    # ВАЖНО: Хешируем пароль! В базе будет лежать абракадабра, а не "pass123"
                    pwd_hash = generate_password_hash(row['password'].strip())
                    
                    # Проверяем, есть ли такой юзер
                    existing = User.query.filter_by(username=username).first()
                    
                    if not existing:
                        new_user = User(username=username, password_hash=pwd_hash)
                        db.session.add(new_user)
                        count += 1
                        print(f"Добавлен: {username}")
                    else:
                        print(f"Обновляем пароль для: {username}")
                        existing.password_hash = pwd_hash # Обновим пароль если юзер есть
                        
                db.session.commit()
                print(f"✅ Обработано {count} новых пользователей.")
                
        except FileNotFoundError:
            print(f"Файл {FILENAME} не найден!")

if __name__ == '__main__':
    import_users()