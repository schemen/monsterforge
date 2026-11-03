runDevenv:
	docker compose build && docker compose up app

stopDevenv:
	docker compose down app