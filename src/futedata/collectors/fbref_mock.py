import pandas as pd
import numpy as np
from pathlib import Path
from futedata.utils.logging import get_logger

logger = get_logger(__name__)

def generate_mock_fbref_data():
    logger.info("Gerando dataset mock do FBRef com distribuição estatística...")
    players_csv = Path("data/raw/transfermarkt/players/players.csv")
    if not players_csv.exists():
        logger.error(f"Arquivo não encontrado: {players_csv}")
        return

    df = pd.read_csv(players_csv)
    
    # Gerando as estatísticas baseadas na posição para dar realismo
    # Tackles: Zagueiros e Volantes tem muito mais
    # Interceptações: Zagueiros tem mais
    # Pass Completion: Zagueiros e Meias tem mais
    
    def get_tackles(pos):
        if pd.isna(pos): return np.random.uniform(0.5, 1.5)
        pos = pos.lower()
        if "defender" in pos or "back" in pos: return np.random.uniform(1.5, 4.0)
        if "midfield" in pos: return np.random.uniform(1.0, 3.0)
        return np.random.uniform(0.2, 1.2)

    def get_interceptions(pos):
        if pd.isna(pos): return np.random.uniform(0.5, 1.5)
        pos = pos.lower()
        if "defender" in pos or "back" in pos: return np.random.uniform(1.0, 3.0)
        if "midfield" in pos: return np.random.uniform(0.5, 2.0)
        return np.random.uniform(0.1, 0.8)

    def get_pass_pct(pos):
        if pd.isna(pos): return np.random.uniform(70, 85)
        pos = pos.lower()
        if "defender" in pos or "back" in pos: return np.random.uniform(75, 95)
        if "midfield" in pos: return np.random.uniform(75, 92)
        if "goalkeeper" in pos: return np.random.uniform(40, 80)
        return np.random.uniform(65, 85)

    np.random.seed(42) # para ser determinístico
    df["tackles_per_90"] = df["position"].apply(get_tackles).round(2)
    df["interceptions_per_90"] = df["position"].apply(get_interceptions).round(2)
    df["pass_completion_pct"] = df["position"].apply(get_pass_pct).round(2)
    
    out_dir = Path("data/raw/fbref")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "defense.csv"
    
    df[["player_id", "tackles_per_90", "interceptions_per_90", "pass_completion_pct"]].to_csv(out_file, index=False)
    logger.info(f"Mock dataset salvo em {out_file} com {len(df)} registros.")

if __name__ == "__main__":
    generate_mock_fbref_data()
