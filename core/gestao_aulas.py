import re
import json
from io import BytesIO
from pathlib import Path
from docx import Document

from config import REGISTRO_PROXIMA_GERACAO_PATH


_PADRAO_AULA = re.compile(r"\bAULA\s*(\d+)\b", re.IGNORECASE)
_PADRAO_BIMESTRE = re.compile(r"\b([1-4])\s*(?:[º°]|[oa])?\s*BIMESTRE\b", re.IGNORECASE)


def _numero_bimestre(texto: str) -> int:
    correspondencia = _PADRAO_BIMESTRE.search(str(texto or ""))
    return int(correspondencia.group(1)) if correspondencia else 0


def _bimestres_do_cabecalho(documento: Document) -> set[int]:
    """Localiza o valor do bimestre no cabeçalho, não em notas das aulas."""
    bimestres = set()
    for tabela in documento.tables:
        for indice_linha, linha in enumerate(tabela.rows[:-1]):
            for indice_coluna, celula in enumerate(linha.cells):
                if str(celula.text or "").strip().upper() != "BIMESTRE":
                    continue
                for linha_dados in tabela.rows[indice_linha + 1:]:
                    numero = _numero_bimestre(linha_dados.cells[indice_coluna].text)
                    if numero:
                        bimestres.add(numero)
                        break
    return bimestres


def detectar_resumo_aulas_de_docx_bytes(docx_bytes: bytes, bimestre: str = "") -> dict[str, int]:
    """Analisa um .docx e retorna última aula e quantidade de aulas distintas."""
    if not docx_bytes:
        return {"ultima_aula": 0, "total_aulas": 0}

    try:
        documento = Document(BytesIO(docx_bytes))
        bimestre_esperado = _numero_bimestre(bimestre)
        bimestres_cabecalho = _bimestres_do_cabecalho(documento)
        if bimestre_esperado and bimestres_cabecalho and bimestre_esperado not in bimestres_cabecalho:
            return {"ultima_aula": 0, "total_aulas": 0}

        aulas_detectadas = []
        textos = [paragrafo.text for paragrafo in documento.paragraphs]
        celulas_vistas = set()
        for tabela in documento.tables:
            for linha in tabela.rows:
                for celula in linha.cells:
                    chave_celula = celula._tc
                    if chave_celula not in celulas_vistas:
                        celulas_vistas.add(chave_celula)
                        textos.append(celula.text)

        for texto in textos:
            aulas_detectadas.extend(
                int(correspondencia.group(1))
                for correspondencia in _PADRAO_AULA.finditer(texto or "")
            )

        if aulas_detectadas:
            aulas_unicas = sorted(set(aulas_detectadas))
            return {"ultima_aula": max(aulas_unicas), "total_aulas": len(aulas_unicas)}
    except Exception:
        pass

    return {"ultima_aula": 0, "total_aulas": 0}


def detectar_ultima_aula_de_docx_bytes(docx_bytes: bytes, bimestre: str = "") -> int:
    """
    Analisa os bytes de um arquivo .docx para extrair o número máximo de aula gerado.
    """
    return detectar_resumo_aulas_de_docx_bytes(docx_bytes, bimestre)["ultima_aula"]

def obter_aula_parada_do_json(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    """
    Tenta obter o número da aula de parada a partir do arquivo JSON de mapeamento.
    """
    prof_upper = str(professor or "").strip().upper()
    disc_upper = str(disciplina or "").strip().upper()
    turma_upper = str(turma or "").strip().upper()

    try:
        json_path = Path(REGISTRO_PROXIMA_GERACAO_PATH)
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as fj:
                dados = json.load(fj)
                for item in dados:
                    if (str(item.get("professor") or "").strip().upper() == prof_upper and
                        str(item.get("disciplina") or "").strip().upper() == disc_upper and
                        str(item.get("turma") or "").strip().upper() == turma_upper):
                        if bimestre and item.get("bimestre"):
                            if str(item.get("bimestre")).strip().lower() != bimestre.strip().lower():
                                continue
                        return int(item.get("aula_parada") or 0)
    except Exception:
        pass

    return 0


def obter_referencia_ultima_aula_historico(
    professor: str,
    disciplina: str,
    turma: str,
    bimestre: str = "",
) -> dict | None:
    """Consulta o último plano salvo e identifica a última aula registrada nele.

    Esta função auxilia no cálculo da continuidade pedagógica e na seleção automática
    de PDFs da interface.
    """
    from core.database import (
        obter_arquivo_historico,
        obter_ultimo_historico_por_contexto,
    )

    historico = obter_ultimo_historico_por_contexto(
        professor,
        disciplina,
        turma,
        bimestre,
    )
    if not historico:
        return None

    if historico.get("ultima_aula") is not None:
        ultima_aula = int(historico.get("ultima_aula") or 0)
    else:
        _, docx_bytes = obter_arquivo_historico(historico["id"])
        ultima_aula = detectar_ultima_aula_de_docx_bytes(docx_bytes, bimestre)

    return {
        **historico,
        "ultima_aula": ultima_aula,
    }


def obter_referencia_ultima_aula_ampla(
    professor: str,
    disciplina: str,
    turma: str,
    bimestre: str = "",
) -> dict:
    """
    Consulta a última aula identificada para o contexto (professor, disciplina, turma).
    Ordem de busca:
    1. Tabela dedicada progresso_aulas (SQLite)
    2. historico_planos no bimestre informado
    3. historico_planos em qualquer bimestre (mais recente por data de geração)
    4. Inspeção de arquivos DOCX em Planos feitos/<PROFESSOR>/<DISCIPLINA>
    """
    from core.database import (
        obter_progresso_aula,
        salvar_progresso_aula,
    )
    from core.normalizacao import normalizar as normalizar_texto

    # 1. Tabela progresso_aulas
    prog = obter_progresso_aula(professor, disciplina, turma)
    if prog and prog.get("ultima_aula", 0) > 0:
        return {
            "ultima_aula": prog["ultima_aula"],
            "ultimo_pdf": prog.get("ultimo_pdf", ""),
            "origem": "memoria_progresso",
            "mes": prog.get("mes_referencia", ""),
        }

    # 2. Histórico no bimestre informado
    if bimestre:
        ref_bim = obter_referencia_ultima_aula_historico(professor, disciplina, turma, bimestre=bimestre)
        if ref_bim and ref_bim.get("ultima_aula", 0) > 0:
            return {
                "ultima_aula": ref_bim["ultima_aula"],
                "ultimo_pdf": ref_bim.get("ultimo_pdf", ""),
                "origem": "historico_bimestre",
                "mes": ref_bim.get("mes_plano", ""),
            }

    # 3. Histórico geral (qualquer bimestre, mais recente)
    ref_geral = obter_referencia_ultima_aula_historico(professor, disciplina, turma, bimestre="")
    if ref_geral and ref_geral.get("ultima_aula", 0) > 0:
        return {
            "ultima_aula": ref_geral["ultima_aula"],
            "ultimo_pdf": ref_geral.get("ultimo_pdf", ""),
            "origem": "historico_geral",
            "mes": ref_geral.get("mes_plano", ""),
        }

    # 4. Fallback: procurar DOCX na pasta de finalizados
    try:
        from config import PLANOS_FINALIZADOS_DIR
        from core.helpers import normalizar_para_pasta
        pasta_prof = PLANOS_FINALIZADOS_DIR / normalizar_para_pasta(professor) / normalizar_para_pasta(disciplina)
        if pasta_prof.exists():
            arquivos = sorted(pasta_prof.rglob("*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
            for arq in arquivos:
                if arq.name.startswith("~$"):
                    continue
                if normalizar_texto(turma) in normalizar_texto(arq.name):
                    resumo = detectar_resumo_aulas_de_docx_bytes(arq.read_bytes())
                    if resumo.get("ultima_aula", 0) > 0:
                        salvar_progresso_aula(professor, disciplina, turma, resumo["ultima_aula"])
                        return {
                            "ultima_aula": resumo["ultima_aula"],
                            "ultimo_pdf": "",
                            "origem": "arquivo_docx",
                            "mes": "",
                        }
    except Exception:
        pass

    return {
        "ultima_aula": 0,
        "ultimo_pdf": "",
        "origem": "nenhuma",
        "mes": "",
    }


def obter_ultima_aula_gerada_sistema_impl(professor: str, disciplina: str, turma: str, bimestre: str = "") -> int:
    """
    Retorna o número da última aula gerada para servir de ponto
    de partida e continuidade na nova geração.
    """
    ref = obter_referencia_ultima_aula_ampla(professor, disciplina, turma, bimestre)
    return int(ref.get("ultima_aula") or 0)
