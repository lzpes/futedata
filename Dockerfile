FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema para o PyMSSQL (FreeTDS)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências
COPY . /app/

# Instalar os pacotes necessários da API
RUN pip install --no-cache-dir fastapi uvicorn pymssql sqlalchemy pydantic python-dotenv pandas

# Exportar a porta
EXPOSE 8000

# Variável para o Python encontrar o módulo src
ENV PYTHONPATH=/app

# Iniciar a API
CMD ["uvicorn", "src.futedata.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
