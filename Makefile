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
		notifications \
		referrals \
		schools \
		students \
		users \
		-o models.png

# For the next time I think about making this faster:
# -n auto --dist loadfile, 8 CPUs, 445 tests, 1m15s
# -n 4    --dist loadfile, 4 CPUs, 445 tests, 43s
# -n 2    --dist loadfile, 4 CPUs, 445 tests, 39s
# no parallelism,                  445 tests, 41s
coverage:
	pytest --cov=homeschool --migrations -n 2 --dist loadfile

# fcof == "fast coverage" by skipping migrations checking. Save that for CI.
# -n 8 --dist loadfile, 8 CPUs, 515 tests, 20s
# -n 4 --dist loadfile, 4 CPUs, 515 tests, 13s
# -n 2 --dist loadfile, 4 CPUs, 515 tests, 15s
fcov:
	@echo "Running fast coverage check"
	@pytest --cov=homeschool -n 4 --dist loadfile -q

mypy:
	mypy homeschool project manage.py

docs:
	make -C docs html

servedocs:
	cd docs/_build/html && python3 -m http.server
