import hashlib
import re
import difflib
from core.lib.classificador import normalizar_texto
from core.database import obter_professor_id_por_nome

# Perfis determinísticos de Língua Portuguesa
PERFIS_LP = [
    "LEITURA INVESTIGATIVA",
    "COMPARAÇÃO E DIÁLOGO",
    "ANÁLISE MODELADA",
    "ESCRITA E AUTORIA"
]

def selecionar_perfil_metodologico(professor_nome: str, turma: str, disciplina: str, bimestre: str) -> str:
    """Seleciona de forma determinística e estável um dos perfis para Língua Portuguesa."""
    prof = str(professor_nome or "").strip().upper()
    t = str(turma or "").strip().upper()
    d = str(disciplina or "").strip().upper()
    b = str(bimestre or "").strip().upper()
    
    chave = f"{prof}|{t}|{d}|{b}"
    h = hashlib.sha256(chave.encode('utf-8')).hexdigest()
    idx = int(h, 16) % len(PERFIS_LP)
    return PERFIS_LP[idx]

def selecionar_proximo_perfil(perfil_atual: str) -> str:
    """Retorna o próximo perfil disponível na lista (usado em caso de colisão de similaridade)."""
    if perfil_atual not in PERFIS_LP:
        return perfil_atual
    idx = PERFIS_LP.index(perfil_atual)
    novo_idx = (idx + 1) % len(PERFIS_LP)
    return PERFIS_LP[novo_idx]

def montar_fingerprint_contexto(
    hash_pdf: str,
    versao_gerador: str,
    professor_nome: str,
    turma: str,
    disciplina: str,
    bimestre: str,
    tipo_aula: str,
    perfil_metodologico: str,
) -> str:
    """Gera um hash sha256 estável do contexto completo de geração."""
    prof = str(professor_nome or "").strip().upper()
    t = str(turma or "").strip().upper()
    d = str(disciplina or "").strip().upper()
    b = str(bimestre or "").strip().upper()
    ta = str(tipo_aula or "").strip().upper()
    pm = str(perfil_metodologico or "").strip().upper()
    v = str(versao_gerador or "").strip().upper()
    h_pdf = str(hash_pdf or "").strip().upper()
    
    chave = f"{h_pdf}|{v}|{prof}|{t}|{d}|{b}|{ta}|{pm}"
    return hashlib.sha256(chave.encode('utf-8')).hexdigest()

def extrair_sentencas(texto: str) -> list[str]:
    """Divide o texto em sentenças limpas."""
    sentencas = []
    for s in re.split(r'[.!?]', str(texto or "")):
        s_limpa = s.strip()
        if s_limpa:
            sentencas.append(s_limpa)
    return sentencas

def contar_palavras(s: str) -> int:
    return len(s.split())

def detectar_frases_longas_repetidas(t1: str, t2: str, min_palavras: int = 10) -> int:
    """Retorna a quantidade de frases longas idênticas entre dois textos."""
    s1 = [normalizar_texto(s) for s in extrair_sentencas(t1)]
    s2 = [normalizar_texto(s) for s in extrair_sentencas(t2)]
    
    repetidas = 0
    for s in s1:
        if contar_palavras(s) >= min_palavras:
            if s in s2:
                repetidas += 1
    return repetidas

def comparar_similaridade_texto(t1: str, t2: str) -> float:
    return difflib.SequenceMatcher(None, t1, t2).ratio()

def detectar_similaridade_excessiva(metodologia_a: list[dict], metodologia_b: list[dict]) -> bool:
    """Determina se duas metodologias são excessivamente semelhantes."""
    if not metodologia_a or not metodologia_b:
        return False
        
    t1 = " ".join([m.get("texto", "") for m in metodologia_a if isinstance(m, dict)])
    t2 = " ".join([m.get("texto", "") for m in metodologia_b if isinstance(m, dict)])
    
    t1_norm = normalizar_texto(t1)
    t2_norm = normalizar_texto(t2)
    
    # 1. Similaridade geral igual ou superior a aproximadamente 0.82
    sim_geral = comparar_similaridade_texto(t1_norm, t2_norm)
    if sim_geral >= 0.82:
        return True
        
    # 2. Três ou mais frases idênticas com pelo menos 10 ou 12 palavras
    frases_rep = detectar_frases_longas_repetidas(t1, t2, min_palavras=10)
    if frases_rep >= 3:
        return True
        
    return False
