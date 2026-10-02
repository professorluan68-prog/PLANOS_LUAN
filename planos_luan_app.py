
import streamlit as st
import logging
import re
import os
import json
import base64
import html
import math
import traceback
import unicodedata
import hashlib
from datetime import date, timedelta, datetime
from io import BytesIO
from pathlib import Path
import time
import threading
import signal

# Monitorador para fechar o servidor automaticamente quando o navegador for fechado
def _monitorar_sessoes_ativas():
    time.sleep(10)  # Período de tolerância inicial
    has_connected = False
    consecutive_zero_sessions = 0
    while True:
        try:
            # [CORREÇÃO A4] Proteger acesso à API privada do Streamlit.
            # runtime._session_mgr é API interna que pode mudar entre versões.
            # Se indisponível, count=-1 impede encerramento indevido do servidor.
            from streamlit.runtime import get_instance
            runtime = get_instance()
            if runtime and hasattr(runtime, "_session_mgr"):
                active_sessions = runtime._session_mgr.list_active_sessions()
                count = len(active_sessions)
                if count > 0:
                    has_connected = True
                    consecutive_zero_sessions = 0
                else:
                    if has_connected:
                        consecutive_zero_sessions += 1
            else:
                count = -1  # API indisponível — não encerrar
                consecutive_zero_sessions = 0
        except Exception as _monitor_exc:
            import logging as _log
            _log.getLogger(__name__).debug(
                "Monitor de sessões: API Streamlit indisponível (%s)", _monitor_exc
            )
            count = -1  # API indisponível — não encerrar
            consecutive_zero_sessions = 0
        
        if has_connected and consecutive_zero_sessions >= 5:
            # Encerramento gracioso: usa SIGTERM para permitir que handlers de
            # cleanup (finally, atexit, flush de arquivos) rodem antes de sair.
            # NÃO usar os._exit(0) pois interrompe gravações sem liberar recursos.
            try:
                signal.raise_signal(signal.SIGTERM)
            except (AttributeError, OSError):
                # Fallback para Python < 3.8 ou plataformas sem raise_signal
                os.kill(os.getpid(), signal.SIGTERM)
            return  # Encerra a thread de monitoramento
        time.sleep(1)

_monitor_thread = threading.Thread(target=_monitorar_sessoes_ativas, daemon=True)
_monitor_thread.start()
# ── Modernização da tela inicial ──────────────────────────────────────────────
from ui.tela_inicial_moderna import (
    HERO_CSS,
    HERO_HTML,
    STATS_HTML,
    SECTION_HEADER_HTML,
    OPTION_MENU_STYLES,
)
from ui.ui_components import render_sidebar
from core.constantes import (
    HORARIOS_AULA,
    HORARIOS_SIMPLES,
    HORARIOS_DUPLAS,
    TURNOS_HORARIOS,
    MESES,
    DIAS_SEMANA_CADASTRO,
    AULAS_SEMANA_OPCOES,
    EXTENSAO_MES_ANTECIPACOES,
    EXTENSAO_MES_OPCOES,
    EXTENSAO_MES_VALORES,
    ESCOLAS,
)

from ui.shared import (
    _rotulo_horario,
    _rotulo_data_aula_com_dia,
    _serializar_horarios_padronizados,
    _tipo_horario,
    _turno_e_aulas_de_horario,
    _montar_horario_flexivel,
    nome_arquivo_plano,
    _normalizar_texto_simples,
    _normalizar_label_aula,
    _slug_key,
    _chave_cadastro,
    _eh_cadastro_cdp_eja,
    _arquivo_existe,
    _ler_bytes_arquivo_cache,
    _obter_professores_db_cache,
    _carregar_professores_dos_planos_cache,
    _diagnosticar_modelos_professores_cache,
    carregar_css,
    carregar_chaves_locais,
    _is_aula_dupla,
    _divisao_pdf_padrao,
    _sincronizar_divisao_pdf_padrao,
    _proxima_data_pelo_dia,
    _sugerir_horario_e_tipo,
    _normalizar_horario_cadastro,
    _horarios_extraidos_texto,
    _dia_semana_numero,
    _partes_dia_config,
    _partes_horario_config,
    _resumo_grade_cadastrada,
    _sugerir_horario_cadastrado,
    _indice_horario,
    _horarios_padronizados_de_texto,
    _defaults_grade_horarios,
    _asset_data_uri,
    _selecionar_turma,
    _selecionar_mes,
    _selecionar_aulas_semana,
    _datas_horarios_do_mes,
    _datas_do_mes_por_dia,
    _padroes_horario_config,
    _mes_numero_app,
    DIAS_SEMANA_COMPLETOS,
    TURMAS_PADRAO,
    _texto_metodologia_app,
    _metodologia_app_para_blocos,
)
from ui.relatorio_conferencia import _salvar_relatorios_conferencia
from ui.painel_pdfs import _render_painel_pdfs
from ui.revisao_aulas import renderizar_passo_revisao
from ui.cadastro import _renderizar_cadastro_professor
from ui.historico import _renderizar_historico
from ui.diagnostico import _renderizar_diagnostico_modelos
from ui.reescrita_cdp import _renderizar_reescrita_cdp_em

# ── Banco de Dados e Cadastro ──────────────────────────────────────────
from core.database import (
    listar_vinculos_professores,
    atualizar_vinculo_professor,
    salvar_professor_turma,
    duplicar_vinculo_professor,
    excluir_vinculo_professor,
    init_db,
    obter_professores_db,
    salvar_historico_plano,
    migrar_json_para_sqlite,
    verificar_plano_gerado_por_outro_professor,
)
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
from core.cdp_em_docx import reescrever_docx_cdp_contextual_matematica
from core.calendario import (
    datas_do_periodo as _datas_do_periodo,
    datas_feriado_padrao as _datas_feriado_padrao,
    datas_sem_aula_padrao as _datas_sem_aula_padrao,
    datas_por_dia_ate_limite as _datas_por_dia_ate_limite,
    fim_periodo_mes_com_extensao as _fim_periodo_mes_com_extensao,
    inicio_periodo_mes_com_antecipacao as _inicio_periodo_mes_com_antecipacao,
    filtrar_datas_sem_aula as _filtrar_datas_sem_aula,
    rotulo_data_sem_aula as _rotulo_data_sem_aula,
)
from core.lote import processar_varios_pdfs
from core.seguranca_upload import (
    limpar_upload_temporario,
    salvar_pdf_upload_temporario,
)
from core.operacao import (
    detectar_alteracoes_planos_revisados,
    gerar_docx_final as _gerar_docx_final,
    gerar_planos_finais_sem_revisao as _gerar_planos_finais_sem_revisao,
    montar_zip_planos as _montar_zip_planos,
)
from core.validador_plano import validar_aulas_geradas
from config import MODELO_OPENAI_PADRAO, MODELO_GEMINI_PADRAO, PASTA_PLANOS_PROFESSORES, PLANOS_FINALIZADOS_DIR, PLANOS_FEITOS_DIR, TEMPLATES_DOCX_DIR, PASTA_BACKUP, inicializar_pastas, BASE_DIR, HABILITAR_REVISAO_POS_GERACAO, PDF_AULAS_DIR
from docx_generator.preencher_cdp import preencher_documento_cdp, prever_aulas_cdp
from core.helpers import (
    LocalFileWrapper,
    filtrar_pdfs_para_aulas,
    garantir_caminho_na_raiz,
    arquivos_na_ordem_de_envio,
    horario_para_plano,
    listar_falhas_ia,
    normalizar_para_pasta,
    numeros_pdfs_faltantes,
    ordenar_pdfs_por_numero,
    ordenar_pdfs_por_sequencia,
    resolver_pasta_pdfs,
    resumir_falhas_ia,
    texto_lista as _texto_lista,
    numero_aula_pdf,
)
from core.validacao_pdfs_contexto import validar_lote_pdfs_contexto_sem_ia
from core.proveniencia_docx import resumir_proveniencia_docx
from core.turmas import turmas_espelho_mesma_serie
from core.professores_planos import (
    atualizar_cabecalho_modelo_professor,
    carregar_professores_dos_planos,
    criar_ou_atualizar_modelo_professor,
    diagnosticar_modelos_professores,
    extrair_datas_horarios_de_bytes,
    mesclar_professores,
)
from core.modelos_docx import (
    caminho_template_central,
    resolver_template_id_geracao,
    template_id_por_contexto,
)
from core.ae_priorizado import (
    aplicar_ae_priorizado_nas_aulas,
    contexto_ae_priorizado_disponivel,
    disciplina_ae_priorizado_disponivel,
    sequencia_aulas_ae_priorizado,
)
from core.lib.classificador import perfil_disciplina

APP_ICON_PNG = BASE_DIR / "assets" / "planos_luan_icon.png"

st.set_page_config(
    page_title="Planos de Aula — SEDUC",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

carregar_css(BASE_DIR)

try:
    from core.cache_manager import CacheManager
    CacheManager().limpar_arquivos_expirados()
except Exception:
    pass


CAMPOS_TELA = {
    "modelo_file",
    "pdfs_aulas_files",
    "modo_upload_pdf",
    "salvar_historico_geracao",
    "novo_modelo_file",
    "escolha_template",
    "escolha_template_manual",
    "modo_tela",
    "modo_ia",
    "professor",
    "professor_select",
    "aula_prof_select",
    "last_aula_prof",
    "disc_prof_select",
    "disciplina_opcao",
    "disciplina_cdp_opcao",
    "disciplina_outra",
    "turma",
    "turma_select",
    "turma_prof_select",
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
    "extensao_mes",
    "datas_sem_aula",
    "datas_sem_aula_assinatura",
    "escola",
    "componente_curricular",
    "last_componente_curricular",
    "observacao",
    "last_mes_for_obs",
    "deixar_antecipacao_vazia",
    "auto_repetir_semana",
    "usar_ae_priorizado",
    "caminho_ae_priorizado",
    "professor_cadastro_select",
    "cadastro_busca",
    "cadastro_filtro_disciplina",
    "cadastro_filtro_origem",
    "cadastro_filtro_professor",
    "cadastro_filtro_sem_modelo",
    "cadastro_filtro_turma",
    "cadastro_selecionado",
    "planos_gerados",
    "turmas_processadas",
    "avisos_processamento",
    "geracao_em_andamento",
    "revisao_token",
    "relatorio_conferencia_chave",
    "relatorio_conferencia_paths",
    "erro_processamento",
    "erro_processamento_detalhe",
    "permitir_dia_sem_pdf_portugues",
    "frequencia_dia_sem_pdf_opcao",
    "modo_aula_dupla_sem_pdf_opcao",
    "dia_sem_pdf_portugues",
}

PREFIXOS_TELA = (
    "pdfs_aulas_files_auto_",
    "data_aula_",
    "horario_aula_",
    "tipo_horario_aula_",
    "dividir_pdf_aula_",
    "data_turma2_aula_",
    "horario_turma2_aula_",
    "tipo_horario_turma2_aula_",
    "dividir_pdf_turma2_aula_",
    "cadastro_grade_",
    "ajuste_grade_",
)

PREFIXOS_REVISAO = ("tema_", "apr_", "acomp_", "acess_", "met_")
MODO_UPLOAD_PDF_PADRAO = "Todos de uma vez"


def _limpar_revisao_aulas() -> None:
    for chave in list(st.session_state.keys()):
        if any(str(chave).startswith(prefixo) for prefixo in PREFIXOS_REVISAO):
            del st.session_state[chave]


def limpar_dados_tela() -> None:
    _limpar_revisao_aulas()
    for chave in list(st.session_state.keys()):
        if chave in CAMPOS_TELA or any(str(chave).startswith(prefixo) for prefixo in PREFIXOS_TELA):
            del st.session_state[chave]
    st.session_state["modo_tela"] = "Planos gerais"


def _limpar_erro_processamento() -> None:
    st.session_state.pop("erro_processamento", None)
    st.session_state.pop("erro_processamento_detalhe", None)


def _assinatura_pdfs_automaticos(arquivos) -> str:
    """Identifica a lista atual de PDFs para evitar selecao antiga do Streamlit."""
    partes = []
    for arquivo in ordenar_pdfs_por_numero(arquivos or []):
        caminho = Path(arquivo)
        caminho_identificador = caminho.resolve(strict=False)
        try:
            stat = caminho.stat()
            partes.append(
                f"{caminho_identificador}|{stat.st_size}|{stat.st_mtime_ns}|"
                f"{numero_aula_pdf(caminho) or ''}"
            )
        except OSError:
            partes.append(
                f"{caminho_identificador}|0|0|{numero_aula_pdf(caminho) or ''}"
            )
    base = "\n".join(partes)
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:12] if base else "sem_pdfs"

# [CORREÇÃO B1] import unicodedata removido aqui — já importado no topo do arquivo.
def _remover_acentos(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def _normalizar_nome_diretorio(nome: str) -> str:
    if not nome:
        return ""
    res = nome.strip().replace(" ", "_").upper()
    res = "".join(c for c in res if c not in r'\/:*?"<>|')
    return res

def _resolver_caminho_professor_disciplina(professor: str, disciplina: str, mes: str = "") -> Path:
    if not professor:
        base = PLANOS_FINALIZADOS_DIR
        if mes:
            mes_norm = _normalizar_nome_diretorio(mes)
            caminho_mes = base / mes_norm
            caminho_mes.mkdir(parents=True, exist_ok=True)
            return caminho_mes
        return base
        
    prof_norm = _normalizar_nome_diretorio(professor)
    prof_norm_sem_acento = _remover_acentos(prof_norm)
    
    disc_norm = _normalizar_nome_diretorio(disciplina)
    disc_norm_sem_acento = _remover_acentos(disc_norm)
    
    PLANOS_FEITOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Busca o professor de forma case-insensitive e acento-insensitive
    caminho_prof = PLANOS_FEITOS_DIR / prof_norm
    for p_child in PLANOS_FEITOS_DIR.iterdir():
        if p_child.is_dir():
            child_norm_sem_acento = _remover_acentos(p_child.name.upper())
            if child_norm_sem_acento == prof_norm_sem_acento:
                caminho_prof = p_child
                break
                
    caminho_prof.mkdir(parents=True, exist_ok=True)
    
    # Busca a disciplina de forma case-insensitive e acento-insensitive sob o professor
    caminho_disc = caminho_prof / disc_norm
    for d_child in caminho_prof.iterdir():
        if d_child.is_dir():
            child_norm_sem_acento = _remover_acentos(d_child.name.upper())
            if child_norm_sem_acento == disc_norm_sem_acento:
                caminho_disc = d_child
                break
                
    caminho_disc.mkdir(parents=True, exist_ok=True)

    if mes:
        mes_norm = _normalizar_nome_diretorio(mes)
        mes_norm_sem_acento = _remover_acentos(mes_norm)
        caminho_mes = caminho_disc / mes_norm
        for m_child in caminho_disc.iterdir():
            if m_child.is_dir():
                child_norm_sem_acento = _remover_acentos(m_child.name.upper())
                if child_norm_sem_acento == mes_norm_sem_acento:
                    caminho_mes = m_child
                    break
        caminho_mes.mkdir(parents=True, exist_ok=True)
        return caminho_mes

    return caminho_disc

def _salvar_planos_na_pasta_finalizados(planos_gerados, disciplina: str, professor: str = None, mes: str = "") -> list[str]:
    caminhos_salvos = []
    try:
        if professor:
            dir_destino = _resolver_caminho_professor_disciplina(professor, disciplina, mes=mes)
        else:
            PLANOS_FINALIZADOS_DIR.mkdir(parents=True, exist_ok=True)
            dir_destino = PLANOS_FINALIZADOS_DIR
            if mes:
                dir_destino = dir_destino / _normalizar_nome_diretorio(mes)
                dir_destino.mkdir(parents=True, exist_ok=True)
            
        for plano in planos_gerados or []:
            nome_arq = nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano.get("ia_usada", False))
            caminho_completo = dir_destino / nome_arq
            with open(caminho_completo, "wb") as f:
                f.write(plano["docx_bytes"].getvalue())
            caminhos_salvos.append(str(caminho_completo))

            # Atualiza a memória de progresso para a turma deste plano
            if professor and plano.get("turma"):
                try:
                    from core.gestao_aulas import detectar_ultima_aula_de_docx_bytes
                    from core.database import salvar_progresso_aula
                    ua = detectar_ultima_aula_de_docx_bytes(plano["docx_bytes"].getvalue())
                    if ua > 0:
                        salvar_progresso_aula(professor, disciplina, plano["turma"], ua, mes=mes)
                except Exception:
                    pass
    except Exception as e:
        destino_mensagem = str(dir_destino) if 'dir_destino' in locals() else str(PLANOS_FINALIZADOS_DIR)
        st.warning(f"Não foi possível salvar os arquivos localmente em {destino_mensagem}: {e}")
    return caminhos_salvos


def _salvar_planos_gerados_se_configurado(
    planos_gerados,
    professor: str,
    disciplina: str,
    bimestre: str,
    mes: str = "",
) -> bool:
    if not st.session_state.get("salvar_historico_geracao", False):
        return False

    for plano in planos_gerados or []:
        ultimo_pdf_nome = ""
        aulas_plano = plano.get("aulas") or []
        for aula in reversed(aulas_plano):
            caminho_pdf_orig = aula.get("caminho_pdf")
            if caminho_pdf_orig:
                ultimo_pdf_nome = Path(caminho_pdf_orig).name
                break

        salvar_historico_plano(
            professor,
            disciplina,
            plano["turma"],
            nome_arquivo_plano(plano["turma"], disciplina, ia_usada=plano.get("ia_usada", False)),
            plano["docx_bytes"].getvalue(),
            bimestre=bimestre,
            mes_plano=mes,
            ultimo_pdf=ultimo_pdf_nome,
        )
    return True


def _registrar_mensagem_memoria_plano(salvou_historico: bool) -> None:
    if salvou_historico:
        st.session_state["mensagem_historico_planos_tipo"] = "success"
        st.session_state["mensagem_historico_planos"] = (
            "Plano salvo no histórico. Os próximos planos continuarão começando pela Aula 1."
        )
    else:
        st.session_state["mensagem_historico_planos_tipo"] = "info"
        st.session_state["mensagem_historico_planos"] = (
            "Plano gerado sem salvar no histórico."
        )





def _registrar_erro_processamento(exc: Exception) -> None:
    mensagem = str(exc).strip() or exc.__class__.__name__
    st.session_state["erro_processamento"] = (
        "Nao foi possivel concluir o processamento das aulas. "
        f"Motivo: {mensagem}"
    )
    st.session_state["erro_processamento_detalhe"] = traceback.format_exc()



def _selecionar_turma_espelho(turma_principal: str, turmas_cadastradas: list[str]) -> str:
    opcoes = turmas_espelho_mesma_serie(turma_principal, list(dict.fromkeys(turmas_cadastradas or [])))
    if not turma_principal:
        st.warning("Selecione a turma principal antes de gerar para a 2ª turma.")
        st.session_state["turma_espelho"] = ""
        return ""

    if not opcoes:
        st.warning("Não encontrei outra turma cadastrada da mesma série para este professor e disciplina.")
        st.session_state["turma_espelho"] = ""
        return ""

    if len(opcoes) == 1:
        turma_unica = opcoes[0]
        st.session_state["turma_espelho"] = turma_unica
        st.info(f"2ª turma selecionada automaticamente: {turma_unica}.")
        return turma_unica

    valor_atual = str(st.session_state.get("turma_espelho", "") or "").strip()
    if valor_atual not in opcoes:
        valor_atual = opcoes[0]
        st.session_state["turma_espelho"] = valor_atual
        if "turma_espelho_select" in st.session_state:
            del st.session_state["turma_espelho_select"]

    indice = opcoes.index(valor_atual)
    escolha = st.selectbox("2ª Série/Turma", opcoes, index=indice, key="turma_espelho_select")
    st.session_state["turma_espelho"] = escolha
    st.caption("Opções limitadas às turmas cadastradas da mesma série.")
    return escolha


# ── Banco de Dados e Cadastro ──────────────────────────────────────────
inicializar_pastas()
carregar_chaves_locais(BASE_DIR)
init_db()
migrar_json_para_sqlite()
PROFESSORES_DB = mesclar_professores(
    _obter_professores_db_cache(),
    _carregar_professores_dos_planos_cache(),
)

PROFESSORES = {}
for prof, dados_prof in PROFESSORES_DB.items():
    disciplinas_unicas = []
    for d in dados_prof.get("disciplinas", []):
        nome_disc = d.get("disciplina")
        if nome_disc and nome_disc not in disciplinas_unicas:
            disciplinas_unicas.append(nome_disc)
    PROFESSORES[prof] = disciplinas_unicas

_NOMES_PROFESSORES = ["(selecione o professor)"] + sorted(PROFESSORES.keys()) + ["Outro (digitar)"]


def _pontuacao_config_cadastro(config: dict | None) -> int:
    config = config or {}
    pontuacao = 0
    if config.get("datas_horarios"):
        pontuacao += 100
    if str(config.get("arquivo") or config.get("arquivo_modelo") or "").strip():
        pontuacao += 40
    if str(config.get("dia_semana") or "").strip():
        pontuacao += 20
    if str(config.get("horario") or "").strip():
        pontuacao += 20
    if str(config.get("aulas_semana") or "").strip():
        pontuacao += 15
    if str(config.get("componente_curricular") or "").strip():
        pontuacao += 5
    return pontuacao


def _selecionar_config_cadastro(disciplinas: list[dict], disciplina: str, turma: str) -> dict | None:
    candidatos = [
        d
        for d in (disciplinas or [])
        if d.get("disciplina") == disciplina and d.get("turma") == turma
    ]
    if not candidatos:
        return None
    return max(
        candidatos,
        key=lambda item: (
            _pontuacao_config_cadastro(item),
            len(str(item.get("arquivo") or item.get("arquivo_modelo") or "")),
        ),
    )

def _abrir_cadastro_com_filtros(professor: str, disciplina: str, turma: str) -> None:
    st.session_state["modo_tela"] = "Cadastro"
    st.session_state["cadastro_filtro_professor"] = professor
    st.session_state["cadastro_filtro_disciplina"] = disciplina
    st.session_state["cadastro_busca"] = turma

# [CORREÇÃO B2] Definição morta de _falhas_ia() removida.
# A versão canônica é _falhas_ia_atualizadas que delega para listar_falhas_ia().
def _falhas_ia_atualizadas(aulas, exigir_ia: bool = True) -> list[str]:
    return listar_falhas_ia(aulas, exigir_ia=exigir_ia)


_falhas_ia = _falhas_ia_atualizadas


def _extrair_primeiro_texto_metodologia(aula) -> str:
    metodologia = aula.get("metodologia") or []
    if not metodologia:
        return ""

    primeiro_bloco = metodologia[0]
    return primeiro_bloco.get("texto", "") if isinstance(primeiro_bloco, dict) else str(primeiro_bloco)

def _salvar_pdf_temporario(pdf_file) -> str:
    """Valida o upload e o guarda em um diretório temporário exclusivo."""
    nome_original = getattr(pdf_file, "name", "aula.pdf")
    try:
        pdf_file.seek(0)
    except Exception:
        pass
    if hasattr(pdf_file, "getvalue"):
        conteudo = pdf_file.getvalue()
    else:
        conteudo = pdf_file.read()
    return str(salvar_pdf_upload_temporario(conteudo, nome_original))


def _preparar_pdf_para_processamento(pdf_file) -> tuple[str, bool]:
    """Retorna o caminho do PDF e se ele deve ser apagado ao final.

    No modo automatico, o arquivo ja existe na pasta base configurada para PDFs. Usar esse caminho
    real preserva os JSONs, DOCXs de referencia e hashes da pasta original.
    No upload manual, criamos uma copia temporaria como antes.
    """
    caminho_local = getattr(pdf_file, "path", None)
    if caminho_local:
        caminho = Path(caminho_local)
        if caminho.exists():
            return str(caminho), False

    return _salvar_pdf_temporario(pdf_file), True


def _disciplina_suporta_modalidade_eja(disciplina: str) -> bool:
    texto = _normalizar_texto_simples(disciplina).replace("-", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto in {
        "BIOLOGIA",
        "BIOLOGIA EJA",
        "INGLES",
        "LINGUA INGLESA",
        "LIDERANCA E ORATORIA",
        "LIDERANCA ORATORIA",
        "QUIMICA",
        "QUIMICA EJA",
    }


def _sincronizar_datas_horarios_mes(
    config: dict,
    mes: str,
    professor: str,
    disciplina: str,
    turma: str,
    extensao: int = 0,
    antecipacao: int = 0,
    datas_sem_aula: list[date] | set[date] | None = None,
) -> list[dict]:
    itens = _filtrar_datas_sem_aula(
        _datas_horarios_do_mes(config, mes, turma, extensao=extensao, antecipacao=antecipacao),
        datas_sem_aula,
    )
    if not itens:
        for idx in range(40):
            for prefixo in ("data_aula_", "horario_aula_", "tipo_horario_aula_"):
                st.session_state.pop(f"{prefixo}{idx}", None)
        return []

    def _serializar_horario(item: dict) -> str:
        horario = item.get("horario")
        aula = item.get("aula")
        if isinstance(horario, (tuple, list)):
            return ":".join(str(parte) for parte in horario)
        return str(aula or horario or "")

    agenda = "|".join(f"{item['data'].isoformat()}:{_serializar_horario(item)}" for item in itens)
    cadastro = f"{config.get('dia_semana', '')}|{config.get('horario', '')}|{config.get('aulas_semana', '')}"
    datas_bloqueadas = ",".join(sorted(dt.isoformat() for dt in set(datas_sem_aula or [])))
    assinatura = f"{professor}|{disciplina}|{turma}|{mes}|{extensao}|{antecipacao}|{cadastro}|{agenda}|{datas_bloqueadas}"
    if st.session_state.get("agenda_mes_assinatura") == assinatura:
        return itens

    st.session_state["agenda_mes_assinatura"] = assinatura
    for idx, item in enumerate(itens):
        horario = item.get("horario")
        st.session_state[f"data_aula_{idx}"] = item["data"]
        if isinstance(horario, tuple):
            st.session_state[f"horario_aula_{idx}"] = horario
            st.session_state[f"tipo_horario_aula_{idx}"] = _tipo_horario(horario)

    for idx in range(len(itens), 40):
        for prefixo in ("data_aula_", "horario_aula_", "tipo_horario_aula_"):
            st.session_state.pop(f"{prefixo}{idx}", None)
    return itens




def _sincronizar_datas_horarios_mes_turma2(
    config: dict,
    mes: str,
    professor: str,
    disciplina: str,
    turma: str,
    extensao: int = 0,
    antecipacao: int = 0,
    datas_sem_aula: list[date] | set[date] | None = None,
) -> list[dict]:
    """Versão da sincronização de datas/horários dedicada à 2ª turma (chaves prefixadas com 'turma2_')."""
    itens = _filtrar_datas_sem_aula(
        _datas_horarios_do_mes(config, mes, turma, extensao=extensao, antecipacao=antecipacao),
        datas_sem_aula,
    )
    if not itens:
        for idx in range(40):
            for prefixo in ("turma2_data_aula_", "turma2_horario_aula_", "turma2_tipo_horario_aula_"):
                st.session_state.pop(f"{prefixo}{idx}", None)
        return []

    def _serializar_horario_t2(item: dict) -> str:
        horario = item.get("horario")
        aula = item.get("aula")
        if isinstance(horario, (tuple, list)):
            return ":".join(str(parte) for parte in horario)
        return str(aula or horario or "")

    agenda = "|".join(f"{item['data'].isoformat()}:{_serializar_horario_t2(item)}" for item in itens)
    cadastro = f"{config.get('dia_semana', '')}|{config.get('horario', '')}|{config.get('aulas_semana', '')}"
    datas_bloqueadas = ",".join(sorted(dt.isoformat() for dt in set(datas_sem_aula or [])))
    assinatura = f"turma2|{professor}|{disciplina}|{turma}|{mes}|{extensao}|{antecipacao}|{cadastro}|{agenda}|{datas_bloqueadas}"
    if st.session_state.get("agenda_mes_assinatura_turma2") == assinatura:
        return itens

    st.session_state["agenda_mes_assinatura_turma2"] = assinatura
    for idx, item in enumerate(itens):
        horario = item.get("horario")
        st.session_state[f"turma2_data_aula_{idx}"] = item["data"]
        if isinstance(horario, tuple):
            st.session_state[f"turma2_horario_aula_{idx}"] = horario
            st.session_state[f"turma2_tipo_horario_aula_{idx}"] = _tipo_horario(horario)

    for idx in range(len(itens), 40):
        for prefixo in ("turma2_data_aula_", "turma2_horario_aula_", "turma2_tipo_horario_aula_"):
            st.session_state.pop(f"{prefixo}{idx}", None)
    return itens

def _config_agenda_a_partir_do_modelo(modelo_bytes: bytes | None) -> dict:
    if not modelo_bytes:
        return {}
    datas_horarios = extrair_datas_horarios_de_bytes(modelo_bytes)
    if not datas_horarios:
        return {}
    dias = []
    horarios = []
    for item in datas_horarios:
        data_aula = item.get("data")
        if hasattr(data_aula, "weekday"):
            dia_nome = DIAS_SEMANA_CADASTRO[data_aula.weekday()].upper()
            if dia_nome not in dias:
                dias.append(dia_nome)
        trecho_horario = " ".join(str(item.get(chave) or "").strip() for chave in ("horario", "aula")).strip()
        if trecho_horario and trecho_horario not in horarios:
            horarios.append(trecho_horario)
    return {
        "datas_horarios": datas_horarios,
        "dia_semana": " - ".join(dias),
        "horario": ", ".join(horarios),
        "repetir_modelo_semanal": True,
    }


def _inicio_semana(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())

def _tamanho_bloco_primeira_semana(datas: list[date]) -> int:
    """Retorna o número de aulas por semana (padrão semanal).

    Usa os dias-da-semana únicos presentes em TODAS as datas para determinar
    o tamanho do bloco semanal. Isso evita que feriados na 1ª semana reduzam
    o bloco incorretamente (ex: quinta feriada faz o sistema achar que a semana
    tem só terças).
    """
    if not datas:
        return 0
    # Coletar dias da semana únicos em todo o conjunto (não só na 1ª semana)
    dias_unicos = set()
    for dt in datas:
        dias_unicos.add(dt.weekday())
    bloco = len(dias_unicos)
    return max(1, bloco)

def _eh_data_antecipacao(data_aula: date, mes: str, antecipacao_mes: int) -> bool:
    if not mes or antecipacao_mes <= 0:
        return False
    ano = date.today().year
    mes_num = _mes_numero_app(mes)
    inicio_mes_oficial = date(ano, mes_num, 1)
    return data_aula < inicio_mes_oficial


_PERFIS_PORTUGUES_PERMITEM_SEM_PDF = {
    "lingua_portuguesa_ef",
    "lingua_portuguesa_em",
    "leitura_redacao",
    "matematica",
    "ciencias_ef",
    "biologia",
    "quimica",
    "fisica",
    "historia",
    "geografia",
    "ingles",
    "arte",
    "educacao_financeira",
    "tecnologia_inovacao",
    "sociologia",
    "orientacao_estudos",
    "lideranca_oratoria",
    "geral",
}


def _permite_um_dia_sem_pdf(
    disciplina: str,
    turma: str = "",
    modo_eja: bool = False,
    modo_cdp: bool = False,
) -> bool:
    """Verifica se a disciplina/modalidade permite a opção de deixar 1 dia da semana sem PDF.

    Permitido em Artes e demais disciplinas regulares, EXCETO:
    - Projeto de Vida
    - Aprofundamento em Biologia
    - Aprofundamento em Geografia
    - Nenhuma disciplina do CDP
    - Nenhuma disciplina do EJA
    """
    if modo_eja or modo_cdp:
        return False

    disc_str = str(disciplina or "").strip()
    if not disc_str:
        return False

    disc_norm = re.sub(r"\s+", " ", disc_str).lower()
    disc_norm_sem_acento = (
        unicodedata.normalize("NFKD", disc_norm).encode("ASCII", "ignore").decode("ascii")
    )

    # 1. Bloquear CDP ou EJA no nome da disciplina
    if "cdp" in disc_norm_sem_acento or "eja" in disc_norm_sem_acento:
        return False

    # 2. Bloquear Projeto de Vida
    if "projeto" in disc_norm_sem_acento and "vida" in disc_norm_sem_acento:
        return False
    try:
        if perfil_disciplina(disc_str, turma=turma) == "projeto_de_vida":
            return False
    except Exception:
        pass

    # 3. Bloquear Aprofundamento em Biologia
    if "aprofundamento" in disc_norm_sem_acento and "biologia" in disc_norm_sem_acento:
        return False

    # 4. Bloquear Aprofundamento em Geografia
    if "aprofundamento" in disc_norm_sem_acento and "geografia" in disc_norm_sem_acento:
        return False

    return True


def _permite_um_dia_sem_pdf_portugues(disciplina: str, turma: str = "") -> bool:
    return _permite_um_dia_sem_pdf(disciplina, turma=turma)


_PERFIS_SEMANAIS_SEM_PDF = {
    "lingua_portuguesa_ef",
    "lingua_portuguesa_em",
    "leitura_redacao",
    "matematica",
    "ciencias_ef",
}


def _frequencia_dia_sem_pdf(disciplina: str, turma: str = "") -> str:
    """Retorna 'semanal' se a disciplina usa 1 dia sem PDF por semana (ex: Português, Matemática, Ciências),

    ou 'quinzenal' se a disciplina usa 1 dia sem PDF a cada 15 dias (ex: Arte, Biologia, Geografia, etc.).
    """
    try:
        if perfil_disciplina(disciplina, turma=turma) in _PERFIS_SEMANAIS_SEM_PDF:
            return "semanal"
    except Exception:
        disciplina_norm = re.sub(r"\s+", " ", str(disciplina or "")).strip().lower()
        if any(term in disciplina_norm for term in ["portugu", "reda", "leitura", "matem", "cienc", "cien"]):
            return "semanal"

    return "quinzenal"


def _eh_data_sem_pdf(
    data_aula: date | None,
    dia_sem_pdf_semana: int | None,
    datas_agenda: list[date] | None = None,
    frequencia: str = "semanal",
) -> bool:
    """Verifica se uma data de aula específica deve ficar sem PDF conforme a frequência (semanal ou quinzenal)."""
    if not isinstance(data_aula, date) or dia_sem_pdf_semana is None:
        return False

    if data_aula.weekday() != dia_sem_pdf_semana:
        return False

    if frequencia != "quinzenal":
        return True

    # Para frequência quinzenal (a cada 15 dias):
    # Identificar a ordem relativa dessa data entre todas as datas da agenda no mesmo dia da semana
    if not datas_agenda:
        return True

    datas_dia = sorted(
        list(dict.fromkeys(d for d in datas_agenda if isinstance(d, date) and d.weekday() == dia_sem_pdf_semana))
    )
    if data_aula not in datas_dia:
        return True

    idx_data = datas_dia.index(data_aula)
    # A cada 15 dias (semanas alternadas): ocorrências em índices 0, 2, 4... ficam sem PDF
    return idx_data % 2 == 0


def _eh_horario_duplo(item=None, tipo_horario_str: str | None = None) -> bool:
    """Verifica se um item de horário ou string representa uma aula dupla."""
    if tipo_horario_str == "Dupla":
        return True
    if item in HORARIOS_DUPLAS:
        return True
    if isinstance(item, (tuple, list)):
        texto = " ".join(str(x) for x in item).lower()
        if " e " in texto or "dupla" in texto:
            return True
    elif isinstance(item, str):
        texto = item.lower()
        if " e " in texto or "dupla" in texto or "1ª e 2ª" in texto or "3ª e 4ª" in texto or "6ª e 7ª" in texto or "8ª e 9ª" in texto:
            return True
    return False


def _eh_aula_sem_pdf(
    idx: int,
    data_aula: date | None,
    dia_sem_pdf_semana: int | None,
    datas_agenda: list[date] | None = None,
    frequencia: str = "semanal",
    modo_aula_dupla: str = "uma_aula",
    eh_horario_duplo: bool = False,
) -> bool:
    """Verifica se uma aula específica (pelo índice e data) deve ficar sem PDF."""
    if not isinstance(data_aula, date) or dia_sem_pdf_semana is None:
        return False

    if not _eh_data_sem_pdf(data_aula, dia_sem_pdf_semana, datas_agenda=datas_agenda, frequencia=frequencia):
        return False

    if not datas_agenda:
        return not (eh_horario_duplo and modo_aula_dupla == "uma_aula")

    # Identificar todas as aulas registradas no mesmo dia de data_aula
    indices_do_dia = [i for i, d in enumerate(datas_agenda) if d == data_aula]

    # Caso 1: Há múltiplos cards/linhas na mesma data (ex: 2 cards na mesma terça-feira)
    if len(indices_do_dia) > 1:
        if modo_aula_dupla == "uma_aula":
            # A 1ª aula do dia (posição 0) fica COM PDF (False)
            # As demais aulas do dia (posição > 0) ficam SEM PDF (True)
            posicao_no_dia = indices_do_dia.index(idx) if idx in indices_do_dia else 0
            return posicao_no_dia > 0
        else:
            return True

    # Caso 2: Há apenas UM card/linha nesta data (len(indices_do_dia) == 1)
    # Se este card for uma AULA DUPLA (horário duplo) e o modo for "uma_aula":
    if eh_horario_duplo:
        if modo_aula_dupla == "uma_aula":
            # 1 das 2 aulas é com PDF -> este card PRECISA receber PDF (retorna False)
            return False
        else:
            # Ambas as aulas da aula dupla ficam sem PDF (retorna True)
            return True

    # Aula simples e única no dia: fica sem PDF (retorna True)
    return True


def _eh_bloco_sem_pdf(aula: dict) -> bool:
    return bool((aula or {}).get("bloco_sem_pdf"))


def _filtrar_aulas_com_pdf_obrigatorio(
    aulas_envio: list[dict],
    mes: str = "",
    antecipacao_mes: int = 0,
    deixar_antecipacao_vazia: bool = False,
) -> list[dict]:
    aulas_validas = []
    for aula in aulas_envio or []:
        if deixar_antecipacao_vazia and _eh_data_antecipacao(aula["data"], mes, antecipacao_mes):
            continue
        if _eh_bloco_sem_pdf(aula):
            continue
        aulas_validas.append(aula)
    return aulas_validas


def _opcoes_dia_sem_pdf(datas_horarios_mes: list[dict] | None = None) -> list[tuple[int, str]]:
    dias_presentes = []
    for entrada in datas_horarios_mes or []:
        data_atual = entrada.get("data")
        if isinstance(data_atual, date):
            dia = data_atual.weekday()
            if dia not in dias_presentes:
                dias_presentes.append(dia)
    base = dias_presentes or list(range(7))
    return [(dia, DIAS_SEMANA_COMPLETOS[dia]) for dia in base]

def validar_entrada(
    modelo_bytes, disciplina: str, disciplina_config, aulas_envio,
    professor: str, turma: str, bimestre: str, mes: str,
    aulas_previstas_manual: str, pdfs_enviados: int = 0, pdfs_necessarios: int = 0,
    deixar_antecipacao_vazia: bool = False, antecipacao_mes: int = 0,
) -> str:
    disciplina_norm = re.sub(r"\s+", " ", str(disciplina or "")).strip().lower()
    orientacao_estudos = "orienta" in disciplina_norm and "estudo" in disciplina_norm
    if not modelo_bytes:
        return "Selecione ou envie o modelo DOCX."
    if not disciplina.strip():
        return "Selecione ou informe a disciplina."
    campos_obrigatorios = []
    if not (professor or "").strip(): campos_obrigatorios.append("Nome do professor")
    if not (turma or "").strip(): campos_obrigatorios.append("Turma")
    if not (bimestre or "").strip(): campos_obrigatorios.append("Bimestre")
    if not (mes or "").strip(): campos_obrigatorios.append("Mês")
    if not (aulas_previstas_manual or "").strip(): campos_obrigatorios.append("Aulas na semana")
    if campos_obrigatorios:
        return "Preencha os campos obrigatórios antes de gerar o plano: " + ", ".join(campos_obrigatorios) + "."
    if disciplina_config.exige_pdf and not aulas_envio:
        return "Envie os PDFs das aulas para gerar o plano."
    
    aulas_obrigatorias = _filtrar_aulas_com_pdf_obrigatorio(
        aulas_envio,
        mes=mes,
        antecipacao_mes=antecipacao_mes,
        deixar_antecipacao_vazia=deixar_antecipacao_vazia,
    )
    pdf_unico_orientacao = bool(orientacao_estudos and pdfs_enviados == 1 and pdfs_necessarios >= 1)
    if disciplina_config.exige_pdf and pdfs_necessarios and pdfs_enviados != pdfs_necessarios and not pdf_unico_orientacao:
        return f"Quantidade de PDFs incorreta: foram adicionados {pdfs_enviados}, mas o plano possui {pdfs_necessarios} linha(s)."
    if disciplina_config.exige_pdf and any(not aula["pdf"] for aula in aulas_obrigatorias):
        return "Preencha data, horário e PDF em todas as aulas cadastradas do mês oficial."
    return ""

def validar_aulas_secundarias(gerar_turma_espelho: bool, turma_espelho: str, aulas_envio_espelho, exige_pdf: bool) -> str:
    if not gerar_turma_espelho: return ""
    if not (turma_espelho or "").strip(): return "Preencha a 2ª série/turma antes de gerar os planos em conjunto."
    if exige_pdf and any(not aula["pdf"] for aula in aulas_envio_espelho if not _eh_bloco_sem_pdf(aula)): return "Preencha data, horário e PDF da 2ª turma."
    return ""

def _grupos_pdf_por_aula(aulas_envio: list[dict]) -> list[dict]:
    grupos = []
    idx = 0
    while idx < len(aulas_envio):
        aula = aulas_envio[idx]
        if _eh_bloco_sem_pdf(aula):
            idx += 1
            continue
        proxima_aula_valida = idx + 1 < len(aulas_envio) and not _eh_bloco_sem_pdf(aulas_envio[idx + 1])
        dividir = bool(aula.get("dividir_pdf")) and proxima_aula_valida
        if dividir and idx + 1 < len(aulas_envio):
            grupos.append({"indices": [idx, idx + 1], "dividir": True})
            idx += 2
            continue
        grupos.append({"indices": [idx], "dividir": False})
        idx += 1
    return grupos

def _aplicar_pdfs_a_grupos(aulas_envio: list[dict], pdfs_aulas_files, replicar_pdf_unico: bool = False) -> tuple[list[dict], int]:
    grupos = _grupos_pdf_por_aula(aulas_envio)
    for grupo_idx, grupo in enumerate(grupos):
        if replicar_pdf_unico and len(pdfs_aulas_files or []) == 1:
            pdf = pdfs_aulas_files[0]
        else:
            pdf = pdfs_aulas_files[grupo_idx] if grupo_idx < len(pdfs_aulas_files) else None
        for indice in grupo["indices"]:
            aulas_envio[indice]["pdf"] = pdf
            aulas_envio[indice]["grupo_pdf"] = grupo_idx
            aulas_envio[indice]["dividir_pdf"] = grupo["dividir"]
    return aulas_envio, len(grupos)




def _estimar_pdfs_por_estado(num_rows: int, dividir_metodologia: bool, key_prefix: str = "", lista_aulas: list = None) -> int:
    num_rows = int(num_rows or 0)
    if num_rows <= 0:
        return 0
    if not dividir_metodologia:
        return num_rows

    aulas_simuladas = []
    for idx in range(num_rows):
        chave = f"{key_prefix}dividir_pdf_aula_{idx}"
        dividir_pdf = st.session_state.get(chave, _divisao_pdf_padrao(idx, num_rows, lista_aulas))
        aulas_simuladas.append({"dividir_pdf": bool(dividir_pdf)})
    return len(_grupos_pdf_por_aula(aulas_simuladas))

def _status_visual_aula(idx: int, num_rows: int, bloqueado: bool, continuidade_anterior: bool, dividir_pdf_ativo: bool) -> tuple:
    badges = []
    if continuidade_anterior:
        badges.extend(['<span class="lesson-badge lesson-badge--info">2o momento</span>', '<span class="lesson-badge lesson-badge--soft">PDF compartilhado</span>'])
        return "lesson-card lesson-card--continuation", "Continuacao da aula anterior", "Esta linha recebe a segunda parte da metodologia e usa o mesmo material.", badges
    if dividir_pdf_ativo:
        badges.extend(['<span class="lesson-badge lesson-badge--success">PDF em 2 aulas</span>', '<span class="lesson-badge lesson-badge--soft">1o momento</span>'])
        return "lesson-card lesson-card--paired", "Material compartilhado com a proxima aula", "Reaproveita o PDF na proxima linha.", badges
    if bloqueado:
        badges.append('<span class="lesson-badge lesson-badge--neutral">Repeticao semanal</span>')
        return "lesson-card lesson-card--locked", "Aula preenchida pela repeticao automatica", "Protegida para manter a sequencia.", badges
    if idx == num_rows - 1:
        badges.append('<span class="lesson-badge lesson-badge--neutral">Ultima aula</span>')
        return "lesson-card", "Configuracao individual", "Ajuste a data e o horario normalmente.", badges
    return "lesson-card", "Configuracao individual", "Defina a data, o horario e se o PDF continua.", badges

def _coletar_aulas_envio(
    num_rows: int,
    pdfs_aulas_files,
    dividir_metodologia: bool,
    auto_repetir_semana: bool,
    replicar_pdf_unico: bool = False,
    key_prefix: str = "",
    titulo_secao: str = "",
    modo_upload_individual: bool = False,
    preservar_datas_sincronizadas: bool = False,
    sequencia_pdf_esperada: list[int] | None = None,
    deixar_antecipacao_vazia: bool = False,
    mes: str = "",
    antecipacao_mes: int = 0,
    permitir_um_dia_sem_pdf: bool = False,
    dia_sem_pdf_semana: int | None = None,
    frequencia_dia_sem_pdf: str = "semanal",
    modo_aula_dupla: str = "uma_aula",
):
    aulas_envio = []
    datas_cache = []
    horarios_cache = []

    for idx in range(num_rows):
        chave_data = f"{key_prefix}data_aula_{idx}"
        chave_horario = f"{key_prefix}horario_aula_{idx}"
        data_fallback = st.session_state.get(f"{key_prefix}data_aula_{idx}", date.today())
        horario_fallback = st.session_state.get(f"{key_prefix}horario_aula_{idx}", HORARIOS_AULA[0])
        if chave_data not in st.session_state: st.session_state[chave_data] = data_fallback
        if chave_horario not in st.session_state: st.session_state[chave_horario] = horario_fallback
        datas_cache.append(st.session_state[chave_data])
        horarios_cache.append(st.session_state[chave_horario])

    bloco_semana = 0 if preservar_datas_sincronizadas else _tamanho_bloco_primeira_semana(datas_cache)
    if (
        auto_repetir_semana
        and not preservar_datas_sincronizadas
        and bloco_semana > 0
        and num_rows > bloco_semana
    ):
        # Construir padrão semanal a partir dos dias-da-semana únicos em TODAS as datas
        # (não apenas da 1ª semana, que pode estar incompleta por feriados)
        dias_vistos: dict[int, tuple] = {}  # dia_semana -> horário representativo
        for dt, hr in zip(datas_cache, horarios_cache):
            dia = dt.weekday()
            if dia not in dias_vistos:
                dias_vistos[dia] = hr
        padrao = sorted(dias_vistos.items())  # [(dia_semana, horario), ...]

        # Para cada aula, determinar: qual dia da semana e qual semana
        for idx in range(num_rows):
            pos_no_padrao = idx % len(padrao)
            semana_num = idx // len(padrao)
            dia_semana_alvo, horario_padrao = padrao[pos_no_padrao]

            # Encontrar a data real: semana_num * 7 dias a partir da 1ª ocorrência desse dia
            # Usar a primeira data do padrão como âncora para a segunda-feira da semana 0
            data_ancora = next(
                (dt for dt in datas_cache if dt.weekday() == dia_semana_alvo),
                datas_cache[0]
            )
            segunda_ancora = data_ancora - timedelta(days=data_ancora.weekday())
            segunda_alvo = segunda_ancora + timedelta(weeks=semana_num)
            nova_data = segunda_alvo + timedelta(days=dia_semana_alvo)

            st.session_state[f"{key_prefix}data_aula_{idx}"] = nova_data
            st.session_state[f"{key_prefix}horario_aula_{idx}"] = horario_padrao
            st.session_state[f"{key_prefix}tipo_horario_aula_{idx}"] = _tipo_horario(horario_padrao)

    if titulo_secao: st.markdown(f"**{titulo_secao}**")

    aula_valida_count = 0
    for idx in range(num_rows):
        chave_data = f"{key_prefix}data_aula_{idx}"
        chave_horario = f"{key_prefix}horario_aula_{idx}"
        chave_tipo = f"{key_prefix}tipo_horario_aula_{idx}"
        chave_dividir = f"{key_prefix}dividir_pdf_aula_{idx}"
        data_fallback = st.session_state.get(chave_data, date.today())
        horario_fallback = st.session_state.get(chave_horario, HORARIOS_AULA[0])
        if chave_data not in st.session_state: st.session_state[chave_data] = data_fallback
        if chave_horario not in st.session_state: st.session_state[chave_horario] = horario_fallback
        
        horario_padrao_item = st.session_state.get(chave_horario, horario_fallback)
        bloqueado = (not preservar_datas_sincronizadas) and auto_repetir_semana and idx >= bloco_semana
        continuidade_anterior = bool(dividir_metodologia and idx > 0 and st.session_state.get(f"{key_prefix}dividir_pdf_aula_{idx - 1}", False))
        dividir_pdf_ativo = bool(dividir_metodologia and st.session_state.get(chave_dividir, False))
        card_class, status_titulo, status_texto, badges = _status_visual_aula(idx, num_rows, bloqueado, continuidade_anterior, dividir_pdf_ativo)
        
        eh_antecipacao_vazia = deixar_antecipacao_vazia and _eh_data_antecipacao(data_fallback, mes, antecipacao_mes)
        if eh_antecipacao_vazia:
            badges_html = "".join([f'<span class="lesson-badge lesson-badge--index" style="background:var(--pl-bg-soft); color:var(--pl-text-soft); border-color:var(--pl-border);">Vazia</span>'] + badges)
        else:
            aula_valida_count += 1
            badges_html = "".join([f'<span class="lesson-badge lesson-badge--index">Aula {aula_valida_count}</span>'] + badges)
            
        numero_pdf_esperado = None
        if not dividir_metodologia and sequencia_pdf_esperada and idx < len(sequencia_pdf_esperada):
            numero_pdf_esperado = sequencia_pdf_esperada[idx]

        with st.container(border=True):
            st.markdown(
                """
                <div class="{card_class}">
                    <div class="lesson-header" style="margin-bottom: 5px;">
                        <div>
                            <div class="lesson-title" style="font-size: 1.1em; font-weight: bold;">{status_titulo}</div>
                            <div class="lesson-subtitle" style="font-size: 0.9em; opacity: 0.8;">{status_texto}</div>
                        </div>
                        <div class="lesson-badges">{badges_html}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if numero_pdf_esperado:
                st.caption(f"PDF esperado neste bloco: AULA {int(numero_pdf_esperado)}")
            col_data, col_horario = st.columns([1, 1])
            with col_data:
                data_label = _rotulo_data_aula_com_dia(st.session_state.get(chave_data, data_fallback))
                st.markdown(
                    f'<div class="lesson-field-label">Data da aula</div><div class="lesson-field-help">{data_label}</div>',
                    unsafe_allow_html=True,
                )
                data_aula = st.date_input(
                    "Data da aula",
                    format="DD/MM/YYYY",
                    key=chave_data,
                    disabled=bloqueado,
                    label_visibility="collapsed",
                )
                st.caption(f"Dia da semana: {DIAS_SEMANA_COMPLETOS[data_aula.weekday()]}")
            with col_horario:
                tipo_padrao = _tipo_horario(horario_padrao_item)
                if chave_tipo not in st.session_state or st.session_state[chave_tipo] not in ["Simples", "Dupla"]:
                    st.session_state[chave_tipo] = tipo_padrao
                tipo_horario = st.radio("Tipo de horário", ["Simples", "Dupla"], horizontal=True, key=chave_tipo, disabled=bloqueado)
                
                opcoes_horario = list(HORARIOS_SIMPLES if tipo_horario == "Simples" else HORARIOS_DUPLAS)
                horario_atual = st.session_state.get(chave_horario)
                if horario_atual not in opcoes_horario and isinstance(horario_atual, tuple):
                    opcoes_horario.insert(0, horario_atual)
                if st.session_state.get(chave_horario) not in opcoes_horario:
                    st.session_state[chave_horario] = opcoes_horario[0]
                horario_aula = st.selectbox("Horário", opcoes_horario, format_func=_rotulo_horario, key=chave_horario, disabled=bloqueado)

        eh_bloco_sem_pdf = bool(
            permitir_um_dia_sem_pdf
            and dia_sem_pdf_semana is not None
            and _eh_aula_sem_pdf(
                idx,
                data_aula,
                dia_sem_pdf_semana,
                datas_agenda=datas_cache,
                frequencia=frequencia_dia_sem_pdf,
                modo_aula_dupla=modo_aula_dupla,
                eh_horario_duplo=_eh_horario_duplo(horario_aula, tipo_horario),
            )
        )
        st.divider()
        dividir_pdf = False
        if dividir_metodologia:
            sugestao_dividir = _divisao_pdf_padrao(idx, num_rows)
            if chave_dividir not in st.session_state: st.session_state[chave_dividir] = sugestao_dividir
            if continuidade_anterior or eh_bloco_sem_pdf: st.session_state[chave_dividir] = False
            # Corrigido: bloqueado não impede o checkbox quando dividir_metodologia está ativo
            dividir_pdf = st.checkbox("Usar o mesmo PDF na próxima", key=chave_dividir, disabled=(bloqueado and not dividir_metodologia) or idx == num_rows - 1 or continuidade_anterior or eh_bloco_sem_pdf)
            if continuidade_anterior: st.caption("Esta já é continuação da anterior.")

        # Upload individual por aula
        pdf_individual = None
        pdf_individual_2 = None
        eh_antecipacao_vazia = deixar_antecipacao_vazia and _eh_data_antecipacao(data_aula, mes, antecipacao_mes)
        if modo_upload_individual:
            if eh_antecipacao_vazia:
                st.caption("ℹ️ Aula na semana extra (bloco configurado para vir vazio).")
            elif eh_bloco_sem_pdf:
                st.caption("ℹ️ Este dia da semana foi configurado para ficar sem PDF neste plano.")
            elif continuidade_anterior:
                st.caption("📎 PDF compartilhado com a aula anterior.")
            else:
                chave_pdf_ind = f"{key_prefix}pdf_individual_aula_{idx}"
                aceitar_multiplos = st.session_state.get(chave_tipo, "Simples") == "Dupla"
                uploaded = st.file_uploader(f"PDF da Aula {idx + 1}", type=["pdf"], accept_multiple_files=aceitar_multiplos, key=chave_pdf_ind, label_visibility="collapsed")
                
                if aceitar_multiplos and isinstance(uploaded, list):
                    # Organizar PDFs múltiplos pelo número para evitar inversão por ordem alfabética (ex: AULA 3 antes de Trilha)
                    uploaded_sorted = ordenar_pdfs_por_numero(uploaded)
                    if len(uploaded_sorted) >= 2:
                        pdf_individual = uploaded_sorted[0]
                        pdf_individual_2 = uploaded_sorted[1]
                    elif len(uploaded_sorted) == 1:
                        pdf_individual = uploaded_sorted[0]
                else:
                    pdf_individual = uploaded
                    
                if isinstance(uploaded, list) and len(uploaded) > 0:
                    st.caption(f"✅ {len(uploaded)} arquivo(s)")
                elif uploaded and not isinstance(uploaded, list):
                    st.caption(f"✅ {uploaded.name}")
                else:
                    msg = "⬆️ Adicione até 2 PDFs" if aceitar_multiplos else "⬆️ Adicione o PDF desta aula"
                    st.caption(msg)

        if pdf_individual_2:
            turno, aulas_numeros = _turno_e_aulas_de_horario(horario_aula)
            sugestoes = [_montar_horario_flexivel(turno, [a]) for a in aulas_numeros if a]
            if len(sugestoes) >= 2:
                h1, h2 = sugestoes[0], sugestoes[1]
            else:
                horario_str = horario_aula[1] if isinstance(horario_aula, tuple) and len(horario_aula) > 1 else str(horario_aula)
                match = re.search(r"(\d+)(?:[ªºoa])?\s*e\s*(\d+)(?:[ªºoa])?\s*aula", horario_str, flags=re.IGNORECASE)
                a1, a2 = match.groups() if match else ("1", "2")
                horas = re.findall(r"\b\d{1,2}h\d{0,2}\b", str(horario_aula), flags=re.IGNORECASE)
                if len(horas) >= 2:
                    h1, h2 = (horas[0], f"{a1}ª aula"), (horas[1], f"{a2}ª aula")
                elif len(horas) == 1:
                    h1, h2 = (horas[0], f"{a1}ª aula"), (horas[0], f"{a2}ª aula")
                elif match:
                    h1, h2 = f"{a1}ª aula", f"{a2}ª aula"
                else:
                    h1, h2 = f"Aula 1 ({horario_str})", f"Aula 2 ({horario_str})"

            aulas_envio.append({"data": data_aula, "horario": h1, "pdf": pdf_individual, "dividir_pdf": False})
            aulas_envio.append({"data": data_aula, "horario": h2, "pdf": pdf_individual_2, "dividir_pdf": False})
        else:
            # Verificar se é aula dupla em dia sem PDF com modo "uma_aula":
            # neste caso, gerar dois registros separados (1 com PDF + 1 sem PDF),
            # para que o DOCX produza uma linha com conteúdo e uma linha em branco
            # abaixo (para preenchimento manual pelo professor), assim como acontece
            # quando o professor edita manualmente o plano.
            eh_dia_sem_pdf_base = bool(
                permitir_um_dia_sem_pdf
                and dia_sem_pdf_semana is not None
                and _eh_data_sem_pdf(
                    data_aula,
                    dia_sem_pdf_semana,
                    datas_agenda=datas_cache,
                    frequencia=frequencia_dia_sem_pdf,
                )
            )
            eh_aula_dupla_splittavel = (
                eh_dia_sem_pdf_base
                and _eh_horario_duplo(horario_aula, tipo_horario)
                and modo_aula_dupla == "uma_aula"
                and not eh_antecipacao_vazia
            )
            if eh_aula_dupla_splittavel:
                # Extrair os números individuais das aulas (ex: "1ª e 2ª aula" → "1" e "2")
                horario_str_dupla = (
                    horario_aula[1]
                    if isinstance(horario_aula, tuple) and len(horario_aula) > 1
                    else str(horario_aula)
                )
                match_dupla = re.search(
                    r"(\d+)(?:[ªºoa])?\s*e\s*(\d+)(?:[ªºoa])?\s*aula",
                    horario_str_dupla,
                    flags=re.IGNORECASE,
                )
                if match_dupla:
                    aula1_num, aula2_num = match_dupla.groups()
                    horario_com_pdf = f"{aula1_num}ª aula"
                    horario_sem_pdf = f"{aula2_num}ª aula"
                else:
                    horario_com_pdf = horario_str_dupla
                    horario_sem_pdf = horario_str_dupla
                # Registro 1: aula com conteúdo pedagógico (PDF)
                aulas_envio.append({
                    "data": data_aula,
                    "horario": horario_com_pdf,
                    "pdf": pdf_individual,
                    "dividir_pdf": False,
                    "bloco_sem_pdf": False,
                    "ordem_original": idx * 2,
                })
                # Registro 2: aula sem PDF (linha em branco para preenchimento manual)
                aulas_envio.append({
                    "data": data_aula,
                    "horario": horario_sem_pdf,
                    "pdf": None,
                    "dividir_pdf": False,
                    "bloco_sem_pdf": True,
                    "ordem_original": idx * 2 + 1,
                })
            else:
                aulas_envio.append({
                    "data": data_aula,
                    "horario": horario_aula,
                    "pdf": None if eh_bloco_sem_pdf else pdf_individual,
                    "dividir_pdf": False if eh_bloco_sem_pdf else dividir_pdf,
                    "bloco_sem_pdf": eh_bloco_sem_pdf,
                })

    if modo_upload_individual:
        # Propagar PDF para aulas de continuação (mesmo PDF da aula anterior)
        for i in range(1, len(aulas_envio)):
            if deixar_antecipacao_vazia and _eh_data_antecipacao(aulas_envio[i]["data"], mes, antecipacao_mes):
                continue
            if _eh_bloco_sem_pdf(aulas_envio[i]) or _eh_bloco_sem_pdf(aulas_envio[i - 1]):
                continue
            if aulas_envio[i - 1].get("dividir_pdf") and aulas_envio[i].get("pdf") is None:
                aulas_envio[i]["pdf"] = aulas_envio[i - 1]["pdf"]
                aulas_envio[i]["grupo_pdf"] = aulas_envio[i - 1].get("grupo_pdf")
                aulas_envio[i]["dividir_pdf"] = False
    else:
        # Organizar automaticamente os PDFs do upload em lote pela numeração da aula,
        # para que arquivos com prefixos como "TRILHA" não fiquem no final devido à ordem alfabética do navegador.
        pdfs_aulas_files = ordenar_pdfs_por_numero(pdfs_aulas_files)
        
        if deixar_antecipacao_vazia and antecipacao_mes > 0:
            aulas_antecipacao = [a for a in aulas_envio if _eh_data_antecipacao(a["data"], mes, antecipacao_mes)]
            aulas_oficiais = [a for a in aulas_envio if not _eh_data_antecipacao(a["data"], mes, antecipacao_mes)]
            _aplicar_pdfs_a_grupos(aulas_oficiais, pdfs_aulas_files, replicar_pdf_unico=replicar_pdf_unico)
            for a in aulas_antecipacao:
                a["pdf"] = None
                a["dividir_pdf"] = False
        else:
            aulas_envio, _ = _aplicar_pdfs_a_grupos(aulas_envio, pdfs_aulas_files, replicar_pdf_unico=replicar_pdf_unico)
    for ordem_original, aula in enumerate(aulas_envio):
        aula["ordem_original"] = ordem_original
    return aulas_envio


def _extrair_aulas_dos_pdfs(
    aulas_envio, disciplina: str, turma_atual: str, bimestre: str, modo_ia: str,
    modelo_openai: str, modelo_gemini: str, dividir_metodologia: bool,
    modalidade_eja: bool = False, usar_ae_priorizado: bool = False,
    progress_callback=None, professor: str = "",
    deixar_antecipacao_vazia: bool = False, mes: str = "", antecipacao_mes: int = 0,
):
    temp_paths = []
    caminhos_para_apagar = []
    try:
        dados_aulas = []
        avisos_ia = []
        
        eh_ant_vazia = deixar_antecipacao_vazia and antecipacao_mes > 0
        if eh_ant_vazia:
            aulas_antecipacao = [a for a in aulas_envio if _eh_data_antecipacao(a["data"], mes, antecipacao_mes)]
            aulas_base = [a for a in aulas_envio if not _eh_data_antecipacao(a["data"], mes, antecipacao_mes)]
        else:
            aulas_antecipacao = []
            aulas_base = aulas_envio

        aulas_sem_pdf = [a for a in aulas_base if _eh_bloco_sem_pdf(a)]
        aulas_processamento = [a for a in aulas_base if not _eh_bloco_sem_pdf(a)]

        grupos = _grupos_pdf_por_aula(aulas_processamento) if dividir_metodologia else [{"indices": [idx], "dividir": False} for idx in range(len(aulas_processamento))]
        dividir_por_pdf = []
        for grupo in grupos:
            aula_envio = aulas_processamento[grupo["indices"][0]]
            caminho_pdf, apagar_ao_final = _preparar_pdf_para_processamento(aula_envio["pdf"])
            temp_paths.append(caminho_pdf)
            if apagar_ao_final:
                caminhos_para_apagar.append(caminho_pdf)
            dividir_por_pdf.append(bool(grupo["dividir"]))
            
        for aula_envio in aulas_processamento:
            if disciplina and turma_atual and disciplina.lower() == "matemática" and ("6º/7º" in turma_atual.lower() or "8º/9º" in turma_atual.lower() or "1º/2º/3º e.m" in turma_atual.lower() or "multisseriado 1º" in turma_atual.lower()):
                dados_aulas.append({"data": aula_envio["data"].strftime("%d/%m"), "horario": ""})
            else:
                dados_aulas.append({"data": aula_envio["data"].strftime("%d/%m"), "horario": horario_para_plano(aula_envio["horario"])})

        aulas = []
        avisos_ae = []
        avisos_repeticao = []
        if aulas_processamento:
            aulas = processar_varios_pdfs(
                temp_paths, disciplina=disciplina, turma=turma_atual, bimestre=bimestre, usar_ia=modo_ia != "Sem IA",
                provedor_ia=modo_ia.lower(), modelo_ia=(modelo_openai if modo_ia == "OpenAI" else modelo_gemini) if modo_ia != "Sem IA" else "",
                dividir_metodologia=dividir_metodologia, dividir_por_pdf=dividir_por_pdf, modalidade_eja=modalidade_eja,
                progress_callback=progress_callback, professor=professor,
            )
            if not aulas: raise RuntimeError("Nenhuma aula foi extraída dos PDFs oficiais.")
            
            if modo_ia != "Sem IA":
                falhas_ia = _falhas_ia(aulas, exigir_ia=not eh_cdp_contextual(disciplina))
                if falhas_ia and len(falhas_ia) == len(aulas or []):
                    raise RuntimeError("Falha de IA detectada em todas as aulas oficiais:\n" + "\n".join(falhas_ia))
                aviso_ia = resumir_falhas_ia(falhas_ia)
                if aviso_ia:
                    avisos_ia.append(aviso_ia)
            
            for aula, dados in zip(aulas, dados_aulas): aula.update(dados)

            if usar_ae_priorizado:
                aulas, avisos_ae = aplicar_ae_priorizado_nas_aulas(
                    aulas,
                    disciplina=disciplina,
                    turma=turma_atual,
                    bimestre=bimestre,
                    caminho_planilha=str(st.session_state.get("caminho_ae_priorizado") or "").strip(),
                )
            cdp_contextual = eh_cdp_contextual(disciplina) or any(
                str(aula.get("contexto_metodologico") or "") == "cdp_eja"
                for aula in aulas
            )
            problemas_plano = validar_aulas_geradas(aulas, permitir_temas_repetidos=cdp_contextual, permitir_metodologia_simples=cdp_contextual or dividir_metodologia)
            
            problemas_bloqueantes = []
            for problema in problemas_plano:
                if "repetido de aula anterior" in str(problema).lower():
                    avisos_repeticao.append(problema)
                else:
                    problemas_bloqueantes.append(problema)
            if problemas_bloqueantes:
                raise ValueError("Problemas encontrados:\n" + "\n".join(problemas_bloqueantes))

        aulas_vazias = []
        for aula_envio in aulas_antecipacao + aulas_sem_pdf:
            horario_vazio = (
                disciplina and turma_atual and disciplina.lower() == "matemática" and (
                    "6º/7º" in turma_atual.lower()
                    or "8º/9º" in turma_atual.lower()
                    or "1º/2º/3º e.m" in turma_atual.lower()
                    or "multisseriado 1º" in turma_atual.lower()
                )
            )
            aulas_vazias.append({
                "tema": "",
                "conteudo": "",
                "aprendizagem": "",
                "metodologia": [],
                "acompanhamento": [],
                "acessibilidade": [],
                "ia_usada": False,
                "data": aula_envio["data"].strftime("%d/%m"),
                "horario": "" if horario_vazio else horario_para_plano(aula_envio["horario"]),
                "aula_vazia": True,
                "ordem_original": aula_envio.get("ordem_original", 0),
            })

        for aula, aula_envio in zip(aulas, aulas_processamento):
            aula["ordem_original"] = aula_envio.get("ordem_original", 0)

        aulas_completas = sorted(aulas_vazias + aulas, key=lambda item: item.get("ordem_original", 0))

        # Garantir numeração sequencial a partir da primeira aula válida (ignora as vazias do bloco de antecipação)
        contador = 1
        for aula in aulas_completas:
            if not aula.get("aula_vazia"):
                # Define explícito para o gerador DOCX não se perder
                aula["numero_aula"] = str(contador)
                contador += 1

        for aula in aulas_completas:
            metodologia = aula.get("metodologia", [])
            for i, item in enumerate(metodologia):
                if isinstance(item, dict) and "texto" in item:
                    item["texto"] = re.sub(r'\s+', ' ', re.sub(r'\(\s*\)', '', re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item["texto"]))).strip()
                elif isinstance(item, str):
                    metodologia[i] = re.sub(r'\s+', ' ', re.sub(r'\(\s*\)', '', re.sub(r'(?i)\s*(?:\(|-)?\s*\d+\s*min(?:uto)?s?(?:\))?', '', item))).strip()
                    
        return {
            "aulas": aulas_completas,
            "avisos_repeticao": avisos_repeticao,
            "avisos_ae": avisos_ae,
            "avisos_ia": avisos_ia
        }
    finally:
        for caminho_temp in caminhos_para_apagar:
            if caminho_temp:
                if not limpar_upload_temporario(caminho_temp):
                    logging.getLogger(__name__).warning(
                        "Não foi possível remover completamente o upload temporário: %s",
                        caminho_temp,
                    )

def _gerar_docx_cdp_final(modelo_bytes: bytes, escola: str, professor: str, disciplina: str, turma_atual: str, mes: str, bimestre: str, semana: str, observacao: str, aulas_previstas_manual: str, cdp_aula_inicial: int, turma_cdp: str = "", modo_ia: str = "Sem IA", modelo_openai: str = "", modelo_gemini: str = "", datas_horarios: list[dict] | None = None):
    docx_bytes = preencher_documento_cdp(
        BytesIO(modelo_bytes), escola=escola, professor=professor, turma=turma_atual, mes=mes, bimestre=bimestre,
        aula_inicial=int(cdp_aula_inicial or 1), fundamental=eh_cdp_fundamental(disciplina), multisseriada=eh_cdp_multisseriada(disciplina),
        serie_cdp=turma_cdp or "", usar_ia=modo_ia != "Sem IA", provedor_ia=modo_ia.lower() if modo_ia != "Sem IA" else "",
        modelo_ia=(modelo_openai if modo_ia == "OpenAI" else modelo_gemini) if modo_ia != "Sem IA" else "",
        datas_horarios=datas_horarios, semana=semana, observacao=observacao, aulas_previstas_manual=aulas_previstas_manual,
    )
    tipo = "CDP - Ciclo I" if eh_cdp_fundamental(disciplina) else "CDP/EJA Multisseriada"
    relatorio = f"Plano gerado em modo {tipo}.\nProfessor: {professor}\nDisciplina: {disciplina}\nTurma: {turma_atual}\nBimestre: {bimestre}\nMês: {mes}\nAula inicial CDP: {int(cdp_aula_inicial or 1)}\n"
    if turma_cdp: relatorio += f"Turma multisseriada: {turma_cdp}\n"
    if modo_ia != "Sem IA": relatorio += f"IA: {modo_ia}\n"
    return {"turma": turma_atual, "aulas": [], "docx_bytes": docx_bytes, "relatorio": relatorio, "ia_usada": modo_ia != "Sem IA"}

if not HABILITAR_REVISAO_POS_GERACAO:
    st.session_state["turmas_processadas"] = []
    st.session_state["avisos_processamento"] = []
    st.session_state.pop("revisao_token", None)
    _limpar_revisao_aulas()

st.markdown(HERO_CSS, unsafe_allow_html=True)

st.markdown(HERO_HTML, unsafe_allow_html=True)
st.markdown(STATS_HTML, unsafe_allow_html=True)
render_sidebar()

col_limpar, _ = st.columns([1, 5])
with col_limpar: st.button("Limpar dados da tela", type="secondary", on_click=limpar_dados_tela)

st.markdown(SECTION_HEADER_HTML, unsafe_allow_html=True)

from streamlit_option_menu import option_menu

modos_disponiveis = ["Planos gerais", "CDP-EF/EM", "EJA", "Cadastro", "Diagnóstico", "Histórico"]
if st.session_state.get("modo_tela") == "Geração em Lote":
    st.session_state["modo_tela"] = "Planos gerais"

# Sincroniza o modo_tela default a partir do session_state se existir
default_modo = st.session_state.get("modo_tela", "Planos gerais")
if default_modo not in modos_disponiveis:
    default_modo = "Planos gerais"
idx_default = modos_disponiveis.index(default_modo)

modo_tela = option_menu(
    menu_title=None,
    options=modos_disponiveis,
    icons=["file-earmark-text", "file-earmark-spreadsheet", "people", "person-badge", "tools", "clock-history"],
    menu_icon="cast",
    default_index=idx_default,
    orientation="horizontal",
    styles=OPTION_MENU_STYLES,
)
st.session_state["modo_tela"] = modo_tela

modo_cdp_dedicado = modo_tela == "CDP - Ciclo I"
modo_cdp_ef_em = modo_tela == "CDP-EF/EM"
modo_eja = modo_tela == "EJA"
modo_cadastro_professor = modo_tela == "Cadastro"
modo_diagnostico_modelos = modo_tela == "Diagnóstico"
modo_historico = modo_tela == "Histórico"

if modo_cadastro_professor: _renderizar_cadastro_professor(PROFESSORES_DB); st.stop()
if modo_diagnostico_modelos: _renderizar_diagnostico_modelos(); st.stop()
if modo_historico: _renderizar_historico(PROFESSORES_DB); st.stop()

TEMPLATES_DIR = TEMPLATES_DOCX_DIR
TEMPLATES_DIR.mkdir(exist_ok=True)
templates_disponiveis = [f.name for f in TEMPLATES_DIR.glob("*.docx")]

OPCAO_MODELO_AUTOMATICO = "Automático pelo professor"
modelo_bytes = None
modelo_automatico_arquivo = ""
modelo_automatico_template_id = ""
escolha_template = "MODELOCDP.docx" if modo_cdp_dedicado else OPCAO_MODELO_AUTOMATICO
pdfs_aulas_files = []

if modo_cdp_ef_em:
    st.info(
        "Aba CDP-EF/EM: geração de planos de aula sob metodologia tradicional (lousa, giz, livro, caderno) para salas multisseriadas, EJA e centro de detenção.",
        icon="🏢",
    )

if modo_eja:
    st.info(
        "Modalidade EJA: escolha Língua Inglesa, Biologia, Liderança e Oratória ou Química. "
        "A geração usará linguagem adulta, direta e ligada ao mundo do trabalho.",
        icon="👥",
    )

st.markdown('<div class="section-title">🧠 Configuração de Inteligência</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Defina se o processamento será manual ou apoiado por IA.</div>', unsafe_allow_html=True)
modo_ia = st.radio("Motor de processamento", ["Sem IA", "OpenAI", "Gemini"], index=0, horizontal=True, key="modo_ia")
modelo_openai = os.environ.get("OPENAI_MODEL", MODELO_OPENAI_PADRAO) if modo_ia == "OpenAI" else ""
modelo_gemini = os.environ.get("GEMINI_MODEL", MODELO_GEMINI_PADRAO) if modo_ia == "Gemini" else ""

st.markdown('<div class="section-title">📝 Dados do Cabeçalho</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Preencha professor, disciplina, turma, período e dados que irão para o documento final.</div>', unsafe_allow_html=True)
col_prof, col_disciplina = st.columns([1, 1])
with col_prof:
    professor_selecionado = st.selectbox("Professor", _NOMES_PROFESSORES, key="professor_select")
    if professor_selecionado == "Outro (digitar)":
        professor = st.text_input("Nome do professor", key="professor").strip()
        if professor:
            from rapidfuzz import process, fuzz
            nomes_existentes = [p for p in PROFESSORES.keys() if p]
            if nomes_existentes:
                match = process.extractOne(professor, nomes_existentes, scorer=fuzz.WRatio)
                if match:
                    sugerido, score, _ = match
                    if 72 <= score < 100:
                        st.info(f"💡 **Dica de Digitação:** O nome digitado é semelhante ao professor cadastrado **'{sugerido}'** ({int(score)}% de similaridade). Se for ele, selecione-o no campo de seleção acima para evitar duplicidade.")
    else:
        professor = professor_selecionado if professor_selecionado != "(selecione o professor)" else ""

with col_disciplina:
    dados_prof = PROFESSORES_DB.get(professor, {})
    disciplinas_cadastradas = (
        []
        if modo_cdp_dedicado
        else [
            item
            for item in dados_prof.get("disciplinas", [])
            if obter_config(item.get("disciplina", "")).habilitado
        ]
    )
    if modo_eja:
        disciplinas_cadastradas = [
            item
            for item in disciplinas_cadastradas
            if _disciplina_suporta_modalidade_eja(item.get("disciplina", ""))
        ]
        disciplinas_gerais = [
            item
            for item in nomes_disciplinas()
            if not eh_cdp(item) and _disciplina_suporta_modalidade_eja(item)
        ]
    elif modo_cdp_ef_em:
        disciplinas_cadastradas = [
            item
            for item in disciplinas_cadastradas
            if eh_cdp_contextual(item.get("disciplina", "")) or item.get("disciplina", "").upper().endswith("-CDP") or eh_cdp(item.get("disciplina", ""))
        ]
        disciplinas_gerais = [
            item
            for item in nomes_disciplinas()
            if eh_cdp_contextual(item) or item.upper().endswith("-CDP") or eh_cdp(item)
        ]
    else:
        disciplinas_gerais = [item for item in nomes_disciplinas() if not eh_cdp(item)]
    
    if disciplinas_cadastradas:
        disciplinas_unicas_prof = list(dict.fromkeys(d["disciplina"] for d in disciplinas_cadastradas))
        disc_selecionada = st.selectbox("Disciplina", ["(escolha a disciplina)"] + disciplinas_unicas_prof + ["Outra..."], key="disc_prof_select")
        disciplina = st.selectbox("Disciplina (Geral)", disciplinas_gerais, key="disciplina_opcao") if disc_selecionada == "Outra..." else (disc_selecionada if disc_selecionada != "(escolha a disciplina)" else "")
    else:
        disciplina = "" if modo_cdp_dedicado else st.selectbox("Disciplina", disciplinas_gerais, key="disciplina_opcao")

if disciplina == "Outra":
    disciplina = st.text_input("Informe a disciplina", key="disciplina_outra").strip()
    if disciplina:
        from rapidfuzz import process, fuzz
        match = process.extractOne(disciplina, disciplinas_gerais, scorer=fuzz.WRatio)
        if match:
            sugerido, score, _ = match
            if 70 <= score < 100:
                st.info(f"💡 **Dica de Digitação:** A disciplina digitada é semelhante a **'{sugerido}'** ({int(score)}% de similaridade). Se for ela, você pode usar o nome oficial para garantir que o sistema aplique as regras pedagógicas corretas.")
if modo_cdp_dedicado: disciplina = st.selectbox("Tipo de plano CDP", ["CDP- Multisseriada", "CDP - Ciclo I"], key="disciplina_cdp_opcao")

disciplina_config = obter_config(disciplina)
disciplina_norm = re.sub(r"\s+", " ", str(disciplina or "")).strip().lower()
orientacao_estudos = "orienta" in disciplina_norm and "estudo" in disciplina_norm
disciplina_cdp = eh_cdp(disciplina)
disciplina_saida = f"{disciplina} - EJA" if modo_eja and disciplina else disciplina

# Verificar disponibilidade das planilhas CDP (desativado temporariamente)
from core.cdp_legacy import PLANILHA_CDP, PLANILHA_CDP_MULTISSERIADA
if (disciplina_cdp or eh_cdp_fundamental(disciplina) or modo_cdp_dedicado) and escolha_template != "Upload de novo modelo...":
    modelo_cdp = TEMPLATES_DIR / "MODELOCDP.docx"
    if modelo_cdp.exists(): modelo_bytes = modelo_cdp.read_bytes()

config_turma_selecionada = None
col_turma, col_bimestre, col_mes, col_previstas = st.columns([2, 2, 2, 1])
with col_turma:
    turmas_cadastradas = [d["turma"] for d in dados_prof.get("disciplinas", []) if d["disciplina"] == disciplina]
    if turmas_cadastradas:
        turma_selecionada = st.selectbox("Série/Turma", ["(escolha a turma)"] + list(dict.fromkeys(turmas_cadastradas)) + ["Outra..."], key="turma_prof_select")
        if turma_selecionada == "Outra...": turma = _selecionar_turma("Série/Turma (Outra)", "turma_select", "turma")
        elif turma_selecionada == "(escolha a turma)": turma = ""
        else:
            turma = turma_selecionada
            st.session_state["turma"] = turma
            config_selecionada = _selecionar_config_cadastro(
                dados_prof.get("disciplinas", []),
                disciplina,
                turma,
            )
            if config_selecionada:
                config_turma_selecionada = config_selecionada
                modelo_automatico_arquivo = str(config_selecionada.get("arquivo") or "")
                modelo_automatico_template_id = str(config_selecionada.get("template_id") or "")
                
                selecao_vaga_id = f"{professor}-{disciplina}-{turma}"
                if st.session_state.get("last_aula_prof") != selecao_vaga_id:
                    st.session_state["last_aula_prof"] = selecao_vaga_id
                    val_aulas = str(config_selecionada.get("aulas_semana") or "")
                    
                    if not val_aulas:
                        for d_conf in dados_prof.get("disciplinas", []):
                            if d_conf.get("disciplina") == disciplina and d_conf.get("aulas_semana"):
                                val_aulas = str(d_conf.get("aulas_semana"))
                                break
                    
                    if val_aulas:
                        st.session_state["aulas_previstas_manual"] = val_aulas
                        if "aulas_previstas_manual_select" in st.session_state:
                            del st.session_state["aulas_previstas_manual_select"]
                        
                    datas_horarios = list(config_selecionada.get("datas_horarios") or [])
                    if datas_horarios:
                        for i, item in enumerate(datas_horarios):
                            st.session_state[f"data_aula_{i}"] = item.get("data", date.today())
                            sug = _sugerir_horario_cadastrado(" ".join(str(item.get(k) or "") for k in ("horario", "aula")), turma)
                            if sug: st.session_state[f"horario_aula_{i}"] = sug; st.session_state[f"tipo_horario_aula_{i}"] = _tipo_horario(sug)
    else:
        turma = _selecionar_turma("Série/Turma", "turma_select", "turma")

with col_bimestre: bimestre = st.selectbox("Bimestre", BIMESTRES, key="bimestre")
with col_mes: mes = _selecionar_mes()
with col_previstas: aulas_previstas_manual = _selecionar_aulas_semana("Aulas", "aulas_previstas_manual_select", "aulas_previstas_manual")



resumo_grade_cadastrada = _resumo_grade_cadastrada(config_turma_selecionada)
if resumo_grade_cadastrada:
    st.info(f"Horário cadastrado: {resumo_grade_cadastrada}", icon="🕒")

# ── Alerta: plano já gerado para outro professor ──────────────────────
if professor and disciplina and turma:
    outros = verificar_plano_gerado_por_outro_professor(
        professor,
        disciplina_saida,
        turma,
        bimestre=bimestre,
    )
    if outros:
        nomes_outros = list(dict.fromkeys(r["professor_nome"] for r in outros))
        nomes_formatados = ", ".join(f"**{nome}**" for nome in nomes_outros[:3])
        data_recente = outros[0]["data_geracao"]
        try:
            if " " in str(data_recente):
                data_so = str(data_recente).split(" ")[0]
                partes = data_so.split("-")
                data_amigavel = f"{partes[2]}/{partes[1]}/{partes[0]}"
            else:
                data_amigavel = str(data_recente)
        except Exception:
            data_amigavel = str(data_recente)
            
        st.warning(
            f"⚠️ **ATENÇÃO:** O plano de **{disciplina_saida} — {turma}** já foi gerado anteriormente neste **{bimestre}** para {nomes_formatados} (última geração em {data_amigavel}). Certifique-se de que é isso mesmo que deseja antes de prosseguir.",
            icon="⚠️"
        )


extensao_mes_rotulo = st.selectbox("Extensão após o mês", EXTENSAO_MES_OPCOES, index=0, key="extensao_mes")
extensao_mes = EXTENSAO_MES_VALORES.get(extensao_mes_rotulo, 0)
antecipacao_mes = EXTENSAO_MES_ANTECIPACOES.get(extensao_mes_rotulo, 0)

datas_horarios_mes, datas_sem_aula = [], []
config_agenda_mes = config_turma_selecionada
if modo_cdp_dedicado and modelo_bytes:
    config_agenda_mes = {**(config_turma_selecionada or {}), **_config_agenda_a_partir_do_modelo(modelo_bytes)}

if config_agenda_mes and mes and (not disciplina_cdp or modo_cdp_dedicado):
    datas_horarios_mes_base = _datas_horarios_do_mes(
        config_agenda_mes,
        mes,
        turma,
        extensao=extensao_mes,
        antecipacao=antecipacao_mes,
    )
    inicio_periodo = _inicio_periodo_mes_com_antecipacao(date.today().year, _mes_numero_app(mes), antecipacao_mes)
    fim_periodo = _fim_periodo_mes_com_extensao(date.today().year, _mes_numero_app(mes), extensao_mes)
    datas_opcoes_sem_aula = _datas_do_periodo(inicio_periodo, fim_periodo)
    
    assinatura_datas = f"{professor}|{disciplina}|{turma}|{mes}|{extensao_mes}|{antecipacao_mes}"
    if st.session_state.get("datas_sem_aula_assinatura") != assinatura_datas:
        st.session_state["datas_sem_aula_assinatura"] = assinatura_datas
        st.session_state["datas_sem_aula"] = _datas_feriado_padrao(datas_opcoes_sem_aula) or _datas_sem_aula_padrao(datas_horarios_mes_base)

    if datas_opcoes_sem_aula:
        datas_sem_aula = st.multiselect("Dias sem aula", options=datas_opcoes_sem_aula, format_func=_rotulo_data_sem_aula, key="datas_sem_aula")
    
    deixar_antecipacao_vazia = False
    if antecipacao_mes > 0:
        deixar_antecipacao_vazia = st.checkbox(
            "Deixar bloco da semana extra vazio",
            key="deixar_antecipacao_vazia",
            value=bool(st.session_state.get("deixar_antecipacao_vazia", False)),
            help="Se marcado, as aulas da semana extra anterior ao início do mês virão completamente em branco no plano, e a correspondência com os PDFs começará a partir da primeira data oficial do mês."
        )
    
    datas_horarios_mes = _sincronizar_datas_horarios_mes(
        config_agenda_mes,
        mes,
        professor,
        disciplina,
        turma,
        extensao=extensao_mes,
        antecipacao=antecipacao_mes,
        datas_sem_aula=datas_sem_aula,
    )

if professor and disciplina and turma and not disciplina_cdp and escolha_template == OPCAO_MODELO_AUTOMATICO:
    template_id_central = resolver_template_id_geracao(
        template_id=modelo_automatico_template_id or "",
        disciplina=disciplina,
        componente_curricular=str((config_turma_selecionada or {}).get("componente_curricular") or disciplina),
        escola=st.session_state.get("escola", ""),
        arquivo_modelo=modelo_automatico_arquivo,
    )
    caminho_template = caminho_template_central(template_id_central)
    if caminho_template.exists(): modelo_bytes = caminho_template.read_bytes()

if bool(professor and disciplina and turma and not disciplina_cdp and not modelo_bytes):
    st.markdown('<div class="section-title">Modelo DOCX</div>', unsafe_allow_html=True)
    escolha_template = st.selectbox("Modelo DOCX Base", templates_disponiveis + ["Upload de novo modelo..."], key="escolha_template_manual")
    if escolha_template == "Upload de novo modelo...":
        modelo_file = st.file_uploader("Novo Modelo", type=["docx"], key="novo_modelo_file")
        if modelo_file:
            modelo_bytes = modelo_file.getvalue()
            # --- P1: Contenção de caminho (path traversal) ---
            # Garantir que o nome do arquivo não contenha diretórios
            safe_name = Path(modelo_file.name).name  # descarta qualquer prefixo de caminho
            if Path(safe_name).suffix.lower() != ".docx":
                st.error("Apenas arquivos .docx são permitidos como modelo.")
                modelo_bytes = None
            else:
                destino_modelo = (TEMPLATES_DIR / safe_name).resolve()
                templates_dir_resolvido = Path(TEMPLATES_DIR).resolve()
                # Bloquear acesso fora da pasta de templates
                if not str(destino_modelo).startswith(str(templates_dir_resolvido)):
                    st.error("Caminho de destino inválido. O arquivo deve ficar dentro da pasta de templates.")
                    modelo_bytes = None
                else:
                    modelo_existe = destino_modelo.exists()
                    confirmar_modelo = True
                    if modelo_existe:
                        confirmar_modelo = st.checkbox(
                            f"Confirmo que desejo substituir o modelo existente '{safe_name}'.",
                            key="confirmar_substituir_modelo_manual",
                        )
                        st.warning("Ja existe um modelo com esse nome. Marque a confirmacao para substituir.")
                    if st.button("Salvar para futuro", disabled=modelo_existe and not confirmar_modelo):
                        destino_modelo.write_bytes(modelo_bytes)
                        st.rerun()
    else:
        if (TEMPLATES_DIR / escolha_template).exists(): modelo_bytes = (TEMPLATES_DIR / escolha_template).read_bytes()

if professor and disciplina and turma:
    st.button("Editar cadastro", type="secondary", on_click=_abrir_cadastro_com_filtros, args=(professor, disciplina, turma))

assinatura_comp = f"{professor}|{disciplina}|{turma}|{(config_turma_selecionada or {}).get('componente_curricular', '')}"
if st.session_state.get("last_componente_curricular") != assinatura_comp:
    st.session_state["last_componente_curricular"] = assinatura_comp
    st.session_state["componente_curricular"] = str((config_turma_selecionada or {}).get("componente_curricular") or disciplina)

col_escola, col_comp = st.columns([1, 1])
with col_escola: escola = st.selectbox("Escola", ESCOLAS, key="escola")
with col_comp: componente_curricular = st.text_input("Componente curricular", key="componente_curricular")

modalidade_eja = bool(modo_eja)


def _resolver_pasta_pdfs_oficial(
    disciplina: str,
    turma: str,
    bimestre: str,
    professor: str = "",
) -> Path:
    """Resolve PDFs automaticos sem permitir saida da raiz oficial."""
    raiz_oficial = Path(PDF_AULAS_DIR).resolve(strict=False)
    if not raiz_oficial.is_dir():
        raise FileNotFoundError(
            f"Pasta oficial de PDFs indisponivel: {raiz_oficial}"
        )

    disciplinas_busca = [f"{disciplina} EJA", disciplina] if modo_eja else [disciplina]
    candidatos = []
    for disciplina_busca in disciplinas_busca:
        pasta = resolver_pasta_pdfs(
            str(raiz_oficial),
            disciplina_busca,
            turma,
            bimestre,
            professor=professor,
            modalidade_eja=modalidade_eja,
        )
        pasta_segura = garantir_caminho_na_raiz(pasta, raiz_oficial)
        candidatos.append(pasta_segura)
        if pasta_segura.is_dir():
            return pasta_segura
    return candidatos[0]


def _resolver_caminho_ae_priorizado(disciplina: str, turma: str, bimestre: str, professor: str = "") -> str:
    try:
        pasta = _resolver_pasta_pdfs_oficial(
            disciplina,
            turma,
            bimestre,
            professor=professor,
        )
    except Exception:
        return ""

    if not getattr(pasta, "exists", lambda: False)():
        return ""

    candidatos = []
    padroes = ["GUIA*.xlsx", "*GUIA*.xlsx", "planilha.xlsx", "*.xlsx"]
    for padrao in padroes:
        for arquivo in sorted(pasta.glob(padrao)):
            nome = str(getattr(arquivo, "name", "") or "")
            if nome.startswith("~$"):
                continue
            if arquivo not in candidatos:
                candidatos.append(arquivo)

    return str(candidatos[0]) if candidatos else ""


caminho_ae_priorizado = _resolver_caminho_ae_priorizado(disciplina, turma, bimestre, professor)
st.session_state["caminho_ae_priorizado"] = caminho_ae_priorizado
usar_ae_priorizado = False
contexto_ae_ok = False
if disciplina_ae_priorizado_disponivel(disciplina) or caminho_ae_priorizado:
    contexto_ae_ok = contexto_ae_priorizado_disponivel(
        disciplina,
        turma,
        bimestre,
        caminho_planilha=caminho_ae_priorizado,
    )
    st.checkbox(
        "Usar AE no lugar da habilidade",
        value=bool(st.session_state.get("usar_ae_priorizado", False)),
        key="usar_ae_priorizado",
        disabled=not contexto_ae_ok,
        help="Quando ativado, o sistema troca a coluna de aprendizagem pelo AE correspondente do guia priorizado, quando houver base cadastrada para a disciplina, turma e bimestre.",
    )
    usar_ae_priorizado = bool(contexto_ae_ok and st.session_state.get("usar_ae_priorizado", False))
    if contexto_ae_ok:
        if caminho_ae_priorizado:
            st.caption("Guia priorizado encontrado para este contexto. Se alguma aula nao estiver na planilha, o sistema mantém a habilidade normal.")
        else:
            st.caption("Base AE encontrada para este contexto. Se alguma aula não estiver no mapa, o sistema mantém a habilidade normal.")
    else:
        st.caption("Esta opção fica disponível quando existe base AE ou guia priorizado para a disciplina, série e bimestre selecionados.")
else:
    st.session_state["usar_ae_priorizado"] = False

def _resumo_tela(valor: str, fallback: str = "Não definido") -> str:
    return str(valor).strip() if str(valor or "").strip() else fallback


def _rotulo_sequencia_pdfs_esperada(numeros: list[int]) -> str:
    return " | ".join(
        f"{indice + 1}. AULA {int(numero)}"
        for indice, numero in enumerate(numeros or [])
        if str(numero).strip()
    )


def _limitar_sequencia_ae(numeros: list[int], limite: int | None = None) -> list[int]:
    if limite is None:
        return list(numeros or [])
    try:
        limite_int = int(limite)
    except (TypeError, ValueError):
        limite_int = 0
    if limite_int <= 0:
        return list(numeros or [])
    return list(numeros or [])[:limite_int]




sequencia_ae_contexto = []
if usar_ae_priorizado and contexto_ae_ok:
    sequencia_ae_contexto = sequencia_aulas_ae_priorizado(
        disciplina,
        turma,
        bimestre,
        caminho_planilha=caminho_ae_priorizado,
    )
    if sequencia_ae_contexto:
        st.info(
            "Modo AE ativo neste contexto. Ordem base do guia priorizado: "
            f"{_rotulo_sequencia_pdfs_esperada(sequencia_ae_contexto)}."
        )
        st.caption("Mais abaixo, o envio dos PDFs do mês usará essa mesma ordem.")
    else:
        st.warning("Modo AE ativo, mas não encontrei a sequência do guia para este contexto.")


def _render_previa_aulas_cdp(preview: list[dict]):
    if not preview:
        st.warning("Não consegui localizar as aulas do CDP no modelo atual.")
        return

    st.markdown('<div class="section-subtitle">Prévia das aulas que serão puxadas da planilha</div>', unsafe_allow_html=True)
    st.info(
        "No CDP, a aula inicial é aplicada dentro de cada disciplina que aparece no modelo. A prévia abaixo mostra qual disciplina e qual aula da planilha entrarão em cada bloco.",
        icon="ℹ️",
    )

    cards = []
    for item in preview[:6]:
        aula_planilha = f"Aula {item.get('aula_planilha')}" if str(item.get("aula_planilha") or "").strip() else "Aula sem número"
        titulo = str(item.get("titulo") or "").strip() or "Sem título identificado"
        disciplina = str(item.get("disciplina") or "").strip() or "Disciplina não identificada"
        planilha = str(item.get("componente_planilha") or disciplina).strip()
        cards.append(
            (
                f'<div class="cdp-preview-card">'
                f'<div class="cdp-preview-card__top">'
                f'<span class="cdp-preview-card__ordem">Bloco {item.get("ordem")}</span>'
                f'<span class="cdp-preview-card__aula">{aula_planilha}</span>'
                f'</div>'
                f'<div class="cdp-preview-card__disciplina">{disciplina}</div>'
                f'<div class="cdp-preview-card__planilha">Planilha: {planilha}</div>'
                f'<div class="cdp-preview-card__titulo">{titulo}</div>'
                f'</div>'
            )
        )

    st.markdown(f'<div class="cdp-preview-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    if len(preview) > 6:
        st.caption(f"Mostrando os 6 primeiros blocos do modelo. Total identificado: {len(preview)}.")

semana = ""

# Texto padrão fixo para NOVEMBRO
default_novembro = (
    "O professor poderá realizar adequações neste plano de aula, sempre que necessário, "
    "em função do andamento das aulas, do ritmo da turma e das necessidades pedagógicas "
    "identificadas, preservando os objetivos de aprendizagem estabelecidos.\n"
    "02/11 - FERIADO (FINADOS)   15/11 - FERIADO (Proclamação da República)\n"
    "20/11 - FERIADO (Dia da Consciência Negra)\n"
    "04/11 e 05/11 Provão Paulista - 3º Série   06/11 a 09/11 SARESP ENSINO MÉDIO\n"
    "10/11 a 13//1 - PROVÃO PAULISTA 1ª e 2ª SÉRIE ENSINO MÉDIO \n"
    "18/11 E 19/11 SARESP - 6º ANO   26/11 E 27/11 SARESP 7ºANO  30/11 - SARESP 8º ANO "
)

# Texto padrão fixo para OUTUBRO
default_outubro = (
    "O professor poderá realizar adequações neste plano de aula, sempre que necessário, "
    "em função do andamento das aulas, do ritmo da turma e das necessidades pedagógicas "
    "identificadas, preservando os objetivos de aprendizagem estabelecidos, bem como "
    "poderá fazer uso de tecnologias, quando achar necessário.\n"
    "12/10 – Feriado Nacional\n"
    "15/10 - Feriado (Dia do Professor)\n"
    "16/10 - Conselho de Classe 3º Bimestre"
)

# Texto padrão fixo para AGOSTO
default_agosto = (
    "Replanejamento – 22 e 23.07;\n"
    "Período do plano – 24.07 até 31.08;\n"
    "Reunião de pais/responsáveis – 04.08;\n"
    "Feriado Municipal – 06.08;"
)
default_agosto_legado = "06/08 - Aniversário da cidade\n07/08 - Ponto facultativo"
observacoes_automaticas_agosto = {default_agosto, default_agosto_legado}

# Conjunto de todos os textos automáticos conhecidos (para detectar troca de mês)
_obs_automaticas_conhecidas = (
    observacoes_automaticas_agosto
    | {default_outubro, default_novembro}
    | {obs.strip() for obs in (default_outubro, default_novembro)}
    | {default_novembro.replace("13//1", "13/11"), default_novembro.replace("13//1", "13/11").strip()}
)

if "observacao" not in st.session_state or not st.session_state["observacao"]:
    if mes.strip().upper() == "AGOSTO":
        st.session_state["observacao"] = default_agosto
    elif mes.strip().upper() == "OUTUBRO":
        st.session_state["observacao"] = default_outubro
    elif mes.strip().upper() == "NOVEMBRO":
        st.session_state["observacao"] = default_novembro
elif (
    mes.strip().upper() == "AGOSTO"
    and str(st.session_state.get("observacao", "") or "").strip() == default_agosto_legado
):
    st.session_state["observacao"] = default_agosto
elif (
    mes.strip().upper() == "NOVEMBRO"
    and str(st.session_state.get("observacao", "") or "").strip() in (observacoes_automaticas_agosto | {default_outubro})
):
    st.session_state["observacao"] = default_novembro

if "last_mes_for_obs" not in st.session_state:
    st.session_state["last_mes_for_obs"] = mes

if st.session_state["last_mes_for_obs"] != mes:
    current_obs = st.session_state.get("observacao", "").strip()
    if mes.strip().upper() == "AGOSTO":
        if not current_obs or current_obs in {"", default_agosto_legado} or current_obs in _obs_automaticas_conhecidas:
            st.session_state["observacao"] = default_agosto
    elif mes.strip().upper() == "OUTUBRO":
        if not current_obs or current_obs in _obs_automaticas_conhecidas:
            st.session_state["observacao"] = default_outubro
    elif mes.strip().upper() == "NOVEMBRO":
        if not current_obs or current_obs in _obs_automaticas_conhecidas:
            st.session_state["observacao"] = default_novembro
    else:
        if current_obs in _obs_automaticas_conhecidas:
            st.session_state["observacao"] = ""
    st.session_state["last_mes_for_obs"] = mes

observacao = st.text_area("Observação", key="observacao")
gerar_turma_espelho = st.checkbox("Gerar para 2ª turma", value=False, key="gerar_turma_espelho")
turma_espelho = _selecionar_turma_espelho(turma, turmas_cadastradas) if gerar_turma_espelho else ""
aulas_envio_espelho = []
# Buscar configuração cadastrada da turma espelho para usar os horários corretos
config_turma_espelho = None
if gerar_turma_espelho and turma_espelho:
    config_turma_espelho = _selecionar_config_cadastro(
        dados_prof.get("disciplinas", []),
        disciplina,
        turma_espelho,
    )

st.markdown('<div class="section-title">📚 Gestão das Aulas</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Confira os PDFs necessários, a ordem de processamento e o que ainda falta antes de gerar o plano.</div>', unsafe_allow_html=True)
if disciplina_cdp:
    if eh_cdp_multisseriada(disciplina):
        col1, col2 = st.columns([2, 1])
        with col1: turma_cdp = st.selectbox("Turma filtro", TURMAS_CDP_MULTISSERIADA, key="turma_cdp")
        with col2: cdp_aula_inicial = st.number_input("Aula inicial", min_value=1, value=1, key="cdp_aula_inicial")
    else: cdp_aula_inicial = st.number_input("Aula inicial", min_value=1, value=1, key="cdp_aula_inicial")
    if modelo_bytes:
        try:
            previa_cdp = prever_aulas_cdp(
                BytesIO(modelo_bytes),
                aula_inicial=int(cdp_aula_inicial or 1),
                fundamental=eh_cdp_fundamental(disciplina),
                multisseriada=eh_cdp_multisseriada(disciplina),
                serie_cdp=turma_cdp if eh_cdp_multisseriada(disciplina) else "",
                bimestre=bimestre,
                turma=turma,
            )
            _render_previa_aulas_cdp(previa_cdp)
        except Exception:
            st.warning("Não consegui montar a prévia das aulas do CDP com o modelo atual.")
else:
    linhas_modelo = len(datas_horarios_mes or []) or len((config_turma_selecionada or {}).get("datas_horarios") or [])
    sequencia_pdf_esperada_ae = []
    contexto_divisao_pdf = "|".join(str(valor or "") for valor in [professor, disciplina, turma, mes, bimestre])
    frequencia_dia_sem_pdf = _frequencia_dia_sem_pdf(disciplina, turma=turma)
    permitir_dia_sem_pdf_portugues = bool(
        _permite_um_dia_sem_pdf(
            disciplina,
            turma=turma,
            modo_eja=modo_eja,
            modo_cdp=disciplina_cdp or modo_cdp_dedicado or modo_cdp_ef_em,
        )
    )
    usar_dia_sem_pdf_portugues = False
    dia_sem_pdf_portugues = None
    modo_aula_dupla = "uma_aula"

    deixar_ant_vazia = bool(st.session_state.get("deixar_antecipacao_vazia", False))
    if deixar_ant_vazia and datas_horarios_mes:
        aulas_oficiais_modelo = [d for d in datas_horarios_mes if not _eh_data_antecipacao(d["data"], mes, antecipacao_mes)]
        linhas_modelo_pdf = len(aulas_oficiais_modelo)
    else:
        aulas_oficiais_modelo = datas_horarios_mes or []
        linhas_modelo_pdf = linhas_modelo

    datas_horarios_mes_espelho = None
    aulas_oficiais_modelo_espelho = []
    if gerar_turma_espelho and config_turma_espelho and mes:
        datas_horarios_mes_espelho = _sincronizar_datas_horarios_mes_turma2(
            config_turma_espelho, mes, professor, disciplina, turma_espelho,
            extensao=extensao_mes, antecipacao=antecipacao_mes, datas_sem_aula=datas_sem_aula,
        )
        if datas_horarios_mes_espelho:
            aulas_oficiais_modelo_espelho = [d for d in datas_horarios_mes_espelho if not _eh_data_antecipacao(d["data"], mes, antecipacao_mes)] if deixar_ant_vazia else datas_horarios_mes_espelho

    if bool(len(datas_horarios_mes or [])):
        st.session_state["auto_repetir_semana"] = False
    elif "auto_repetir_semana" not in st.session_state:
        st.session_state["auto_repetir_semana"] = True
    auto_repetir_semana = st.checkbox("Repetir semana", key="auto_repetir_semana", disabled=bool(len(datas_horarios_mes or [])))
    dividir_metodologia = st.checkbox("Dividir metodologia em dois dias", value=False, key="dividir_metodologia")
    if permitir_dia_sem_pdf_portugues:
        st.checkbox(
            "Permitir 1 dia sem PDF",
            key="permitir_dia_sem_pdf_portugues",
            help="Use esta opção para deixar um dos dias da disciplina em branco no plano (sem PDF), mantendo apenas a data.",
        )
        usar_dia_sem_pdf_portugues = bool(st.session_state.get("permitir_dia_sem_pdf_portugues", False))
        if usar_dia_sem_pdf_portugues:
            opcoes_dia_sem_pdf = _opcoes_dia_sem_pdf(datas_horarios_mes)
            valores_dia_sem_pdf = [dia for dia, _ in opcoes_dia_sem_pdf]
            if valores_dia_sem_pdf:
                col_freq, col_dia, col_dupla = st.columns([1, 1, 1])
                with col_freq:
                    opcoes_freq = ["A cada 15 dias (semanas alternadas)", "Toda semana (semanal)"]
                    default_freq_idx = 0 if _frequencia_dia_sem_pdf(disciplina, turma=turma) == "quinzenal" else 1
                    chave_freq_opcao = "frequencia_dia_sem_pdf_opcao"
                    if st.session_state.get(chave_freq_opcao) not in opcoes_freq:
                        st.session_state[chave_freq_opcao] = opcoes_freq[default_freq_idx]
                    freq_selecionada = st.selectbox(
                        "Frequência do dia sem PDF",
                        opcoes_freq,
                        key=chave_freq_opcao,
                        help="Escolha se a isenção de PDF ocorrerá a cada 15 dias ou toda semana.",
                    )
                    frequencia_dia_sem_pdf = "quinzenal" if "15 dias" in str(freq_selecionada) else "semanal"
                with col_dia:
                    chave_dia_sem_pdf = "dia_sem_pdf_portugues"
                    if st.session_state.get(chave_dia_sem_pdf) not in valores_dia_sem_pdf:
                        st.session_state[chave_dia_sem_pdf] = valores_dia_sem_pdf[0]
                    dia_sem_pdf_portugues = st.selectbox(
                        "Dia da semana que ficará sem PDF",
                        valores_dia_sem_pdf,
                        key=chave_dia_sem_pdf,
                        format_func=lambda valor: DIAS_SEMANA_COMPLETOS[int(valor)],
                    )
                with col_dupla:
                    opcoes_dupla = ["1 aula com PDF + 1 sem PDF", "Ambas as aulas sem PDF"]
                    chave_dupla_opcao = "modo_aula_dupla_sem_pdf_opcao"
                    if st.session_state.get(chave_dupla_opcao) not in opcoes_dupla:
                        st.session_state[chave_dupla_opcao] = opcoes_dupla[0]
                    dupla_selecionada = st.selectbox(
                        "Em dias com aula dupla",
                        opcoes_dupla,
                        key=chave_dupla_opcao,
                        help="Escolha se apenas 1 das aulas duplas fica sem PDF ou se ambas ficam sem PDF.",
                    )
                    modo_aula_dupla = "uma_aula" if "1 aula" in str(dupla_selecionada) else "ambas"
    _sincronizar_divisao_pdf_padrao(linhas_modelo, dividir_metodologia, contexto=contexto_divisao_pdf, lista_aulas=aulas_oficiais_modelo)

    opcoes_modo_upload = ["Automatico", "Todos de uma vez", "Um por aula"]
    if st.session_state.get("modo_upload_pdf") not in opcoes_modo_upload:
        st.session_state["modo_upload_pdf"] = MODO_UPLOAD_PDF_PADRAO
    modo_upload_pdf = st.radio(
        "Modo de envio dos PDFs",
        opcoes_modo_upload,
        horizontal=True,
        key="modo_upload_pdf",
        help=(
            f"Automatico: busca os PDFs em {PDF_AULAS_DIR} e aplica a ordem do sistema.\n"
            "Todos de uma vez: envie os arquivos manualmente em lote.\n"
            "Um por aula: envie o PDF diretamente em cada card."
        ),
    )
    modo_upload_individual = modo_upload_pdf == "Um por aula"
    modo_upload_automatico = modo_upload_pdf == "Automatico"

    pdfs_aulas_files = []
    qtd_aulas = 0
    pdfs_auto_total = 0
    pasta_pdfs_resolvida = None
    pasta_pdfs_auto = ""
    erro_pasta_pdfs_auto = ""
    if modo_upload_automatico:
        try:
            pasta_pdfs_resolvida = _resolver_pasta_pdfs_oficial(
                disciplina,
                turma,
                bimestre,
                professor=professor,
            )
            pasta_pdfs_auto = str(pasta_pdfs_resolvida)
        except (OSError, ValueError) as exc:
            erro_pasta_pdfs_auto = str(exc)
    faltantes_ae_auto = []
    pdfs_selecionados_tela = []
    from core.gestao_aulas import obter_referencia_ultima_aula_ampla
    from core.database import salvar_progresso_aula

    referencia_historico = obter_referencia_ultima_aula_ampla(
        professor,
        disciplina,
        turma,
        bimestre,
    )
    ultima_aula_sugerida = int(referencia_historico.get("ultima_aula") or 0)

    # Campo interativo para definir ou confirmar a última aula utilizada
    col_ua1, col_ua2 = st.columns([1, 2])
    chave_input_ua = f"input_ultima_aula_{_slug_key(professor)}_{_slug_key(disciplina)}_{_slug_key(turma)}"
    with col_ua1:
        ultima_aula_digitada = st.number_input(
            "🔢 Última aula usada no mês anterior",
            min_value=0,
            max_value=300,
            value=ultima_aula_sugerida,
            key=chave_input_ua,
            help="Informe ou ajuste o número da última aula utilizada no mês anterior. O sistema começará a seleção a partir da aula seguinte.",
        )
    with col_ua2:
        if ultima_aula_digitada > 0:
            detalhe_origem = ""
            if referencia_historico.get("origem") == "memoria_progresso":
                detalhe_origem = " (gravada na memória do sistema)"
            elif referencia_historico.get("origem") in ("historico_bimestre", "historico_geral"):
                detalhe_origem = " (identificada no plano anterior)"
            elif referencia_historico.get("origem") == "arquivo_docx":
                detalhe_origem = " (detectada no último DOCX da pasta)"

            ultimo_pdf_info = ""
            if referencia_historico.get("ultimo_pdf"):
                ultimo_pdf_info = f" • PDF: `{referencia_historico['ultimo_pdf']}`"

            st.markdown(
                f'<div style="padding-top: 26px; font-weight: 600; color: #1e7e34; font-size: 0.95rem;">'
                f'🟢 Iniciando a seleção a partir da <strong>AULA {ultima_aula_digitada + 1}</strong>{detalhe_origem}{ultimo_pdf_info}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="padding-top: 26px; color: #6c757d; font-size: 0.95rem;">'
                'ℹ️ Iniciando da <strong>AULA 1</strong> (ou digite o número da última aula ao lado)'
                '</div>',
                unsafe_allow_html=True,
            )

    # Se o usuário alterou manualmente o número da última aula na tela, atualiza imediatamente a memória
    if ultima_aula_digitada != ultima_aula_sugerida:
        salvar_progresso_aula(professor, disciplina, turma, ultima_aula_digitada, mes=mes)

    if not modo_upload_individual:
        # Calcular PDFs necessários estimados para o rótulo do uploader
        est_necessarios = 0
        datas_modelo_base = [a.get("data") for a in aulas_oficiais_modelo if isinstance(a.get("data"), date)]
        aulas_oficiais_modelo_pdf = [
            aula for idx_a, aula in enumerate(aulas_oficiais_modelo)
            if not (
                usar_dia_sem_pdf_portugues
                and dia_sem_pdf_portugues is not None
                and isinstance(aula.get("data"), date)
                and _eh_aula_sem_pdf(
                    idx_a,
                    aula["data"],
                    dia_sem_pdf_portugues,
                    datas_agenda=datas_modelo_base,
                    frequencia=frequencia_dia_sem_pdf,
                    modo_aula_dupla=modo_aula_dupla,
                    eh_horario_duplo=_eh_horario_duplo(aula.get("horario")),
                )
            )
        ]
        if linhas_modelo_pdf > 0:
            est_necessarios = _estimar_pdfs_por_estado(
                len(aulas_oficiais_modelo_pdf),
                dividir_metodologia,
                lista_aulas=aulas_oficiais_modelo_pdf,
            )
            
        if gerar_turma_espelho and len(aulas_oficiais_modelo_espelho) > 0:
            datas_modelo_espelho = [a.get("data") for a in aulas_oficiais_modelo_espelho if isinstance(a.get("data"), date)]
            aulas_oficiais_modelo_espelho_pdf = [
                aula for idx_a, aula in enumerate(aulas_oficiais_modelo_espelho)
                if not (
                    usar_dia_sem_pdf_portugues
                    and dia_sem_pdf_portugues is not None
                    and isinstance(aula.get("data"), date)
                    and _eh_aula_sem_pdf(
                        idx_a,
                        aula["data"],
                        dia_sem_pdf_portugues,
                        datas_agenda=datas_modelo_espelho,
                        frequencia=frequencia_dia_sem_pdf,
                        modo_aula_dupla=modo_aula_dupla,
                        eh_horario_duplo=_eh_horario_duplo(aula.get("horario")),
                    )
                )
            ]
            est_necessarios_espelho = _estimar_pdfs_por_estado(
                len(aulas_oficiais_modelo_espelho_pdf),
                dividir_metodologia,
                lista_aulas=aulas_oficiais_modelo_espelho_pdf,
            )
            est_necessarios = max(est_necessarios, est_necessarios_espelho)

        if usar_ae_priorizado and sequencia_ae_contexto:
            sequencia_pdf_esperada_ae = _limitar_sequencia_ae(
                sequencia_ae_contexto,
                est_necessarios or linhas_modelo_pdf,
            )

        label_uploader = "Envio Manual de PDFs"
        if est_necessarios > 0:
            label_uploader = f"Envio Manual (Insira exatamente {est_necessarios} PDF(s) para as {linhas_modelo_pdf} aulas do mês)"

        if sequencia_pdf_esperada_ae:
            st.info(
                "Modo AE ativo. Sequencia esperada dos PDFs neste contexto: "
                f"{_rotulo_sequencia_pdfs_esperada(sequencia_pdf_esperada_ae)}."
            )
            st.caption("Envie os arquivos nessa ordem do guia priorizado.")

        # Busca automatica de PDFs locais ou envio manual, conforme modo escolhido.
        if modo_upload_individual:
            if linhas_modelo_pdf == 0:
                qtd_aulas = st.number_input(
                    "O sistema não tem o horário do professor configurado. Quantas aulas este plano terá no total?",
                    min_value=1, max_value=40, value=8, step=1,
                    key="qtd_aulas_manual_individual"
                )
            else:
                qtd_aulas = linhas_modelo_pdf
        elif modo_upload_automatico:
            pasta_pdfs = pasta_pdfs_resolvida

            pdf_files_disponiveis = []
            if erro_pasta_pdfs_auto:
                st.error(erro_pasta_pdfs_auto)
            elif pasta_pdfs is not None and pasta_pdfs.exists():
                msg = f"📁 **PASTA LOCALIZADA EM:**\n`{pasta_pdfs}`"
                if est_necessarios > 0:
                    msg += f"\n\n📎 **Quantidade de PDFs que o plano precisa:** {est_necessarios}"
                st.info(msg)
                pdfs_encontrados = filtrar_pdfs_para_aulas(pasta_pdfs.glob("*.pdf"))
                pdfs_auto_total = len(pdfs_encontrados)
                validacao_pdfs = validar_lote_pdfs_contexto_sem_ia(
                    pdfs_encontrados,
                    disciplina=disciplina,
                    turma=turma,
                    bimestre=bimestre,
                )
                if validacao_pdfs.suspeitos:
                    st.error(
                        "Alguns PDFs da pasta foram bloqueados antes da geracao "
                        "porque nao conferem com o contexto selecionado."
                    )
                    for suspeito in validacao_pdfs.suspeitos:
                        motivos = "; ".join(suspeito.motivos)
                        st.caption(f"{suspeito.caminho.name}: {motivos}")
                pdfs_encontrados = [resultado.caminho for resultado in validacao_pdfs.validos]
                if pdfs_auto_total > 0 and not pdfs_encontrados:
                    st.error(
                        "Nenhum PDF da pasta passou na validacao de contexto. "
                        "Confira se a pasta pertence a disciplina, turma e bimestre selecionados."
                    )
                pdfs_com_numero = [pdf for pdf in pdfs_encontrados if numero_aula_pdf(pdf) is not None]
                pdfs_para_ordenar = pdfs_com_numero or pdfs_encontrados
                pdf_files_disponiveis = ordenar_pdfs_por_numero(pdfs_para_ordenar)
            elif pasta_pdfs is not None:
                st.warning(
                    "A pasta esperada para este contexto nao existe dentro da "
                    f"fonte oficial: {pasta_pdfs}"
                )

            if pdf_files_disponiveis:
                default_selection = []
                ultima_aula = int(ultima_aula_digitada or 0)
                
                pdf_files_filtrados = []
                for p in pdf_files_disponiveis:
                    num_aula = numero_aula_pdf(p)
                    if num_aula is not None and num_aula > ultima_aula:
                        pdf_files_filtrados.append(p)
                
                # Fallback se a lista filtrada ficar vazia
                if not pdf_files_filtrados:
                    pdf_files_filtrados = pdf_files_disponiveis

                if est_necessarios > 0:
                    default_selection = pdf_files_filtrados[:est_necessarios]

                faltantes_ae_auto = numeros_pdfs_faltantes(pdf_files_disponiveis, sequencia_pdf_esperada_ae)
                assinatura_pdfs_auto = _assinatura_pdfs_automaticos(pdf_files_disponiveis)

                chave_contexto_auto = "_".join(
                    [
                        "pdfs_aulas_files_auto_v3",
                        normalizar_para_pasta(disciplina),
                        normalizar_para_pasta(professor),
                        normalizar_para_pasta(turma),
                        normalizar_para_pasta(bimestre),
                        "-".join(str(numero) for numero in sequencia_pdf_esperada_ae) or "sem_ae",
                        f"ultima_{ultima_aula}",
                        str(est_necessarios or 0),
                        f"pdfs_{assinatura_pdfs_auto}",
                    ]
                )
                if est_necessarios > 0:
                    st.markdown(f"<div style='background-color: #ffe6e6; border: 2px solid #ff4b4b; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px; color: #2b0f14 !important;'><h3 style='color: #c81e2d !important; margin: 0;'>🚨 QUANTIDADE NECESSÁRIA: {est_necessarios} PDFs 🚨</h3><p style='color: #2b0f14 !important; margin-top: 5px; font-weight: 700;'>O sistema precisa de exatamente {est_necessarios} PDFs para montar o plano deste mês.</p></div>", unsafe_allow_html=True)

                selecionados = st.multiselect(
                    "PDFs automaticos na ordem de processamento",
                    options=pdf_files_disponiveis,
                    format_func=lambda p: p.name,
                    default=default_selection,
                    key=chave_contexto_auto,
                    help="A ordem abaixo ja e a ordem que o sistema vai usar. No modo AE, ela segue a sequencia do guia priorizado.",
                )
                selecionados = ordenar_pdfs_por_numero(selecionados)
                pdfs_selecionados_tela = list(selecionados)
                pdfs_aulas_files = [LocalFileWrapper(p) for p in selecionados]
        else:
            if est_necessarios > 0:
                st.markdown(
                    f"<div style='background-color: #ffe6e6; border: 2px solid #ff4b4b; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px; color: #2b0f14 !important;'><h3 style='color: #c81e2d !important; margin: 0;'>🚨 QUANTIDADE NECESSÁRIA: {est_necessarios} PDFs 🚨</h3><p style='color: #2b0f14 !important; margin-top: 5px; font-weight: 700;'>O sistema precisa de exatamente {est_necessarios} PDFs para montar o plano deste mês.</p></div>",
                    unsafe_allow_html=True,
                )
            pdfs_aulas_files = st.file_uploader(
                label_uploader,
                type=["pdf"],
                accept_multiple_files=True,
                key="pdfs_aulas_files",
                help="Envie todos os PDFs do plano em lote, na ordem em que devem ser processados.",
            ) or []
            qtd_aulas = len(pdfs_aulas_files)
            pdfs_selecionados_tela = list(pdfs_aulas_files)

    deixar_ant_vazia = bool(st.session_state.get("deixar_antecipacao_vazia", False))

    num_rows = linhas_modelo or int(qtd_aulas) * (2 if dividir_metodologia else 1)
    _sincronizar_divisao_pdf_padrao(num_rows, dividir_metodologia, contexto=contexto_divisao_pdf, lista_aulas=aulas_oficiais_modelo)
    aulas_envio = _coletar_aulas_envio(
        num_rows,
        pdfs_aulas_files,
        dividir_metodologia,
        auto_repetir_semana,
        replicar_pdf_unico=bool(orientacao_estudos and qtd_aulas == 1),
        modo_upload_individual=modo_upload_individual,
        preservar_datas_sincronizadas=bool(datas_horarios_mes),
        sequencia_pdf_esperada=sequencia_pdf_esperada_ae,
        deixar_antecipacao_vazia=deixar_ant_vazia,
        mes=mes,
        antecipacao_mes=antecipacao_mes,
        permitir_um_dia_sem_pdf=usar_dia_sem_pdf_portugues,
        dia_sem_pdf_semana=dia_sem_pdf_portugues,
        frequencia_dia_sem_pdf=frequencia_dia_sem_pdf,
        modo_aula_dupla=modo_aula_dupla,
    )

    aulas_mes_oficial = [a for a in aulas_envio if not _eh_data_antecipacao(a["data"], mes, antecipacao_mes)] if deixar_ant_vazia else list(aulas_envio)
    aulas_para_pdf = _filtrar_aulas_com_pdf_obrigatorio(
        aulas_envio,
        mes=mes,
        antecipacao_mes=antecipacao_mes,
        deixar_antecipacao_vazia=deixar_ant_vazia,
    )

    if modo_upload_individual:
        grupos_individuais = (
            _grupos_pdf_por_aula(aulas_mes_oficial)
            if dividir_metodologia
            else [{"indices": [idx]} for idx, aula in enumerate(aulas_mes_oficial) if not _eh_bloco_sem_pdf(aula)]
        )
        pdfs_individuais = [
            aulas_mes_oficial[grupo["indices"][0]].get("pdf")
            for grupo in grupos_individuais
            if aulas_mes_oficial[grupo["indices"][0]].get("pdf") is not None
        ]
        pdfs_necessarios = len(grupos_individuais) if dividir_metodologia else len([a for a in aulas_mes_oficial if not _eh_bloco_sem_pdf(a)])
        pdfs_prontos = len(pdfs_individuais)
        _render_painel_pdfs(
            modo=modo_upload_pdf,
            necessarios=pdfs_necessarios,
            carregados=pdfs_prontos,
            total_aulas=len(aulas_mes_oficial),
            dividir_metodologia=dividir_metodologia,
            selecionados=pdfs_individuais,
        )
    else:
        pdfs_necessarios = est_necessarios if est_necessarios > 0 else (len(_grupos_pdf_por_aula(aulas_mes_oficial)) if dividir_metodologia else len(aulas_para_pdf))

        if linhas_modelo_pdf > 0:
            pdf_unico_orientacao = bool(orientacao_estudos and qtd_aulas == 1 and pdfs_necessarios >= 1)
            if qtd_aulas == pdfs_necessarios or pdf_unico_orientacao:
                st.success(f"Quantidade de PDFs correta: {qtd_aulas}/{pdfs_necessarios} PDF(s) carregado(s).")
            elif qtd_aulas > 0:
                st.warning(f"Quantidade de PDFs incorreta: foram adicionados {qtd_aulas}, mas o plano requer exatamente {pdfs_necessarios} PDF(s).")
            else:
                st.info(f"Aguardando o envio de {pdfs_necessarios} PDF(s) para {linhas_modelo_pdf} aula(s).")

    if gerar_turma_espelho:
        # Determine num_rows_espelho based on 2nd class config if month is selected
        num_rows_espelho = num_rows
        
        if datas_horarios_mes_espelho:
            linhas_modelo_espelho = len(datas_horarios_mes_espelho)
            if linhas_modelo_espelho > 0:
                num_rows_espelho = linhas_modelo_espelho

        contexto_divisao_pdf_espelho = f"{contexto_divisao_pdf}|{turma_espelho}"
        _sincronizar_divisao_pdf_padrao(num_rows_espelho, dividir_metodologia, key_prefix="turma2_", contexto=contexto_divisao_pdf_espelho, lista_aulas=aulas_oficiais_modelo_espelho)
        
        aulas_envio_espelho = _coletar_aulas_envio(
            num_rows_espelho,
            pdfs_aulas_files,
            dividir_metodologia,
            auto_repetir_semana,
            replicar_pdf_unico=bool(orientacao_estudos and qtd_aulas == 1),
            key_prefix="turma2_",
            titulo_secao="2ª turma",
            modo_upload_individual=modo_upload_individual,
            preservar_datas_sincronizadas=bool(datas_horarios_mes_espelho),
            sequencia_pdf_esperada=sequencia_pdf_esperada_ae,
            permitir_um_dia_sem_pdf=usar_dia_sem_pdf_portugues,
            dia_sem_pdf_semana=dia_sem_pdf_portugues,
            frequencia_dia_sem_pdf=frequencia_dia_sem_pdf,
            modo_aula_dupla=modo_aula_dupla,
        )

st.markdown('<div class="section-title">🚀 Passo 1: Extração e Processamento</div>', unsafe_allow_html=True)
if HABILITAR_REVISAO_POS_GERACAO:
    st.markdown('<div class="section-subtitle">Confira a organização das aulas e inicie o processamento para transformar os PDFs em blocos prontos para revisão.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="section-subtitle">Confira a organização das aulas e gere o documento final diretamente, sem abrir a etapa de revisão na tela.</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="process-panel">
        <div class="panel-title">Tudo pronto para processar</div>
        <div class="panel-text">Revise rapidamente as datas, horários e PDFs vinculados. Quando estiver ok, o sistema prepara as aulas e segue para a geração do arquivo final.</div>
        <div class="panel-pills">
            <span class="panel-pill">Fluxo guiado</span>
            <span class="panel-pill">Menos retrabalho</span>
            <span class="panel-pill">DOCX direto</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
erro_processamento = str(st.session_state.get("erro_processamento") or "").strip()
if erro_processamento:
    st.error(erro_processamento)
    erro_processamento_detalhe = str(st.session_state.get("erro_processamento_detalhe") or "").strip()
    if erro_processamento_detalhe:
        with st.expander("Ver detalhe tecnico"):
            st.code(erro_processamento_detalhe)
geracao_em_andamento = bool(st.session_state.get("geracao_em_andamento", False))
if disciplina_cdp:
    st.checkbox(
        "Salvar este plano no histórico",
        key="salvar_historico_geracao",
        value=bool(st.session_state.get("salvar_historico_geracao", True)),
        help="Mantenha marcado para salvar este plano no histórico e habilitar a continuidade da sequência de PDFs na próxima geração.",
    )
rotulo_botao_geracao = "GERAR PLANO" if disciplina_cdp else ("PROCESSAR AULAS" if HABILITAR_REVISAO_POS_GERACAO else "PROCESSAR E GERAR DOCX")
if st.button(rotulo_botao_geracao, disabled=geracao_em_andamento, type="primary"):
    _limpar_erro_processamento()
    st.session_state["geracao_em_andamento"] = True
    aulas_mes_oficial_temp = [a for a in aulas_envio if not _eh_data_antecipacao(a["data"], mes, antecipacao_mes)] if deixar_ant_vazia else list(aulas_envio)
    aulas_para_pdf_temp = _filtrar_aulas_com_pdf_obrigatorio(
        aulas_envio,
        mes=mes,
        antecipacao_mes=antecipacao_mes,
        deixar_antecipacao_vazia=deixar_ant_vazia,
    )
    pdfs_enviados_val = len([g for g in _grupos_pdf_por_aula(aulas_mes_oficial_temp) if aulas_mes_oficial_temp[g["indices"][0]].get("pdf") is not None]) if (not disciplina_cdp and st.session_state.get("modo_upload_pdf") == "Um por aula") else len(pdfs_aulas_files or [])
    deixar_ant_vazia = bool(st.session_state.get("deixar_antecipacao_vazia", False))
    erro = validar_entrada(
        modelo_bytes, disciplina, disciplina_config, aulas_envio, professor, turma,
        bimestre, mes, aulas_previstas_manual, pdfs_enviados_val, pdfs_necessarios,
        deixar_antecipacao_vazia=deixar_ant_vazia,
        antecipacao_mes=antecipacao_mes,
    )
    if not erro:
        erro = validar_aulas_secundarias(
            gerar_turma_espelho,
            turma_espelho,
            aulas_envio_espelho if not disciplina_cdp else [],
            bool(disciplina_config.exige_pdf and not disciplina_cdp),
        )
    if erro:
        st.error(erro); st.session_state["geracao_em_andamento"] = False
    elif disciplina_cdp:
        planos_gerados = []
        with st.status("📚 Gerando...", expanded=True) as status:
            for t in [turma] + ([turma_espelho] if gerar_turma_espelho else []):
                planos_gerados.append(_gerar_docx_cdp_final(modelo_bytes, escola, professor, disciplina, t, mes, bimestre, semana, observacao, aulas_previstas_manual, cdp_aula_inicial, turma_cdp, modo_ia, modelo_openai, modelo_gemini, datas_horarios_mes))
            st.session_state["planos_gerados"] = planos_gerados
            salvou_historico = _salvar_planos_gerados_se_configurado(
                planos_gerados,
                professor,
                disciplina_saida,
                bimestre,
                mes,
            )
            _registrar_mensagem_memoria_plano(salvou_historico)
            status.update(label="✅ Concluído", state="complete", expanded=False)
        st.session_state["geracao_em_andamento"] = False; st.rerun()
    else:
        turmas_processadas, avisos = [], []
        blocos_processamento = [(turma, aulas_envio)] + ([(turma_espelho, aulas_envio_espelho)] if gerar_turma_espelho else [])
        total_pdfs_processamento = sum(
            len(_grupos_pdf_por_aula(aulas_bloco) if dividir_metodologia else aulas_bloco)
            for _, aulas_bloco in blocos_processamento
        )
        progresso_estado = {"atual": 0}
        with st.status("⏳ Extraindo...", expanded=True) as status:
            progress_bar = st.progress(0, text="Preparando os PDFs para extração...")
            try:
                for t, a in blocos_processamento:
                    def _callback_pdf(indice_pdf, total_pdf_turma, caminho_pdf, turma_atual=t):
                        progresso_estado["atual"] += 1
                        total_base = max(1, total_pdfs_processamento)
                        pct = min(100, int(round((progresso_estado["atual"] / total_base) * 100)))
                        nome_pdf = Path(str(caminho_pdf)).name
                        progress_bar.progress(
                            pct,
                            text=f"Processando {progresso_estado['atual']}/{total_base} PDF(s) • {turma_atual} • {nome_pdf}",
                        )
                        st.write(f"✓ Aula {indice_pdf + 1}: {nome_pdf} processada para {turma_atual}")

                    res = _extrair_aulas_dos_pdfs(
                        a,
                        disciplina,
                        t,
                        bimestre,
                        modo_ia,
                        modelo_openai,
                        modelo_gemini,
                        dividir_metodologia,
                        modalidade_eja,
                        usar_ae_priorizado=usar_ae_priorizado,
                        progress_callback=_callback_pdf,
                        professor=professor,
                        deixar_antecipacao_vazia=deixar_ant_vazia,
                        mes=mes,
                        antecipacao_mes=antecipacao_mes,
                    )
                    turmas_processadas.append({"turma": t, "aulas": res["aulas"]})
                    avisos_turma = []
                    if res.get("avisos_repeticao"):
                        avisos_turma.extend(res["avisos_repeticao"])
                    if res.get("avisos_ae"):
                        avisos_turma.extend(res["avisos_ae"])
                    if res.get("avisos_ia"):
                        avisos_turma.extend(res["avisos_ia"])
                    if avisos_turma:
                        avisos.append({"turma": t, "avisos": avisos_turma})
                if HABILITAR_REVISAO_POS_GERACAO:
                    progress_bar.progress(100, text="Extração concluída. Preparando a revisão...")
                    status.update(label="✅ Extraído!", state="complete", expanded=False)
                    st.session_state["turmas_processadas"] = turmas_processadas
                    st.session_state["avisos_processamento"] = avisos
                    st.session_state["revisao_token"] = st.session_state.get("revisao_token", 0) + 1
                else:
                    progress_bar.progress(100, text="Extração concluída. Gerando DOCX final...")
                    planos_gerados = _gerar_planos_finais_sem_revisao(
                        modelo_bytes,
                        turmas_processadas,
                        escola,
                        professor,
                        disciplina,
                        componente_curricular,
                        mes,
                        bimestre,
                        semana,
                        observacao,
                        aulas_previstas_manual,
                    )
                    st.session_state["planos_gerados"] = planos_gerados
                    st.session_state["turmas_processadas"] = []
                    st.session_state["avisos_processamento"] = avisos
                    st.session_state.pop("revisao_token", None)
                    _limpar_revisao_aulas()
                    _salvar_planos_na_pasta_finalizados(planos_gerados, disciplina_saida, professor, mes=mes)
                    salvou_historico = _salvar_planos_gerados_se_configurado(
                        planos_gerados,
                        professor,
                        disciplina_saida,
                        bimestre,
                        mes,
                    )
                    _registrar_mensagem_memoria_plano(salvou_historico)
                    status.update(label="✅ DOCX gerado!", state="complete", expanded=False)
            except Exception as e:
                _registrar_erro_processamento(e)
            st.session_state["geracao_em_andamento"] = False
            st.rerun()
turmas_revisadas = []
alteracoes_detectadas = False

if st.session_state.get("turmas_processadas"):
    turmas_revisadas, alteracoes_detectadas = renderizar_passo_revisao(
        professor=professor,
        disciplina=disciplina,
        disciplina_saida=disciplina_saida,
        turma=turma,
        mes=mes,
        bimestre=bimestre,
        modo_ia=modo_ia,
        modo_upload_pdf=modo_upload_pdf,
        pasta_pdfs_auto=pasta_pdfs_auto,
        pdfs_selecionados_tela=pdfs_selecionados_tela,
        modelo_bytes=modelo_bytes,
        escola=escola,
        componente_curricular=componente_curricular,
        semana=semana,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
        fn_gerar_docx_final=_gerar_docx_final,
        fn_salvar_planos_na_pasta_finalizados=_salvar_planos_na_pasta_finalizados,
        fn_salvar_planos_gerados_se_configurado=_salvar_planos_gerados_se_configurado,
        fn_registrar_mensagem_memoria_plano=_registrar_mensagem_memoria_plano,
    )

if st.session_state.get("planos_gerados"):
    if alteracoes_detectadas:
        st.warning("⚠️ **Alterações detectadas nos campos da tela!** Os arquivos de download abaixo ainda contêm a versão anterior. Clique no botão abaixo para atualizar os arquivos finais com as suas correções.")
        if st.button("🔄 ATUALIZAR ARQUIVOS DOCX COM AS CORREÇÕES DA TELA", type="primary"):
            planos_gerados = []
            for tr in turmas_revisadas:
                planos_gerados.append(_gerar_docx_final(modelo_bytes, tr["aulas"], escola, professor, disciplina, componente_curricular, tr["turma"], mes, bimestre, semana, observacao, aulas_previstas_manual))
            st.session_state["planos_gerados"] = planos_gerados
            
            # Salva localmente e no histórico
            _salvar_planos_na_pasta_finalizados(planos_gerados, disciplina_saida, professor, mes=mes)
            if st.session_state.get("salvar_historico_geracao", False):
                _salvar_planos_gerados_se_configurado(planos_gerados, professor, disciplina_saida, bimestre, mes)
            st.success("✓ Arquivos finais atualizados e salvos com as novas correções da tela!")
            st.rerun()

    planos_gerados = st.session_state["planos_gerados"]
    dir_destino = (
        _resolver_caminho_professor_disciplina(professor, disciplina_saida, mes=mes)
        if professor
        else (PLANOS_FINALIZADOS_DIR / _normalizar_nome_diretorio(mes) if mes else PLANOS_FINALIZADOS_DIR)
    )
    st.info(f"📂 Os arquivos `.docx` estão salvos e atualizados na pasta: `{dir_destino}`")

    resumo_docx = resumir_proveniencia_docx(
        st.session_state.get("turmas_processadas") or []
    )
    total_com_docx = (
        resumo_docx["docx_literal"] + resumo_docx["docx_refinado_ia"]
    )
    if total_com_docx:
        detalhes_origem = []
        if resumo_docx["docx_literal"]:
            detalhes_origem.append(
                f'{resumo_docx["docx_literal"]} aula(s) copiada(s) literalmente'
            )
        if resumo_docx["docx_refinado_ia"]:
            detalhes_origem.append(
                f'{resumo_docx["docx_refinado_ia"]} aula(s) refinada(s) pela IA a partir do DOCX'
            )
        arquivos_origem = ", ".join(resumo_docx["arquivos"])
        mensagem_origem = (
            "Fonte dos textos centrais confirmada: " + "; ".join(detalhes_origem) + "."
        )
        if arquivos_origem:
            mensagem_origem += f" Arquivo(s): {arquivos_origem}."
        st.success(mensagem_origem)

    if resumo_docx["fallback"]:
        st.warning(
            f'Atenção: {resumo_docx["fallback"]} aula(s) não puderam usar o '
            "DOCX externo. O motivo está detalhado abaixo."
        )
        with st.expander("Ver aulas que não utilizaram o DOCX externo"):
            for falha in resumo_docx["falhas"]:
                identificacao = f'Turma {falha["turma"]} - Aula {falha["numero_aula"]}'
                if falha["tema"]:
                    identificacao += f' - {falha["tema"]}'
                st.write(f'**{identificacao}:** {falha["motivo"]}')
    
    mensagem_historico = str(st.session_state.pop("mensagem_historico_planos", "") or "").strip()
    mensagem_historico_tipo = str(st.session_state.pop("mensagem_historico_planos_tipo", "") or "").strip()
    if mensagem_historico:
        if mensagem_historico_tipo == "success":
            st.success(mensagem_historico)
        else:
            st.info(mensagem_historico)
    st.markdown('<div class="section-title">📥 Passo 3: Download</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Baixe o arquivo final já pronto para envio ou salve um pacote com todas as turmas processadas.</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="download-panel">
            <div class="panel-title">Arquivos finais disponíveis</div>
            <div class="panel-text">O sistema preparou <strong>{len(planos_gerados)}</strong> arquivo(s) final(is). Você pode baixar um documento único ou um pacote completo, conforme a quantidade de turmas processadas.</div>
            <div class="panel-pills">
                <span class="panel-pill">DOCX pronto</span>
                <span class="panel-pill">Compatível com modelo</span>
                <span class="panel-pill">Entrega organizada</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if len(planos_gerados) == 1:
        st.download_button("Baixar DOCX", data=planos_gerados[0]["docx_bytes"].getvalue(), file_name=nome_arquivo_plano(planos_gerados[0]["turma"], disciplina_saida, ia_usada=planos_gerados[0].get("ia_usada", False)), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.download_button("📦 Baixar ZIP", data=_montar_zip_planos(planos_gerados, disciplina_saida), file_name="planos.zip", mime="application/zip")
        for p in planos_gerados:
            st.download_button(f"Baixar DOCX - {p['turma']}", data=p["docx_bytes"].getvalue(), file_name=nome_arquivo_plano(p["turma"], disciplina_saida, ia_usada=p.get("ia_usada", False)), key=f"dl_{p['turma']}")
