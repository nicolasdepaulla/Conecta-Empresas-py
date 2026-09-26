FROM python:3.12-slim

WORKDIR /app

# Copia só o requirements primeiro para aproveitar cache do Docker
# (só reinstala as dependências se esse arquivo mudar)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY public/ ./public/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
