setup:
	poetry install

docker-setup:
	poetry install --no-interaction --no-ansi
	
test:
	poetry run pytest

tox-test:
	poetry run tox

docs:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build

clean:
	rm -rf .tox
	rm -rf site
	rm -rf dist
	rm -rf */.pytest_cache
	rm -rf */__pycache__
	rm -rf .pytest_cache
	rm -rf __pycache__

export:
	poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt

django-migrate:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate

django-start-dev:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate
	poetry run python -Wd src/manage.py create_superuser_if_none_exists \
	 --username ${DJANGO_SUPERUSER_USERNAME} --email ${DJANGO_SUPERUSER_EMAIL} --password ${DJANGO_SUPERUSER_PASSWORD}
	poetry run python -Wd src/manage.py loaddata src/umlars_app/fixtures/uml_models_data.json
	nohup poetry run python -Wd src/manage.py launch_queue_listeners > logs/queue_listeners.log 2>&1 &
	poetry run python -Wd src/manage.py runserver 0.0.0.0:8000

django-start:
	poetry run python -Wd src/manage.py makemigrations
	poetry run python -Wd src/manage.py migrate
	poetry run python -Wd src/manage.py create_superuser_if_none_exists \
	 --username ${DJANGO_SUPERUSER_USERNAME} --email ${DJANGO_SUPERUSER_EMAIL}
	nohup poetry run python -Wd src/manage.py launch_queue_listeners > logs/queue_listeners.log 2>&1 &
	poetry run python -Wd src/manage.py runserver 0.0.0.0:8000


.PHONY: setup setup-docker tests tox-test docs clean export
