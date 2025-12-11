import csv
from app import app, db, PromoCode

# Имя твоего файла
FILENAME = 'codes.csv'

def import_data():
    # Важно: работаем в контексте приложения, чтобы видеть Базу Данных
    with app.app_context():
        print(f"Начинаю импорт из {FILENAME}...")
        
        try:
            with open(FILENAME, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                
                count = 0
                for row in csv_reader:
                    code_str = row['code'].strip()
                    amount = int(row['amount'])
                    
                    # Проверка: есть ли уже такой код в базе? Чтобы не было дублей.
                    exists = PromoCode.query.filter_by(code=code_str).first()
                    
                    if not exists:
                        new_promo = PromoCode(code=code_str, prize_amount=amount)
                        db.session.add(new_promo)
                        count += 1
                    else:
                        print(f"Дубликат пропущен: {code_str}")
                
                db.session.commit()
                print(f"✅ Успешно добавлено {count} новых кодов!")
                
        except FileNotFoundError:
            print(f"❌ Ошибка: Файл {FILENAME} не найден!")
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")

if __name__ == '__main__':
    import_data()