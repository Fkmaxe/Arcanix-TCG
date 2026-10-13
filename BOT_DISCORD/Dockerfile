# Étape 1 : Image de base officielle Python
FROM python:3.11-slim

# Étape 2 : Définir le répertoire de travail
WORKDIR /app

# Étape 3 : Copier les fichiers nécessaires
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier le reste du projet (code bot, modules…)
COPY . .

# Étape 5 : Commande de démarrage
CMD ["python", "bot.py"]