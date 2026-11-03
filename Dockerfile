FROM python:3.14-slim-trixie
ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.5.1

RUN pip install --no-cache-dir --upgrade pip

RUN apt-get update \
&& apt-get install -y --no-install-recommends curl \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL "https://install.python-poetry.org" -o install-poetry.py \
    && python install-poetry.py \
    && rm install-poetry.py

ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /app
RUN mkdir ./static

VOLUME ["/app/static"]

COPY pyproject.toml poetry.lock manage.py README.md /app/

RUN --mount=type=cache,target=${POETRY_CACHE_DIR} poetry install --no-root

COPY dndtools/ dndtools
COPY nginx/ nginx
COPY paperminis/ paperminis
COPY templates/ templates
COPY tokens/ tokens

# Server
EXPOSE 8080

ENTRYPOINT [ \
  "poetry", "run", \
  "gunicorn", \
  "--bind", \
  "0.0.0.0:8080" \
]
CMD ["--workers=4", "dndtools.wsgi"]
