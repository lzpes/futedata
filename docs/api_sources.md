# Fontes de Dados e APIs

## 1. football-data.org
- **Tipo**: REST API
- **Formato**: JSON
- **Acesso**: Requer API Key (`FOOTBALL_DATA_API_KEY`) no `.env`.
- **Limites**: Tier gratuito tem rate-limit rigoroso (10 requests/minuto).
- **Endpoints Coletados**:
  - `matches`: Partidas agendadas e concluídas.
  - `standings`: Tabela de classificação atualizada.
  - `teams`: Elencos dos times do Brasileirão.
  - `scorers`: Top artilheiros do Brasileirão.

## 2. Transfermarkt (via Dataset Aberto)
- **Tipo**: Arquivos estáticos em dump
- **Formato**: CSV (Gzipped) hospedados via comunidade.
- **Acesso**: Sem autenticação.
- **Limites**: Baixa frequência de atualização (diário/semanal), arquivos pesados (centenas de MB).
- **Filtro Aplicado**: `competition_id == "BRA1"`
- **Arquivos Coletados**:
  - `competitions.csv`, `games.csv`, `clubs.csv`, `players.csv`, `appearances.csv`, `player_valuations.csv`, `transfers.csv`, `game_lineups.csv`.
