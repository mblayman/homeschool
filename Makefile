.PHONY: local

local:
	heroku local -f Procfile.local

graph:
	./manage.py graph_models core courses schools users -o models.png
