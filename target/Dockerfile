FROM python:3.11-slim

RUN pip install --no-cache-dir pymodbus==3.6.9

WORKDIR /app
COPY plc_simulator.py .

EXPOSE 502

CMD ["python3", "plc_simulator.py"]
