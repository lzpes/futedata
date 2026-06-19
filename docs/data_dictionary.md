# Dicionário de Dados Base

*(Nota: Este dicionário reflete os schemas dos arquivos consolidados na camada `validated`)*

## Football-Data

### `matches.json`
- `id` (int): Identificador único da partida.
- `utcDate` (string): Data e hora em formato UTC ISO8601.
- `status` (string): Status da partida (ex: "FINISHED", "SCHEDULED").
- `matchday` (int): Rodada do campeonato.
- `homeTeam`, `awayTeam` (dict): IDs e nomes das equipes.
- `score` (dict): Gols do mandante e visitante no tempo normal e penaltis.

## Transfermarkt

### `players.csv`
- `player_id` (int): ID único do Transfermarkt.
- `first_name`, `last_name`, `name` (string): Nomes do jogador.
- `current_club_id` (int): ID do clube atual, relaciona-se com `clubs.csv`.
- `market_value_in_eur` (float): Valor de mercado atual em Euros.
- `date_of_birth` (string): Data de nascimento.
- `position`, `sub_position` (string): Posição tática principal.

### `player_valuations.csv`
- `player_id` (int): ID do jogador.
- `date` (string): Data da avaliação.
- `market_value_in_eur` (float): Valor de mercado naquela data específica (útil para série temporal).
