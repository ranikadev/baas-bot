FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

# Run with uvicorn (use --host 0.0.0.0 for Docker)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
