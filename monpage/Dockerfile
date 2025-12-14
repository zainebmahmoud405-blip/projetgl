FROM python:3.9-slim

WORKDIR /app

# Affiche le contenu du dossier pour vérifier la copie
COPY requirements.txt .
RUN ls -la && cat requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]