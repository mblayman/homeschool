web: gunicorn project.wsgi --workers 2 --log-file - --bind 0.0.0.0:8000
worker: ./manage.py run_huey --skip-checks
frontend: npm --prefix frontend run watch
