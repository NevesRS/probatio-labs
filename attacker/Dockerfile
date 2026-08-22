FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nmap \
        python3 \
        python3-pip \
        python3-venv \
        netcat-traditional \
        curl \
        ca-certificates \
        wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 \
        -O /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir scapy pymodbus

COPY hints.md /root/hints.md

EXPOSE 7681

CMD ["ttyd", "-p", "7681", "--writable", "bash"]
