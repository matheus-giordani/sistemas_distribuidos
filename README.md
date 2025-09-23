# Sistema de Coordenação de Energia Distribuída

Este projeto implementa, com FastAPI e Docker, a arquitetura proposta onde um agente central coordena agentes especializados (painel solar, bateria residencial, veículo elétrico e cargas da casa). Cada agente roda como um microserviço independente, e o `docker-compose` orquestra a comunicação entre eles.

## Visão Geral da Arquitetura

- **Agente Central** (`services/central`): agrega os estados dos demais serviços e decide ações de carga/descarga ou shed de cargas flexíveis.
- **Agente Painel Solar** (`services/solar_agent`): expõe a produção instantânea dos painéis e permite atualizar medições.
- **Agente Bateria** (`services/battery_agent`): controla o estado de carga da bateria residencial e recebe comandos de carga/descarga.
- **Agente Veículo Elétrico** (`services/vehicle_agent`): representa o carregador do veículo, permitindo comandos de carga/descarga quando conectado.
- **Agente Cargas** (`services/load_agent`): mantém o perfil de consumo da residência e permite aplicar shedding em cargas flexíveis.

Todos os serviços oferecem endpoints `GET /health` e `GET /status` para monitoramento.

## Requisitos

- Docker 24+
- Docker Compose

## Como executar com Docker Compose

```bash
docker compose build
docker compose up
```

O agente central ficará disponível em `http://localhost:8000`.

## Fluxo típico
a) Atualize medições recebidas dos sensores (produção solar, consumo da casa, estado do veículo/bateria):

```bash
curl -X POST http://localhost:8000/coordinate \
  -H 'Content-Type: application/json' \
  -d '{
        "solar": {"production_kw": 9.5},
        "load": {"critical_load_kw": 5.0, "flexible_load_kw": 3.0},
        "battery": {"state_of_charge_kwh": 6.0},
        "vehicle": {"connected": true, "state_of_charge_kwh": 40.0}
      }'
```

b) O agente central consulta os outros serviços, calcula excedentes/deficits e envia comandos para bateria, veículo e cargas flexíveis. A resposta lista as ações tomadas e o estado consolidado:

```json
{
  "actions": {
    "battery": {"mode": "charge", "power_kw": 1.5},
    "vehicle": {"mode": "idle", "power_kw": 0.0},
    "load": {"shed_kw": 0.0}
  },
  "status": {
    "solar": {...},
    "battery": {...},
    "vehicle": {...},
    "load": {...}
  }
}
```

c) Consulte o estado agregado a qualquer momento:

```bash
curl http://localhost:8000/status | jq
```

## Execução local (sem Docker)

Cada serviço pode ser executado via Uvicorn, desde que as URLs dos agentes sejam configuradas com `localhost` e portas distintas. Exemplo para o agente central:

```bash
export SOLAR_AGENT_URL=http://localhost:8001
export BATTERY_AGENT_URL=http://localhost:8002
export VEHICLE_AGENT_URL=http://localhost:8003
export LOAD_AGENT_URL=http://localhost:8004
uvicorn services.central.app.main:app --reload --port 8000
```

Em terminais separados execute os demais agentes, ajustando a porta:

```bash
uvicorn services.solar_agent.app.main:app --reload --port 8001
uvicorn services.battery_agent.app.main:app --reload --port 8002
uvicorn services.vehicle_agent.app.main:app --reload --port 8003
uvicorn services.load_agent.app.main:app --reload --port 8004
```

## Endpoints principais

| Serviço | Endpoint | Descrição |
|---------|----------|-----------|
| Central | `POST /coordinate` | Recebe medições, coordena agentes e devolve ações aplicadas |
| Central | `GET /status` | Retorna estados consolidados |
| Solar   | `POST /production` | Atualiza produção instantânea |
| Bateria | `POST /update` | Atualiza estado medido da bateria (SoC, capacidade) |
| Bateria | `POST /control` | Define modo (charge/discharge/idle) e potência |
| Veículo | `POST /update` | Atualiza conexão e estado medido do veículo |
| Veículo | `POST /control` | Define modo e potência quando conectado |
| Cargas  | `POST /update` | Atualiza perfil de carga crítica/flexível |
| Cargas  | `POST /shed` | Aplica shedding em cargas flexíveis |

Os modelos completos estão definidos nos arquivos `services/*/app/main.py`.
