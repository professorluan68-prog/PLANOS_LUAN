import streamlit as st
import tempfile
import re
import os
import json
import base64
import zipfile
import unicodedata
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from core.disciplinas import (
    BIMESTRES,
    TURMAS_CDP_MULTISSERIADA,
    eh_cdp,
    eh_cdp_contextual,
    eh_cdp_fundamental,
    eh_cdp_multisseriada,
    nomes_disciplinas,
    obter_config,
)
from core.cdp import SEQUENCIA_PADRAO_CDP_MULTISSERIADA
from core.lote import processar_varios_pdfs
from core.validador_plano import validar_aulas_geradas
from config import MODELO_OPENAI_PADRAO, MODELO_GEMINI_PADRAO, PASTA_PLANOS_PROFESSORES, PLANOS_FINALIZADOS_DIR
from docx_generator.preencher import preencher_documento
from docx_generator.preencher_cdp import preencher_documento_cdp
from core.helpers import horario_para_plano, montar_relatorio_geracao, texto_lista as _texto_lista
from core.database import init_db, migrar_json_para_sqlite, obter_professores_db, salvar_professor_turma, salvar_historico_plano, listar_historico_planos, obter_arquivo_historico
from core.professores_planos import carregar_professores_dos_planos, criar_ou_atualizar_modelo_professor, diagnosticar_modelos_professores, mesclar_professores

BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

st.set_page_config(page_title="PLANOS_LUAN", layout="wide")


@st.cache_data(show_spinner=False, ttl=300)
def _carregar_professores_dos_planos_cache():
    return carregar_professores_dos_planos()


@st.cache_data(show_spinner=False, ttl=120)
def _diagnosticar_modelos_professores_cache():
    return diagnosticar_modelos_professores()


@st.cache_data(show_spinner=False, ttl=300)
def _ler_bytes_arquivo_cache(caminho: str) -> bytes | None:
    caminho_path = Path(caminho)
    if not caminho_path.exists():
        return None
    return caminho_path.read_bytes()

# Lógica para carregar chaves do arquivo texto (se existir)
def carregar_chaves_locais():
    caminho_chaves = BASE_DIR / "chaves.txt"
    if caminho_chaves.exists():
        conteudo = caminho_chaves.read_text(encoding="utf-8").splitlines()
        for linha in conteudo:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip().upper()
            valor = valor.strip()
            if valor:
                os.environ[chave] = valor

carregar_chaves_locais()


CAMPOS_TELA = {
    "modelo_file",
    "pdfs_aulas_files",
    "novo_modelo_file",
    "escolha_template",
    "escolha_template_manual",
    "modo_tela",
    "modo_ia",
    "professor",
    "professor_select",
    "aula_prof_select",
    "last_aula_prof",
    "disciplina_opcao",
    "disciplina_cdp_opcao",
    "disciplina_outra",
    "turma",
    "turma_select",
    "turma_cdp",
    "cdp_aula_inicial",
    "gerar_turma_espelho",
    "turma_espelho",
    "turma_espelho_select",
    "bimestre",
    "mes",
    "mes_select",
    "aulas_previstas_manual",
    "aulas_previstas_manual_select",
    "escola",
    "componente_curricular",
    "last_componente_curricular",
    "professor_cadastro_select",
    "nova_turma_select",
    "nova_turma_digitada",
    "novas_aulas_semana",
    "novas_aulas_semana_select",
    "novo_componente_curricular",
    "observacao",
    "auto_repetir_semana",
    "dividir_metodologia",
    "geracao_em_andamento",
    "turmas_processadas",
    "planos_gerados",
    "revisao_token",
}
PREFIXOS_TELA = (
    "data_aula_",
    "horario_aula_",
    "tipo_horario_aula_",
    "data_turma2_aula_",
    "horario_turma2_aula_",
    "tipo_horario_turma2_aula_",
    "cadastro_grade_",
    "ajuste_grade_",
)
PREFIXOS_REVISAO = ("tema_", "apr_", "acomp_", "acess_", "met_")


def _limpar_revisao_aulas() -> None:
    for chave in list(st.session_state.keys()):
        if any(str(chave).startswith(prefixo) for prefixo in PREFIXOS_REVISAO):
            del st.session_state[chave]


def limpar_dados_tela() -> None:
    _limpar_revisao_aulas()
    for chave in list(st.session_state.keys()):
        if chave in CAMPOS_TELA or any(str(chave).startswith(prefixo) for prefixo in PREFIXOS_TELA):
            del st.session_state[chave]


def _asset_data_uri(nome_arquivo: str, mime_type: str = "image/svg+xml") -> str:
    caminho = BASE_DIR / "assets" / nome_arquivo
    if not caminho.exists():
        return ""
    dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{dados}"

HORARIOS_AULA = [
    ("07h", "1ª aula"),
    ("07h50", "2ª aula"),
    ("08h40", "3ª aula"),
    ("09h50", "4ª aula"),
    ("10h40", "5ª aula"),
    ("11h30", "6ª aula"),
    ("13h", "1ª aula"),
    ("13h50", "2ª aula"),
    ("14h40", "3ª aula"),
    ("15h50", "4ª aula"),
    ("16h40", "5ª aula"),
    ("17h30", "6ª aula"),
    ("19h", "1ª aula"),
    ("19h45", "2ª aula"),
    ("20h30", "3ª aula"),
    ("21h30", "4ª aula"),
    ("22h15", "5ª aula"),
    # Faixas para professores com duas aulas seguidas (sem alterar o restante do fluxo)
    ("07h - 08h40", "1ª e 2ª aula"),
    ("07h50 - 09h50", "2ª e 3ª aula"),
    ("08h40 - 10h40", "3ª e 4ª aula"),
    ("09h50 - 11h30", "4ª e 5ª aula"),
    ("10h40 - 12h20", "5ª e 6ª aula"),
    ("13h - 14h40", "1ª e 2ª aula"),
    ("13h50 - 15h50", "2ª e 3ª aula"),
    ("14h40 - 16h40", "3ª e 4ª aula"),
    ("15h50 - 17h30", "4ª e 5ª aula"),
    ("16h40 - 18h20", "5ª e 6ª aula"),
    ("19h - 20h30", "1ª e 2ª aula"),
    ("19h45 - 21h30", "2ª e 3ª aula"),
    ("20h30 - 22h15", "3ª e 4ª aula"),
    ("21h30 - 23h", "4ª e 5ª aula"),
    # Faixas não consecutivas (escolas com alternância de horário)
    ("07h - 10h40", "1ª e 4ª aula"),
    ("13h - 16h40", "1ª e 4ª aula"),
    ("08h40 - 11h30", "3ª e 6ª aula"),
    ("14h40 - 17h30", "3ª e 6ª aula"),
    ("07h50 - 10h40", "2ª e 5ª aula"),
    ("13h50 - 16h40", "2ª e 5ª aula"),
    ("07h50 - 11h30", "2ª e 6ª aula"),
    ("13h50 - 17h30", "2ª e 6ª aula"),
    ("19h - 21h30", "1ª e 4ª aula"),
    ("19h45 - 22h15", "2ª e 5ª aula"),
]

HORARIOS_LABELS = {item: f"{item[0]} - {item[1]}" for item in HORARIOS_AULA}
HORARIOS_SIMPLES = HORARIOS_AULA[:17]
HORARIOS_DUPLAS = HORARIOS_AULA[17:]

DIAS_SEMANA_CADASTRO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
TURNOS_HORARIOS = {
    "Manhã": ["07h", "07h50", "08h40", "09h50", "10h40", "11h30", "12h20"],
    "Tarde": ["13h", "13h50", "14h40", "15h50", "16h40", "17h30", "18h20"],
    "Noite": ["19h", "19h45", "20h30", "21h30", "22h15", "23h"],
}


def _rotulo_horario(horario) -> str:
    if isinstance(horario, tuple) and len(horario) >= 2:
        return HORARIOS_LABELS.get(horario, f"{horario[0]} - {horario[1]}")
    return str(horario or "")


def _serializar_horarios_padronizados(horarios) -> str:
    return "\n".join(_rotulo_horario(item) for item in horarios or [] if _rotulo_horario(item).strip())

MESES = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO",
]

AULAS_SEMANA_OPCOES = ["(selecione)"] + [str(i) for i in range(1, 16)]

TURMAS_PADRAO = ["(selecione a turma)"]
TURMAS_PADRAO += [f"{ano}º ANO {letra}" for ano in range(1, 10) for letra in ["A", "B", "C", "D", "E", "F"]]
TURMAS_PADRAO += [f"{ano}º ANO" for ano in range(1, 10)]
TURMAS_PADRAO += [
    "8º e 9º ano",
    "MULTISSERIADO 1º, 2º e 3º ano",
    "MULTISSERIADO 4º e 5º ano",
]
TURMAS_PADRAO += [turma for turma in TURMAS_CDP_MULTISSERIADA if turma not in TURMAS_PADRAO]
TURMAS_PADRAO += ["Outra (digitar)"]


def _selecionar_turma(label: str, key_select: str, key_texto: str, placeholder: str = "Ex.: 7º ANO A") -> str:
    valor_atual = str(st.session_state.get(key_texto, "") or "").strip()
    opcoes = list(TURMAS_PADRAO)
    if valor_atual and valor_atual not in opcoes:
        opcoes.insert(-1, valor_atual)
    indice = opcoes.index(valor_atual) if valor_atual in opcoes else 0
    escolha = st.selectbox(label, opcoes, index=indice, key=key_select)
    if escolha == "Outra (digitar)":
        return st.text_input("Digite a turma", key=key_texto, placeholder=placeholder, autocomplete="off").strip()
    if escolha == "(selecione a turma)":
        st.session_state[key_texto] = ""
        return ""
    st.session_state[key_texto] = escolha
    return escolha


def _selecionar_mes() -> str:
    valor_atual = str(st.session_state.get("mes", "") or "").strip().upper()
    mes_padrao = MESES[date.today().month - 1]
    indice = MESES.index(valor_atual) if valor_atual in MESES else MESES.index(mes_padrao)
    mes_escolhido = st.selectbox("Mês", MESES, index=indice, key="mes_select")
    st.session_state["mes"] = mes_escolhido
    return mes_escolhido


def _selecionar_aulas_semana(label: str, key_select: str, key_texto: str) -> str:
    valor_atual = str(st.session_state.get(key_texto, "") or "").strip()
    opcoes = list(AULAS_SEMANA_OPCOES)
    if valor_atual and valor_atual not in opcoes:
        opcoes.append(valor_atual)
    indice = opcoes.index(valor_atual) if valor_atual in opcoes else 0
    escolha = st.selectbox(label, opcoes, index=indice, key=key_select)
    valor = "" if escolha == "(selecione)" else escolha
    st.session_state[key_texto] = valor
    return valor

# ── Banco de Dados e Cadastro ──────────────────────────────────────────
init_db()
migrar_json_para_sqlite()
PROFESSORES_DB = mesclar_professores(obter_professores_db(), _carregar_professores_dos_planos_cache())

# Cadastro de professores fica como uma area propria da tela principal.
def _renderizar_cadastro_professor() -> None:
    st.markdown('<div class="section-title">Cadastro de professor</div>', unsafe_allow_html=True)
    st.caption("Cadastre um novo professor ou ajuste disciplina, turma, dia, horario e quantidade de aulas.")

    with st.form("form_cadastro_prof", clear_on_submit=True):
        col_prof_cad, col_disc_cad = st.columns(2)
        with col_prof_cad:
            professor_cadastro = st.selectbox(
                "Professor",
                ["Novo professor"] + sorted(PROFESSORES_DB.keys()),
                key="professor_cadastro_select",
            )
            if professor_cadastro == "Novo professor":
                novo_nome = st.text_input("Nome do Professor").strip().upper()
            else:
                novo_nome = professor_cadastro
        with col_disc_cad:
            nova_disc_op = st.selectbox("Disciplina", nomes_disciplinas())
            nova_disc_outra = st.text_input("Qual disciplina?") if nova_disc_op == "Outra" else ""

        col_turma_cad, col_aulas_cad = st.columns([2, 1])
        with col_turma_cad:
            nova_turma = _selecionar_turma("Turma", "nova_turma_select", "nova_turma_digitada")
        with col_aulas_cad:
            novas_aulas_semana = _selecionar_aulas_semana(
                "Qtd. aulas na semana",
                "novas_aulas_semana_select",
                "novas_aulas_semana",
            )

        novo_componente_curricular = st.text_input(
            "Componente curricular (como aparecerá no plano)",
            placeholder="Ex.: CDP-E. F -EJA - MATEMÁTICA",
            key="novo_componente_curricular",
        )

        novo_dia, novo_horario, total_grade = _renderizar_grade_horarios(
            "cadastro_grade",
            contexto=nova_turma,
        )

        submitted = st.form_submit_button("Salvar cadastro", type="primary")
        if submitted:
            disc_final = nova_disc_outra if nova_disc_op == "Outra" else nova_disc_op
            aulas_semana_final = novas_aulas_semana or (str(total_grade) if total_grade else "")
            if novo_nome and disc_final and nova_turma:
                salvar_professor_turma(
                    novo_nome,
                    disc_final,
                    nova_turma,
                    novo_dia,
                    novo_horario,
                    aulas_semana_final,
                    componente_curricular=novo_componente_curricular.strip(),
                )
                _carregar_professores_dos_planos_cache.clear()
                st.success(f"Cadastro de {novo_nome} salvo.")
                st.rerun()
            else:
                st.error("Preencha ao menos nome, disciplina e turma.")


def _renderizar_diagnostico_modelos() -> None:
    st.markdown('<div class="section-title">Diagnóstico dos modelos</div>', unsafe_allow_html=True)
    st.caption("Confira se os modelos dos professores estão prontos para preenchimento automático.")

    col_atualizar, _ = st.columns([1, 4])
    with col_atualizar:
        if st.button("Atualizar diagnóstico"):
            _diagnosticar_modelos_professores_cache.clear()
            _carregar_professores_dos_planos_cache.clear()
            st.rerun()

    diagnostico = _diagnosticar_modelos_professores_cache()
    if diagnostico.get("erro_base"):
        st.error(str(diagnostico["erro_base"]))
        return

    professores_banco = obter_professores_db()
    professores_pasta = _carregar_professores_dos_planos_cache()

    col_total, col_ok, col_sem_hora, col_dup, col_banco = st.columns(5)
    col_total.metric("Modelos DOCX", int(diagnostico.get("total_docx", 0)))
    col_ok.metric("Lidos sem erro", int(diagnostico.get("lidos_ok", 0)))
    col_sem_hora.metric("Sem data/horário", len(diagnostico.get("sem_datas_horarios", [])))
    col_dup.metric("Duplicidades", len(diagnostico.get("duplicidades", [])))
    col_banco.metric("Banco / pastas", f"{len(professores_banco)} / {len(professores_pasta)}")

    erros = diagnostico.get("erros_leitura", [])
    sem_disciplina_turma = diagnostico.get("sem_disciplina_turma", [])
    sem_datas_horarios = diagnostico.get("sem_datas_horarios", [])
    duplicidades = diagnostico.get("duplicidades", [])

    if not erros and not sem_disciplina_turma and not duplicidades:
        st.success("Estrutura principal dos modelos lida sem erros.")

    with st.expander("Modelos sem data/horário detectável", expanded=bool(sem_datas_horarios)):
        if sem_datas_horarios:
            st.dataframe(sem_datas_horarios, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum modelo sem data/horário foi encontrado.")

    with st.expander("Duplicidades por professor, disciplina e turma", expanded=bool(duplicidades)):
        if duplicidades:
            linhas_dup = [
                {
                    "professor": item.get("professor", ""),
                    "disciplina": item.get("disciplina", ""),
                    "turma": item.get("turma", ""),
                    "arquivos": "\n".join(item.get("arquivos", [])),
                }
                for item in duplicidades
            ]
            st.dataframe(linhas_dup, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma duplicidade foi encontrada.")

    with st.expander("Arquivos sem disciplina/turma ou com erro de leitura", expanded=bool(erros or sem_disciplina_turma)):
        if sem_disciplina_turma:
            st.markdown("**Sem disciplina ou turma**")
            st.dataframe(sem_disciplina_turma, use_container_width=True, hide_index=True)
        if erros:
            st.markdown("**Erro de leitura**")
            st.dataframe(erros, use_container_width=True, hide_index=True)
        if not erros and not sem_disciplina_turma:
            st.info("Nenhum problema de leitura foi encontrado.")

    with st.expander("Backup e restauração"):
        st.caption("Use estes comandos quando quiser fazer uma cópia completa fora do sistema.")
        st.code(
            "\n".join(
                [
                    "$Data = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'",
                    "$Backup = \"D:\\BACKUPS_PLANOS_LUAN\\BACKUP_$Data\"",
                    f"Copy-Item -LiteralPath \"{BASE_DIR}\" -Destination \"$Backup\\PLANOS_LUAN\" -Recurse -Force",
                    f"Copy-Item -LiteralPath \"{PASTA_PLANOS_PROFESSORES}\" -Destination \"$Backup\\PLANOS DE JUNHO\" -Recurse -Force",
                    f"Copy-Item -LiteralPath \"{PLANOS_FINALIZADOS_DIR}\" -Destination \"$Backup\\PLANOS-FINALIZADOS\" -Recurse -Force",
                    "Compress-Archive -Path \"$Backup\\*\" -DestinationPath \"$Backup.zip\" -Force",
                ]
            ),
            language="powershell",
        )


with st.sidebar:
    st.markdown("### Histórico de Planos")
    historico = listar_historico_planos()
    if not historico:
        st.info("Nenhum plano gerado ainda.")
    else:
        # Pega apenas os 5 mais recentes para não poluir
        for plano_id, prof, disc, t, data_gen, arq_nome in historico[:5]:
            with st.expander(f"{t} - {data_gen[:10]}"):
                st.caption(f"Prof: {prof}")
                st.caption(f"Arquivo: {arq_nome}")
                # Quando o usuário clicar, carrega o blob
                if st.button("Preparar Download", key=f"prep_{plano_id}"):
                    arq_info = obter_arquivo_historico(plano_id)
                    if arq_info:
                        st.session_state[f"download_bytes_{plano_id}"] = arq_info[1]
                
                if f"download_bytes_{plano_id}" in st.session_state:
                    st.download_button(
                        label="📥 Baixar DOCX",
                        data=st.session_state[f"download_bytes_{plano_id}"],
                        file_name=arq_nome,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_hist_{plano_id}"
                    )

# Extrair lista simples de disciplinas únicas para cada professor
PROFESSORES = {}
for prof, dados_prof in PROFESSORES_DB.items():
    disciplinas_unicas = []
    for d in dados_prof.get("disciplinas", []):
        nome_disc = d.get("disciplina")
        if nome_disc and nome_disc not in disciplinas_unicas:
            disciplinas_unicas.append(nome_disc)
    PROFESSORES[prof] = disciplinas_unicas

# Lista ordenada para o selectbox
_NOMES_PROFESSORES = ["(selecione o professor)"] + sorted(PROFESSORES.keys()) + ["Outro (digitar)"]



def _tipo_horario(item) -> str:
    if item in HORARIOS_DUPLAS:
        return "Dupla"
    if isinstance(item, tuple) and len(item) >= 2 and (" - " in str(item[0]) or len(_numeros_aulas_de_texto(item[1])) > 1):
        return "Dupla"
    return "Simples"


def nome_arquivo_plano(turma: str, disciplina: str, ia_usada: bool = False) -> str:
    turma_limpa = (turma or "Turma").strip()
    disciplina_limpa = (disciplina or "Disciplina").strip()

    turma_limpa = turma_limpa.replace("º", "").replace("ª", "")
    turma_limpa = re.sub(r"\s+", "", turma_limpa)
    disciplina_limpa = re.sub(r"\s+", "", disciplina_limpa)

    nome = f"{turma_limpa}{disciplina_limpa}"
    if ia_usada:
        nome += "COMIA"
    nome = re.sub(r'[\\/:*?"<>|]', "", nome)
    nome = nome.strip(". ") or "PlanoDeAula"
    return f"{nome}.docx"


def _slug_download(texto: str) -> str:
    valor = re.sub(r'[\\/:*?"<>|]+', "_", (texto or "").strip())
    valor = re.sub(r"\s+", "_", valor)
    valor = valor.strip("._") or "arquivo"
    return valor


def _resumo_ia(aulas) -> str:
    if any(aula.get("ia_usada") for aula in aulas):
        provedores = sorted({str(aula.get("ia_provedor", "")).strip() for aula in aulas if aula.get("ia_usada")})
        provedor = provedores[0] if provedores else "IA"
        return f"Plano gerado COM IA ({provedor})."
    return "Plano gerado sem IA."


def _falhas_ia(aulas) -> list[str]:
    falhas = []
    for idx, aula in enumerate(aulas or [], start=1):
        if aula.get("ia_usada"):
            continue
        erro = str(aula.get("ia_erro") or "").strip()
        tema = str(aula.get("tema") or f"Aula {idx}").strip()
        if erro:
            falhas.append(f"Aula {idx} ({tema}): {erro}")
        else:
            falhas.append(f"Aula {idx} ({tema}): a IA não retornou desenvolvimento completo.")
    return falhas


def _extrair_primeiro_texto_metodologia(aula) -> str:
    metodologia = aula.get("metodologia") or []
    if not metodologia:
        return ""

    primeiro_bloco = metodologia[0]
    return primeiro_bloco.get("texto", "") if isinstance(primeiro_bloco, dict) else str(primeiro_bloco)


def _salvar_pdf_temporario(pdf_file) -> str:
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        pdf_file.seek(0)
    except Exception:
        pass
    temp_pdf.write(pdf_file.read())
    temp_pdf.close()
    return temp_pdf.name


def _chave_ordenacao_pdf(uploaded_file):
    nome = getattr(uploaded_file, "name", "") or ""
    partes = re.split(r"(\d+)", nome.lower())
    return [int(parte) if parte.isdigit() else parte for parte in partes]


def _proxima_data_pelo_dia(dia_nome: str, data_referencia: date) -> date:
    dias = {"segunda": 0, "terça": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sábado": 5, "domingo": 6}
    dia_alvo = dias.get(dia_nome.lower().strip(), 0)
    dias_para_frente = (dia_alvo - data_referencia.weekday() + 7) % 7
    if dias_para_frente == 0: dias_para_frente = 7
    return data_referencia + timedelta(days=dias_para_frente)

def _sugerir_horario_e_tipo(horario_str: str) -> tuple:
    horario_str = (horario_str or "").strip().lower()
    for h, label in HORARIOS_AULA:
        if h.lower() in horario_str:
            return h, label
    return HORARIOS_AULA[0]


def _normalizar_horario_cadastro(trecho: str) -> str:
    texto = (trecho or "").strip().lower()
    match = re.search(r"\b(\d{1,2})\s*(?:h|:)?\s*(\d{2})?\b", texto)
    if not match:
        return ""
    hora = int(match.group(1))
    minuto = match.group(2)
    if minuto:
        return f"{hora:02d}h{minuto}"
    return f"{hora:02d}h"


def _horarios_extraidos_texto(texto: str) -> list[str]:
    horarios = []
    for hora, minuto in re.findall(r"\b0?(\d{1,2})\s*(?:h|:)\s*(\d{2})?\b", str(texto or ""), flags=re.I):
        valor = f"{int(hora):02d}h{minuto or ''}"
        horarios.append(valor)
    return horarios


def _normalizar_label_aula(texto: str) -> str:
    texto = (texto or "").lower()
    texto = texto.replace("º", "ª").replace("°", "ª")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _normalizar_texto_simples(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto.upper()


def _horarios_padronizados_de_texto(texto: str, contexto: str = "") -> list[tuple[str, str]]:
    horarios = []
    vistos = set()
    partes = _partes_horario_config(texto)
    if not partes and texto:
        partes = [str(texto)]
    for parte in partes:
        sugestao = _sugerir_horario_cadastrado(parte, contexto)
        if sugestao and sugestao not in vistos:
            horarios.append(sugestao)
            vistos.add(sugestao)
    return horarios


def _prefixo_turno(contexto: str) -> str:
    texto = _normalizar_texto_simples(contexto)
    if "NOITE" in texto or "NOTURNO" in texto:
        return "19"
    if "TARDE" in texto:
        return "13"
    return "07"


def _partes_horario_config(texto: str) -> list[str]:
    texto = str(texto or "").strip()
    if not texto:
        return []
    partes = [parte.strip() for parte in re.split(r"[;\n]+", texto) if parte.strip()]
    if len(partes) == 1:
        partes = [parte.strip() for parte in re.split(r",\s*(?=\d{1,2}h)", texto, flags=re.I) if parte.strip()]
    return partes


def _partes_dia_config(texto: str) -> list[str]:
    original = str(texto or "").strip()
    if not original:
        return []

    normalizado = _normalizar_texto_simples(original).replace("-", " ")
    padrao = re.compile(
        r"\b(SEGUNDA(?: FEIRA)?|TERCA(?: FEIRA)?|QUARTA(?: FEIRA)?|QUINTA(?: FEIRA)?|"
        r"SEXTA(?: FEIRA)?|SABADO|DOMINGO)\b"
    )
    dias = []
    vistos = set()
    for encontrado in padrao.finditer(normalizado):
        dia_num = _dia_semana_numero(encontrado.group(1))
        if dia_num is not None and dia_num not in vistos:
            vistos.add(dia_num)
            dias.append(DIAS_SEMANA_CADASTRO[dia_num])
    if dias:
        return dias

    return [parte.strip() for parte in re.split(r"[;,\n]+|\s+-\s+", original) if parte.strip()]


def _numeros_aulas_de_texto(texto: str) -> list[int]:
    base = re.sub(r"\b\d{1,2}h\d*\b", " ", str(texto or "").lower())
    numeros = []
    for numero in range(1, 7):
        if re.search(rf"\b{numero}\s*(?:ª|º|a|o)?\b", base):
            numeros.append(numero)
    return numeros


def _turno_por_horario_inicio(horario: str, contexto: str = "") -> str:
    horario_norm = _normalizar_horario_cadastro(horario)
    if horario_norm.startswith(("13", "14", "15", "16", "17")):
        return "Tarde"
    if horario_norm.startswith(("19", "20", "21", "22")):
        return "Noite"
    prefixo = _prefixo_turno(contexto)
    if prefixo == "13":
        return "Tarde"
    if prefixo == "19":
        return "Noite"
    return "Manhã"


def _formatar_label_aulas(numeros: list[int]) -> str:
    partes = [f"{numero}ª" for numero in sorted(set(numeros))]
    if not partes:
        return ""
    if len(partes) == 1:
        return f"{partes[0]} aula"
    if len(partes) == 2:
        return f"{partes[0]} e {partes[1]} aula"
    return f"{', '.join(partes[:-1])} e {partes[-1]} aula"


def _montar_horario_flexivel(turno: str, aulas: list[int | str]):
    slots = TURNOS_HORARIOS.get(turno) or TURNOS_HORARIOS["Manhã"]
    max_aulas = len(slots) - 1
    numeros = []
    for aula in aulas or []:
        match = re.search(r"\d+", str(aula))
        if match:
            numero = int(match.group(0))
            if 1 <= numero <= max_aulas:
                numeros.append(numero)
    numeros = sorted(set(numeros))
    if not numeros:
        return None

    primeira = numeros[0]
    ultima = numeros[-1]
    consecutivas = numeros == list(range(primeira, ultima + 1))
    inicio = slots[primeira - 1]
    fim = slots[ultima if consecutivas else ultima - 1]
    label = _formatar_label_aulas(numeros)
    return (inicio, label) if len(numeros) == 1 else (f"{inicio} - {fim}", label)


def _turno_e_aulas_de_horario(horario, contexto: str = "") -> tuple[str, list[str]]:
    if not horario:
        return ("Manhã", [])
    texto = _rotulo_horario(horario)
    horarios_texto = _horarios_extraidos_texto(texto)
    turno = _turno_por_horario_inicio(horarios_texto[0], contexto) if horarios_texto else _turno_por_horario_inicio("", contexto)
    numeros = _numeros_aulas_de_texto(texto)
    return turno, [f"{numero}ª" for numero in numeros]


def _horario_flexivel_por_texto(trecho: str, contexto: str = ""):
    numeros = _numeros_aulas_de_texto(trecho)
    if not numeros:
        return None
    horarios_texto = _horarios_extraidos_texto(trecho)
    turno = _turno_por_horario_inicio(horarios_texto[0], contexto) if horarios_texto else _turno_por_horario_inicio("", contexto)
    return _montar_horario_flexivel(turno, numeros)


def _indice_horario(horario) -> int:
    if horario in HORARIOS_AULA:
        return HORARIOS_AULA.index(horario)
    horarios_texto = _horarios_extraidos_texto(_rotulo_horario(horario))
    if not horarios_texto:
        return len(HORARIOS_AULA) + 99
    inicio = horarios_texto[0].lower()
    todos = [hora for slots in TURNOS_HORARIOS.values() for hora in slots[:-1]]
    for idx, hora in enumerate(todos):
        if hora.lower() == inicio:
            return idx
    return len(HORARIOS_AULA) + 50


def _defaults_grade_horarios(dia_texto: str = "", horario_texto: str = "", contexto: str = "") -> dict[str, dict[str, object]]:
    defaults: dict[str, dict[str, object]] = {}
    dias = _partes_dia_config(dia_texto)
    horarios = _horarios_padronizados_de_texto(horario_texto, contexto)
    for idx, dia in enumerate(dias):
        dia_num = _dia_semana_numero(dia)
        if dia_num is None or dia_num >= len(DIAS_SEMANA_CADASTRO):
            continue
        horario = horarios[idx] if idx < len(horarios) else (horarios[0] if horarios else None)
        turno, aulas = _turno_e_aulas_de_horario(horario, contexto)
        defaults[DIAS_SEMANA_CADASTRO[dia_num]] = {"turno": turno, "aulas": aulas}
    return defaults


def _renderizar_grade_horarios(prefixo: str, dia_texto: str = "", horario_texto: str = "", contexto: str = "") -> tuple[str, str, int]:
    st.markdown("**Grade semanal de horários**")
    st.caption("Selecione o turno e as aulas de cada dia. Deixe vazio o dia em que não há aula.")
    defaults = _defaults_grade_horarios(dia_texto, horario_texto, contexto)
    selecionados = []
    turnos = list(TURNOS_HORARIOS.keys())

    for indice, dia in enumerate(DIAS_SEMANA_CADASTRO):
        default_dia = defaults.get(dia, {})
        turno_default = str(default_dia.get("turno") or "Manhã")
        aulas_opcoes_default = [f"{numero}ª" for numero in range(1, len(TURNOS_HORARIOS.get(turno_default, TURNOS_HORARIOS["Manhã"])))]
        aulas_default = [aula for aula in default_dia.get("aulas", []) if aula in aulas_opcoes_default]

        col_dia, col_turno, col_aulas, col_previa = st.columns([1.1, 1.1, 2.2, 2.1])
        with col_dia:
            st.markdown(f"**{dia}**")
        with col_turno:
            turno = st.selectbox(
                "Turno",
                turnos,
                index=turnos.index(turno_default) if turno_default in turnos else 0,
                key=f"{prefixo}_turno_{indice}",
                label_visibility="collapsed",
            )
        aulas_opcoes = [f"{numero}ª" for numero in range(1, len(TURNOS_HORARIOS[turno]))]
        aulas_default = [aula for aula in aulas_default if aula in aulas_opcoes]
        with col_aulas:
            aulas = st.multiselect(
                "Aulas",
                aulas_opcoes,
                default=aulas_default,
                key=f"{prefixo}_aulas_{indice}",
                label_visibility="collapsed",
            )
        horario = _montar_horario_flexivel(turno, aulas)
        with col_previa:
            st.caption(_rotulo_horario(horario) if horario else "Sem aula neste dia")
        if horario:
            selecionados.append({"dia": dia, "horario": horario, "aulas": aulas})

    dia_serializado = " - ".join(item["dia"] for item in selecionados)
    horario_serializado = _serializar_horarios_padronizados([item["horario"] for item in selecionados])
    total_aulas = sum(len(item["aulas"]) for item in selecionados)
    if total_aulas:
        st.caption(f"Total selecionado na semana: {total_aulas} aula(s).")
    return dia_serializado, horario_serializado, total_aulas


def _mes_numero_app(mes: str) -> int:
    meses = {
        "JANEIRO": 1,
        "FEVEREIRO": 2,
        "MARCO": 3,
        "MARCO": 3,
        "ABRIL": 4,
        "MAIO": 5,
        "JUNHO": 6,
        "JULHO": 7,
        "AGOSTO": 8,
        "SETEMBRO": 9,
        "OUTUBRO": 10,
        "NOVEMBRO": 11,
        "DEZEMBRO": 12,
    }
    return meses.get(_normalizar_texto_simples(mes), date.today().month)


def _dia_semana_numero(texto: str):
    dias = {
        "SEGUNDA": 0,
        "SEGUNDA FEIRA": 0,
        "TERCA": 1,
        "TERCA FEIRA": 1,
        "QUARTA": 2,
        "QUARTA FEIRA": 2,
        "QUINTA": 3,
        "QUINTA FEIRA": 3,
        "SEXTA": 4,
        "SEXTA FEIRA": 4,
        "SABADO": 5,
        "DOMINGO": 6,
    }
    return dias.get(_normalizar_texto_simples(texto).replace("-", " "))


def _datas_do_mes_por_dia(mes: str, dia_semana: int, ano: int | None = None) -> list[date]:
    ano = ano or date.today().year
    mes_num = _mes_numero_app(mes)
    atual = date(ano, mes_num, 1)
    datas = []
    while atual.month == mes_num:
        if atual.weekday() == dia_semana:
            datas.append(atual)
        atual += timedelta(days=1)
    return datas


def _padroes_horario_config(config: dict, turma: str = "") -> list[dict]:
    padroes = []
    vistos = set()
    datas_horarios = list((config or {}).get("datas_horarios") or [])
    dias_semana = [
        _dia_semana_numero(parte.strip())
        for parte in _partes_dia_config(str((config or {}).get("dia_semana") or ""))
        if parte.strip()
    ]
    dias_semana = [dia for dia in dias_semana if dia is not None]
    horarios_cadastro = _horarios_padronizados_de_texto(str((config or {}).get("horario") or ""), turma)

    if horarios_cadastro and dias_semana:
        for idx, dia in enumerate(dias_semana):
            sugestao = horarios_cadastro[idx] if idx < len(horarios_cadastro) else horarios_cadastro[0]
            chave = (dia, sugestao)
            if chave in vistos:
                continue
            vistos.add(chave)
            padroes.append({"dia": dia, "horario": sugestao})
        return sorted(padroes, key=lambda item: (item["dia"], _indice_horario(item["horario"])))

    if horarios_cadastro and datas_horarios:
        dias_datas = []
        for item in datas_horarios:
            data_aula = item.get("data")
            if hasattr(data_aula, "weekday") and data_aula.weekday() not in dias_datas:
                dias_datas.append(data_aula.weekday())
        for idx, dia in enumerate(dias_datas):
            sugestao = horarios_cadastro[idx] if idx < len(horarios_cadastro) else horarios_cadastro[0]
            chave = (dia, sugestao)
            if chave in vistos:
                continue
            vistos.add(chave)
            padroes.append({"dia": dia, "horario": sugestao})
        if padroes:
            return sorted(padroes, key=lambda item: (item["dia"], _indice_horario(item["horario"])))

    for item in datas_horarios:
        data_aula = item.get("data")
        if not hasattr(data_aula, "weekday"):
            continue
        trecho_horario = " ".join(str(item.get(chave) or "").strip() for chave in ("horario", "aula")).strip()
        sugestao = _sugerir_horario_cadastrado(trecho_horario, turma) or HORARIOS_AULA[0]
        chave = (data_aula.weekday(), sugestao)
        if chave in vistos:
            continue
        vistos.add(chave)
        padroes.append({"dia": data_aula.weekday(), "horario": sugestao})

    if padroes:
        return sorted(padroes, key=lambda item: (item["dia"], _indice_horario(item["horario"])))

    partes_horario = _partes_horario_config(str((config or {}).get("horario") or ""))
    sugestoes_h = [_sugerir_horario_cadastrado(parte, turma) or HORARIOS_AULA[0] for parte in partes_horario]
    if dias_semana and not sugestoes_h:
        sugestoes_h = [HORARIOS_AULA[0]]

    for idx, dia in enumerate(dias_semana):
        sugestao = sugestoes_h[idx] if idx < len(sugestoes_h) else sugestoes_h[0]
        padroes.append({"dia": dia, "horario": sugestao})
    return padroes


def _datas_horarios_do_mes(config: dict, mes: str, turma: str = "") -> list[dict]:
    if not config or not mes:
        return []
    itens = []
    for padrao in _padroes_horario_config(config, turma):
        for data_aula in _datas_do_mes_por_dia(mes, padrao["dia"]):
            itens.append({"data": data_aula, "horario": padrao["horario"]})
    return sorted(itens, key=lambda item: (item["data"], _indice_horario(item["horario"])))


def _sincronizar_datas_horarios_mes(config: dict, mes: str, professor: str, disciplina: str, turma: str) -> list[dict]:
    itens = _datas_horarios_do_mes(config, mes, turma)
    if not itens:
        return []

    agenda = "|".join(
        f"{item['data'].isoformat()}:{item['horario'][0]}:{item['horario'][1]}"
        for item in itens
    )
    cadastro = f"{config.get('dia_semana', '')}|{config.get('horario', '')}|{config.get('aulas_semana', '')}"
    assinatura = f"{professor}|{disciplina}|{turma}|{mes}|{cadastro}|{agenda}"
    if st.session_state.get("agenda_mes_assinatura") == assinatura:
        return itens

    st.session_state["agenda_mes_assinatura"] = assinatura
    for idx, item in enumerate(itens):
        horario = item["horario"]
        st.session_state[f"data_aula_{idx}"] = item["data"]
        st.session_state[f"horario_aula_{idx}"] = horario
        st.session_state[f"tipo_horario_aula_{idx}"] = _tipo_horario(horario)

    for idx in range(len(itens), 40):
        for prefixo in ("data_aula_", "horario_aula_", "tipo_horario_aula_"):
            st.session_state.pop(f"{prefixo}{idx}", None)
    return itens


def _sugerir_horario_cadastrado(trecho: str, contexto: str = ""):
    trecho_norm = _normalizar_label_aula(trecho)
    horarios_no_texto = _horarios_extraidos_texto(trecho)
    horario_flexivel = _horario_flexivel_por_texto(trecho, contexto)
    if horario_flexivel:
        return horario_flexivel

    if len(horarios_no_texto) >= 2:
        inicio, fim = horarios_no_texto[:2]
        for horario in HORARIOS_DUPLAS:
            if _horarios_extraidos_texto(horario[0])[:2] == [inicio, fim]:
                return horario

    for horario in HORARIOS_DUPLAS + HORARIOS_SIMPLES:
        label_norm = _normalizar_label_aula(horario[1])
        horario_norm = _normalizar_label_aula(HORARIOS_LABELS.get(horario, ""))
        if label_norm and label_norm in trecho_norm:
            return horario
        if horario_norm and horario_norm in trecho_norm:
            return horario

    horario_norm = _normalizar_horario_cadastro(trecho)
    if horario_norm:
        horario_sem_zero = horario_norm[1:] if horario_norm.startswith("0") else horario_norm
        for horario in HORARIOS_SIMPLES + HORARIOS_DUPLAS:
            base = horario[0].lower()
            if base == horario_norm or base == horario_sem_zero:
                return horario
            if base.startswith(f"{horario_sem_zero} ") or base.startswith(f"{horario_norm} "):
                return horario

    if not trecho_norm:
        return None
    candidatos = [h for h in HORARIOS_DUPLAS + HORARIOS_SIMPLES if _normalizar_label_aula(h[1]) in trecho_norm]
    if candidatos:
        prefixo = _prefixo_turno(contexto)
        for candidato in candidatos:
            if candidato[0].startswith(prefixo):
                return candidato
        return candidatos[0]
    return None

def _inicio_semana(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())

def _tamanho_bloco_primeira_semana(datas: list[date]) -> int:
    if not datas:
        return 0
    inicio = _inicio_semana(datas[0])
    tamanho = 0
    for dt in datas:
        if _inicio_semana(dt) == inicio:
            tamanho += 1
        else:
            break
    return max(1, tamanho)


def validar_entrada(
    modelo_bytes,
    disciplina: str,
    disciplina_config,
    aulas_envio,
    professor: str,
    turma: str,
    bimestre: str,
    mes: str,
    aulas_previstas_manual: str,
    pdfs_enviados: int = 0,
    pdfs_necessarios: int = 0,
) -> str:
    if not modelo_bytes:
        return "Selecione ou envie o modelo DOCX."
    if not disciplina.strip():
        return "Selecione ou informe a disciplina."
    campos_obrigatorios = []
    if not (professor or "").strip():
        campos_obrigatorios.append("Nome do professor")
    if not (turma or "").strip():
        campos_obrigatorios.append("Turma")
    if not (bimestre or "").strip():
        campos_obrigatorios.append("Bimestre")
    if not (mes or "").strip():
        campos_obrigatorios.append("Mês")
    if not (aulas_previstas_manual or "").strip():
        campos_obrigatorios.append("Aulas na semana")
    if campos_obrigatorios:
        return (
            "Preencha os campos obrigatórios antes de gerar o plano: "
            + ", ".join(campos_obrigatorios)
            + "."
        )
    if disciplina_config.exige_pdf and not aulas_envio:
        return "Envie os PDFs das aulas para gerar o plano."
    if disciplina_config.exige_pdf and pdfs_necessarios and pdfs_enviados != pdfs_necessarios:
        return (
            f"Quantidade de PDFs incorreta: foram adicionados {pdfs_enviados}, "
            f"mas o plano selecionado possui {pdfs_necessarios} linha(s) de aula. "
            "Adicione um PDF para cada linha de aula antes de gerar."
        )
    if disciplina_config.exige_pdf and any(not aula["pdf"] for aula in aulas_envio):
        return "Preencha data, horário e PDF em todas as aulas cadastradas."
    return ""


def validar_aulas_secundarias(gerar_turma_espelho: bool, turma_espelho: str, aulas_envio_espelho, exige_pdf: bool) -> str:
    if not gerar_turma_espelho:
        return ""
    if not (turma_espelho or "").strip():
        return "Preencha a 2ª série/turma antes de gerar os planos em conjunto."
    if exige_pdf and any(not aula["pdf"] for aula in aulas_envio_espelho):
        return "Preencha data, horário e PDF em todas as aulas da 2ª turma."
    return ""


def _coletar_aulas_envio(
    num_rows: int,
    pdfs_aulas_files,
    dividir_metodologia: bool,
    auto_repetir_semana: bool,
    key_prefix: str = "",
    titulo_secao: str = "",
):
    aulas_envio = []
    datas_cache = []
    horarios_cache = []

    for idx in range(num_rows):
        chave_data = f"{key_prefix}data_aula_{idx}"
        chave_horario = f"{key_prefix}horario_aula_{idx}"
        data_fallback = st.session_state.get(f"data_aula_{idx}", date.today()) if key_prefix else date.today()
        horario_fallback = st.session_state.get(f"horario_aula_{idx}", HORARIOS_AULA[0]) if key_prefix else HORARIOS_AULA[0]
        if chave_data not in st.session_state:
            st.session_state[chave_data] = data_fallback
        if chave_horario not in st.session_state:
            st.session_state[chave_horario] = horario_fallback
        datas_cache.append(st.session_state[chave_data])
        horarios_cache.append(st.session_state[chave_horario])

    bloco_semana = _tamanho_bloco_primeira_semana(datas_cache)
    if auto_repetir_semana and bloco_semana > 0 and num_rows > bloco_semana:
        for idx in range(bloco_semana, num_rows):
            pos_bloco = idx % bloco_semana
            semana_offset = idx // bloco_semana
            data_base = datas_cache[pos_bloco]
            horario_base = horarios_cache[pos_bloco]
            st.session_state[f"{key_prefix}data_aula_{idx}"] = data_base + timedelta(days=7 * semana_offset)
            st.session_state[f"{key_prefix}horario_aula_{idx}"] = horario_base
            st.session_state[f"{key_prefix}tipo_horario_aula_{idx}"] = _tipo_horario(horario_base)

    if titulo_secao:
        st.markdown(f"**{titulo_secao}**")

    for idx in range(num_rows):
        st.markdown(f"**Aula {idx + 1}**")
        col_data, col_horario = st.columns([1, 1])
        chave_data = f"{key_prefix}data_aula_{idx}"
        chave_horario = f"{key_prefix}horario_aula_{idx}"
        chave_tipo = f"{key_prefix}tipo_horario_aula_{idx}"
        data_fallback = st.session_state.get(f"data_aula_{idx}", date.today()) if key_prefix else date.today()
        horario_fallback = st.session_state.get(f"horario_aula_{idx}", HORARIOS_AULA[0]) if key_prefix else HORARIOS_AULA[0]
        if chave_data not in st.session_state:
            st.session_state[chave_data] = data_fallback
        if chave_horario not in st.session_state:
            st.session_state[chave_horario] = horario_fallback
        horario_padrao_item = st.session_state.get(chave_horario, horario_fallback)
        bloqueado = auto_repetir_semana and idx >= bloco_semana

        with col_data:
            data_aula = st.date_input(
                "Data",
                format="DD/MM/YYYY",
                key=chave_data,
                disabled=bloqueado,
            )
        with col_horario:
            tipo_padrao = _tipo_horario(horario_padrao_item)
            if chave_tipo not in st.session_state or st.session_state[chave_tipo] not in ["Simples", "Dupla"]:
                st.session_state[chave_tipo] = tipo_padrao
            tipo_horario = st.radio(
                "Tipo de horário",
                ["Simples", "Dupla"],
                horizontal=True,
                key=chave_tipo,
                disabled=bloqueado,
            )
            opcoes_horario = list(HORARIOS_SIMPLES if tipo_horario == "Simples" else HORARIOS_DUPLAS)
            horario_atual = st.session_state.get(chave_horario)
            if horario_atual not in opcoes_horario and isinstance(horario_atual, tuple):
                opcoes_horario.insert(0, horario_atual)
            if st.session_state.get(chave_horario) not in opcoes_horario:
                st.session_state[chave_horario] = opcoes_horario[0]
            horario_aula = st.selectbox(
                "Horário",
                opcoes_horario,
                format_func=_rotulo_horario,
                key=chave_horario,
                disabled=bloqueado,
            )

        pdf_idx = idx // 2 if dividir_metodologia else idx
        aulas_envio.append(
            {
                "data": data_aula,
                "horario": horario_aula,
                "pdf": pdfs_aulas_files[pdf_idx] if pdf_idx < len(pdfs_aulas_files) else None,
            }
        )

    return aulas_envio


def _texto_metodologia_app(aula: dict) -> str:
    metodologia = aula.get("metodologia") or []
    blocos = []
    for item in metodologia:
        if isinstance(item, dict):
            titulo = item.get("titulo", "").strip()
            texto = item.get("texto", "").strip()
            if titulo:
                blocos.append(f"{titulo}: {texto}")
            else:
                blocos.append(texto)
        else:
            blocos.append(str(item))
    return "\n\n".join(blocos)


_TITULOS_METODOLOGIA_APP = {
    "para comecar": "Para comecar",
    "para começar": "Para comecar",
    "contextualizacao": "Contextualizacao",
    "contextualização": "Contextualizacao",
    "leitura analitica": "Leitura analitica",
    "leitura analítica": "Leitura analitica",
    "leitura e construcao do conteudo": "Leitura e construcao do conteudo",
    "leitura e construção do conteúdo": "Leitura e construcao do conteudo",
    "exploracao": "Exploracao",
    "exploração": "Exploracao",
    "foco no conteudo": "Foco no conteudo",
    "foco no conteúdo": "Foco no conteudo",
    "formalizacao": "Formalizacao",
    "formalização": "Formalizacao",
    "pause e responda": "Pause e responda",
    "na pratica": "Na pratica",
    "na prática": "Na pratica",
    "analise de caso": "Analise de caso",
    "análise de caso": "Analise de caso",
    "calculos financeiros": "Calculos financeiros",
    "cálculos financeiros": "Calculos financeiros",
    "planejamento orcamentario": "Planejamento orcamentario",
    "planejamento orçamentário": "Planejamento orcamentario",
    "projeto empreendedor": "Projeto empreendedor",
    "revisao e reescrita": "Revisao e reescrita",
    "revisão e reescrita": "Revisao e reescrita",
    "relembre": "Relembre",
    "sistematizacao": "Sistematizacao",
    "sistematização": "Sistematizacao",
    "encerramento": "Encerramento",
}


def _normalizar_titulo_metodologia_app(texto: str) -> str:
    texto = (texto or "").strip().lower()
    mapa = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    texto = texto.translate(mapa)
    return re.sub(r"\s+", " ", texto).strip()


def _metodologia_app_para_blocos(texto: str):
    """Reconstrói blocos estruturados após edição manual no textarea."""
    linhas = [linha.rstrip() for linha in str(texto or "").splitlines()]
    blocos = []
    atual = None

    for linha in linhas:
        limpa = linha.strip()
        if not limpa:
            continue

        match = re.match(r"^([^:]{2,80}):\s*(.*)$", limpa)
        titulo_chave = _normalizar_titulo_metodologia_app(match.group(1)) if match else ""
        if match and titulo_chave in _TITULOS_METODOLOGIA_APP:
            if atual:
                atual["texto"] = " ".join(atual["texto"]).strip()
                blocos.append(atual)
            atual = {
                "titulo": _TITULOS_METODOLOGIA_APP[titulo_chave],
                "texto": [match.group(2).strip()] if match.group(2).strip() else [],
            }
            continue

        if atual:
            atual["texto"].append(limpa)
        else:
            blocos.append(limpa)

    if atual:
        atual["texto"] = " ".join(atual["texto"]).strip()
        blocos.append(atual)

    return blocos or [str(texto or "").strip()]


def _extrair_aulas_dos_pdfs(
    aulas_envio,
    disciplina: str,
    turma_atual: str,
    bimestre: str,
    modo_ia: str,
    modelo_openai: str,
    modelo_gemini: str,
    dividir_metodologia: bool,
):
    temp_paths = []
    try:
        dados_aulas = []
        for aula_envio in aulas_envio:
            temp_paths.append(_salvar_pdf_temporario(aula_envio["pdf"]))
            dados_aulas.append(
                {
                    "data": aula_envio["data"].strftime("%d/%m"),
                    "horario": horario_para_plano(aula_envio["horario"]),
                }
            )

        aulas = processar_varios_pdfs(
            temp_paths,
            disciplina=disciplina,
            turma=turma_atual,
            bimestre=bimestre,
            usar_ia=modo_ia != "Sem IA",
            provedor_ia=modo_ia.lower(),
            modelo_ia=(modelo_openai if modo_ia == "OpenAI" else modelo_gemini) if modo_ia != "Sem IA" else "",
            dividir_metodologia=dividir_metodologia,
        )
        if not aulas:
            raise RuntimeError(
                "Nenhuma aula foi extraída dos PDFs enviados. Verifique se os arquivos são slides de aula, e não guias, escopos-sequência ou referências."
            )
        if modo_ia != "Sem IA":
            falhas_ia = _falhas_ia(aulas)
            if falhas_ia:
                raise RuntimeError(
                    "Falha de IA detectada:\n" + "\n".join(falhas_ia)
                )
        for aula, dados in zip(aulas, dados_aulas):
            aula.update(dados)

        cdp_contextual = eh_cdp_contextual(disciplina)
        problemas_plano = validar_aulas_geradas(
            aulas,
            permitir_temas_repetidos=cdp_contextual,
            permitir_metodologia_simples=cdp_contextual,
        )
        if problemas_plano:
            raise ValueError("Problemas encontrados no plano:\n" + "\n".join(problemas_plano))

        # Limpar os minutos de todas as metodologias extraídas
        for aula in aulas:
            metodologia = aula.get("metodologia", [])
            for i, item in enumerate(metodologia):
                if isinstance(item, dict):
                    if "texto" in item:
                        texto_limpo = re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item["texto"])
                        texto_limpo = re.sub(r'\(\s*\)', '', texto_limpo)
                        item["texto"] = re.sub(r'\s+', ' ', texto_limpo).strip()
                elif isinstance(item, str):
                    texto_limpo = re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item)
                    texto_limpo = re.sub(r'\(\s*\)', '', texto_limpo)
                    metodologia[i] = re.sub(r'\s+', ' ', texto_limpo).strip()

        return aulas
    finally:
        for caminho_temp in temp_paths:
            if caminho_temp:
                try:
                    os.unlink(caminho_temp)
                except OSError:
                    pass

def _gerar_docx_final(
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
    ia_usada_plano = any(aula.get("ia_usada") for aula in aulas)
    return {
        "turma": turma_atual,
        "aulas": aulas,
        "docx_bytes": docx_bytes,
        "relatorio": relatorio,
        "ia_usada": ia_usada_plano,
    }


def _gerar_docx_cdp_final(
    modelo_bytes: bytes,
    escola: str,
    professor: str,
    disciplina: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    semana: str,
    observacao: str,
    aulas_previstas_manual: str,
    cdp_aula_inicial: int,
    turma_cdp: str = "",
):
    docx_bytes = preencher_documento_cdp(
        BytesIO(modelo_bytes),
        escola=escola,
        professor=professor,
        turma=turma_atual,
        mes=mes,
        bimestre=bimestre,
        aula_inicial=int(cdp_aula_inicial or 1),
        fundamental=eh_cdp_fundamental(disciplina),
        multisseriada=eh_cdp_multisseriada(disciplina),
        serie_cdp=turma_cdp if eh_cdp_multisseriada(disciplina) else "",
        semana=semana,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )
    tipo = "CDP - Ciclo I" if eh_cdp_fundamental(disciplina) else "CDP/EJA Multisseriada"
    relatorio = (
        f"Plano gerado em modo {tipo}.\n"
        f"Professor: {professor}\n"
        f"Disciplina: {disciplina}\n"
        f"Turma: {turma_atual}\n"
        f"Bimestre: {bimestre}\n"
        f"Mês: {mes}\n"
        f"Aula inicial CDP: {int(cdp_aula_inicial or 1)}\n"
    )
    if turma_cdp:
        relatorio += f"Turma multisseriada usada para filtro: {turma_cdp}\n"
    return {
        "turma": turma_atual,
        "aulas": [],
        "docx_bytes": docx_bytes,
        "relatorio": relatorio,
        "ia_usada": False,
    }


def _montar_zip_planos(planos: list[dict], disciplina: str) -> bytes:
    saida = BytesIO()
    with zipfile.ZipFile(saida, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for plano in planos:
            nome_docx = nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano["ia_usada"])
            zf.writestr(nome_docx, plano["docx_bytes"].getvalue())
            zf.writestr(nome_docx.replace(".docx", "_relatorio.txt"), plano["relatorio"].encode("utf-8"))
    saida.seek(0)
    return saida.read()


st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        :root {
            --app-bg: #E5F4FB;
            --app-bg-soft: #D6ECF7;
            --panel-bg: #F4FAFD;
            --panel-bg-strong: #E8F4FA;
            --panel-border: #B8D6E6;
            --field-bg: #F8FCFE;
            --ink: #163044;
            --muted: #557386;
            --brand: #1F6F9F;
            --brand-dark: #164D73;
            --accent: #2E8BC0;
            --focus: #75B7DC;
            --card-shadow: 0 12px 28px rgba(39, 100, 140, 0.14), 0 2px 8px rgba(39, 100, 140, 0.10);
            --font-main: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(117, 183, 220, 0.24), transparent 30%),
                linear-gradient(180deg, #EAF7FC 0%, #DDF0F9 48%, #D2EAF6 100%);
            color: var(--ink);
            font-family: var(--font-main);
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: transparent !important;
        }

        [data-testid="stHeader"] {
            background: rgba(234, 247, 252, 0.86) !important;
            backdrop-filter: blur(10px);
        }

        .block-container {
            padding-top: 2rem;
            max-width: 1150px;
        }

        /* Hero Section */
        .app-hero {
            background: linear-gradient(135deg, #F8FCFE 0%, #E7F5FB 52%, #C9E8F7 100%);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 28px 36px;
            margin-bottom: 24px;
            color: var(--ink);
            box-shadow: var(--card-shadow);
        }

        .app-hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 260px;
            gap: 28px;
            align-items: center;
        }

        .hero-visual {
            display: flex;
            justify-content: flex-end;
        }

        .hero-visual img {
            max-width: 260px;
            width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 10px 22px rgba(39, 100, 140, 0.12);
        }

        .app-title {
            font-size: 2.4rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0;
        }

        .app-subtitle {
            font-size: 1.05rem;
            color: var(--muted);
            margin-top: 8px;
            max-width: 700px;
        }

        .hero-badges {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .hero-badge {
            background: #E8F4FA;
            border: 1px solid var(--panel-border);
            color: var(--brand-dark);
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        [data-testid="stFileUploader"],
        [data-testid="stTextInput"],
        [data-testid="stSelectbox"],
        [data-testid="stNumberInput"],
        [data-testid="stTextArea"] {
            background-color: rgba(248, 252, 254, 0.92) !important;
            border: 1px solid var(--panel-border) !important;
            border-radius: 8px !important;
            padding: 6px !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
        }

        [data-baseweb="input"],
        [data-baseweb="input"] > div,
        [data-baseweb="base-input"],
        [data-baseweb="base-input"] > div,
        [data-baseweb="input"] input,
        [data-baseweb="base-input"] input,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] textarea {
            background-color: var(--field-bg) !important;
            border-color: var(--panel-border) !important;
            color: var(--ink) !important;
        }

        input,
        textarea,
        [data-baseweb="select"] span,
        [data-baseweb="select"] div {
            color: var(--ink) !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #6A8595 !important;
            opacity: 1 !important;
        }

        [data-baseweb="input"]:focus-within,
        [data-baseweb="base-input"]:focus-within,
        [data-baseweb="select"]:focus-within,
        [data-baseweb="textarea"]:focus-within {
            border-color: var(--focus) !important;
            box-shadow: 0 0 0 2px rgba(136, 165, 182, 0.28) !important;
        }

        /* Ocultar texto de dica "Press Enter" em formulários que fica sobreposto */
        [data-testid="InputInstructions"] {
            display: none !important;
        }

        [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"] p {
            color: var(--ink) !important;
            font-weight: 600 !important;
        }

        [data-testid="stWidgetLabel"] p {
            font-size: 0.9rem !important;
        }

        [data-testid="stFileUploader"] [data-testid="stWidgetLabel"] p,
        [data-testid="stTextInput"] [data-testid="stWidgetLabel"] p,
        [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
        [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p,
        [data-testid="stTextArea"] [data-testid="stWidgetLabel"] p {
            color: var(--ink) !important;
            text-shadow: none !important;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--muted) !important;
        }

        /* Botões */
        .stButton>button {
            background-color: var(--brand) !important;
            color: white !important;
            border: 1px solid rgba(22, 77, 115, 0.72) !important;
            border-radius: 6px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            width: 100%;
            transition: all 0.2s ease !important;
            box-shadow: 0 7px 18px rgba(31, 111, 159, 0.20);
        }

        .stButton>button:hover {
            background-color: var(--brand-dark) !important;
            border-color: #123E5F !important;
            box-shadow: 0 10px 22px rgba(31, 111, 159, 0.28) !important;
            transform: translateY(-1px);
        }

        /* Botão Secundário */
        .stButton>button[kind="secondary"] {
            background-color: #F4FAFD !important;
            border: 1px solid var(--panel-border) !important;
            color: var(--brand-dark) !important;
            font-size: 0.8rem !important;
            box-shadow: none;
        }

        .stButton>button[kind="secondary"]:hover {
            background-color: #DCEFF8 !important;
            color: var(--brand-dark) !important;
        }

        /* Cards de Seção */
        .section-card {
            background: rgba(46, 139, 192, 0.20);
            border: 0;
            border-radius: 999px;
            height: 1px;
            padding: 0;
            margin: 26px 0 14px 0;
            box-shadow: none;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--ink);
            display: flex;
            align-items: center;
            gap: 10px;
            text-shadow: none;
        }

        .section-title::before {
            content: "";
            width: 4px;
            height: 18px;
            background: var(--accent);
            border-radius: 2px;
        }

        /* Radio e Checkbox */
        div[role="radiogroup"] {
            background: #F4FAFD;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--panel-border);
        }

        div[role="radiogroup"] p,
        div[role="radiogroup"] span,
        div[role="radiogroup"] label {
            color: var(--ink) !important;
            text-shadow: none !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #D8EEF8;
            border-right: 1px solid var(--panel-border);
            color: var(--ink);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: var(--ink) !important;
        }

        [data-testid="stSidebar"] [data-testid="stTextInput"],
        [data-testid="stSidebar"] [data-testid="stSelectbox"],
        [data-testid="stSidebar"] [data-testid="stNumberInput"] {
            background-color: rgba(248, 252, 254, 0.92) !important;
            border-color: var(--panel-border) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 8px !important;
            border: 1px solid rgba(106, 133, 149, 0.34) !important;
        }

        hr {
            border-color: rgba(161, 175, 186, 0.55) !important;
        }

        /* Responsividade */
        @media (max-width: 760px) {
            .app-hero { padding: 20px; }
            .app-hero-grid { grid-template-columns: 1fr; }
            .app-title { font-size: 1.8rem; }
            .hero-visual { display: none; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

hero_img = _asset_data_uri("hero-planejamento.svg")

st.markdown(
    f"""
    <div class="app-hero">
        <div class="app-hero-grid">
            <div class="app-hero-content">
                <div class="app-title">Plano de Aula Inteligente</div>
                <div class="app-subtitle">
                    Gere planejamentos oficiais a partir dos PDFs das aulas, com cadastro de professores,
                    preenchimento automático e documentos padronizados.
                </div>
                <div class="hero-badges">
                    <div class="hero-badge">Automação</div>
                    <div class="hero-badge">DOCX</div>
                    <div class="hero-badge">Cadastro</div>
                </div>
            </div>
            <div class="hero-visual">
                <img src="{hero_img}" alt="Hero Image">
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_limpar, _ = st.columns([1, 5])
with col_limpar:
    st.button("Limpar dados da tela", type="secondary", on_click=limpar_dados_tela)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Área de trabalho</div>', unsafe_allow_html=True)
modo_tela = st.radio(
    "Área do PLANOS_LUAN",
    ["Planos gerais", "CDP - Ciclo I", "Cadastro", "Diagnóstico"],
    horizontal=True,
    key="modo_tela",
    label_visibility="collapsed",
)
modo_cdp_dedicado = modo_tela == "CDP - Ciclo I"
modo_cadastro_professor = modo_tela == "Cadastro"
modo_diagnostico_modelos = modo_tela == "Diagnóstico"
if modo_cadastro_professor:
    st.caption("Área para cadastrar ou ajustar professores, disciplinas, turmas e horários.")
elif modo_diagnostico_modelos:
    st.caption("Área para conferir modelos, duplicidades, data/horário e apoio de backup.")
elif modo_cdp_dedicado:
    st.caption("Área exclusiva para CDP - Ciclo I. Usa o modelo CDP, sem IA, sem tecnologia e sem envio de PDFs.")
else:
    st.caption("Área para planos comuns gerados a partir dos PDFs das aulas.")
st.markdown('</div>', unsafe_allow_html=True)

if modo_cadastro_professor:
    _renderizar_cadastro_professor()
    st.stop()

if modo_diagnostico_modelos:
    _renderizar_diagnostico_modelos()
    st.stop()

TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)
templates_disponiveis = [f.name for f in TEMPLATES_DIR.glob("*.docx")]

OPCAO_MODELO_AUTOMATICO = "Automático pelo professor"
modelo_bytes = None
modelo_automatico_arquivo = ""
escolha_template = "MODELOCDP.docx" if modo_cdp_dedicado else OPCAO_MODELO_AUTOMATICO
pdfs_aulas_files = []

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🧠 Configuração de Inteligência</div>', unsafe_allow_html=True)
opcoes_modo_ia = ["Sem IA"] if modo_cdp_dedicado else ["Sem IA", "OpenAI", "Gemini"]
modo_ia = st.radio(
    "Motor de processamento",
    opcoes_modo_ia,
    index=0,
    horizontal=True,
    key="modo_ia",
    disabled=modo_cdp_dedicado,
)

modelo_openai = ""
modelo_gemini = ""
if modo_cdp_dedicado:
    modo_ia = "Sem IA"
    st.caption("CDP - Ciclo I ativo: geração por regras próprias, sem IA, sem tecnologia e sem PDFs.")
elif modo_ia == "OpenAI":
    modelo_openai = os.environ.get("OPENAI_MODEL", MODELO_OPENAI_PADRAO)
    os.environ["OPENAI_MODEL"] = modelo_openai.strip() or MODELO_OPENAI_PADRAO
    st.caption(f"✨ OpenAI ativo com modelo `{modelo_openai}`.")
elif modo_ia == "Gemini":
    modelo_gemini = os.environ.get("GEMINI_MODEL", MODELO_GEMINI_PADRAO)
    os.environ["GEMINI_MODEL"] = modelo_gemini.strip() or MODELO_GEMINI_PADRAO
    st.caption(f"✨ Gemini ativo com modelo `{modelo_gemini}`.")
else:
    st.caption("⚡ Modo modular ativo (Sem IA). Gerando plano baseado em regras pedagógicas fixas.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 Dados do Cabeçalho</div>', unsafe_allow_html=True)
col_prof, col_disciplina = st.columns([1, 1])
with col_prof:
    professor_selecionado = st.selectbox(
        "Professor",
        _NOMES_PROFESSORES,
        key="professor_select",
    )
    if professor_selecionado == "Outro (digitar)":
        professor = st.text_input("Nome do professor", key="professor", autocomplete="off")
    elif professor_selecionado == "(selecione o professor)":
        professor = ""
    else:
        professor = professor_selecionado

with col_disciplina:
    # Lógica avançada para professores cadastrados
    dados_prof = PROFESSORES_DB.get(professor, {})
    disciplinas_cadastradas = dados_prof.get("disciplinas", [])
    if modo_cdp_dedicado:
        disciplinas_cadastradas = []
    
    disciplinas_gerais = [d for d in nomes_disciplinas() if not eh_cdp(d)]
    
    if disciplinas_cadastradas:
        disciplinas_unicas_prof = []
        for d in disciplinas_cadastradas:
            if d["disciplina"] not in disciplinas_unicas_prof:
                disciplinas_unicas_prof.append(d["disciplina"])
        
        opcoes_disc = ["(escolha a disciplina)"] + disciplinas_unicas_prof + ["Outra..."]
        disc_selecionada = st.selectbox("Disciplina", opcoes_disc, key="disc_prof_select")
        
        if disc_selecionada == "Outra...":
            disciplina = st.selectbox("Disciplina (Geral)", disciplinas_gerais, key="disciplina_opcao")
        elif disc_selecionada == "(escolha a disciplina)":
            disciplina = ""
        else:
            disciplina = disc_selecionada
    else:
        if modo_cdp_dedicado:
            disciplina = ""
            st.caption("Selecione abaixo o tipo de plano CDP.")
        else:
            disciplina = st.selectbox("Disciplina", disciplinas_gerais, key="disciplina_opcao")

if disciplina == "Outra":
    disciplina = st.text_input("Informe a disciplina", key="disciplina_outra", autocomplete="off")

if modo_cdp_dedicado:
    disciplina = st.selectbox(
        "Tipo de plano CDP",
        ["CDP- Multisseriada", "CDP - Ciclo I"],
        key="disciplina_cdp_opcao",
    )

disciplina_config = obter_config(disciplina)
disciplina_cdp = eh_cdp(disciplina)
if disciplina_cdp and escolha_template != "Upload de novo modelo...":
    modelo_cdp = TEMPLATES_DIR / "MODELOCDP.docx"
    if modelo_cdp.exists():
        modelo_bytes = modelo_cdp.read_bytes()
        st.info("Modo CDP/EJA ativo: usando automaticamente o modelo local MODELOCDP.docx.")

config_turma_selecionada = None
col_turma, col_bimestre, col_mes, col_previstas = st.columns([2, 2, 2, 1])
with col_turma:
    turmas_cadastradas = []
    if professor and disciplina:
        dados_prof = PROFESSORES_DB.get(professor, {})
        for d in dados_prof.get("disciplinas", []):
            if d["disciplina"] == disciplina and d["turma"] not in turmas_cadastradas:
                turmas_cadastradas.append(d["turma"])
    
    if turmas_cadastradas:
        opcoes_turma = ["(escolha a turma)"] + turmas_cadastradas + ["Outra..."]
        turma_selecionada = st.selectbox("Série/Turma", opcoes_turma, key="turma_prof_select")
        
        if turma_selecionada == "Outra...":
            turma = _selecionar_turma("Série/Turma (Outra)", "turma_select", "turma")
        elif turma_selecionada == "(escolha a turma)":
            turma = ""
            st.session_state["turma"] = ""
        else:
            turma = turma_selecionada
            st.session_state["turma"] = turma
            
            # Preenchimento automático de aulas e horários
            config_selecionada = None
            for d in dados_prof.get("disciplinas", []):
                if d["disciplina"] == disciplina and d["turma"] == turma:
                    config_selecionada = d
                    break
            
            if config_selecionada:
                config_turma_selecionada = config_selecionada
                modelo_automatico_arquivo = str(config_selecionada.get("arquivo") or "").strip()
                selecao_vaga_id = f"{professor}-{disciplina}-{turma}"
                if st.session_state.get("last_aula_prof") != selecao_vaga_id:
                    st.session_state["last_aula_prof"] = selecao_vaga_id
                    aulas_semana_cadastradas = str(config_selecionada.get("aulas_semana") or "").strip()
                    if aulas_semana_cadastradas:
                        st.session_state["aulas_previstas_manual"] = aulas_semana_cadastradas

                    datas_horarios = list(config_selecionada.get("datas_horarios") or [])
                    if datas_horarios:
                        for i, item in enumerate(datas_horarios):
                            data_aula = item.get("data")
                            if data_aula:
                                st.session_state[f"data_aula_{i}"] = data_aula
                            trecho_horario = " ".join(
                                str(item.get(chave) or "").strip()
                                for chave in ("horario", "aula")
                            ).strip()
                            sugestao = _sugerir_horario_cadastrado(trecho_horario, turma)
                            if sugestao:
                                st.session_state[f"horario_aula_{i}"] = sugestao
                                st.session_state[f"tipo_horario_aula_{i}"] = _tipo_horario(sugestao)
                    else:
                        dias_semana = _partes_dia_config(config_selecionada["dia_semana"])
                        partes_horario = _partes_horario_config(config_selecionada["horario"] or "")
                        sugestoes_h = []
                        for ph in partes_horario:
                            sugestao = _sugerir_horario_cadastrado(ph, turma)
                            if sugestao:
                                sugestoes_h.append(sugestao)

                        hoje = date.today()
                        for i, dia in enumerate(dias_semana):
                            data_sugerida = _proxima_data_pelo_dia(dia, hoje)
                            if i < 4:
                                st.session_state[f"data_aula_{i}"] = data_sugerida
                                if i < len(sugestoes_h):
                                    sugestao = sugestoes_h[i]
                                    st.session_state[f"horario_aula_{i}"] = sugestao
                                    st.session_state[f"tipo_horario_aula_{i}"] = _tipo_horario(sugestao)
    else:
        turma = _selecionar_turma("Série/Turma", "turma_select", "turma")
with col_bimestre:
    bimestre = st.selectbox("Bimestre", BIMESTRES, key="bimestre")
with col_mes:
    mes = _selecionar_mes()
with col_previstas:
    aulas_previstas_manual = _selecionar_aulas_semana(
        "Aulas na semana",
        "aulas_previstas_manual_select",
        "aulas_previstas_manual",
    )
datas_horarios_mes = []
if config_turma_selecionada and mes and not disciplina_cdp:
    datas_horarios_mes = _sincronizar_datas_horarios_mes(
        config_turma_selecionada,
        mes,
        professor,
        disciplina,
        turma,
    )
if modelo_automatico_arquivo and not disciplina_cdp and escolha_template == OPCAO_MODELO_AUTOMATICO:
    modelo_automatico_bytes = _ler_bytes_arquivo_cache(modelo_automatico_arquivo)
    if modelo_automatico_bytes:
        modelo_bytes = modelo_automatico_bytes
        st.caption(f"Modelo automático: {Path(modelo_automatico_arquivo).name}")
    else:
        st.warning("O plano cadastrado para esta turma não foi encontrado na pasta do professor.")

modelo_manual_necessario = bool(professor and disciplina and turma and not disciplina_cdp and not modelo_bytes)
if modelo_manual_necessario:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Modelo DOCX</div>', unsafe_allow_html=True)
    st.caption("Nenhum DOCX automático foi encontrado para esta seleção. Escolha um modelo salvo ou envie um novo.")

    opcoes_template_manual = templates_disponiveis + ["Upload de novo modelo..."]
    escolha_template = st.selectbox(
        "Modelo DOCX Base",
        opcoes_template_manual,
        key="escolha_template_manual",
        help="Este campo aparece somente quando o sistema não encontra um plano DOCX automático para o professor/turma.",
    )

    if escolha_template == "Upload de novo modelo...":
        modelo_file = st.file_uploader("Faça upload do novo Modelo DOCX", type=["docx"], key="novo_modelo_file")
        if modelo_file:
            modelo_bytes = modelo_file.getvalue()
            if st.button("Salvar este modelo para usos futuros", type="secondary"):
                (TEMPLATES_DIR / modelo_file.name).write_bytes(modelo_bytes)
                st.success(f"Modelo {modelo_file.name} salvo com sucesso!")
                st.rerun()
    else:
        caminho_template = TEMPLATES_DIR / escolha_template
        if caminho_template.exists():
            modelo_bytes = caminho_template.read_bytes()
    st.markdown('</div>', unsafe_allow_html=True)

if professor and disciplina and turma:
    with st.expander("Ajustar cadastro deste professor/turma"):
        st.caption("O ajuste salvo aqui fica registrado no banco e passa a ter prioridade sobre a leitura automática da pasta.")
        with st.form("form_ajuste_cadastro_atual"):
            ajuste_professor = st.text_input("Professor", value=professor, key="ajuste_professor")
            ajuste_disciplina = st.text_input("Disciplina", value=disciplina, key="ajuste_disciplina")
            ajuste_turma = st.text_input("Turma", value=turma, key="ajuste_turma")
            ajuste_componente_curricular = st.text_input(
                "Componente curricular",
                value=str((config_turma_selecionada or {}).get("componente_curricular") or disciplina),
                key="ajuste_componente_curricular",
            )
            ajuste_dia, ajuste_horario, total_grade_ajuste = _renderizar_grade_horarios(
                "ajuste_grade",
                str((config_turma_selecionada or {}).get("dia_semana") or ""),
                str((config_turma_selecionada or {}).get("horario") or ""),
                turma,
            )
            ajuste_aulas = st.text_input(
                "Aulas na semana",
                value=str((config_turma_selecionada or {}).get("aulas_semana") or aulas_previstas_manual or ""),
                key="ajuste_aulas_semana",
            )
            salvar_ajuste = st.form_submit_button("Salvar ajuste" if disciplina_cdp else "Salvar ajuste e atualizar DOCX")
            if salvar_ajuste:
                if not ajuste_professor.strip() or not ajuste_disciplina.strip() or not ajuste_turma.strip():
                    st.error("Preencha professor, disciplina e turma para salvar o ajuste.")
                else:
                    try:
                        ajuste_aulas_final = ajuste_aulas.strip() or (str(total_grade_ajuste) if total_grade_ajuste else "")
                        if disciplina_cdp:
                            arquivo_corrigido = str((config_turma_selecionada or {}).get("arquivo") or "")
                        else:
                            arquivo_corrigido = criar_ou_atualizar_modelo_professor(
                                professor=ajuste_professor.strip(),
                                disciplina=ajuste_disciplina.strip(),
                                turma=ajuste_turma.strip(),
                                origem=modelo_automatico_arquivo,
                                aulas_semana=ajuste_aulas_final,
                            )
                        salvar_professor_turma(
                            ajuste_professor.strip(),
                            ajuste_disciplina.strip(),
                            ajuste_turma.strip(),
                            ajuste_dia.strip(),
                            ajuste_horario.strip(),
                            ajuste_aulas_final,
                            arquivo_corrigido,
                            ajuste_componente_curricular.strip(),
                        )
                        _carregar_professores_dos_planos_cache.clear()
                        _ler_bytes_arquivo_cache.clear()
                        st.success("Cadastro CDP ajustado." if disciplina_cdp else "Cadastro ajustado e DOCX atualizado na pasta do professor.")
                        st.rerun()
                    except Exception as exc:
                        st.error("Não foi possível salvar o ajuste.")
                        with st.expander("Ver detalhe técnico"):
                            st.exception(exc)
assinatura_componente = f"{professor}|{disciplina}|{turma}|{(config_turma_selecionada or {}).get('componente_curricular', '')}"
if st.session_state.get("last_componente_curricular") != assinatura_componente:
    st.session_state["last_componente_curricular"] = assinatura_componente
    st.session_state["componente_curricular"] = str(
        (config_turma_selecionada or {}).get("componente_curricular")
        or disciplina
        or ""
    )

col_escola, col_componente = st.columns([1, 1])
with col_escola:
    escola = st.selectbox(
        "Escola",
        ["EE PROFª. EGLE LUPORINI COSTA", "PADRE GERALDO LOURENÇO"],
        key="escola",
    )
with col_componente:
    componente_curricular = st.text_input(
        "Componente curricular",
        placeholder="Ex.: CDP-E. F -EJA - MATEMÁTICA",
        key="componente_curricular",
    )
semana = ""

observacao = st.text_area(
    "Observação",
    placeholder="Opcional: acrescente orientações específicas para o campo de observações do plano.",
    height=90,
    key="observacao",
)
gerar_turma_espelho = st.checkbox(
    "Gerar o mesmo plano para uma 2ª turma",
    value=False,
    help="Usa os mesmos PDFs, mas permite informar outra turma com datas e horários próprios.",
    key="gerar_turma_espelho",
)
turma_espelho = ""
if gerar_turma_espelho:
    turma_espelho = _selecionar_turma("2ª Série/Turma", "turma_espelho_select", "turma_espelho")
turma_cdp = ""
aulas_envio = []
aulas_envio_espelho = []
cdp_aula_inicial = 1
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📚 Gestão das Aulas</div>', unsafe_allow_html=True)
pdfs_aulas_files = []
auto_repetir_semana = False
dividir_metodologia = False
pdfs_necessarios = 0

if disciplina_cdp:
    if eh_cdp_multisseriada(disciplina):
        col_cdp_turma, col_cdp_aula = st.columns([2, 1])
        with col_cdp_turma:
            turma_cdp = st.selectbox(
                "Turma multisseriada usada para filtrar as habilidades",
                TURMAS_CDP_MULTISSERIADA,
                key="turma_cdp",
            )
        with col_cdp_aula:
            cdp_aula_inicial = st.number_input(
                "Iniciar a partir da aula nº",
                min_value=1,
                value=1,
                step=1,
                key="cdp_aula_inicial",
            )
        st.info("Sequência padrão da semana: " + " → ".join(SEQUENCIA_PADRAO_CDP_MULTISSERIADA))
    else:
        cdp_aula_inicial = st.number_input(
            "Iniciar a partir da aula nº",
            min_value=1,
            value=1,
            step=1,
            key="cdp_aula_inicial",
        )
        st.info("Modo CDP - Ciclo I: o plano será montado a partir dos arquivos locais de habilidades por disciplina.")
else:
    pdfs_aulas_files = st.file_uploader(
        "PDFs das aulas (envio único; o sistema ordena pelo nome)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Use nomes como aula_01.pdf, aula_02.pdf, aula_10.pdf. O sistema organiza automaticamente pela numeração do arquivo.",
        key="pdfs_aulas_files",
    )
    if pdfs_aulas_files:
        pdfs_aulas_files = sorted(pdfs_aulas_files, key=_chave_ordenacao_pdf)
        nomes_ordenados = ", ".join(getattr(pdf, "name", "") for pdf in pdfs_aulas_files)
        st.caption(f"Ordem aplicada: {nomes_ordenados}")

    qtd_aulas = len(pdfs_aulas_files)
    linhas_modelo_original = len((config_turma_selecionada or {}).get("datas_horarios") or [])
    linhas_mes = len(datas_horarios_mes or [])
    linhas_modelo = linhas_mes or linhas_modelo_original
    if linhas_mes:
        st.caption(f"Linhas de aula para {mes}: {linhas_mes}")
        if linhas_modelo_original and linhas_modelo_original != linhas_mes:
            st.caption(
                f"O modelo original tinha {linhas_modelo_original} linha(s), mas o mês selecionado pede {linhas_mes}."
            )
    elif linhas_modelo_original:
        st.caption(f"Linhas de aula encontradas no plano do professor: {linhas_modelo_original}")
    if qtd_aulas == 0:
        st.info("Envie os PDFs das aulas para preencher datas e horários.")
    else:
        st.info(f"PDFs adicionados: {qtd_aulas}")

    if linhas_mes:
        st.session_state["auto_repetir_semana"] = False
    auto_repetir_semana = st.checkbox(
        "Repetir automaticamente datas e horários da 1ª semana nas semanas seguintes",
        value=False if linhas_mes else True,
        help="Preencha a 1ª semana normalmente. As próximas semanas replicam o mesmo padrão com +7 dias.",
        key="auto_repetir_semana",
        disabled=bool(linhas_mes),
    )
    if linhas_mes:
        st.caption("Datas e horários atualizados automaticamente pelo mês selecionado.")

    dividir_metodologia = st.checkbox(
        "Dividir metodologia em dois dias (Primeiro/Segundo Momento)",
        value=False,
        key="dividir_metodologia",
        help="Se marcado, cada PDF gerará duas aulas no plano: uma com a primeira parte da metodologia e outra com a segunda."
    )

    if linhas_modelo and dividir_metodologia:
        st.info("Como o plano do professor já define uma linha por PDF, a divisão em dois dias foi desativada nesta seleção.")
        dividir_metodologia = False

    if dividir_metodologia:
        pdfs_necessarios = qtd_aulas
        num_rows = linhas_modelo or int(qtd_aulas) * 2
    else:
        pdfs_necessarios = linhas_modelo or qtd_aulas
        num_rows = linhas_modelo or int(qtd_aulas)

    if pdfs_necessarios:
        if qtd_aulas == pdfs_necessarios:
            st.success(f"PDFs conferidos: {qtd_aulas}/{pdfs_necessarios}.")
        else:
            st.warning(
                f"PDFs adicionados: {qtd_aulas}/{pdfs_necessarios}. "
                "A quantidade precisa bater com as linhas de aula do plano."
            )

    aulas_envio = _coletar_aulas_envio(
        num_rows=num_rows,
        pdfs_aulas_files=pdfs_aulas_files,
        dividir_metodologia=dividir_metodologia,
        auto_repetir_semana=auto_repetir_semana,
    )
    if gerar_turma_espelho:
        st.markdown("---")
        aulas_envio_espelho = _coletar_aulas_envio(
            num_rows=num_rows,
            pdfs_aulas_files=pdfs_aulas_files,
            dividir_metodologia=dividir_metodologia,
            auto_repetir_semana=auto_repetir_semana,
            key_prefix="turma2_",
            titulo_secao="Datas e horários da 2ª turma",
        )

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🚀 Passo 1: Extração e Processamento</div>', unsafe_allow_html=True)
geracao_em_andamento = bool(st.session_state.get("geracao_em_andamento", False))
label_processar = "GERAR PLANO CDP/EJA" if disciplina_cdp else "PROCESSAR AULAS PARA REVISÃO"
processar_aulas = st.button(label_processar, disabled=geracao_em_andamento)
if not modo_cdp_dedicado:
    st.caption("Geração por pasta pausada por enquanto. Use a geração individual, que já busca o modelo automaticamente pelo professor.")

st.markdown('</div>', unsafe_allow_html=True)

if processar_aulas:
    st.session_state["geracao_em_andamento"] = True
    erro_validacao = validar_entrada(
        modelo_bytes,
        disciplina,
        disciplina_config,
        aulas_envio,
        professor,
        turma,
        bimestre,
        mes,
        aulas_previstas_manual,
        pdfs_enviados=len(pdfs_aulas_files or []),
        pdfs_necessarios=pdfs_necessarios,
    )
    erro_validacao_secundaria = validar_aulas_secundarias(
        gerar_turma_espelho,
        turma_espelho,
        aulas_envio_espelho,
        disciplina_config.exige_pdf,
    )
    if erro_validacao:
        st.error(erro_validacao)
        st.session_state["geracao_em_andamento"] = False
    elif erro_validacao_secundaria:
        st.error(erro_validacao_secundaria)
        st.session_state["geracao_em_andamento"] = False
    elif not disciplina_cdp and modo_ia == "OpenAI" and not os.environ.get("OPENAI_API_KEY", "").strip():
        st.error("Modo OpenAI selecionado, mas a chave não foi encontrada no Windows (`OPENAI_API_KEY`).")
        st.session_state["geracao_em_andamento"] = False
    elif not disciplina_cdp and modo_ia == "Gemini" and not os.environ.get("GEMINI_API_KEY", "").strip():
        st.error("Modo Gemini selecionado, mas a chave não foi encontrada no Windows (`GEMINI_API_KEY`).")
        st.session_state["geracao_em_andamento"] = False
    elif disciplina_cdp:
        planos_gerados = []
        with st.status("📚 Gerando plano CDP/EJA...", expanded=True) as status:
            try:
                turmas_para_gerar = [turma]
                if gerar_turma_espelho:
                    turmas_para_gerar.append(turma_espelho)

                for turma_atual in turmas_para_gerar:
                    status.write(f"Montando plano da turma `{turma_atual}`...")
                    planos_gerados.append(
                        _gerar_docx_cdp_final(
                            modelo_bytes=modelo_bytes,
                            escola=escola,
                            professor=professor,
                            disciplina=disciplina,
                            turma_atual=turma_atual,
                            mes=mes,
                            bimestre=bimestre,
                            semana=semana,
                            observacao=observacao,
                            aulas_previstas_manual=aulas_previstas_manual,
                            cdp_aula_inicial=cdp_aula_inicial,
                            turma_cdp=turma_cdp,
                        )
                    )

                st.session_state["planos_gerados"] = planos_gerados
                st.session_state["turmas_processadas"] = []
                for plano in planos_gerados:
                    nome_arq = nome_arquivo_plano(plano["turma"], disciplina, ia_usada=False)
                    salvar_historico_plano(professor, disciplina, plano["turma"], nome_arq, plano["docx_bytes"].getvalue())
                status.update(label="✅ Plano CDP/EJA gerado!", state="complete", expanded=False)
                st.session_state["geracao_em_andamento"] = False
                st.rerun()
            except Exception as exc:
                status.update(label="❌ Não foi possível gerar o plano CDP/EJA.", state="error", expanded=True)
                st.error("Erro técnico ao gerar o plano CDP/EJA.")
                with st.expander("Ver detalhe técnico do erro"):
                    st.exception(exc)
                st.session_state["geracao_em_andamento"] = False
    else:
        turmas_processadas = []
        with st.status("🚀 Extraindo dados dos arquivos...", expanded=True) as status:
            try:
                if professor and disciplina and turma and componente_curricular.strip():
                    salvar_professor_turma(
                        professor,
                        disciplina,
                        turma,
                        str((config_turma_selecionada or {}).get("dia_semana") or ""),
                        str((config_turma_selecionada or {}).get("horario") or ""),
                        str((config_turma_selecionada or {}).get("aulas_semana") or aulas_previstas_manual or ""),
                        str(modelo_automatico_arquivo or (config_turma_selecionada or {}).get("arquivo") or ""),
                        componente_curricular.strip(),
                    )
                    _carregar_professores_dos_planos_cache.clear()

                turmas_para_gerar = [(turma, aulas_envio)]
                if gerar_turma_espelho:
                    turmas_para_gerar.append((turma_espelho, aulas_envio_espelho))

                for turma_atual, aulas_turma in turmas_para_gerar:
                    status.write(f"Processando aulas da turma `{turma_atual}`...")
                    aulas_extraidas = _extrair_aulas_dos_pdfs(
                        aulas_envio=aulas_turma,
                        disciplina=disciplina,
                        turma_atual=turma_atual,
                        bimestre=bimestre,
                        modo_ia=modo_ia,
                        modelo_openai=modelo_openai,
                        modelo_gemini=modelo_gemini,
                        dividir_metodologia=dividir_metodologia,
                    )
                    turmas_processadas.append({
                        "turma": turma_atual,
                        "aulas": aulas_extraidas
                    })

                status.update(label="✅ Extração concluída!", state="complete", expanded=False)
                _limpar_revisao_aulas()
                st.session_state["turmas_processadas"] = turmas_processadas
                st.session_state["planos_gerados"] = []
                st.session_state["revisao_token"] = int(st.session_state.get("revisao_token", 0)) + 1
                st.session_state["geracao_em_andamento"] = False
                st.rerun()
            except Exception as exc:
                status.update(label="❌ Não foi possível extrair as aulas.", state="error", expanded=True)
                mensagem = str(exc)
                if mensagem.startswith("Falha de IA detectada:\n"):
                    falhas_ia = [linha for linha in mensagem.splitlines()[1:] if linha.strip()]
                    st.error("A IA não conseguiu processar todas as aulas.")
                    for falha in falhas_ia:
                        st.write(f"- {falha}")
                elif mensagem.startswith("Problemas encontrados no plano:\n"):
                    problemas_plano = [linha for linha in mensagem.splitlines()[1:] if linha.strip()]
                    st.error("A conferência automática encontrou erros:")
                    for problema in problemas_plano:
                        st.write(f"- {problema}")
                elif "Nenhuma aula foi extraída" in mensagem:
                    st.error("Nenhuma aula extraída. Verifique se são slides válidos.")
                else:
                    st.error("Erro técnico.")
                    with st.expander("Ver detalhe técnico do erro"):
                        st.exception(exc)
                st.session_state["geracao_em_andamento"] = False

if st.session_state.get("turmas_processadas"):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✏️ Passo 2: Revisão e Edição das Aulas</div>', unsafe_allow_html=True)
    
    turmas_revisadas = []
    revisao_token = int(st.session_state.get("revisao_token", 0))
    
    for t_idx, turma_data in enumerate(st.session_state["turmas_processadas"]):
        st.markdown(f"### Turma: {turma_data['turma']}")
        aulas_editadas = []
        
        for a_idx, aula in enumerate(turma_data["aulas"]):
            with st.expander(f"Aula {a_idx + 1} - {aula.get('tema', '')}", expanded=False):
                col1, col2 = st.columns([1, 1])
                with col1:
                    novo_tema = st.text_input(f"Tema", value=aula.get("tema", ""), key=f"tema_{revisao_token}_{t_idx}_{a_idx}")
                    nova_aprendizagem = st.text_area(f"Aprendizagem", value=aula.get("aprendizagem", ""), height=100, key=f"apr_{revisao_token}_{t_idx}_{a_idx}")
                with col2:
                    novo_acomp = st.text_area(f"Acompanhamento", value="\n".join(aula.get("acompanhamento", [])), height=100, key=f"acomp_{revisao_token}_{t_idx}_{a_idx}")
                    nova_acess = st.text_area(f"Acessibilidade", value="\n".join(aula.get("acessibilidade", [])), height=100, key=f"acess_{revisao_token}_{t_idx}_{a_idx}")
                
                texto_met = _texto_metodologia_app(aula)
                nova_metodologia = st.text_area(f"Metodologia (Desenvolvimento)", value=texto_met, height=200, key=f"met_{revisao_token}_{t_idx}_{a_idx}")
                
                aula_editada = aula.copy()
                aula_editada["tema"] = novo_tema
                aula_editada["aprendizagem"] = nova_aprendizagem
                aula_editada["acompanhamento"] = [x.strip() for x in novo_acomp.split("\n") if x.strip()]
                aula_editada["acessibilidade"] = [x.strip() for x in nova_acess.split("\n") if x.strip()]
                aula_editada["metodologia"] = _metodologia_app_para_blocos(nova_metodologia)
                aulas_editadas.append(aula_editada)
                
        turmas_revisadas.append({"turma": turma_data["turma"], "aulas": aulas_editadas})
    
    if st.button("CONFIRMAR E GERAR DOCX", type="primary"):
        planos_gerados = []
        for turma_rev in turmas_revisadas:
            planos_gerados.append(
                _gerar_docx_final(
                    modelo_bytes=modelo_bytes,
                    aulas=turma_rev["aulas"],
                    escola=escola,
                    professor=professor,
                    disciplina=disciplina,
                    componente_curricular=componente_curricular.strip(),
                    turma_atual=turma_rev["turma"],
                    mes=mes,
                    bimestre=bimestre,
                    semana=semana,
                    observacao=observacao,
                    aulas_previstas_manual=aulas_previstas_manual,
                )
            )
        st.session_state["planos_gerados"] = planos_gerados
        
        # Salvar histórico no banco
        for plano in planos_gerados:
            nome_arq = nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano["ia_usada"])
            salvar_historico_plano(professor, disciplina, plano["turma"], nome_arq, plano["docx_bytes"].getvalue())
            
        st.success("Planos gerados, salvos no histórico e prontos para download!")
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("planos_gerados"):
    planos_gerados = st.session_state["planos_gerados"]
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📥 Passo 3: Download</div>', unsafe_allow_html=True)
    if len(planos_gerados) == 1:
        plano = planos_gerados[0]
        st.download_button(
            label="Baixar Plano de Aula (DOCX)",
            data=plano["docx_bytes"].getvalue(),
            file_name=nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano["ia_usada"]),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.download_button(
            label="Baixar relatório",
            data=plano["relatorio"].encode("utf-8"),
            file_name=nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano["ia_usada"]).replace(".docx", "_relatorio.txt"),
            mime="text/plain",
        )
    else:
        zip_data = _montar_zip_planos(planos_gerados, disciplina)
        st.download_button(
            label="📦 Baixar planos em ZIP",
            data=zip_data,
            file_name=f"{_slug_download(disciplina or 'planos')}_turmas.zip",
            mime="application/zip",
        )
        for plano in planos_gerados:
            nome_plano = nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano["ia_usada"])
            st.download_button(
                label=f"Baixar DOCX - {plano['turma']}",
                data=plano["docx_bytes"].getvalue(),
                file_name=nome_plano,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_docx_pos_{_slug_download(plano['turma'])}",
            )
    st.markdown('</div>', unsafe_allow_html=True)
