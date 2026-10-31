# syntax=docker/dockerfile:1

FROM python:3.11-slim

RUN pip install --no-cache-dir flask markdown

WORKDIR /app
COPY app.py .
COPY templates/ templates/
COPY static/ static/
COPY --from=ctx-attacker hints-lab1.md hints-lab2.md hints-lab3.md hints/

EXPOSE 8080

CMD ["python3", "app.py"]
