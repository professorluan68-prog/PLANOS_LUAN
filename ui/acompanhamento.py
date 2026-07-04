from __future__ import annotations

from collections import defaultdict
from io import StringIO
import re
import unicodedata

import pandas as pd
import streamlit as st

import core.database as database
from core.disciplinas import BIMESTRES


def _normalizar_chave(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().upper()


def _formatar_data(data_texto: str) -> str:
    texto = str(data_texto or "").strip()
    if not texto:
        return ""
    partes = texto.split(" ")
    data_parte = partes[0]
    if re.match(r"^\d{4}-\d{2}-\d{2}$", data_parte):
        ano, mes, dia = data_parte.split("-")
        hora = partes[1][:5] if len(partes) > 1 and ":" in partes[1] else ""
        return f"{dia}/{mes}/{ano}" + (f" {hora}" if hora else "")
    return texto


def _rotulo_plano(disciplina: str, turma: str) -> str:
    disciplina = str(disciplina or "").strip()
    turma = str(turma or "").strip()
    if disciplina and turma:
        return f"{disciplina} - {turma}"
    return disciplina or turma or "Plano sem identificação"


def _csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = StringIO()
    df.to_csv(buffer, index=False, sep=";", encoding="utf-8-sig")
    return buffer.getvalue().encode("utf-8-sig")


def _listar_ultimos_planos_por_contexto(bimestre: str = "") -> list[dict]:
    if hasattr(database, "listar_ultimos_planos_por_contexto"):
        return database.listar_ultimos_planos_por_contexto(bimestre)

    bimestre = str(bimestre or "").strip()
    with database.get_connection() as conn:
        cursor = conn.cursor()
        if bimestre:
            cursor.execute(
                """
                SELECT
                    h.id,
                    h.professor_nome,
                    h.disciplina,
                    h.turma,
                    COALESCE(h.bimestre, ''),
                    h.data_geracao,
                    h.arquivo_nome
                FROM historico_planos h
                JOIN (
                    SELECT
                        UPPER(TRIM(professor_nome)) AS professor_chave,
                        UPPER(TRIM(disciplina)) AS disciplina_chave,
                        UPPER(TRIM(turma)) AS turma_chave,
                        UPPER(TRIM(COALESCE(bimestre, ''))) AS bimestre_chave,
                        MAX(id) AS ultimo_id
                    FROM historico_planos
                    WHERE UPPER(TRIM(COALESCE(bimestre, ''))) = UPPER(TRIM(?))
                    GROUP BY
                        UPPER(TRIM(professor_nome)),
                        UPPER(TRIM(disciplina)),
                        UPPER(TRIM(turma)),
                        UPPER(TRIM(COALESCE(bimestre, '')))
                ) ultimos
                    ON h.id = ultimos.ultimo_id
                ORDER BY
                    UPPER(TRIM(h.professor_nome)),
                    UPPER(TRIM(h.disciplina)),
                    UPPER(TRIM(h.turma)),
                    h.data_geracao DESC,
                    h.id DESC
                """,
                (bimestre,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    h.id,
                    h.professor_nome,
                    h.disciplina,
                    h.turma,
                    COALESCE(h.bimestre, ''),
                    h.data_geracao,
                    h.arquivo_nome
                FROM historico_planos h
                JOIN (
                    SELECT
                        UPPER(TRIM(professor_nome)) AS professor_chave,
                        UPPER(TRIM(disciplina)) AS disciplina_chave,
                        UPPER(TRIM(turma)) AS turma_chave,
                        UPPER(TRIM(COALESCE(bimestre, ''))) AS bimestre_chave,
                        MAX(id) AS ultimo_id
                    FROM historico_planos
                    GROUP BY
                        UPPER(TRIM(professor_nome)),
                        UPPER(TRIM(disciplina)),
                        UPPER(TRIM(turma)),
                        UPPER(TRIM(COALESCE(bimestre, '')))
                ) ultimos
                    ON h.id = ultimos.ultimo_id
                ORDER BY
                    UPPER(TRIM(h.professor_nome)),
                    UPPER(TRIM(h.disciplina)),
                    UPPER(TRIM(h.turma)),
                    UPPER(TRIM(COALESCE(h.bimestre, ''))),
                    h.data_geracao DESC,
                    h.id DESC
                """
            )

        return [
            {
                "id": int(row[0]),
                "professor_nome": row[1] or "",
                "disciplina": row[2] or "",
                "turma": row[3] or "",
                "bimestre": row[4] or "",
                "data_geracao": row[5] or "",
                "arquivo_nome": row[6] or "",
            }
            for row in cursor.fetchall()
        ]


def _montar_linhas_acompanhamento(bimestre: str) -> tuple[list[dict], list[dict]]:
    professores_db = database.obter_professores_db()
    bimestre_filtro = "" if bimestre == "Todos" else bimestre
    historico = _listar_ultimos_planos_por_contexto(bimestre_filtro)

    historico_por_chave: dict[tuple[str, str, str], dict] = {}
    for item in historico:
        chave = (
            _normalizar_chave(item.get("professor_nome", "")),
            _normalizar_chave(item.get("disciplina", "")),
            _normalizar_chave(item.get("turma", "")),
        )
        historico_por_chave[chave] = item

    cadastros_por_chave: dict[tuple[str, str, str], dict] = {}
    todos_professores = set()

    for professor, dados in professores_db.items():
        todos_professores.add(str(professor or "").strip())
        for item in dados.get("disciplinas", []):
            chave = (
                _normalizar_chave(professor),
                _normalizar_chave(item.get("disciplina", "")),
                _normalizar_chave(item.get("turma", "")),
            )
            cadastro = cadastros_por_chave.setdefault(
                chave,
                {
                    "professor": str(professor or "").strip(),
                    "disciplina": str(item.get("disciplina") or "").strip(),
                    "turma": str(item.get("turma") or "").strip(),
                    "componente_curricular": str(item.get("componente_curricular") or "").strip(),
                    "horario": str(item.get("horario") or "").strip().replace("\n", " | "),
                    "aulas_semana": str(item.get("aulas_semana") or "").strip(),
                    "origem": "Cadastro",
                },
            )
            if not cadastro.get("componente_curricular") and item.get("componente_curricular"):
                cadastro["componente_curricular"] = str(item.get("componente_curricular") or "").strip()
            if not cadastro.get("horario") and item.get("horario"):
                cadastro["horario"] = str(item.get("horario") or "").strip().replace("\n", " | ")
            if not cadastro.get("aulas_semana") and item.get("aulas_semana"):
                cadastro["aulas_semana"] = str(item.get("aulas_semana") or "").strip()

    linhas_detalhe: list[dict] = []
    chaves_processadas = set()

    for chave, cadastro in sorted(
        cadastros_por_chave.items(),
        key=lambda item: (
            _normalizar_chave(item[1].get("professor", "")),
            _normalizar_chave(item[1].get("disciplina", "")),
            _normalizar_chave(item[1].get("turma", "")),
        ),
    ):
        item_hist = historico_por_chave.get(chave)
        chaves_processadas.add(chave)
        linhas_detalhe.append(
            {
                "Professor": cadastro.get("professor", ""),
                "Disciplina": cadastro.get("disciplina", ""),
                "Turma": cadastro.get("turma", ""),
                "Componente": cadastro.get("componente_curricular", ""),
                "Bimestre": str(item_hist.get("bimestre") if item_hist else bimestre_filtro or bimestre).strip(),
                "Status": "Gerado" if item_hist else "Pendente",
                "Gerado em": _formatar_data(str(item_hist.get("data_geracao") or "")) if item_hist else "",
                "_data_sort": str(item_hist.get("data_geracao") or "") if item_hist else "",
                "Arquivo": str(item_hist.get("arquivo_nome") or "") if item_hist else "",
                "Horario": cadastro.get("horario", ""),
                "Aulas/semana": cadastro.get("aulas_semana", ""),
                "Origem": cadastro.get("origem", "Cadastro"),
            }
        )

    for item_hist in historico:
        chave = (
            _normalizar_chave(item_hist.get("professor_nome", "")),
            _normalizar_chave(item_hist.get("disciplina", "")),
            _normalizar_chave(item_hist.get("turma", "")),
        )
        if chave in chaves_processadas:
            continue
        professor = str(item_hist.get("professor_nome") or "").strip()
        todos_professores.add(professor)
        linhas_detalhe.append(
            {
                "Professor": professor,
                "Disciplina": str(item_hist.get("disciplina") or "").strip(),
                "Turma": str(item_hist.get("turma") or "").strip(),
                "Componente": "",
                "Bimestre": str(item_hist.get("bimestre") or "").strip(),
                "Status": "Gerado",
                "Gerado em": _formatar_data(str(item_hist.get("data_geracao") or "")),
                "_data_sort": str(item_hist.get("data_geracao") or ""),
                "Arquivo": str(item_hist.get("arquivo_nome") or "").strip(),
                "Horario": "",
                "Aulas/semana": "",
                "Origem": "Histórico",
            }
        )

    resumo_por_professor: dict[str, dict] = defaultdict(
        lambda: {
            "Professor": "",
            "Cadastros": 0,
            "Gerados": 0,
            "Pendentes": 0,
            "Última geração": "",
            "_ultima_geracao_sort": "",
            "Planos do bimestre": [],
        }
    )

    for professor in todos_professores:
        resumo_por_professor[professor]["Professor"] = professor

    for linha in linhas_detalhe:
        professor = str(linha.get("Professor") or "").strip()
        resumo = resumo_por_professor[professor]
        resumo["Professor"] = professor
        if str(linha.get("Origem") or "") != "Histórico":
            resumo["Cadastros"] += 1
        if str(linha.get("Status") or "") == "Gerado":
            resumo["Gerados"] += 1
            resumo["Planos do bimestre"].append(
                _rotulo_plano(linha.get("Disciplina", ""), linha.get("Turma", ""))
            )
            data_sort = str(linha.get("_data_sort") or "").strip()
            data_geracao = str(linha.get("Gerado em") or "").strip()
            if data_sort and data_sort >= str(resumo.get("_ultima_geracao_sort") or ""):
                resumo["_ultima_geracao_sort"] = data_sort
                resumo["Última geração"] = data_geracao
        elif str(linha.get("Origem") or "") != "Histórico":
            resumo["Pendentes"] += 1

    linhas_resumo = []
    for professor in sorted(resumo_por_professor, key=_normalizar_chave):
        item = resumo_por_professor[professor]
        planos = item.pop("Planos do bimestre", [])
        item.pop("_ultima_geracao_sort", None)
        item["Planos do bimestre"] = " | ".join(planos) if planos else ""
        if item["Cadastros"] == 0 and item["Gerados"] == 0:
            situacao = "Sem cadastro"
        elif item["Cadastros"] == 0 and item["Gerados"] > 0:
            situacao = "Somente histórico"
        elif item["Pendentes"] == 0:
            situacao = "Concluído"
        elif item["Gerados"] == 0:
            situacao = "Nada gerado"
        else:
            situacao = "Parcial"
        item["Situação"] = situacao
        linhas_resumo.append(item)

    linhas_detalhe_limpo = []
    for linha in linhas_detalhe:
        linha_limpa = dict(linha)
        linha_limpa.pop("_data_sort", None)
        linhas_detalhe_limpo.append(linha_limpa)

    return linhas_resumo, linhas_detalhe_limpo


def _filtrar_linhas(
    linhas_resumo: list[dict],
    linhas_detalhe: list[dict],
    busca_professor: str,
    somente_pendentes: bool,
) -> tuple[list[dict], list[dict]]:
    busca_norm = _normalizar_chave(busca_professor)

    def professor_ok(linha: dict) -> bool:
        if not busca_norm:
            return True
        return busca_norm in _normalizar_chave(str(linha.get("Professor") or ""))

    detalhe_filtrado = [
        linha
        for linha in linhas_detalhe
        if professor_ok(linha) and (not somente_pendentes or str(linha.get("Status") or "") == "Pendente")
    ]

    professores_visiveis = {_normalizar_chave(str(linha.get("Professor") or "")) for linha in detalhe_filtrado}
    resumo_filtrado = [
        linha
        for linha in linhas_resumo
        if professor_ok(linha) and (
            not professores_visiveis
            or _normalizar_chave(str(linha.get("Professor") or "")) in professores_visiveis
            or (not somente_pendentes and int(linha.get("Cadastros") or 0) == 0 and int(linha.get("Gerados") or 0) == 0)
        )
    ]

    return resumo_filtrado, detalhe_filtrado


def _renderizar_acompanhamento_planos() -> None:
    st.markdown('<div class="section-title">Acompanhamento dos planos</div>', unsafe_allow_html=True)
    st.caption("Veja por professor o que já foi gerado em cada bimestre e o que ainda está pendente.")

    col_bim, col_busca, col_pendente, col_refresh = st.columns([1.2, 1.5, 1.1, 0.8])
    with col_bim:
        bimestre = st.selectbox(
            "Bimestre",
            ["Todos"] + list(BIMESTRES),
            index=0,
            key="painel_bimestre",
        )
    with col_busca:
        busca_professor = st.text_input(
            "Filtrar professor",
            key="painel_busca_professor",
            placeholder="Digite parte do nome",
        ).strip()
    with col_pendente:
        somente_pendentes = st.checkbox(
            "Mostrar só pendentes",
            key="painel_somente_pendentes",
            value=False,
        )
    with col_refresh:
        st.write("")
        st.write("")
        if st.button("Atualizar", key="painel_atualizar"):
            st.rerun()

    linhas_resumo, linhas_detalhe = _montar_linhas_acompanhamento(bimestre)
    linhas_resumo, linhas_detalhe = _filtrar_linhas(
        linhas_resumo,
        linhas_detalhe,
        busca_professor,
        somente_pendentes,
    )

    total_professores = len(linhas_resumo)
    total_planos = len(linhas_detalhe)
    total_gerados = sum(1 for linha in linhas_detalhe if str(linha.get("Status") or "") == "Gerado")
    total_pendentes = sum(1 for linha in linhas_detalhe if str(linha.get("Status") or "") == "Pendente")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Professores visíveis", total_professores)
    col2.metric("Planos no painel", total_planos)
    col3.metric("Gerados", total_gerados)
    col4.metric("Pendentes", total_pendentes)

    if not linhas_resumo and not linhas_detalhe:
        st.info("Ainda não há dados suficientes para montar o acompanhamento.")
        return

    abas = st.tabs(["Resumo por professor", "Detalhamento"])

    with abas[0]:
        df_resumo = pd.DataFrame(linhas_resumo)
        if df_resumo.empty:
            st.info("Nenhum professor encontrado com os filtros informados.")
        else:
            st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    with abas[1]:
        df_detalhe = pd.DataFrame(linhas_detalhe)
        if df_detalhe.empty:
            st.info("Nenhum plano encontrado com os filtros informados.")
        else:
            st.download_button(
                "Exportar acompanhamento (CSV)",
                data=_csv_bytes(df_detalhe),
                file_name="acompanhamento_planos.csv",
                mime="text/csv",
                key="baixar_csv_acompanhamento",
            )
            st.dataframe(df_detalhe, use_container_width=True, hide_index=True)
