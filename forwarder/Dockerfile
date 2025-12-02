FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY forwarder.py .

EXPOSE 9087

CMD ["gunicorn", "forwarder:app", "--bind", "0.0.0.0:9087", "--workers", "1", "--threads", "2"]