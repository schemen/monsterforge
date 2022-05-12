FROM python:3.9-slim
ENV PYTHONUNBUFFERED 1
#RUN apt update; apt install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
# Project Files and Settings
RUN mkdir -p /app && mkdir -p /app/static
VOLUME ["/app/static"]
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
COPY dndtools/settings_secret.py.template ./dndtools/settings_secret.py
# Server
EXPOSE 8080
STOPSIGNAL SIGINT
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080"]
CMD ["--workers=4", "dndtools.wsgi"]
