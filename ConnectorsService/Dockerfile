FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ConnectorsService/requirements.txt /app/ConnectorsService/requirements.txt
RUN pip install --no-cache-dir -r /app/ConnectorsService/requirements.txt

# Copy full application code
COPY . /app

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "-c", "cd /app/ConnectorsService && python -m alembic upgrade head && uvicorn ConnectorsService.api.main:app --host 0.0.0.0 --port 8000"]
