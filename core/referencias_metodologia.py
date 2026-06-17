import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Tuple

REFERENCIA_LEITURA_REDACAO = "🧠🔥 GUIA METODOLÓGICO ESTRUTURADO - LEITURA E REDAÇÃO.md"


BASE_DIR = Path(__file__).resolve().parents[1]
PASTA_ANALISES_NOVAS = Path(r"D:\PDF novos\ANALISES_NOVAS_POR_DISCIPLINA")
PASTAS_BUSCA = [
    PASTA_ANALISES_NOVAS,
    BASE_DIR / "REFERENCIAS_METODOLOGIA",
    Path(r"C:\Users\Prof_L\Desktop\desktop\REFERENCIAS_METODOLOGIA"),
]
PASTA_REFERENCIAS = PASTAS_BUSCA[0]

def resolver_caminho_referencia(arquivo: str) -> Path | None:
    for pasta in PASTAS_BUSCA:
        caminho = pasta / arquivo
        if caminho.exists():
            return caminho
    return None

LIMITE_REFERENCIA_CHARS = 6200
LIMITE_INTERDISCIPLINAR_CHARS = 1800

REFERENCIA_INTERDISCIPLINAR = "ADAPTAÇÃO METODOLÓGICA INTERDISCIPLINAR.md"

REFERENCIA_PORTUGUES_GERAL = "ANÁLISE METODOLÓGICA COMPLETA - LÍNGUA PORTUGUESA.md"
REFERENCIA_PORTUGUES_FUNDAMENTAL = "ANÁLISE METODOLÓGICA - LÍNGUA PORTUGUESA ENSINO FUNDAMENTAL.md"
REFERENCIA_PORTUGUES_MEDIO = "ANÁLISE METODOLÓGICA - LÍNGUA PORTUGUESA ENSINO MÉDIO.md"

REFERENCIA_PV_GERAL = "ANÁLISE METODOLÓGICA COMPLETA - PROJETO DE VIDA.md"
REFERENCIA_PV_FUNDAMENTAL = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA ENSINO FUNDAMENTAL.md"
REFERENCIA_PV_REFINADA_FUNDAMENTAL = "ANÁLISE METODOLÓGICA REFINADA - PROJETO DE VIDA ENSINO FUNDAMENTAL.md"
REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA - ENSINO FUNDAMENTAL ANOS FINAIS.md"
REFERENCIA_PV_7_ANO = "ANÁLISE METODOLÓGICA - PROJETO DE VIDA 7º ANO.md"

MAPA_REFERENCIAS_NOVAS = {
    "arte": "analise_metodologica_arte.md",
    "biologia": "analise_metodologica_biologia.md",
    "ciencias": "analise_metodologica_ciencias.md",
    "ciencia": "analise_metodologica_ciencias.md",
    "educacao financeira": "analise_metodologica_educacao_financeira.md",
    "geografia": "analise_metodologica_geografia.md",
    "historia": "analise_metodologica_historia.md",
    "ingles": "analise_metodologica_lingua_inglesa.md",
    "english": "analise_metodologica_lingua_inglesa.md",
    "lideranca e oratoria": "analise_metodologica_lideranca_e_oratoria.md",
    "lingua portuguesa": "analise_metodologica_lingua_portuguesa.md",
    "portugues": "analise_metodologica_lingua_portuguesa.md",
    "matematica": "analise_metodologica_matematica.md",
    "orientacao de estudos": "analise_metodologica_orientacao_de_estudos.md",
    "projeto de vida": "analise_metodologica_projeto_de_vida.md",
    "quimica": "analise_metodologica_quimica.md",
    "redacao e leitura": "analise_metodologica_redacao_e_leitura.md",
    "leitura e redacao": "analise_metodologica_redacao_e_leitura.md",
    "tecnologia e inovacao": "analise_metodologica_tecnologia_e_inovacao.md",
}

MAPA_REFERENCIAS = {
    "matematica": (
        "ANÁLISE METODOLÓGICA - MATEMÁTICA.md",
        "analise_metodologica_matematica_ensino_medio_seduc_sp.md",
    ),
    "lingua portuguesa": REFERENCIA_PORTUGUES_GERAL,
    "portugues": REFERENCIA_PORTUGUES_GERAL,
    "redacao e leitura": REFERENCIA_LEITURA_REDACAO,
    "leitura e redacao": REFERENCIA_LEITURA_REDACAO,
    "ciencias": (
        "ANALISE_METODOLOGICA_CIENCIAS_EF_ANOS_FINAIS_3B.md",
        "CIÊNCIAS-6ANO_metodologias_ciencias_6ano_versao_final_completa_ajustada.docx",
        "ANÁLISE METODOLÓGICA - CIÊNCIAS 7º ANO.md",
    ),
    "ciencia": (
        "ANALISE_METODOLOGICA_CIENCIAS_EF_ANOS_FINAIS_3B.md",
        "CIÊNCIAS-6ANO_metodologias_ciencias_6ano_versao_final_completa_ajustada.docx",
        "ANÁLISE METODOLÓGICA - CIÊNCIAS 7º ANO.md",
    ),
    "geografia": "GEOGRAFIA-1EM_metodologia.docx",
    "arte": "ANÁLISE METODOLÓGICA - ARTE - ENSINO FUNDAMENTAL ANOS FINAIS.md",
    "artes": "ANÁLISE METODOLÓGICA - ARTE - ENSINO FUNDAMENTAL ANOS FINAIS.md",
    "historia": "ANÁLISE METODOLÓGICA - HISTÓRIA ENSINO FUNDAMENTAL.md",
    "projeto de vida": (
        REFERENCIA_PV_GERAL,
        REFERENCIA_PV_REFINADA_FUNDAMENTAL,
        REFERENCIA_PV_FUNDAMENTAL,
        REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS,
    ),
    "ingles": "ANÁLISE METODOLÓGICA - INGLÊS ENSINO FUNDAMENTAL.md",
    "english": "ANÁLISE METODOLÓGICA - INGLÊS ENSINO FUNDAMENTAL.md",
    "orientacao de estudos": "ANÁLISE METODOLÓGICA PROFUNDA - ORIENTAÇÃO DE ESTUDOS.md",
    "educacao financeira": "EDUCAÇÃO FINANCEIRA-7ANO_METODOLOGIA.docx",
    "cdp": (
        "metodologiacdp.docx",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).md",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).mdparte2.md",
    ),
    "eja": (
        "metodologiacdp.docx",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).md",
        "HABILIDADES POR DISCIPLINA - EDUCAÇÃO DE JOVENS E ADULTOS (EJA).mdparte2.md",
    ),
}


def normalizar_disciplina(texto: str = "") -> str:
    texto = (texto or "").strip().lower()
    mapa = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "â": "a",
            "ã": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
            "º": "",
            "ª": "",
            "°": "",
        }
    )
    texto = texto.translate(mapa)
    return re.sub(r"\s+", " ", texto)

def normalizar_disciplina(texto: str = "") -> str:
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.replace("º", "").replace("ª", "").replace("°", "")
    return re.sub(r"\s+", " ", texto)


def _eh_turma_fundamental(turma: str = "") -> bool:
    turma_norm = normalizar_disciplina(turma)
    return bool(re.search(r"\b(?:6|7|8|9)\s*(?:ano|a|b|c|d|e)?\b", turma_norm))


def _ano_turma(turma: str = "") -> int:
    turma_norm = normalizar_disciplina(turma)
    match = re.search(r"\b([1-9])\s*(?:ano|em|a|b|c|d|e)?\b", turma_norm)
    return int(match.group(1)) if match else 0


def _eh_portugues(disciplina: str = "") -> bool:
    disciplina_norm = normalizar_disciplina(disciplina)
    return "portugues" in disciplina_norm or "lingua portuguesa" in disciplina_norm


def _eh_projeto_vida(disciplina: str = "") -> bool:
    return "projeto de vida" in normalizar_disciplina(disciplina)


def _combinar_arquivos(*grupos: Iterable[str]) -> Tuple[str, ...]:
    vistos = set()
    combinados = []
    for grupo in grupos:
        for arquivo in grupo or ():
            if not arquivo or arquivo in vistos:
                continue
            vistos.add(arquivo)
            combinados.append(arquivo)
    return tuple(combinados)


def _arquivos_novos_para_disciplina(disciplina: str = "") -> Tuple[str, ...]:
    disciplina_norm = normalizar_disciplina(disciplina)
    for chave, arquivo in MAPA_REFERENCIAS_NOVAS.items():
        if chave in disciplina_norm:
            return (arquivo,)
    return ()


def _arquivos_para_disciplina(disciplina: str = "") -> Tuple[str, ...]:
    disciplina_norm = normalizar_disciplina(disciplina)
    for chave, arquivos in MAPA_REFERENCIAS.items():
        if chave in disciplina_norm:
            if isinstance(arquivos, str):
                return (arquivos,)
            return tuple(arquivos)
    return ()


def _limpar_markdown(texto: str) -> str:
    texto = re.sub(r"```.*?```", " ", texto or "", flags=re.DOTALL)
    texto = re.sub(r"#{1,6}\s*", "", texto)
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _priorizar_analise_nova_markdown(texto: str) -> str:
    bruto = str(texto or "")
    titulo = ""
    match_titulo = re.search(r"(?m)^#\s+(.+)$", bruto)
    if match_titulo:
        titulo = match_titulo.group(1).strip()

    secoes_prioritarias = []
    for numero in ("4", "5", "6", "7", "8", "9", "10"):
        match = re.search(
            rf"(?ims)^##\s*{numero}\.\s+.*?(?=^##\s+\d+\.|\Z)",
            bruto,
        )
        if match:
            secoes_prioritarias.append(match.group(0).strip())

    secoes_contexto = []
    for numero in ("2", "3"):
        match = re.search(
            rf"(?ims)^##\s*{numero}\.\s+.*?(?=^##\s+\d+\.|\Z)",
            bruto,
        )
        if match:
            secoes_contexto.append(match.group(0).strip())

    partes = []
    if titulo:
        partes.append(f"# {titulo}")
    partes.extend(secoes_prioritarias)
    partes.extend(secoes_contexto)

    if not partes:
        return _limpar_markdown(bruto)
    return _limpar_markdown("\n\n".join(partes))


def _limpar_interdisciplinar(texto: str) -> str:
    texto = _limpar_markdown(texto)
    texto = re.sub(
        r"(?is)1\.\s*Aplicabilidade dos Padrões por Disciplina.*?(?=2\.\s*Adaptações Específicas por Disciplina)",
        "",
        texto,
    )
    texto = re.sub(r"(?is)3\.\s*Riscos de Confusão no Código Python.*", "", texto)
    texto = re.sub(r"(?im)^#+\s*", "", texto)
    return texto.strip()


def _reforcar_regras_do_sistema(texto: str) -> str:
    reforco = (
        "REGRAS FIXAS DO SISTEMA:\n"
        "- Use esta biblioteca apenas como referência de estilo e qualidade, sem copiar trechos prontos.\n"
        "- Priorize textos completos; não use reticências para encurtar frases em desenvolvimento, acompanhamento ou acessibilidade.\n"
        "- Se precisar reduzir, reescreva a frase de forma mais curta e completa.\n"
        "- Não invente técnicas pedagógicas; só cite técnicas quando estiverem explicitamente presentes nos slides.\n"
        "- Exceção: Pause e responda sempre é verificação da aprendizagem com correção mediada.\n"
        "- Respeite a ordem real dos slides enviados.\n"
        "- Mantenha metodologia fluida, objetiva e adequada ao conteúdo da aula.\n\n"
    )
    return reforco + texto


def _carregar_referencia_interdisciplinar() -> str:
    caminho = resolver_caminho_referencia(REFERENCIA_INTERDISCIPLINAR)
    if not caminho:
        return ""

    texto = _limpar_interdisciplinar(caminho.read_text(encoding="utf-8", errors="ignore"))
    if not texto:
        return ""

    texto = (
        "REFERÊNCIA INTERDISCIPLINAR COMPLEMENTAR:\n"
        "- Use apenas para variar verbos, progressão pedagógica e linguagem de mediação.\n"
        "- Não use esta referência para criar tempos fixos, etapas inexistentes ou técnicas não presentes nos slides.\n"
        "- A referência específica da disciplina e a ordem real dos slides têm prioridade.\n\n"
        + texto
    )
    if len(texto) <= LIMITE_INTERDISCIPLINAR_CHARS:
        return texto
    return texto[:LIMITE_INTERDISCIPLINAR_CHARS].rsplit("\n", 1)[0].strip()


def _ler_docx(caminho: Path) -> str:
    try:
        import docx
        doc = docx.Document(caminho)
        texto_partes = []
        for p in doc.paragraphs:
            txt = p.text.strip()
            if txt:
                texto_partes.append(txt)
        for table in doc.tables:
            for row in table.rows:
                celulas = []
                for cell in row.cells:
                    txt = cell.text.strip()
                    if txt and (not celulas or celulas[-1] != txt):
                        celulas.append(txt)
                linha_txt = " | ".join(celulas)
                if linha_txt:
                    texto_partes.append(linha_txt)
        return "\n".join(texto_partes)
    except Exception as e:
        return f"Referência {caminho.name} (erro ao ler: {e})"


def _ler_arquivos_referencia(arquivos: Iterable[str]) -> str:
    partes = []
    for arquivo in arquivos:
        caminho = resolver_caminho_referencia(arquivo)
        if not caminho:
            continue
        suffix = caminho.suffix.lower()
        if suffix == ".md":
            texto = caminho.read_text(encoding="utf-8", errors="ignore")
            if caminho.parent == PASTA_ANALISES_NOVAS:
                texto = _priorizar_analise_nova_markdown(texto)
            else:
                texto = _limpar_markdown(texto)
        elif suffix == ".docx":
            texto = _ler_docx(caminho)
        else:
            try:
                texto = caminho.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                texto = caminho.name
        if texto:
            partes.append(texto)
    return "\n\n".join(partes)


@lru_cache(maxsize=32)
def carregar_referencia_metodologica(disciplina: str = "", turma: str = "") -> str:
    arquivos_novos = _arquivos_novos_para_disciplina(disciplina)
    if _eh_portugues(disciplina) and _eh_turma_fundamental(turma):
        arquivos_padrao = (REFERENCIA_PORTUGUES_FUNDAMENTAL, REFERENCIA_PORTUGUES_GERAL)
    elif _eh_portugues(disciplina):
        arquivos_padrao = (REFERENCIA_PORTUGUES_MEDIO, REFERENCIA_PORTUGUES_GERAL)
    elif _eh_projeto_vida(disciplina) and _ano_turma(turma) == 7:
        arquivos_padrao = (
            REFERENCIA_PV_GERAL,
            REFERENCIA_PV_REFINADA_FUNDAMENTAL,
            REFERENCIA_PV_7_ANO,
            REFERENCIA_PV_FUNDAMENTAL,
            REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS,
        )
    elif _eh_projeto_vida(disciplina):
        arquivos_padrao = (
            REFERENCIA_PV_GERAL,
            REFERENCIA_PV_REFINADA_FUNDAMENTAL,
            REFERENCIA_PV_FUNDAMENTAL,
            REFERENCIA_PV_FUNDAMENTAL_ANOS_FINAIS,
        )
    else:
        arquivos_padrao = _arquivos_para_disciplina(disciplina)
    
    disc_norm = normalizar_disciplina(disciplina)
    if "redacao" in disc_norm or "leitura" in disc_norm:
        arquivos = _combinar_arquivos(arquivos_padrao, arquivos_novos)
    else:
        arquivos = arquivos_novos if arquivos_novos else arquivos_padrao
        
    if not arquivos:
        return ""

    texto = _ler_arquivos_referencia(arquivos)
    if not texto:
        return ""

    interdisciplinar = _carregar_referencia_interdisciplinar()
    if interdisciplinar:
        limite_texto_principal = max(2600, LIMITE_REFERENCIA_CHARS - len(interdisciplinar) - 400)
        if len(texto) > limite_texto_principal:
            texto = texto[:limite_texto_principal].rsplit("\n", 1)[0].strip()
        texto = texto + "\n\n" + interdisciplinar

    texto = _reforcar_regras_do_sistema(texto)
    if len(texto) <= LIMITE_REFERENCIA_CHARS:
        return texto
    return texto[:LIMITE_REFERENCIA_CHARS].rsplit("\n", 1)[0].strip()


def listar_referencias_disponiveis() -> Dict[str, str]:
    disponiveis = {}
    chaves = set(MAPA_REFERENCIAS) | set(MAPA_REFERENCIAS_NOVAS)
    for disciplina in sorted(chaves):
        lista = _combinar_arquivos(
            _arquivos_novos_para_disciplina(disciplina),
            _arquivos_para_disciplina(disciplina),
        )
        caminhos = []
        for arquivo in lista:
            caminho = resolver_caminho_referencia(arquivo)
            if caminho:
                caminhos.append(str(caminho))
        if caminhos:
            disponiveis[disciplina] = " | ".join(caminhos)
    return disponiveis
