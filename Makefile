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
