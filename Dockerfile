FROM python:3.12-slim AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	build-essential \
	gcc

RUN pip install pip-tools

# module 'packaging' is required for 'mgrs' at runtime
# it has to be forcefully installed because it is also installed by 'pip-tools'
RUN pip install --user --force packaging

COPY pyproject.toml /app/pyproject.toml
RUN pip-compile -o requirements.txt /app/pyproject.toml
RUN pip install --user -r requirements.txt


FROM python:3.12-slim AS runtime-image

COPY --from=compile-image /root/.local /root/.local
COPY . /app

WORKDIR /app
CMD ["python", "main.py"]
