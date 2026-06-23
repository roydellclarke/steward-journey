FROM python:3.12-alpine

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir . \
    && apk del .build-deps

ENV STEWARDPATH_DATA_ROOT=/data/stewardpath
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
