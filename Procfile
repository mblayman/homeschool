release: python manage.py migrate
web: gunicorn project.wsgi --workers 2 --log-file -
