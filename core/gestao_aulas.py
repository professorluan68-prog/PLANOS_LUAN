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


def _buscar_ultima_aula_em_arquivos_docx(
    professor: str,
    disciplina: str,
    turma: str,
) -> dict:
    from config import PLANOS_FEITOS_DIR, PLANOS_FINALIZADOS_DIR
    from core.helpers import normalizar_para_pasta
    from core.normalizacao import normalizar as normalizar_texto
    from core.turmas import chave_serie_turma
    from core.database import _inferir_turma_por_nome_arquivo

    chave_serie_alvo = chave_serie_turma(turma)
    turma_norm = normalizar_texto(turma)

    diretorios = [PLANOS_FEITOS_DIR, PLANOS_FINALIZADOS_DIR]
    max_aula_turma = 0
    max_aula_serie = 0
    mes_encontrado = ""

    for diretorio_base in diretorios:
        if not diretorio_base or not diretorio_base.exists():
            continue
        pasta_prof = diretorio_base / normalizar_para_pasta(professor) / normalizar_para_pasta(disciplina)
        if not pasta_prof.exists():
            pasta_prof_raiz = diretorio_base / normalizar_para_pasta(professor)
            if not pasta_prof_raiz.exists():
                continue
            pastas_candidatas = [p for p in pasta_prof_raiz.iterdir() if p.is_dir() and normalizar_texto(disciplina) in normalizar_texto(p.name)]
        else:
            pastas_candidatas = [pasta_prof]

        for pasta in pastas_candidatas:
            arquivos = sorted(pasta.rglob("*.docx"), key=lambda p: p.stat().st_mtime, reverse=True)
            for arq in arquivos:
                if arq.name.startswith("~$"):
                    continue
                arq_norm = normalizar_texto(arq.name)
                eh_turma_exata = turma_norm in arq_norm
                eh_mesma_serie = False
                if not eh_turma_exata and chave_serie_alvo:
                    turma_inf = _inferir_turma_por_nome_arquivo(arq.name, disciplina)
                    if chave_serie_turma(turma_inf) == chave_serie_alvo:
                        eh_mesma_serie = True

                if eh_turma_exata or eh_mesma_serie:
                    try:
                        resumo = detectar_resumo_aulas_de_docx_bytes(arq.read_bytes())
                        u = int(resumo.get("ultima_aula") or 0)
                        if u > 0:
                            if eh_turma_exata:
                                max_aula_turma = max(max_aula_turma, u)
                            if eh_mesma_serie or eh_turma_exata:
                                max_aula_serie = max(max_aula_serie, u)
                    except Exception:
                        pass

    aula_final = max(max_aula_turma, max_aula_serie)
    if aula_final > 0:
        return {
            "ultima_aula": aula_final,
            "ultimo_pdf": "",
            "origem": "arquivo_docx",
            "mes": mes_encontrado,
        }
    return {}


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
    2. Inspeção de arquivos DOCX em Planos feitos/<PROFESSOR>/<DISCIPLINA> (incluindo turmas espelho)
    3. historico_planos no bimestre informado
    4. historico_planos em qualquer bimestre (mais recente por data de geração)
    5. Fallback por turmas espelho no histórico
    """
    from core.database import (
        obter_progresso_aula,
        salvar_progresso_aula,
        listar_historico_planos,
    )
    from core.turmas import chave_serie_turma

    # 1. Tabela progresso_aulas
    prog = obter_progresso_aula(professor, disciplina, turma)
    if prog and prog.get("ultima_aula", 0) > 0:
        return {
            "ultima_aula": prog["ultima_aula"],
            "ultimo_pdf": prog.get("ultimo_pdf", ""),
            "origem": "memoria_progresso",
            "mes": prog.get("mes_referencia", ""),
        }

    # 2. Inspeção direta de arquivos DOCX reais em Planos feitos
    ref_docx = _buscar_ultima_aula_em_arquivos_docx(professor, disciplina, turma)
    if ref_docx and ref_docx.get("ultima_aula", 0) > 0:
        salvar_progresso_aula(professor, disciplina, turma, ref_docx["ultima_aula"])
        return ref_docx

    # 3. Histórico no bimestre informado
    if bimestre:
        ref_bim = obter_referencia_ultima_aula_historico(professor, disciplina, turma, bimestre=bimestre)
        if ref_bim and ref_bim.get("ultima_aula", 0) > 0:
            return {
                "ultima_aula": ref_bim["ultima_aula"],
                "ultimo_pdf": ref_bim.get("ultimo_pdf", ""),
                "origem": "historico_bimestre",
                "mes": ref_bim.get("mes_plano", ""),
            }

    # 4. Histórico geral (qualquer bimestre, mais recente)
    ref_geral = obter_referencia_ultima_aula_historico(professor, disciplina, turma, bimestre="")
    if ref_geral and ref_geral.get("ultima_aula", 0) > 0:
        return {
            "ultima_aula": ref_geral["ultima_aula"],
            "ultimo_pdf": ref_geral.get("ultimo_pdf", ""),
            "origem": "historico_geral",
            "mes": ref_geral.get("mes_plano", ""),
        }

    # 5. Fallback por turmas espelho da mesma série no histórico SQLite
    chave_serie_alvo = chave_serie_turma(turma)
    if chave_serie_alvo:
        try:
            historico_prof = listar_historico_planos(
                filtro_prof=professor,
                filtro_disc=disciplina,
                limite=30,
            )
            max_espelho = 0
            for h in historico_prof:
                if chave_serie_turma(h.get("turma", "")) == chave_serie_alvo:
                    max_espelho = max(max_espelho, int(h.get("ultima_aula") or 0))
            if max_espelho > 0:
                salvar_progresso_aula(professor, disciplina, turma, max_espelho)
                return {
                    "ultima_aula": max_espelho,
                    "ultimo_pdf": "",
                    "origem": "historico_geral",
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
