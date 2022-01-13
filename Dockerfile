# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10.1-bullseye

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY /requirements requirements/
RUN python -m pip install -r requirements/production.txt

WORKDIR /app
COPY . /app

RUN python /app/manage.py collectstatic --noinput
RUN python /app/manage.py migrate


# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:80", "config.wsgi"]
#/usr/local/bin/gunicorn config.wsgi --bind 0.0.0.0:80 --chdir=/app