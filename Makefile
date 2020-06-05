.PHONY: local

local:
	heroku local -f Procfile.local

graph:
	./manage.py graph_models \
		core \
		courses \
		schools \
		students \
		users \
		-o models.png

coverage:
	coverage run --source='homeschool' -m pytest
	coverage report

mypy:
	mypy homeschool project manage.py
