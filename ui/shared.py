import streamlit as st
import tempfile
import re
import os
import unicodedata
import base64
from datetime import date, timedelta, datetime
from pathlib import Path

from core.constantes import (
    HORARIOS_AULA,
    HORARIOS_SIMPLES,
    HORARIOS_DUPLAS,
    HORARIOS_INTEGRAIS,
    TURNOS_HORARIOS,
    TURNOS_AULAS_ESPECIAIS,
    MESES,
    DIAS_SEMANA_CADASTRO,
    AULAS_SEMANA_OPCOES,
    EXTENSAO_MES_OPCOES,
    EXTENSAO_MES_VALORES,
)
from core.disciplinas import eh_cdp, eh_cdp_contextual, TURMAS_CDP_MULTISSERIADA
from core.database import obter_professores_db
from core.professores_planos import (
    carregar_professores_dos_planos,
    diagnosticar_modelos_professores,
)

# ==========================================
# CONSTANTES DE INTERFACE COMPARTILHADAS
# ==========================================
HORARIOS_LABELS = {item: f"{item[0]} - {item[1]}" for item in HORARIOS_AULA}
TURNO_HORARIO_PERSONALIZADO = "Personalizado"
PREFIXO_HORARIO_PERSONALIZADO = "Personalizado:"
ROTULO_HORARIO_PERSONALIZADO = "Horário personalizado"

DIAS_SEMANA_COMPLETOS = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]

TURMAS_PADRAO = ["(selecione a turma)"]
TURMAS_PADRAO += [f"{ano}º ANO {letra}" for ano in range(1, 10) for letra in ["A", "B", "C", "D", "E", "F"]]
TURMAS_PADRAO += [f"{ano}º ANO" for ano in range(1, 10)]
TURMAS_PADRAO += [
    "8º e 9º ano",
    "1º Termo",
    "2º Termo",
    "3º Termo",
    "MULTISSERIADO 1º, 2º e 3º ano",
    "MULTISSERIADO 4º e 5º ano",
]
TURMAS_PADRAO += [turma for turma in TURMAS_CDP_MULTISSERIADA if turma not in TURMAS_PADRAO]
TURMAS_PADRAO += ["Outra (digitar)"]


# ==========================================
# UTILITÁRIOS E RÓTULOS DE DATAS/HORÁRIOS
# ==========================================
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
def _rotulo_horario(horario) -> str:
    if isinstance(horario, tuple) and len(horario) >= 2:
        return HORARIOS_LABELS.get(horario, f"{horario[0]} - {horario[1]}")
    return str(horario or "")

def _rotulo_data_aula_com_dia(data_aula) -> str:
    if not hasattr(data_aula, "weekday"):
        return ""
    return f"{data_aula.strftime('%d/%m/%Y')} • {DIAS_SEMANA_COMPLETOS[data_aula.weekday()]}"

def _serializar_horarios_padronizados(horarios) -> str:
    return "\n".join(_rotulo_horario(item) for item in horarios or [] if _rotulo_horario(item).strip())

def _tipo_horario(item) -> str:
    if item in HORARIOS_DUPLAS:
        return "Dupla"
    return "Simples"

def _slug_download(texto: str) -> str:
    texto = str(texto or "").replace("º", "o").replace("°", "o").replace("ª", "a")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto).strip("_")

def nome_arquivo_plano(turma: str, disciplina: str, ia_usada: bool = False) -> str:
    # Formata a turma para 1o_ANO_A
    s_turma = str(turma or "").upper().replace("º", "o").replace("°", "o").replace("ª", "a")
    s_turma = unicodedata.normalize("NFKD", s_turma)
    s_turma = "".join(ch for ch in s_turma if not unicodedata.combining(ch))
    s_turma = re.sub(r"[^A-Za-z0-9_-]+", "_", s_turma).strip("_")
    
    # Formata a disciplina para Química -> Quimica
    s_disc = _slug_download(disciplina).title()
    
    s_ia = "_In" if ia_usada else ""
    return f"Plano_{s_turma}_{s_disc}{s_ia}.docx"

# ==========================================
# PARSERS E NORMALIZADORES DE TEXTO
# ==========================================
def _normalizar_texto_simples(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto.upper()

def _normalizar_label_aula(texto: str) -> str:
    texto = (texto or "").lower()
    texto = texto.replace("º", "ª").replace("°", "ª")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def _slug_key(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(texto or "")).strip("_") or "item"

def _chave_cadastro(
    professor: str,
    disciplina: str,
    turma: str,
    componente_curricular: str = "",
) -> tuple[str, str, str, str]:
    def norm(valor: str) -> str:
        valor = unicodedata.normalize("NFKD", str(valor or ""))
        valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", valor).strip().upper()
    return norm(professor), norm(disciplina), norm(turma), norm(componente_curricular)

def _eh_cadastro_cdp_eja(disciplina: str, componente_curricular: str = "") -> bool:
    base = f"{disciplina} {componente_curricular}".upper()
    return eh_cdp(disciplina) or eh_cdp_contextual(disciplina) or "CDP" in base or "EJA" in base

def _arquivo_existe(caminho: str) -> bool:
    try:
        return bool(caminho and Path(caminho).exists())
    except OSError:
        return False

# ==========================================
# CACHES E LEITURAS DE ARQUIVOS
# ==========================================
@st.cache_data(show_spinner=False, ttl=300)
def _ler_bytes_arquivo_cache(caminho: str) -> bytes | None:
    caminho_path = Path(caminho)
    if not caminho_path.exists():
        return None
    return caminho_path.read_bytes()

@st.cache_data(show_spinner=False, ttl=300)
def _carregar_professores_dos_planos_cache():
    return carregar_professores_dos_planos()

@st.cache_data(show_spinner=False, ttl=120)
def _diagnosticar_modelos_professores_cache():
    return diagnosticar_modelos_professores()

# ==========================================
# CSS E CONFIGURAÇÕES DE ENVIROMENT
# ==========================================
# Cache removed to allow immediate UI updates upon CSS modification
def _ler_css_app(caminho: str) -> str:
    return Path(caminho).read_text(encoding="utf-8")

def carregar_css(base_dir: Path):
    css_file = base_dir / "assets" / "style.css"
    if css_file.exists():
        st.markdown(f"<style id='planos-luan-theme'>{_ler_css_app(str(css_file))}</style>", unsafe_allow_html=True)

def carregar_chaves_locais(base_dir: Path):
    caminho_chaves = base_dir / "chaves.txt"
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

def _rotulo_cadastro(cadastro: dict) -> str:
    horario = str(cadastro.get("horario") or "sem horario").replace("\n", " | ")
    componente = str(cadastro.get("componente_curricular") or "").strip()
    disciplina = str(cadastro.get("disciplina") or "DISCIPLINA")
    if componente:
        disciplina = f"{disciplina} | {componente}"
    return " | ".join(
        [
            str(cadastro.get("professor") or "PROFESSOR"),
            disciplina,
            str(cadastro.get("turma") or "TURMA"),
            horario,
        ]
    )

def _aulas_disponiveis_turno(turno: str) -> list[int]:
    if turno == TURNO_HORARIO_PERSONALIZADO:
        return []
    aulas_especiais = TURNOS_AULAS_ESPECIAIS.get(turno)
    if aulas_especiais:
        return sorted(aulas_especiais)
    slots = TURNOS_HORARIOS.get(turno) or TURNOS_HORARIOS["Manhã"]
    return list(range(1, len(slots)))

def _montar_horario_flexivel(turno: str, aulas: list[int | str]):
    aulas_disponiveis = _aulas_disponiveis_turno(turno)
    numeros = []
    for aula in aulas or []:
        match = re.search(r"\d+", str(aula))
        if match:
            numero = int(match.group(0))
            if numero in aulas_disponiveis:
                numeros.append(numero)
    numeros = sorted(set(numeros))
    if not numeros:
        return None

    aulas_especiais = TURNOS_AULAS_ESPECIAIS.get(turno)
    if aulas_especiais:
        if len(numeros) == 1:
            return aulas_especiais[numeros[0]]
        if numeros == [6, 7]:
            return HORARIOS_INTEGRAIS[7]
        if numeros == [8, 9]:
            return HORARIOS_INTEGRAIS[8]
        intervalos = [aulas_especiais[numero][0] for numero in numeros]
        return (" | ".join(intervalos), _formatar_label_aulas(numeros))

    slots = TURNOS_HORARIOS.get(turno) or TURNOS_HORARIOS["Manhã"]
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
    if (
        isinstance(horario, tuple)
        and len(horario) >= 2
        and horario[1] == ROTULO_HORARIO_PERSONALIZADO
    ):
        numeros = _numeros_aulas_de_texto(horario[0])
        return TURNO_HORARIO_PERSONALIZADO, [f"{numero}ª" for numero in numeros]
    texto = _rotulo_horario(horario)
    horario_integral = _horario_integral_por_texto(texto)
    if horario_integral:
        turno_integral = next(iter(TURNOS_AULAS_ESPECIAIS))
        numeros = _numeros_aulas_de_texto(texto)
        return turno_integral, [f"{numero}ª" for numero in numeros]
    horarios_texto = _horarios_extraidos_texto(texto)
    turno = _turno_por_horario_inicio(horarios_texto[0], contexto) if horarios_texto else _turno_por_horario_inicio("", contexto)
    numeros = _numeros_aulas_de_texto(texto)
    return turno, [f"{numero}ª" for numero in numeros]

# ==========================================
# UTILITÁRIOS ADICIONAIS DE DATAS E AULAS
# ==========================================
def _sincronizar_divisao_pdf_padrao(
    num_rows: int,
    dividir_metodologia: bool,
    key_prefix: str = "",
    contexto: str = "",
) -> None:
    assinatura_chave = f"{key_prefix}dividir_metodologia_assinatura"
    assinatura_atual = f"v3|{bool(dividir_metodologia)}|{int(num_rows or 0)}|{contexto}"
    assinatura_anterior = st.session_state.get(assinatura_chave)
    acabou_de_ativar = bool(dividir_metodologia) and assinatura_anterior != assinatura_atual

    st.session_state[assinatura_chave] = assinatura_atual
    if not dividir_metodologia:
        return

    for idx in range(int(num_rows or 0)):
        chave = f"{key_prefix}dividir_pdf_aula_{idx}"
        if acabou_de_ativar or chave not in st.session_state:
            st.session_state[chave] = bool(idx % 2 == 0 and idx < int(num_rows or 0) - 1)

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

def _dia_semana_numero(texto: str):
    dias = {
        "SEGUNDA": 0, "SEGUNDA FEIRA": 0, "TERCA": 1, "TERCA FEIRA": 1,
        "QUARTA": 2, "QUARTA FEIRA": 2, "QUINTA": 3, "QUINTA FEIRA": 3,
        "SEXTA": 4, "SEXTA FEIRA": 4, "SABADO": 5, "DOMINGO": 6,
    }
    return dias.get(_normalizar_texto_simples(texto).replace("-", " "))

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

def _partes_horario_config(texto: str) -> list[str]:
    texto = str(texto or "").strip()
    if not texto:
        return []
    partes = [parte.strip() for parte in re.split(r"[;\n]+", texto) if parte.strip()]
    if len(partes) == 1:
        partes = [parte.strip() for parte in re.split(r",\s*(?=\d{1,2}h)", texto, flags=re.I) if parte.strip()]
    return partes

def _sugerir_horario_cadastrado(trecho: str, contexto: str = ""):
    trecho_norm = _normalizar_label_aula(trecho)
    horarios_no_texto = _horarios_extraidos_texto(trecho)

    horario_personalizado = _horario_personalizado_por_texto(trecho)
    if horario_personalizado:
        return horario_personalizado

    horario_integral = _horario_integral_por_texto(trecho)
    if horario_integral:
        return horario_integral
    
    # Horário Flexível
    numeros_a = []
    base_a = re.sub(r"\b\d{1,2}h\d*\b", " ", str(trecho or "").lower())
    for numero in range(1, 7):
        if re.search(rf"\b{numero}\s*(?:ª|º|a|o)?\b", base_a):
            numeros_a.append(numero)
    numeros_a = sorted(set(numeros_a))
    
    if numeros_a:
        turno = _turno_por_horario_inicio(horarios_no_texto[0], contexto) if horarios_no_texto else _turno_por_horario_inicio("", contexto)
        slots = TURNOS_HORARIOS.get(turno) or TURNOS_HORARIOS["Manhã"]
        max_aulas = len(slots) - 1
        numeros = [n for n in numeros_a if 1 <= n <= max_aulas]
        if numeros:
            primeira = numeros[0]
            ultima = numeros[-1]
            consecutivas = numeros == list(range(primeira, ultima + 1))
            inicio = slots[primeira - 1]
            fim = slots[ultima if consecutivas else ultima - 1]
            label = _formatar_label_aulas(numeros)
            horario_flexivel = (inicio, label) if len(numeros) == 1 else (f"{inicio} - {fim}", label)
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

def _prefixo_turno(contexto: str) -> str:
    texto = _normalizar_texto_simples(contexto)
    if "NOITE" in texto or "NOTURNO" in texto:
        return "19"
    if "TARDE" in texto:
        return "13"
    return "07"

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

def _numeros_aulas_de_texto(texto: str) -> list[int]:
    base = re.sub(r"\b\d{1,2}h\d*\b", " ", str(texto or "").lower())
    numeros = []
    for numero in range(1, 10):
        if re.search(rf"\b{numero}\s*(?:ª|º|a|o)?\b", base):
            numeros.append(numero)
    return numeros

def _formatar_label_aulas(numeros: list[int]) -> str:
    partes = [f"{numero}ª" for numero in sorted(set(numeros))]
    if not partes:
        return ""
    if len(partes) == 1:
        return f"{partes[0]} aula"
    if len(partes) == 2:
        return f"{partes[0]} e {partes[1]} aula"
    return f"{', '.join(partes[:-1])} e {partes[-1]} aula"

def _horario_personalizado_por_texto(trecho: str):
    texto = str(trecho or "").strip()
    if not texto.lower().startswith(PREFIXO_HORARIO_PERSONALIZADO.lower()):
        return None
    valor = texto[len(PREFIXO_HORARIO_PERSONALIZADO):].strip()
    if not valor:
        return None
    return (valor, ROTULO_HORARIO_PERSONALIZADO)

def _horario_integral_por_texto(trecho: str):
    horarios_texto = _horarios_extraidos_texto(trecho)
    if not horarios_texto:
        return None
    numeros = _numeros_aulas_de_texto(trecho)
    inicios_padrao = {
        horarios[0]
        for candidato_padrao in HORARIOS_SIMPLES
        if candidato_padrao not in HORARIOS_INTEGRAIS
        for horarios in [_horarios_extraidos_texto(candidato_padrao[0])]
        if horarios
    }
    for candidato in HORARIOS_INTEGRAIS:
        numeros_candidato = _numeros_aulas_de_texto(candidato[1])
        if numeros and numeros_candidato != numeros:
            continue
        horarios_candidato = _horarios_extraidos_texto(candidato[0])
        if not horarios_candidato:
            continue
        if (
            len(horarios_texto) == 1
            and horarios_texto[0] == horarios_candidato[0]
            and horarios_texto[0] not in inicios_padrao
        ):
            return candidato
        if (
            horarios_texto[0] == horarios_candidato[0]
            and horarios_texto[-1] == horarios_candidato[-1]
        ):
            return candidato
    return None

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

def _defaults_grade_horarios(dia_texto: str = "", horario_texto: str = "", contexto: str = "") -> dict[str, dict[str, object]]:
    defaults: dict[str, dict[str, object]] = {}
    dias = _partes_dia_config(dia_texto)
    partes_horario = _partes_horario_config(horario_texto)
    for idx, dia in enumerate(dias):
        dia_num = _dia_semana_numero(dia)
        if dia_num is None or dia_num >= len(DIAS_SEMANA_CADASTRO):
            continue
        trecho_horario = (
            partes_horario[idx]
            if idx < len(partes_horario)
            else (partes_horario[0] if partes_horario else "")
        )
        horario = _sugerir_horario_cadastrado(trecho_horario, contexto)
        if horario:
            turno, aulas = _turno_e_aulas_de_horario(horario, contexto)
            valor = {"turno": turno, "aulas": aulas}
            if turno == TURNO_HORARIO_PERSONALIZADO:
                valor["horario_personalizado"] = str(horario[0])
        elif trecho_horario:
            valor = {
                "turno": TURNO_HORARIO_PERSONALIZADO,
                "aulas": [f"{numero}ª" for numero in _numeros_aulas_de_texto(trecho_horario)],
                "horario_personalizado": trecho_horario,
            }
        else:
            valor = {"turno": "Manhã", "aulas": []}
        defaults[DIAS_SEMANA_CADASTRO[dia_num]] = valor
    return defaults

def _asset_data_uri(nome_arquivo: str, mime_type: str = "image/svg+xml") -> str:
    path = Path(__file__).resolve().parent.parent / "assets" / nome_arquivo
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"

def _mes_numero_app(mes: str) -> int:
    meses = {
        "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
        "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
    }
    return meses.get(_normalizar_texto_simples(mes), date.today().month)

def _datas_do_mes_por_dia(mes: str, dia_semana: int, ano: int | None = None, extensao: int = 0) -> list[date]:
    from core.calendario import fim_periodo_mes_com_extensao, datas_por_dia_ate_limite
    ano = ano or date.today().year
    mes_num = _mes_numero_app(mes)
    inicio = date(ano, mes_num, 1)
    fim = fim_periodo_mes_com_extensao(ano, mes_num, extensao)
    return datas_por_dia_ate_limite(inicio, fim, dia_semana)

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

def _datas_horarios_do_mes(config: dict, mes: str, turma: str = "", extensao: int = 0) -> list[dict]:
    from core.calendario import fim_periodo_mes_com_extensao
    if not config or not mes:
        return []
    if config.get("repetir_modelo_semanal"):
        base = list(config.get("datas_horarios") or [])
        if not base:
            return []
        primeira_data = next((item.get("data") for item in base if hasattr(item.get("data"), "weekday")), None)
        if not primeira_data:
            return []
        inicio_semana_base = primeira_data - timedelta(days=primeira_data.weekday())

        molde_por_dia: dict[int, dict] = {}
        for item in base:
            data_aula = item.get("data")
            if not hasattr(data_aula, "weekday"):
                continue
            dia = data_aula.weekday()
            if dia not in molde_por_dia:
                molde_por_dia[dia] = {
                    "offset_dias": dia,
                    "horario": item.get("horario") or "",
                    "aula": item.get("aula") or "",
                }
        if not molde_por_dia:
            return []
        molde = sorted(molde_por_dia.values(), key=lambda m: m["offset_dias"])

        ano = date.today().year
        mes_num = _mes_numero_app(mes)
        inicio_mes = date(ano, mes_num, 1)
        fim_periodo = fim_periodo_mes_com_extensao(ano, mes_num, extensao)

        inicio_bloco = inicio_mes - timedelta(days=inicio_mes.weekday())

        itens = []
        while inicio_bloco <= fim_periodo:
            for entrada in molde:
                nova_data = inicio_bloco + timedelta(days=entrada["offset_dias"])
                if nova_data < date(ano, mes_num, 1) or nova_data > fim_periodo:
                    continue
                itens.append({
                    "data": nova_data,
                    "horario": entrada["horario"],
                    "aula": entrada["aula"],
                })
            inicio_bloco += timedelta(days=7)
        return sorted(itens, key=lambda item: (item["data"], _indice_horario(item["horario"])))

    itens = []
    for padrao in _padroes_horario_config(config, turma):
        for data_aula in _datas_do_mes_por_dia(mes, padrao["dia"], extensao=extensao):
            itens.append({"data": data_aula, "horario": padrao["horario"]})
    return sorted(itens, key=lambda item: (item["data"], _indice_horario(item["horario"])))
