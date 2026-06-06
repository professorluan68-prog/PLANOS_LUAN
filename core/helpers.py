import io
import re
import unicodedata
from pathlib import Path
from collections.abc import Iterable


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


def resolver_pasta_pdfs(base_dir: str, disciplina: str, turma: str, bimestre: str) -> Path:
    r"""Monta o caminho D:\PDF novos\<DISCIPLINA>\<AF|EM>\<N>_BIMESTRE\<N>_ANO"""
    def _normalizar_para_pasta(texto: str) -> str:
        t = unicodedata.normalize("NFKD", str(texto or ""))
        t = "".join(ch for ch in t if not unicodedata.combining(ch))
        t = re.sub(r"[^\w\s]", "", t).upper().strip().replace(" ", "_")
        # Ajustar '1O_ANO' para '1_ANO' e '2A_SERIE' para '2_SERIE'
        t = re.sub(r"(\d)[OA]_", r"\1_", t)
        return t

    disc_folder = _normalizar_para_pasta(disciplina)
    turma_norm = _normalizar_para_pasta(turma)

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

    bimestre_norm = _normalizar_para_pasta(bimestre)
    match_bim = re.search(r"(\d)_BIMESTRE", bimestre_norm)
    bim = match_bim.group(1) + "_BIMESTRE" if match_bim else ""

    return Path(base_dir) / disc_folder / nivel / bim / serie

