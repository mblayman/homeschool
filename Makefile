.PHONY: docs local

local:
	heroku local

deploy:
	git push heroku master

graph:
	./manage.py graph_models \
		accounts \
		core \
		courses \
		schools \
		students \
		users \
		-o models.png

coverage:
	coverage run --source='homeschool' -m pytest --migrations
	coverage report

mypy:
	mypy homeschool project manage.py

docs:
	make -C docs html

servedocs:
	cd docs/_build/html && python3 -m http.server
