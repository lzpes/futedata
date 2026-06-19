# Arquitetura FuteData (Fase 1)

## Visão Geral
A arquitetura atual constitui a **Fundação Local** do projeto FuteData. Ela implementa o padrão de ingestão de dados baseado em uma classe abstrata `BaseCollector`, responsável por garantir idempotência parcial e rastreabilidade através de *Audit Logs*.

## Componentes

### 1. Coletores (Extract)
- **`BaseCollector`**: Gerencia a criação de diretórios padronizados (`data/raw/<fonte>`), hashes de schema (`xxhash`), gravação atômica (`io.py`) e geração do log de auditoria JSON.
- **`FootballDataCollector`**: Extrai dados JSON da API `football-data.org`. Focado no campeonato `BSA` (Brasileirão). Suporta rate-limiting manual.
- **`TransfermarktCollector`**: Faz o download dos datasets globais abertos do Transfermarkt (arquivos CSV Gzip) e realiza o filtro por "competition_id" = "BRA1", salvando CSVs mais leves localmente.

### 2. Validadores (Load/Validate)
- **`RawValidator`**: Varre o diretório `data/raw/` após a coleta e verifica a integridade básica dos arquivos gerados. Promove arquivos válidos para `data/validated/`.

### 3. Camadas de Dados Local
- `data/raw/`: Arquivos como foram extraídos da fonte.
- `data/validated/`: Arquivos aprovados pelo validador.
- `data/audit/`: Logs JSON contendo horário de execução, total de linhas extraídas e status de cada endpoint.

## Próximos Passos (Cloud)
Na Fase 2 e posteriores, o diretório `data/` será sincronizado ou substituído por buckets S3, e a orquestração poderá migrar para o Databricks ou Airflow.
