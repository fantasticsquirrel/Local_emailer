run:
	uvicorn protonmailer.main:app --host 127.0.0.1 --port 8000 --reload

test:
	pytest
