FROM node:20-alpine

WORKDIR /app

# Instalar dependências primeiro para aproveitar o cache do Docker
COPY package.json package-lock.json* ./
RUN npm install

# Copiar o resto da aplicação
COPY . .

# Expor a porta que o Vite usa
EXPOSE 5173

# Iniciar o Vite expondo para todas as interfaces de rede do container
CMD ["npm", "run", "dev", "--", "--host"]
