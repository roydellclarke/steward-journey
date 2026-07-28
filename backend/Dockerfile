FROM python:3.12-alpine

# Links the published image to the repo on the GHCR package page.
LABEL org.opencontainers.image.source="https://github.com/roydellclarke/steward-journey"
LABEL org.opencontainers.image.description="StewardPath backend (FastAPI)"
LABEL org.opencontainers.image.licenses="UNLICENSED"

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir . \
    && apk del .build-deps

ENV STEWARDPATH_DATA_ROOT=/data/stewardpath
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
