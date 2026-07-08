from __future__ import annotations

import re
import unicodedata
import zipfile
from io import BytesIO

from docx_generator.preencher import preencher_documento

from core.helpers import montar_relatorio_geracao


def _slug_download(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto).strip("_")


def nome_arquivo_plano_operacao(
    turma: str,
    disciplina: str,
    ia_usada: bool = False,
) -> str:
    s_turma = _slug_download(turma)
    s_disc = _slug_download(disciplina)
    s_ia = "_In" if ia_usada else ""
    return f"Plano_{s_turma}_{s_disc}{s_ia}.docx"


def gerar_docx_final(
    modelo_bytes: bytes,
    aulas,
    escola: str,
    professor: str,
    disciplina: str,
    componente_curricular: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    semana: str,
    observacao: str,
    aulas_previstas_manual: str,
):
    docx_bytes = preencher_documento(
        BytesIO(modelo_bytes),
        aulas,
        escola=escola,
        professor=professor,
        disciplina=componente_curricular or disciplina,
        turma=turma_atual,
        mes=mes,
        bimestre=bimestre,
        semana=semana,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )
    relatorio = montar_relatorio_geracao(aulas, disciplina, turma_atual, bimestre, mes)
    return {
        "turma": turma_atual,
        "aulas": aulas,
        "docx_bytes": docx_bytes,
        "relatorio": relatorio,
        "ia_usada": any(aula.get("ia_usada") for aula in aulas),
    }


def gerar_planos_finais_sem_revisao(
    modelo_bytes: bytes,
    turmas_processadas,
    escola: str,
    professor: str,
    disciplina: str,
    componente_curricular: str,
    mes: str,
    bimestre: str,
    semana: str,
    observacao: str,
    aulas_previstas_manual: str,
):
    planos_gerados = []
    for tr in turmas_processadas or []:
        planos_gerados.append(
            gerar_docx_final(
                modelo_bytes,
                tr["aulas"],
                escola,
                professor,
                disciplina,
                componente_curricular,
                tr["turma"],
                mes,
                bimestre,
                semana,
                observacao,
                aulas_previstas_manual,
            )
        )
    return planos_gerados


def montar_zip_planos(planos: list[dict], disciplina: str) -> bytes:
    saida = BytesIO()
    with zipfile.ZipFile(saida, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for plano in planos:
            nome_docx = nome_arquivo_plano_operacao(
                plano["turma"],
                disciplina,
                ia_usada=plano["ia_usada"],
            )
            zf.writestr(nome_docx, plano["docx_bytes"].getvalue())
            zf.writestr(
                nome_docx.replace(".docx", "_relatorio.txt"),
                plano["relatorio"].encode("utf-8"),
            )
    saida.seek(0)
    return saida.read()


def detectar_alteracoes_planos_revisados(
    planos_gerados: list[dict],
    turmas_revisadas: list[dict],
) -> bool:
    for turma_revisada in turmas_revisadas or []:
        plano_gerado = next(
            (
                plano
                for plano in planos_gerados or []
                if plano.get("turma") == turma_revisada.get("turma")
            ),
            None,
        )
        if not plano_gerado:
            return True
        aulas_geradas = plano_gerado.get("aulas", [])
        aulas_revisadas = turma_revisada.get("aulas", [])
        if len(aulas_geradas) != len(aulas_revisadas):
            return True
        for aula_gerada, aula_revisada in zip(aulas_geradas, aulas_revisadas):
            if (
                aula_gerada.get("tema") != aula_revisada.get("tema")
                or aula_gerada.get("aprendizagem") != aula_revisada.get("aprendizagem")
                or aula_gerada.get("acompanhamento") != aula_revisada.get("acompanhamento")
                or aula_gerada.get("acessibilidade") != aula_revisada.get("acessibilidade")
                or aula_gerada.get("metodologia") != aula_revisada.get("metodologia")
            ):
                return True
    return False
