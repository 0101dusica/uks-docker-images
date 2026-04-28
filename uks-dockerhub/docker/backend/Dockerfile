# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy requirements.txt from backend folder in project root
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend code from backend folder in project root
COPY backend .

RUN mkdir -p /app/logs

ENV DJANGO_SETTINGS_MODULE=config.settings.docker

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
