1. Create virtualenv and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values.
3. Run migrations and create superuser:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```
4. Run server:
   ```bash
   python manage.py runserver
   ```
5. Admin site: http://127.0.0.1:8000/admin/ to manage PollingStations and users.
