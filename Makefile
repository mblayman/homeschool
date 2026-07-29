.PHONY: bootstrap docs local

local:
	uv run honcho start -f Procfile

bootstrap:
	npm --prefix frontend i
	uv run manage.py migrate
	uv run manage.py shell -c "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(username='matt').exists() else 1)" || DJANGO_SUPERUSER_PASSWORD=correcthorse uv run manage.py createsuperuser --noinput --username matt --email matt@example.com
	uv run manage.py shell -c "from django.contrib.auth import get_user_model; user = get_user_model().objects.get(username='matt'); user.email = 'matt@example.com'; user.is_staff = True; user.is_superuser = True; user.set_password('correcthorse'); user.save(update_fields=['email', 'is_staff', 'is_superuser', 'password'])"
	uv run manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'localhost:8000'})"
	uv run manage.py shell -c "from homeschool.core.models import Flag; Flag.objects.update_or_create(name='signup_flag', defaults={'everyone': True})"

build:
	docker compose build

shell:
	docker compose run --rm web bash

# For the next time I think about making this faster:
# -n auto --dist loadfile, 8 CPUs, 445 tests, 1m15s
# -n 4    --dist loadfile, 4 CPUs, 445 tests, 43s
# -n 2    --dist loadfile, 4 CPUs, 445 tests, 39s
# no parallelism,                  445 tests, 41s
# With coverage sysmon enabled, -n 2 --dist loadfile ran 499 tests in about 50s.
# More workers were neutral or slower because each worker pays migration setup cost.
coverage:
	uv run pytest --cov=homeschool --migrations -n 2 --dist loadfile

mypy:
	uv run mypy homeschool project manage.py

docs:
	uv run make -C docs html

servedocs:
	cd docs/_build/html && python3 -m http.server
