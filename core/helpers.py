import io
import re
import unicodedata
from pathlib import Path
from collections.abc import Iterable


DISCIPLINA_PASTA_ALIASES = {
    "PORTUGUES": "LINGUA_PORTUGUESA",
    "LINGUA_PORTUGUESA": "LINGUA_PORTUGUESA",
}


def horario_para_plano(horario) -> str:
    if isinstance(horario, tuple) and len(horario) >= 2:
        return f"{horario[0]}\n{horario[1]}"
    return str(horario or "")


def arquivos_na_ordem_de_envio(arquivos) -> list:
    """Preserva a ordem exata em que os arquivos chegam da interface.

    Em alguns planos a sequência pedagógica não acompanha a numeração do
    material. Por isso, o sistema não deve reordenar os PDFs pelo nome.
    """
    return list(arquivos or [])


def texto_lista(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, Iterable) and not isinstance(valor, (bytes, bytearray, dict)):
        return "\n".join(f"- {item}" for item in valor if str(item).strip())
    return str(valor)


def listar_falhas_ia(aulas, exigir_ia: bool = True) -> list[str]:
    if not exigir_ia:
        return []

    falhas = []
    for idx, aula in enumerate(aulas or [], start=1):
        if aula.get("ia_usada"):
            continue
        origem = str(aula.get("origem_metodologia") or "").strip()
        if origem.startswith("docx_referencia_"):
            continue
        erro = str(aula.get("ia_erro") or "").strip()
        tema = str(aula.get("tema") or f"Aula {idx}").strip()
        if erro:
            falhas.append(f"Aula {idx} ({tema}): {erro}")
        else:
            falhas.append(f"Aula {idx} ({tema}): a IA não retornou desenvolvimento completo.")
    return falhas


def resumir_falhas_ia(falhas_ia) -> str:
    falhas = [str(item).strip() for item in falhas_ia or [] if str(item).strip()]
    if not falhas:
        return ""
    if len(falhas) == 1:
        return (
            "A IA não concluiu 1 aula e o sistema usou o motor local nessa aula. "
            "Revise esse trecho com mais atenção: "
            f"{falhas[0]}"
        )
    return (
        f"A IA não concluiu {len(falhas)} aula(s) e o sistema usou o motor local nesses casos. "
        "Revise essas aulas com mais atenção: "
        + " | ".join(falhas)
    )


def montar_relatorio_geracao(aulas, disciplina: str, turma: str, bimestre: str, mes: str) -> str:
    linhas = [
        "RELATORIO DE CONFERENCIA DO PLANO",
        f"Disciplina: {disciplina}",
        f"Turma: {turma}",
        f"Bimestre: {bimestre}",
        f"Mes: {mes}",
        f"Total de aulas: {len(aulas or [])}",
        "",
    ]
    for idx, aula in enumerate(aulas or [], start=1):
        erro_ia = str(aula.get("ia_erro") or "").strip()
        linhas.extend(
            [
                f"Aula {idx}",
                f"Tema: {aula.get('tema', '')}",
                f"Data: {aula.get('data', '')}",
                f"Horario: {str(aula.get('horario', '')).replace(chr(10), ' - ')}",
                f"IA usada: {'sim' if aula.get('ia_usada') else 'nao'}",
            ]
        )
        if erro_ia:
            linhas.append(f"Observacao IA: {erro_ia}")
        linhas.append("")
    return "\n".join(linhas)


class LocalFileWrapper(io.BytesIO):
    """Wrapper para PDFs locais simular o comportamento de st.file_uploader."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        try:
            content = path.read_bytes()
        except OSError:
            content = b""
        super().__init__(content)


def normalizar_para_pasta(texto: str) -> str:
    texto_norm = unicodedata.normalize("NFKD", str(texto or ""))
    texto_norm = "".join(ch for ch in texto_norm if not unicodedata.combining(ch))
    texto_norm = re.sub(r"[^\w\s]", "", texto_norm).upper().strip().replace(" ", "_")
    # Ajustar entradas comuns como "1o ano" e "2a serie".
    return re.sub(r"(\d)[OA]_", r"\1_", texto_norm)


def _normalizar_disciplina_para_pasta(disciplina: str) -> str:
    disciplina_norm = normalizar_para_pasta(disciplina)
    return DISCIPLINA_PASTA_ALIASES.get(disciplina_norm, disciplina_norm)


def _nome_pasta_normalizado(valor: str | Path) -> str:
    return normalizar_para_pasta(Path(str(valor)).name)


def _pasta_tem_pdfs(caminho: Path) -> bool:
    if not caminho.exists() or not caminho.is_dir():
        return False
    try:
        return any(arquivo.is_file() and arquivo.suffix.lower() == ".pdf" for arquivo in caminho.iterdir())
    except OSError:
        return False


def _tokens_serie_turma(turma_norm: str) -> list[str]:
    tokens = [turma_norm] if turma_norm else []

    match_ano = re.search(r"(\d)_ANO(?:_([A-Z]))?", turma_norm)
    match_serie = re.search(r"(\d)_SERIE(?:_([A-Z]))?", turma_norm)
    match = match_ano or match_serie
    if not match:
        return [token for token in dict.fromkeys(tokens) if token]

    numero = match.group(1)
    letra = match.group(2)
    tokens.extend([f"{numero}_ANO", f"{numero}_SERIE"])
    if letra:
        tokens.extend([f"{numero}_ANO_{letra}", f"{numero}_SERIE_{letra}"])
    return [token for token in dict.fromkeys(tokens) if token]


def _nivel_preferido_para_turma(turma_norm: str) -> str:
    if "EM" in turma_norm or "ENSINO_MEDIO" in turma_norm or "SERIE" in turma_norm:
        return "EM"
    if re.search(r"^[6789]_ANO", turma_norm):
        return "AF"
    if "FUNDAMENTAL" in turma_norm:
        return "AF"
    return "EM"


def _pontuar_pasta_pdf(
    caminho: Path,
    disciplina_root: Path,
    nivel_preferido: str,
    bimestre_token: str,
    serie_tokens: list[str],
    turma_norm: str,
) -> tuple[int, int]:
    try:
        rel_parts = caminho.relative_to(disciplina_root).parts
    except ValueError:
        rel_parts = caminho.parts

    partes_norm = [_nome_pasta_normalizado(parte) for parte in rel_parts]
    partes_set = set(partes_norm)

    score = 0
    if nivel_preferido in partes_set:
        score += 40
    if bimestre_token and bimestre_token in partes_set:
        score += 60
    if turma_norm and turma_norm in partes_set:
        score += 90
    if any(token in partes_set for token in serie_tokens):
        score += 70
    if rel_parts:
        ultimo = partes_norm[-1]
        if turma_norm and ultimo == turma_norm:
            score += 30
        elif any(token == ultimo for token in serie_tokens):
            score += 20

    return score, len(rel_parts)


def _buscar_pasta_pdf_flexivel(
    disciplina_root: Path,
    nivel_preferido: str,
    bimestre_token: str,
    serie_tokens: list[str],
    turma_norm: str,
) -> Path | None:
    if not disciplina_root.exists():
        return None

    melhor: tuple[int, int, Path] | None = None
    for caminho in disciplina_root.rglob("*"):
        if not caminho.is_dir() or not _pasta_tem_pdfs(caminho):
            continue
        score, profundidade = _pontuar_pasta_pdf(
            caminho,
            disciplina_root,
            nivel_preferido,
            bimestre_token,
            serie_tokens,
            turma_norm,
        )
        if score <= 0:
            continue
        candidato = (score, -profundidade, caminho)
        if melhor is None or candidato > melhor:
            melhor = candidato

    return melhor[2] if melhor else None


def arquivo_parece_id_seduc(arquivo) -> bool:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    nome_base = Path(nome).stem.strip()
    return bool(re.fullmatch(r"\d{5,}", nome_base))


def numero_aula_pdf(arquivo) -> int | None:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    nome_base = Path(nome).stem
    
    # Limpar sufixos de cópia comuns
    nome_base = re.sub(r"\s*\(\d+\)$", "", nome_base)  # remove " (1)"
    nome_base = re.sub(r"(?i)\s*-\s*c[oó]pia$", "", nome_base)  # remove " - copia"
    nome_base = re.sub(r"(?i)\s*-\s*copy$", "", nome_base)  # remove " - copy"
    nome_base = nome_base.strip()

    # 1. Tentar encontrar padrão de número no final precedido de _, -, ou espaço (ex: Nome_01, Nome-01, Nome 01)
    match_end = re.search(r"[\s_.-]\s*(\d{1,4})$", nome_base)
    if match_end:
        return int(match_end.group(1))
    
    # 2. Fallback clássico "AULA XX"
    match = re.search(r"\bAULA[_\s-]*(\d{1,4})\b", str(nome), flags=re.I)
    if match:
        return int(match.group(1))
    
    # 3. Fallback geral, evitando IDs longos da SEDUC como "1612757.pdf".
    if arquivo_parece_id_seduc(nome):
        return None
    match_any = re.search(r"(?<!\d)(\d{1,3})(?!\d)", nome_base)
    if match_any:
        return int(match_any.group(1))
    return None


def filtrar_pdfs_para_aulas(arquivos) -> list:
    lista = list(arquivos or [])
    legiveis = [arquivo for arquivo in lista if not arquivo_parece_id_seduc(arquivo)]
    return legiveis or lista


def ordenar_pdfs_por_numero(arquivos) -> list:
    return sorted(
        list(arquivos or []),
        key=lambda arquivo: (
            numero_aula_pdf(arquivo) is None,
            numero_aula_pdf(arquivo) or 10**9,
            getattr(arquivo, "name", None) or Path(str(arquivo)).name,
        ),
    )


def ordenar_pdfs_por_sequencia(arquivos, sequencia_esperada, limite: int | None = None) -> list:
    arquivos_ordenados = ordenar_pdfs_por_numero(arquivos)
    por_numero = {numero_aula_pdf(arquivo): arquivo for arquivo in arquivos_ordenados if numero_aula_pdf(arquivo) is not None}
    sequencia = [int(numero) for numero in (sequencia_esperada or [])]

    selecionados = []
    usados = set()
    for numero in sequencia:
        arquivo = por_numero.get(numero)
        if arquivo is None:
            continue
        selecionados.append(arquivo)
        usados.add(arquivo)

    restantes = [arquivo for arquivo in arquivos_ordenados if arquivo not in usados]
    resultado = selecionados + restantes
    return resultado[:limite] if limite else resultado


def numeros_pdfs_faltantes(arquivos, sequencia_esperada) -> list[int]:
    disponiveis = {numero_aula_pdf(arquivo) for arquivo in (arquivos or [])}
    return [int(numero) for numero in (sequencia_esperada or []) if int(numero) not in disponiveis]


def resolver_pasta_pdfs(base_dir: str, disciplina: str, turma: str, bimestre: str) -> Path:
    r"""Monta o caminho D:\PDF novos\<DISCIPLINA>\<AF|EM>\<N>_BIMESTRE\<N>_ANO"""
    disc_folder = _normalizar_disciplina_para_pasta(disciplina)
    turma_norm = normalizar_para_pasta(turma)

    # Caso especial: se a pasta organizada diretamente por turma existir, usá-la
    caminho_direto = Path(base_dir) / disc_folder / turma_norm
    if caminho_direto.exists():
        return caminho_direto

    nivel = "AF"
    serie = ""

    if "EM" in turma_norm or "ENSINO_MEDIO" in turma_norm or "SERIE" in turma_norm or re.search(r"^[123]_ANO", turma_norm):
        nivel = "EM"

    match_ano = re.search(r"(\d)_ANO", turma_norm)
    match_serie = re.search(r"(\d)_SERIE", turma_norm)
    if match_ano:
        serie = match_ano.group(1) + "_ANO"
    elif match_serie:
        serie = match_serie.group(1) + "_ANO"

    bimestre_norm = normalizar_para_pasta(bimestre)
    match_bim = re.search(r"(\d)_BIMESTRE", bimestre_norm)
    bim = match_bim.group(1) + "_BIMESTRE" if match_bim else ""

    caminho_padrao = Path(base_dir) / disc_folder / nivel / bim / serie
    if caminho_padrao.exists():
        return caminho_padrao

    caminho_flexivel = _buscar_pasta_pdf_flexivel(
        Path(base_dir) / disc_folder,
        nivel_preferido=_nivel_preferido_para_turma(turma_norm),
        bimestre_token=bim,
        serie_tokens=_tokens_serie_turma(turma_norm),
        turma_norm=turma_norm,
    )
    return caminho_flexivel or caminho_padrao
