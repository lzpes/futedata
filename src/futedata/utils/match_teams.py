import difflib
from typing import Dict, List

def create_fuzzy_team_mapping(fd_names: List[str], tm_names: List[str]) -> Dict[str, str]:
    """
    Gera um mapeamento (de-para) dos nomes dos clubes do Football-Data para o Transfermarkt
    usando Fuzzy String Matching nativo do Python (difflib).
    """
    mapping = {}
    
    # Tratamentos de string para facilitar o match (minúsculas, remove FC, etc)
    def clean_name(name: str) -> str:
        if not name:
            return ""
        return str(name).lower().replace(" fc", "").replace("fc ", "").replace(" ca", "").replace("sc ", "").strip()

    tm_cleaned_to_raw = {clean_name(name): name for name in tm_names}
    tm_cleaned_list = list(tm_cleaned_to_raw.keys())

    for fd_name in fd_names:
        cleaned_fd = clean_name(fd_name)
        
        # Procura o match mais próximo
        matches = difflib.get_close_matches(cleaned_fd, tm_cleaned_list, n=1, cutoff=0.6)
        
        if matches:
            matched_clean = matches[0]
            # Mapeia o original do FD para o original do TM
            mapping[fd_name] = tm_cleaned_to_raw[matched_clean]
        else:
            # Fallback seguro
            mapping[fd_name] = fd_name
            
    return mapping
