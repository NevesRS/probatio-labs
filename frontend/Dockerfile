FROM python:3.11-slim

RUN pip install --no-cache-dir flask

WORKDIR /app
COPY app.py .
COPY templates/ templates/
COPY static/ static/

EXPOSE 8080

CMD ["python3", "app.py"]
