DOCKER=docker compose exec -it minimaker
MANAGE_PY = python manage.py

# 
# Build and Setup
# 
build:
	docker compose pull
	docker compose up --build

docker-migrate:
	$(DOCKER) $(MANAGE_PY) migrate

generate-static-files:
	$(DOCKER) $(MANAGE_PY) collectstatic

docker-down:
	docker compose down -v --remove-orphans ${ARGS}

run-docker:
	docker compose up ${ARGS}

# 
# Debugging/Testing
# 
django-shell:
	$(DOCKER) $(MANAGE_PY) shell_plus --ipython

docker-shell:
	$(DOCKER) /bin/bash


# 
# Linters
# 
format:
	poetry run ruff format

ruff-check:
	poetry run ruff check

ruff-fix:
	poetry run ruff check --fix

lint:
	make format
	make ruff-check