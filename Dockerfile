FROM python:3.12-slim AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	build-essential \
	gcc

RUN pip install --user packaging

COPY pyproject.toml /app/pyproject.toml
RUN pip download /app/


FROM python:3.12-slim AS runtime-image

COPY --from=compile-image /root/.local /root/.local
COPY . /app

WORKDIR /app
CMD ["python", "main.py"]
