# Databricks notebook source
# MAGIC %pip install .
# COMMAND ----------
import sys
import os
# No Databricks Notebook, __file__ não existe, mas os.getcwd() retorna a pasta do repo
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "src")))

from futedata.transformers.matches import MatchesTransformer
from futedata.transformers.standings import StandingsTransformer
from futedata.transformers.players import PlayersTransformer
from futedata.transformers.clubs import ClubsTransformer
from futedata.transformers.valuations import ValuationsTransformer
from futedata.transformers.transfers import TransfersTransformer
from futedata.transformers.games import GamesTransformer

if __name__ == "__main__":
    
    transformers = [
        MatchesTransformer(),
        StandingsTransformer(),
        PlayersTransformer(),
        ClubsTransformer(),
        ValuationsTransformer(),
        TransfersTransformer(),
        GamesTransformer(),
    ]

    for t in transformers:
        name = t.__class__.__name__
        print(f"\n{'='*60}")
        print(f"  Executando Job PySpark: {name}")
        print(f"{'='*60}")
        df = t.run()
        print(f"  Resultado: {df.count()} linhas geradas no Delta Lake")
        df.show(5, truncate=False)
