# ⚽ FuteData

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-Transformers-E25A1C?logo=apachespark&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server-2022-CC2927?logo=microsoft-sql-server&logoColor=white)
![Databricks](https://img.shields.io/badge/Databricks-Asset_Bundles-FF3621?logo=databricks&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-AWS-7B42BC?logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

Pipeline de dados ponta-a-ponta sobre o mercado de transferências do futebol mundial, construído sobre dados públicos do Transfermarkt e da football-data.org. Cobre coleta auditada, validação, transformação com PySpark e modelagem dimensional em SQL Server, com infraestrutura como código e orquestração via Databricks Asset Bundles.

---

## Volume de dados

| Tabela | Registros | Conteúdo |
|---|---|---|
| `fact_valuations` | ~187.000 | Série temporal de valor de mercado por jogador |
| `fact_games` | ~33.000 | Partidas detalhadas com lineups, formação e público |
| `fact_transfers` | ~9.600 | Transferências com fee pago vs. valor de mercado na época |
| `dim_players` / `dim_clubs` | — | Dimensões com atributos, contrato e métricas agregadas |

---

## Arquitetura

```text
APIs/Datasets (Transfermarkt, football-data.org)
        │
        ▼
┌─────────────────────────┐
│  Collectors (Extract)   │  BaseCollector abstrato: idempotência parcial,
│  - TransfermarktCollector│  schema hash (xxhash), audit log em JSON
│  - FootballDataCollector │  por execução (ingestion_id, rows, status, duração)
└───────────┬─────────────┘
            ▼
    data/raw/<fonte>/          (local ou S3, via flag use_s3)
            │
            ▼
┌─────────────────────────┐
│  RawValidator (Validate)│  Verifica integridade dos arquivos brutos,
│                          │  promove para validated/ só o que passa
└───────────┬─────────────┘
            ▼
    data/validated/<fonte>/
            │
            ▼
┌─────────────────────────┐
│  Transformers (PySpark) │  Joins, parsing de datas, cálculo de idade
│  clubs / players / games│  na transferência, fee_vs_market_diff,
│  transfers / valuations │  classificação free/loan vs paid
└───────────┬─────────────┘
            ▼
   SQL Server — Star Schema
   dim_players, dim_clubs, fact_matches,
   fact_valuations, fact_transfers, fact_games
            │
            ▼
   vw_master_scout (wide view)
   cost_per_contribution, contributions_per_90, upside_value
```

A pasta `data/` é o contrato entre ambiente local e cloud: localmente vira diretórios versionados (`raw/`, `validated/`, `audit/`); em produção, o mesmo código aponta para buckets S3 (raw/validated) sem mudar a lógica dos validators. O `databricks.yml` empacota os transformers como Databricks Asset Bundle, rodando `run_transform.py` como job orquestrado. O Terraform (`terraform/`) provisiona S3, RDS, IAM e Secrets Manager na AWS.

Documentação complementar: [`docs/architecture.md`](docs/architecture.md) e [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## Camadas do projeto

### 1. Ingestão auditada (`src/futedata/collectors/`)
Toda coleta passa por `BaseCollector`, que padroniza:
- gravação atômica em `data/raw/<fonte>/<endpoint>/`
- hash de schema por arquivo (detecção de drift)
- log de auditoria (`source_audit_log.json`) com `ingestion_id`, linhas extraídas, linhas gravadas, status e duração por execução — sucesso ou falha

`TransfermarktCollector` baixa e filtra os datasets CSV abertos; `FootballDataCollector` consome a API REST da football-data.org com rate-limiting manual.

### 2. Validação (`src/futedata/validators/raw_validator.py`)
Varre `data/raw/`, valida que CSVs e JSONs não estão vazios ou corrompidos, e só promove para `data/validated/` o que passa. Tem implementação dupla — filesystem local e S3 (`boto3`) — selecionada por configuração, sem duplicar a lógica de negócio.

### 3. Transformação (`src/futedata/transformers/`, PySpark)
Cada entidade (clubs, players, games, transfers, valuations) tem seu próprio transformer com `extract()` e `transform()`. Exemplo real — `TransfersTransformer` calcula idade do jogador na data da transferência via `datediff`, classifica o tipo de movimentação (`free/loan` vs `paid`) e deriva `fee_vs_market_diff` (quanto o clube vendedor lucrou ou perdeu frente ao valor de mercado).

### 4. Modelagem dimensional (`src/futedata/db/schema.sql`)
Star schema em SQL Server: `dim_players`, `dim_clubs` como dimensões; `fact_matches`, `fact_valuations`, `fact_transfers`, `fact_games` como fatos, com índices dedicados para consultas OLAP (data, clube, jogador). A view `vw_master_scout` consolida jogador + clube + métricas derivadas (custo por participação em gol, participações a cada 90 minutos, upside de valorização) numa wide table — a camada gold do projeto.

### 5. Validação do modelo (`analytics.py`)
7 consultas SQL sobre o star schema servem como prova de que a modelagem sustenta análises reais: joias subvalorizadas, maior valorização histórica, ROI de transferências, contratos expirando, clubes que mais lucram vendendo, ligas com mais gols por jogo, tendência de alta recente. Usa window functions (`ROW_NUMBER() OVER PARTITION BY`), CTEs e agregações multi-tabela — o tipo de query que só funciona se o grain das tabelas fato estiver correto.

> O repositório também inclui uma API (FastAPI) e um frontend de BI (React) que consomem a `vw_master_scout`, além de modelos de ML em `predict.py` (Gradient Boosting). Esses componentes ficam fora do escopo deste README, que cobre a parte de engenharia de dados do projeto.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Ingestão | Python, `requests`, audit log próprio |
| Transformação | PySpark |
| Armazenamento analítico | SQL Server 2022 (star schema) |
| Orquestração cloud | Databricks Asset Bundles |
| Infraestrutura | AWS: S3, RDS, IAM, Secrets Manager |
| Qualidade | pytest, black, isort, flake8, mypy (ver `Makefile`) |

---

## Como rodar

### Pré-requisitos
[Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/).

### Subir o SQL Server
```bash
docker-compose up sqlserver -d
```
> O `docker-compose.yml` também define os serviços `api` e `frontend` (consumo dos dados), fora do escopo deste README.

### Rodar o pipeline completo
```bash
make install                  # instala o pacote em modo editável
python run_transfermarkt.py   # coleta Transfermarkt
python run_football_data.py   # coleta football-data.org
make run-validators            # valida e promove raw -> validated
python run_transform.py        # transformações PySpark -> SQL Server (star schema)
python analytics.py            # roda as 7 análises exploratórias de validação
```


A senha do SQL Server está hardcoded em `docker-compose.yml`, `analytics.py` e `create_master_view.py` para simplificar o setup local. Em qualquer ambiente além de desenvolvimento, isso deve vir de variável de ambiente ou do Secrets Manager já provisionado no Terraform (`terraform/secrets.tf`).

---

*Projeto de portfólio em Engenharia de Dados.*
