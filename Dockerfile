FROM python:3.6
# Install Python and Package Libraries
RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
RUN apt-get install -y \
    net-tools \
    vim
# Project Files and Settings
RUN mkdir -p /app && mkdir -p /app/static && mkdir -p /app/media
VOLUME ["/app/static", "/app/media"]
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . ./
COPY dndtools/settings_secret.py.template ./dndtools/settings_secret.py
# Server
EXPOSE 8080
STOPSIGNAL SIGINT
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080"]
CMD ["--workers=4", "dndtools.wsgi"]
