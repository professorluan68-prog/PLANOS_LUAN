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
        linhas.extend(
            [
                f"Aula {idx}",
                f"Tema: {aula.get('tema', '')}",
                f"Data: {aula.get('data', '')}",
                f"Horario: {str(aula.get('horario', '')).replace(chr(10), ' - ')}",
                f"IA usada: {'sim' if aula.get('ia_usada') else 'nao'}",
                "",
            ]
        )
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


def numero_aula_pdf(arquivo) -> int | None:
    nome = getattr(arquivo, "name", None) or Path(str(arquivo)).name
    match = re.search(r"\bAULA[_\s-]*(\d{1,4})\b", str(nome), flags=re.I)
    return int(match.group(1)) if match else None


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

    return Path(base_dir) / disc_folder / nivel / bim / serie
