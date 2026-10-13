# Étape 1 : Build du projet avec Node.js (builder)
FROM node:18-alpine AS builder

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY package.json package-lock.json* ./

# Installer les dépendances sans les devDependencies
RUN npm install --frozen-lockfile

# Copier tout le reste du code
COPY . .

# Build de l'app Next.js
ENV NEXT_DISABLE_ESLINT=1
RUN npm run build

# Étape 2 : Image allégée pour servir l'app
FROM node:18-alpine AS runner

WORKDIR /app

# Copier uniquement les fichiers nécessaires depuis le builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Démarrage de l'app Next.js
EXPOSE 3000
CMD ["npm", "start"]