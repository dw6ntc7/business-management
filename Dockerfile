# Dockerfile für deine Flask-App
FROM python:3.12-slim

WORKDIR /app

# Kopiere alle Dateien ins Image
COPY . /app

# Installiere Abhängigkeiten
RUN pip install --no-cache-dir flask flask_sqlalchemy flask_migrate reportlab gunicorn

# Exponiere Port 5000
EXPOSE 5000

# Setze Umgebungsvariablen
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Starte die App mit Gunicorn (empfohlen für Produktion)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
