First u have to run venv:
myenv\Scripts\activate

Then install requirements:
pip install -r requirements.txt

Then run docker compose:
docker compose up -d

Then run app:
python app.py

Then import codes and users:
python import_codes.py
python import_users.py