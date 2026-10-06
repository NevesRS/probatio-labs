FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-pip \
        nmap \
        netcat-traditional \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages pymodbus

RUN useradd -m -s /bin/bash admin && \
    echo "admin:admin" | chpasswd

RUN mkdir -p /run/sshd && \
    ssh-keygen -A && \
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo "UsePAM no" >> /etc/ssh/sshd_config && \
    printf '=== Jump Host - Planta Industrial Probatio ===\nAcesso restrito a operadores autorizados.\n' > /etc/motd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
