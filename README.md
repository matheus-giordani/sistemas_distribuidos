# Sistema de Coordenação de Energia Distribuída (gRPC)

Esta branch substitui todos os endpoints REST por serviços **gRPC**. O agente central e os agentes especializados (solar, bateria, veículo e cargas) trocam mensagens definidas em `proto/energy.proto`, usando metadados `x-api-key` para autenticação simples.

## Arquitetura
- **Central (`energy.CentralCoordinator`)**: recebe medições opcionais, consulta o estado dos agentes e coordena carga/descarga e shed de cargas flexíveis.
- **Solar (`energy.SolarAgent`)**: mantém a produção instantânea (kW).
- **Bateria (`energy.BatteryAgent`)**: controla estado de carga, modos `charge`/`discharge`/`idle` e limites de potência.
- **Veículo (`energy.VehicleAgent`)**: espelha o carregador do veículo elétrico, respeitando conexão e limites.
- **Cargas (`energy.LoadAgent`)**: acompanha o consumo crítico/flexível e aplica shedding.

Todas as respostas usam `google.protobuf.Timestamp` e validações básicas são realizadas antes de atualizar o estado interno.

## Proto e stubs
- Arquivo principal: `proto/energy.proto`.
- Stubs Python: `services/protos/energy_pb2.py` e `services/protos/energy_pb2_grpc.py`.
- Para regenerar (requer `grpcio-tools` instalado):
  ```bash
  python -m grpc_tools.protoc -I proto --python_out=services/protos --grpc_python_out=services/protos proto/energy.proto
  ```
  > O arquivo `energy_pb2_grpc.py` nesta branch replica a saída padrão do plugin oficial.

## Executar com Docker Compose
1. Defina a chave compartilhada (altere em produção):
   ```bash
   export SERVICE_API_KEY=teste
   docker compose build
   docker compose up
   ```
2. Os serviços ficam expostos nas portas `8000-8004`. O compose já injeta `SERVICE_API_KEY=teste`; exporte a mesma variável ao usar clients locais.

## Chamadas de exemplo (grpcurl)
Assumindo os serviços em execução e `grpcurl` instalado, use o proto local:

```bash
# Consultar o estado instantâneo do agente solar
grpcurl -plaintext \
  -H "x-api-key: teste" \
  -import-path proto \
  -proto energy.proto \
  localhost:8001 energy.SolarAgent/GetStatus

# Coordenar o sistema informando novas medições
grpcurl -plaintext \
    -H "x-api-key: teste" \
    -import-path proto \
    -proto energy.proto \
    -d '{
          "updates": {
            "solar": {"productionKw": 9.5},
            "load": {"criticalLoadKw": 5.0, "flexibleLoadKw": 3.0},
            "battery": {"stateOfChargeKwh": 6.0},
            "vehicle": {"stateOfChargeKwh": 40.0, "connected": true}
          }
        }' \
    localhost:8000 energy.CentralCoordinator/Coordinate
```

Os nomes dos campos seguem o padrão `proto3` (camelCase). É obrigatório o cabeçalho `x-api-key` em todas as requisições.

## Execução local manual
Em terminais separados:
```bash
export SERVICE_API_KEY=${SERVICE_API_KEY:-teste}
python -m services.solar_agent.app.main
python -m services.battery_agent.app.main
python -m services.vehicle_agent.app.main
python -m services.load_agent.app.main
python -m services.central.app.main
```
