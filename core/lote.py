import os
import re
import unicodedata
import hashlib
from pathlib import Path

import pdfplumber

from config import PDF_TEXTO_LIMITE_CHARS
from core.avaliacao import gerar_acessibilidade_dinamica, gerar_acompanhamento_dinamico
from core.metodologia_texto import ajustar_verbos_para_infinitivo
from core.projeto_vida_escopo import buscar_item_projeto_vida, montar_aprendizagem_projeto_vida
from core.qualidade_metodologica import detectar_contexto_metodologico, naturalizar_metodologia_professor, revisar_metodologia
from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas
from divisor_metodologia import processar_pdf_e_dividir_metodologia


def _limpar_linhas(texto: str) -> list[str]:
    linhas = []
    for linha in (texto or "").splitlines():
        linha = re.sub(r"\s+", " ", linha).strip()
        if linha:
            linhas.append(linha)
    return linhas


def _extrair_texto_pdf(caminho_pdf: str) -> str:
    partes = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            partes.append(pagina.extract_text() or "")
            if sum(len(p) for p in partes) >= PDF_TEXTO_LIMITE_CHARS:
                break
    return "\n".join(partes)[:PDF_TEXTO_LIMITE_CHARS]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


_PADRAO_ROTULO_PERIODO_ENSINO = re.compile(
    r"^(?:[1-4]\s*(?:o|º|°|ª|a)?\s*)?bimestre(?:\s+ensino(?:\s+(?:medio|fundamental))?)?$",
    flags=re.I,
)


def _linha_periodo_ensino(texto: str) -> bool:
    normalizado = _normalizar(texto).strip(" .:-")
    return bool(_PADRAO_ROTULO_PERIODO_ENSINO.fullmatch(normalizado))


def _limpar_titulo_material(linha: str, disciplina: str) -> str:
    titulo = re.sub(r"\s+", " ", linha or "").strip(" -–—")
    disciplina_norm = _normalizar(disciplina)
    titulo_norm = _normalizar(titulo)

    if _linha_periodo_ensino(titulo_norm):
        return ""

    if titulo_norm == disciplina_norm:
        return ""

    if disciplina_norm and titulo_norm.startswith(disciplina_norm):
        titulo = titulo[len(disciplina):].strip(" -–—:")

    titulo = re.sub(r"\s+(?:[1-4][º°oªa]?)\s*bimestre\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+ensino\s+(?:fundamental|m[eé]dio)\b.*$", "", titulo, flags=re.I)
    titulo = re.sub(r"\s+anos?\s+(?:iniciais|finais)\b.*$", "", titulo, flags=re.I)
    if _linha_periodo_ensino(titulo):
        return ""
    return titulo.strip(" -–—")


def _linha_generica(linha: str, disciplina: str) -> bool:
    texto = _normalizar(linha)
    disciplina_norm = _normalizar(disciplina)
    genericas = {
        "",
        disciplina_norm,
        "ensino fundamental",
        "ensino medio",
        "anos iniciais",
        "anos finais",
        "material digital",
        "aula digital",
    }
    if texto in genericas:
        return True
    if "gps" in texto and "guia" in texto:
        return True
    if "praticas de sala de aula" in texto:
        return True
    if _linha_periodo_ensino(texto):
        return True
    return bool(re.fullmatch(r"(?:[1-4][oº°]?\s*)?bimestre", texto))


def _linha_rotulo_aula(normalizada: str) -> bool:
    return bool(re.match(r"^aula\s*(?:n[.o]?\s*)?\d{1,3}\b", normalizada or ""))


def _titulo_em_linha_aula(linha: str) -> str:
    texto = re.sub(r"\s+", " ", str(linha or "")).strip(" -:–—")
    match = re.match(r"^aula\s*(?:n[.o]?\s*)?\d{1,3}\s*(?:[|:-]|–|—)?\s*(.+)$", texto, flags=re.I)
    if not match:
        return ""
    titulo = match.group(1).strip(" -:–—")
    if not titulo:
        return ""
    if _linha_generica(titulo, ""):
        return ""
    if _normalizar(titulo).startswith(("ensino fundamental", "ensino medio", "bimestre")):
        return ""
    return titulo


def _linhas_relevantes(texto: str, disciplina: str, tema: str) -> list[str]:
    relevantes = []
    vistos = set()
    for linha in _limpar_linhas(texto):
        linha = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(linha)
        if not linha or normalizada in vistos:
            continue
        if _linha_generica(linha, disciplina) or _normalizar(tema) == normalizada:
            continue
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            continue
        vistos.add(normalizada)
        relevantes.append(linha)
    return relevantes


def _extrair_titulo_multilinha(texto: str, disciplina: str) -> str:
    linhas = _limpar_linhas(texto)
    partes = []
    for linha in linhas[:8]:
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(titulo)
        if not titulo or _linha_generica(titulo, disciplina) or normalizada == _normalizar(disciplina):
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            if partes:
                break
            continue
        partes.append(titulo)
        if len(partes) >= 4:
            break

    if not partes:
        return ""

    if len(partes) == 1:
        return _limpar_titulo_material(partes[0], disciplina)

    return _limpar_titulo_material(_juntar_partes_titulo(partes), disciplina)


def _titulo_deve_juntar_continuacao(primeira: str, segunda: str = "") -> bool:
    primeira_limpa = re.sub(r"\s+", " ", str(primeira or "")).strip(" -:")
    segunda_limpa = re.sub(r"\s+", " ", str(segunda or "")).strip(" -:")
    primeira_norm = _normalizar(primeira_limpa)
    segunda_norm = _normalizar(segunda_limpa)
    if not primeira_norm:
        return False
    finais_pendentes = (
        " a",
        " as",
        " o",
        " os",
        " um",
        " uma",
        " de",
        " da",
        " do",
        " das",
        " dos",
        " e",
        " em",
        " para",
        " por",
        " com",
        " sem",
        " sobre",
    )
    if primeira_norm.endswith(finais_pendentes):
        return True
    if segunda_norm.startswith(("por ", "para ", "com ", "sem ", "em ", "e ", "ou ", "que ", "da ", "de ", "do ")):
        return True
    return False


def _juntar_partes_titulo(partes: list[str]) -> str:
    if not partes:
        return ""
    titulo = str(partes[0] or "").rstrip(" -:")
    for proxima in partes[1:]:
        proxima_limpa = str(proxima or "").lstrip("-: ").strip()
        if not proxima_limpa:
            continue
        titulo_limpo = titulo.rstrip()
        if (
            _titulo_deve_juntar_continuacao(titulo_limpo, proxima_limpa)
            or len(titulo_limpo) <= 28
            or (proxima_limpa[:1].islower() and len(titulo_limpo) <= 70)
            or titulo_limpo.endswith((":", ";", "-", "–", "—"))
        ):
            separador = " - " if _normalizar(proxima_limpa).startswith("parte ") else " "
            titulo = f"{titulo_limpo}{separador}{proxima_limpa}".strip()
            continue
        break
    return titulo


_ORIENTACAO_ESTUDOS_TITULOS = {
    ("missao", 1): "Jogos com palavras e imagens",
    ("missao", 2): "Para chorar de rir",
    ("missao", 3): "Da charge à notícia",
    ("missao", 4): "Que tirada!",
    ("missao", 5): "Vamos a fundo nos assuntos",
    ("missao", 6): "Uma palavra puxa a outra",
    ("missao", 7): "A trama do texto",
    ("missao", 8): "Por dentro dos verbetes",
    ("missao", 9): "Narrativas breves",
    ("missao", 10): "A voz da poesia",
    ("missao", 11): "Um mergulho no cordel",
    ("missao", 12): "Poema para mim e para você",
    ("missao", 13): "Lendas e narrativa",
    ("missao", 14): "Qual é a moral da história",
    ("missao", 15): "O texto no teatro",
    ("missao", 16): "Opinião versus fato",
    ("trilha", 1): "Crônicas e conectivos",
    ("trilha", 2): "Romances e conectivos",
    ("trilha", 3): "Crônicas, tirinhas e conectivos",
    ("trilha", 4): "Histórias em quadrinhos e humor",
    ("trilha", 5): "Contos e finalidade do texto",
    ("trilha", 6): "Causos e variação linguística",
    ("trilha", 7): "Projetos culturais e coesão textual",
    ("trilha", 8): "Cartas de leitor e argumento",
    ("trilha", 9): "Elementos da notícia",
    ("trilha", 10): "Notícias e opinião",
    ("trilha", 11): "Notícias, charges e crítica",
    ("trilha", 12): "Carta aberta e argumentação",
    ("trilha", 13): "Muito mais informações",
    ("trilha", 14): "Reportagens e informação",
    ("trilha", 15): "Campanhas comunitárias e informação",
    ("trilha", 16): "Textos de divulgação científica",
    ("jornada", 1): "Nas entrelinhas da notícia",
    ("jornada", 2): "Repercussão das notícias nos quadrinhos",
    ("jornada", 3): "Contando o dia a dia",
    ("jornada", 4): "Diferentes formas de dizer a mesma coisa",
    ("jornada", 5): "Linguagem poética, versos e rimas",
    ("jornada", 6): "Lendas e mitos: rever com olhos novos",
    ("jornada", 7): "Entre manifestos e outras reivindicações",
    ("jornada", 8): "Das resenhas às videorresenhas",
    ("jornada", 9): "Informação visual",
    ("jornada", 10): "Informações em infográficos, gráficos, tabelas e esquemas",
    ("jornada", 11): "Linguagem poética: poema, slam e canção",
    ("jornada", 12): "Palavras, ilustrações e paratextos",
    ("jornada", 13): "Recursos midiáticos",
    ("jornada", 14): "A língua (a) viva: variedades linguísticas",
    ("jornada", 15): "Gêneros científicos e refutação de teses",
    ("jornada", 16): "Anúncios para você",
}


def _familia_numero_orientacao_estudos(caminho_pdf: str) -> tuple[str, int]:
    base_arquivo = _normalizar(Path(caminho_pdf).stem)
    for familia in ("missao", "trilha", "jornada"):
        match = re.search(rf"{familia}[_\s-]*(\d{{1,2}})", base_arquivo)
        if match:
            return familia, int(match.group(1))
    return "", 0


def _titulo_catalogado_orientacao_estudos(caminho_pdf: str, texto: str = "") -> str:
    familia, numero = _familia_numero_orientacao_estudos(caminho_pdf)
    if familia and numero:
        titulo = _ORIENTACAO_ESTUDOS_TITULOS.get((familia, numero))
        if titulo:
            return f"{familia.upper()} {numero} - {titulo}"

    base_texto = _normalizar(texto)
    for (familia_catalogo, numero_catalogo), titulo_catalogado in _ORIENTACAO_ESTUDOS_TITULOS.items():
        if _normalizar(titulo_catalogado) in base_texto:
            return f"{familia_catalogo.upper()} {numero_catalogo} - {titulo_catalogado}"
    return ""


def _titulo_ja_rotulado_orientacao_estudos(titulo: str) -> bool:
    return bool(re.match(r"^(missao|trilha|jornada)\s+\d+\s+-\s+", _normalizar(titulo)))


def _extrair_etapas_orientacao_estudos(texto: str) -> list[dict]:
    """
    Extrai blocos por etapa em materiais de Orientacao de Estudos.
    Exemplo esperado no PDF: Etapa 1, Etapa 2, Etapa 3, Etapa final.
    """
    bruto = str(texto or "")
    if not bruto.strip():
        return []

    linhas = bruto.splitlines()
    if not linhas:
        return []

    def _normalizar_rotulo_etapa(rotulo: str) -> str:
        rotulo = rotulo.strip().lower()
        if rotulo == "final":
            return "final"
        roman_map = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6"}
        if rotulo in roman_map:
            return roman_map[rotulo]
        match_digit = re.search(r"\d+", rotulo)
        if match_digit:
            return str(int(match_digit.group(0)))
        return rotulo

    marcadores = []
    for i, linha in enumerate(linhas):
        atual = re.sub(r"\s+", " ", str(linha or "")).strip().lower()
        if not atual:
            continue

        match_p1 = re.match(r"^etapa\s+(final|[ivxldcm]+|\d+)\b", atual)
        match_p2 = re.match(r"^(\d+)\s*(?:a|o|ª|º|°)?\s*etapa\b", atual)
        
        if match_p1:
            rotulo = _normalizar_rotulo_etapa(match_p1.group(1))
            marcadores.append((i, rotulo))
            continue
        elif match_p2:
            rotulo = _normalizar_rotulo_etapa(match_p2.group(1))
            marcadores.append((i, rotulo))
            continue

        if atual == "etapa":
            prox = re.sub(r"\s+", " ", str(linhas[i + 1] if i + 1 < len(linhas) else "")).strip().lower()
            ant = re.sub(r"\s+", " ", str(linhas[i - 1] if i - 1 >= 0 else "")).strip().lower()
            if re.fullmatch(r"\d+", prox) or prox in ["i", "ii", "iii", "iv", "v", "vi", "final"]:
                marcadores.append((i, _normalizar_rotulo_etapa(prox)))
            elif re.fullmatch(r"\d+", ant) or ant in ["i", "ii", "iii", "iv", "v", "vi", "final"]:
                marcadores.append((i, _normalizar_rotulo_etapa(ant)))

    if not marcadores:
        return []

    # remove duplicatas sequenciais de mesmo rotulo
    compactos = []
    for marcador in marcadores:
        if compactos and compactos[-1][1] == marcador[1] and abs(compactos[-1][0] - marcador[0]) <= 2:
            continue
        compactos.append(marcador)
    marcadores = compactos

    etapas = []
    for idx, (linha_inicio, rotulo) in enumerate(marcadores):
        linha_fim = marcadores[idx + 1][0] if idx + 1 < len(marcadores) else len(linhas)
        bloco_linhas = list(linhas[linha_inicio:linha_fim])
        bloco = "\n".join(bloco_linhas).strip()
        if not bloco:
            continue

        titulo = "Etapa final" if rotulo == "final" else f"Etapa {rotulo}"
        texto_etapa = re.sub(r"\s+", " ", bloco).strip()
        texto_etapa = re.sub(r"(?i)^\s*(?:etapa\s*(?:final|[ivxldcm]+|\d+)?|(?:\d+)\s*(?:a|o|ª|º|°)?\s*etapa)\s*[-:–]?\s*", "", texto_etapa).strip()
        if len(texto_etapa) < 20:
            continue
        etapas.append({"titulo": titulo, "texto": texto_etapa})

    return etapas


def _contem(base: str, termos: list[str]) -> bool:
    return any(termo in base for termo in termos)


def _detectar_tecnicas_matematica(texto: str, tema: str) -> set[str]:
    base = _normalizar(f"{tema} {texto}")
    tecnicas = set()
    mapa = {
        "virem_conversem": ["virem e conversem"],
        "todo_mundo_escreve": ["todo mundo escreve"],
        "com_suas_palavras": ["com suas palavras"],
        "hora_leitura": ["hora da leitura"],
        "de_olho_modelo": ["de olho no modelo"],
        "relembre": ["relembre"],
        "geogebra": ["geogebra"],
        "calculadora": ["calculadora"],
        "arvore_possibilidades": ["arvore de possibilidades", "árvore de possibilidades"],
        "mapa_mental": ["mapa mental"],
        "resolucao_etapas": ["compreender", "planejar", "executar", "verificar"],
    }
    for tecnica, termos in mapa.items():
        if _contem(base, termos):
            tecnicas.add(tecnica)
    return tecnicas


def _detectar_tecnicas_lemov(texto: str, tema: str = "") -> list[str]:
    base = _normalizar(f"{tema} {texto}")
    mapa = [
        ("VIREM E CONVERSEM", ["virem e conversem"]),
        ("TODO MUNDO ESCREVE", ["todo mundo escreve"]),
        ("COM SUAS PALAVRAS", ["com suas palavras"]),
        ("HORA DA LEITURA", ["hora da leitura"]),
        ("DE OLHO NO MODELO", ["de olho no modelo"]),
        ("PAUSE E RESPONDA", ["pause e responda"]),
        ("UM PASSO DE CADA VEZ", ["um passo de cada vez"]),
    ]
    tecnicas = []
    for nome, termos in mapa:
        if any(termo in base for termo in termos):
            tecnicas.append(nome)
    return tecnicas


def _perfil_suporta_eja(perfil: str) -> bool:
    return perfil in {"biologia", "ingles"}


def _texto_tecnica_eja(tecnica: str, perfil: str, destino: str = "") -> str:
    tecnica_norm = _normalizar(tecnica)
    if "virem e conversem" in tecnica_norm:
        return "Aplicar a tecnica VIREM E CONVERSEM, incentivando os estudantes da EJA a compartilhar ideias, experiencias e hipoteses relacionadas ao tema."
    if "todo mundo escreve" in tecnica_norm:
        return "Utilizar a tecnica TODO MUNDO ESCREVE para garantir registro individual, participacao de todos e retomada das respostas durante a correcao."
    if "pause e responda" in tecnica_norm:
        return "Realizar perguntas rapidas no momento PAUSE E RESPONDA, verificando a compreensao e retomando pontos que apresentarem maior dificuldade."
    if "com suas palavras" in tecnica_norm:
        return "Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes expliquem o conceito com linguagem propria e exemplos do cotidiano."
    if "de olho no modelo" in tecnica_norm:
        return "Utilizar a tecnica DE OLHO NO MODELO, apresentando um exemplo comentado antes da atividade individual."
    if "hora da leitura" in tecnica_norm:
        return "Conduzir a tecnica HORA DA LEITURA com pausas para vocabulario, compreensao e relacao com situacoes cotidianas."
    if perfil == "ingles" and ("listen and repeat" in tecnica_norm or "write and share" in tecnica_norm or "say it in english" in tecnica_norm):
        return f"Utilizar a tecnica {tecnica.upper()} com comandos curtos, repeticao orientada e participacao segura dos estudantes da EJA."
    return f"Incorporar a tecnica {tecnica.upper()} de forma contextualizada e acessivel para a turma da EJA."


def _adaptar_metodologia_eja(metodologia, perfil: str, tema: str, texto_pdf: str, tecnicas_pdf: list[str] | None = None):
    if not _perfil_suporta_eja(perfil):
        return metodologia

    tecnicas_pdf = [tecnica for tecnica in list(tecnicas_pdf or []) if _normalizar(tecnica) != "relembre"]
    tem_video = "video" in _normalizar(texto_pdf)
    adaptada = []
    texto_existente = _normalizar(
        " ".join(str(item.get("texto", "") if isinstance(item, dict) else item) for item in metodologia or [])
    )
    usados = {tecnica for tecnica in tecnicas_pdf if _normalizar(tecnica) in texto_existente}

    for item in metodologia or []:
        if not isinstance(item, dict):
            adaptada.append(item)
            continue

        novo = dict(item)
        titulo = _normalizar(novo.get("titulo", ""))
        texto = re.sub(r"\s+", " ", str(novo.get("texto", "") or "")).strip()

        if titulo in {"para comecar", "relembre", "abertura", "contextualizacao"}:
            complemento = (
                f" Retomar conhecimentos previos sobre {tema} por meio de perguntas simples e contextualizadas, "
                "valorizando experiencias dos estudantes jovens e adultos sem infantilizar a abordagem."
            )
            for tecnica in tecnicas_pdf:
                if _normalizar(tecnica) in {"virem e conversem", "com suas palavras"} and tecnica not in usados:
                    complemento += " " + _texto_tecnica_eja(tecnica, perfil)
                    usados.add(tecnica)
                    break
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"foco no conteudo", "conceituacao", "desenvolvimento", "leitura e construcao do conteudo", "leitura"}:
            if perfil == "ingles":
                complemento = (
                    " Explorar vocabulario e estruturas em ingles com exemplos funcionais do cotidiano, "
                    "pronuncia orientada e apoio visual, respeitando diferentes ritmos de leitura e fala da EJA."
                )
            else:
                complemento = (
                    " Explicar o conceito com linguagem acessivel e adulta, de forma pausada e dialogada, "
                    "relacionando o conteudo a situacoes praticas do cotidiano, saude, trabalho, tecnologia ou comunidade."
                )
            if tem_video:
                complemento += " Exibir o video indicado no material e orientar o registro das principais informacoes observadas."
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"pause e responda", "na pratica", "atividade", "atividade principal"}:
            complemento = (
                " Realizar perguntas rapidas para verificar a compreensao, promover correcao coletiva e retomar os pontos "
                "que apresentarem maior dificuldade."
            )
            for tecnica in tecnicas_pdf:
                if _normalizar(tecnica) in {"todo mundo escreve", "pause e responda", "write and share"} and tecnica not in usados:
                    complemento += " " + _texto_tecnica_eja(tecnica, perfil)
                    usados.add(tecnica)
                    break
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {"encerramento", "fechamento", "sistematizacao"}:
            if perfil == "ingles":
                complemento = (
                    " Encerrar retomando expressoes essenciais em ingles e relacionando o uso da lingua a situacoes reais "
                    "de comunicacao, trabalho, servicos, tecnologia ou convivio social."
                )
            else:
                complemento = (
                    f" Encerrar relacionando {tema} a aplicacoes praticas, tecnologias, saude, ambiente ou situacoes do cotidiano, "
                    "reforcando a relevancia do conteudo para a vida adulta e para a participacao social."
                )
            texto = _anexar_orientacao_unica(texto, complemento)

        novo["texto"] = texto
        adaptada.append(novo)

    adaptada = _garantir_tecnicas_lemov_na_metodologia(adaptada, [tecnica for tecnica in tecnicas_pdf if tecnica not in usados])
    tecnicas_lemov = ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "PAUSE E RESPONDA", "COM SUAS PALAVRAS", "DE OLHO NO MODELO", "HORA DA LEITURA", "UM PASSO DE CADA VEZ"]
    for item in adaptada:
        if isinstance(item, dict) and "texto" in item:
            texto_item = item["texto"]
            for tecnica in tecnicas_lemov:
                texto_item = re.sub(re.escape(tecnica), tecnica, texto_item, flags=re.I)
            item["texto"] = texto_item
    return _consolidar_blocos_eja(adaptada)


def _consolidar_blocos_eja(metodologia):
    grupos = [
        ("Para comecar", {"para comecar", "relembre", "abertura", "contextualizacao"}),
        ("Foco no conteudo", {"foco no conteudo", "leitura", "leitura e construcao do conteudo", "conceituacao", "desenvolvimento"}),
        ("Pause e responda", {"pause e responda", "na pratica", "atividade", "atividade principal", "socializacao", "socializacao e correcao"}),
        ("Encerramento", {"encerramento", "fechamento", "sistematizacao"}),
    ]
    saida = {titulo: [] for titulo, _ in grupos}
    extras = []

    for item in metodologia or []:
        if not isinstance(item, dict):
            extras.append(str(item))
            continue
        titulo_norm = _normalizar(item.get("titulo", ""))
        texto = re.sub(r"\s+", " ", str(item.get("texto", "") or "")).strip()
        if not texto:
            continue
        encaixado = False
        for titulo, aliases in grupos:
            if titulo_norm in aliases:
                saida[titulo].append(texto)
                encaixado = True
                break
        if not encaixado:
            extras.append(texto)

    if extras:
        saida["Foco no conteudo"].extend(extras)

    consolidada = []
    for titulo, _ in grupos:
        textos = saida[titulo]
        if textos:
            consolidada.append({"titulo": titulo, "texto": " ".join(textos)})
    return consolidada


def _garantir_tecnicas_lemov_na_metodologia(metodologia, tecnicas_pdf: list[str]):
    if not metodologia or not tecnicas_pdf:
        return metodologia

    metodologia_ajustada = []
    textos_norm = []
    for item in metodologia:
        if isinstance(item, dict):
            textos_norm.append(_normalizar(item.get("texto", "")))
        else:
            textos_norm.append(_normalizar(str(item)))

    faltantes = [tecnica for tecnica in tecnicas_pdf if not any(_normalizar(tecnica) in texto for texto in textos_norm)]
    if not faltantes:
        return metodologia

    for indice, item in enumerate(metodologia):
        if not isinstance(item, dict):
            metodologia_ajustada.append(item)
            continue

        novo_item = dict(item)
        titulo = _normalizar(novo_item.get("titulo", ""))
        texto = str(novo_item.get("texto", "")).strip()

        if faltantes and titulo in {"para comecar", "primeiro momento", "abertura", "relembre"}:
            tecnica = faltantes.pop(0)
            if tecnica == "VIREM E CONVERSEM":
                acrescimo = " Aplicar a tecnica VIREM E CONVERSEM para que os estudantes compartilhem percepcoes, levantem hipoteses e retomem conhecimentos previos."
            elif tecnica == "TODO MUNDO ESCREVE":
                acrescimo = " Utilizar a tecnica TODO MUNDO ESCREVE para garantir o registro individual de hipoteses, ideias centrais ou respostas iniciais."
            elif tecnica == "HORA DA LEITURA":
                acrescimo = " Utilizar a tecnica HORA DA LEITURA para conduzir a leitura orientada do material, com pausas para destacar informacoes importantes."
            elif tecnica == "DE OLHO NO MODELO":
                acrescimo = " Aplicar a tecnica DE OLHO NO MODELO, apresentando um exemplo comentado antes da atividade individual."
            elif tecnica == "PAUSE E RESPONDA":
                acrescimo = " Realizar o momento PAUSE E RESPONDA para checar a compreensao, retomar respostas da turma e esclarecer duvidas antes de avancar."
            elif tecnica == "UM PASSO DE CADA VEZ":
                acrescimo = " Utilizar a tecnica UM PASSO DE CADA VEZ para organizar a explicacao em etapas curtas antes de avancar."
            elif tecnica == "COM SUAS PALAVRAS":
                acrescimo = " Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes expliquem oralmente ou por escrito o que compreenderam."
            else:
                acrescimo = f" Incorporar a tecnica {tecnica} ao desenvolvimento da aula, articulando-a aos exemplos, registros e intervencoes do professor."
            if _normalizar(acrescimo) not in _normalizar(texto):
                novo_item["texto"] = f"{texto}{acrescimo}".strip()

        metodologia_ajustada.append(novo_item)

    if faltantes:
        for item in metodologia_ajustada:
            if not isinstance(item, dict):
                continue
            titulo = _normalizar(item.get("titulo", ""))
            texto = str(item.get("texto", "")).strip()
            if titulo in {"na pratica", "foco no conteudo", "desenvolvimento", "encerramento", "segundo momento"}:
                tecnica = faltantes.pop(0)
                if tecnica == "TODO MUNDO ESCREVE":
                    acrescimo = " Utilizar a tecnica TODO MUNDO ESCREVE para que cada estudante organize por escrito a resolucao ou as ideias centrais da aula."
                elif tecnica == "COM SUAS PALAVRAS":
                    acrescimo = " Aplicar a tecnica COM SUAS PALAVRAS para que os estudantes retomem os pontos principais trabalhados."
                elif tecnica == "PAUSE E RESPONDA":
                    acrescimo = " Realizar o momento PAUSE E RESPONDA para conferir a compreensao da turma antes de avancar."
                else:
                    acrescimo = f" Incorporar a tecnica {tecnica} ao desenvolvimento da aula, articulando-a aos exemplos, registros e intervencoes do professor."
                if _normalizar(acrescimo) not in _normalizar(texto):
                    item["texto"] = f"{texto}{acrescimo}".strip()
                if not faltantes:
                    break

    return metodologia_ajustada


def _linhas_secao_matematica(texto: str, marcador: str) -> list[str]:
    marcadores = {
        "para comecar",
        "relembre",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "encerramento",
    }
    linhas = _limpar_linhas(texto)
    alvo = _normalizar(marcador)
    inicio = None

    for indice, linha in enumerate(linhas):
        if _normalizar(linha) == alvo:
            inicio = indice + 1
            break

    if inicio is None:
        return []

    ignorar = {
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "veja no livro!",
        "resolucao",
        "fica a dica",
        "conversando sobre o tema",
        "planejando fica mais facil",
    }

    coletadas = []
    for linha in linhas[inicio:]:
        normalizada = _normalizar(linha)
        if normalizada in marcadores:
            break
        if normalizada in ignorar:
            continue
        if re.fullmatch(r"\d+\s*minutos?", normalizada):
            continue
        if "freepik" in normalizada or "pixabay" in normalizada or "disponivel em:" in normalizada:
            continue
        coletadas.append(linha)
    return coletadas


def _tem_secao_matematica(texto: str, marcador: str) -> bool:
    alvo = _normalizar(marcador)
    return any(_normalizar(linha) == alvo for linha in _limpar_linhas(texto))


def _primeira_secao_matematica(texto: str) -> str:
    secoes = ["relembre", "para comecar", "exploracao", "foco no conteudo", "na pratica", "encerramento"]
    melhor_indice = None
    melhor_secao = ""
    for indice, linha in enumerate(_limpar_linhas(texto)):
        normalizada = _normalizar(linha)
        if normalizada in secoes and (melhor_indice is None or indice < melhor_indice):
            melhor_indice = indice
            melhor_secao = normalizada
    return melhor_secao


def _contar_atividades_matematica(texto: str) -> int:
    return len(set(re.findall(r"atividade\s*(\d+)", _normalizar(texto), flags=re.I)))


def _detectar_formato_aula_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    primeira_secao = _primeira_secao_matematica(texto)
    tem_pause = _tem_secao_matematica(texto, "pause e responda")
    tem_foco = _tem_secao_matematica(texto, "foco no conteudo")
    total_atividades = _contar_atividades_matematica(texto)

    if "aula de verificacao" in base or re.search(r"\bverificacao\b", _normalizar(tema)):
        return "verificacao"
    if primeira_secao == "relembre" and not tem_foco:
        return "verificacao"
    if primeira_secao == "na pratica" and total_atividades >= 2 and not tem_foco and not tem_pause:
        return "pratica_intensiva"
    if _contem(base, ["modelagem", "polya", "hora da leitura", "de olho no modelo", "um passo de cada vez"]):
        return "modelagem"
    if _contem(_normalizar(tema), ["retomando"]) or _contem(base, ["retomar os conceitos", "retomar os conceitos de"]):
        return "retomada"
    return "conceito_novo"


def _resumo_contexto_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "a situação de Marta, que quer comprar um celular de R$ 3.800,00 e precisa planejar quanto economizar por mês"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "a comparação entre os custos de um carro elétrico e de um carro híbrido, considerando gasto por quilômetro e manutenção anual"
    if "josue" in base and "salada de frutas" in base:
        return "as situações-problema sobre compra de frutas, lucro de vendedores, tempos de viagem e descontos progressivos"
    if "internet discada" in base and "banda larga" in base:
        return "a comparação entre internet discada e banda larga para analisar tempo de download e razão entre grandezas"
    if "construcao civil" in base and "agua" in base and "concreto" in base:
        return "o consumo de água na construção civil para relacionar volume de concreto e quantidade de água utilizada"

    linhas = _linhas_secao_matematica(texto, "para comecar") or _linhas_secao_matematica(texto, "na pratica")
    if linhas:
        linhas_contexto = []
        for linha in linhas:
            if _linha_com_marcador_metodologico(linha):
                continue
            linha_limpa = _limpar_linha_metodologica(linha)
            if _linha_instrucao_matematica(linha_limpa):
                continue
            linhas_contexto.append(linha_limpa)
            if len(linhas_contexto) >= 3:
                break
        resumo = re.sub(r"\s+", " ", " ".join(linhas_contexto)).strip()
        if resumo:
            return resumo[:220].rstrip(" .")
    return tema


def _resumo_pratica_matematica(texto: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "josue" in base and "bia" in base and "bruna" in base:
        return "situações sobre compra de frutas, lucro de vendedores online, tempos de viagem e descontos progressivos"
    if "idade de ana" in base or "triplo da minha idade" in base:
        return "situações sobre idade, distribuição de estudantes e equações do 1º grau"
    if "carro eletrico" in base and "concessionaria" in base:
        return "atividades progressivas de modelagem algébrica em contextos de veículos, produção e investimento"
    if "internet discada" in base and "banda larga" in base:
        return "situações de comparação entre velocidades, tamanhos de arquivo e relações entre grandezas"
    if "construcao civil" in base and "agua" in base:
        return "situações de leitura de tabelas, construção de pares ordenados e representação gráfica entre grandezas"

    if _contar_atividades_matematica(texto) >= 2:
        return "atividades progressivas de resolução, registro e verificação das respostas"
    return f"problemas e registros relacionados a {tema}"


def _pergunta_pause_matematica(texto: str) -> str:
    linhas = _linhas_secao_matematica(texto, "pause e responda")
    if not linhas:
        return ""
    bloco = re.sub(r"\s+", " ", " ".join(linhas)).strip()
    if "idade de ana" in _normalizar(bloco):
        return "O triplo da idade de Ana, aumentado em 6 anos, totaliza 108 anos. Solicitar que os estudantes escrevam a equacao que modela essa situacao."
    citacao = re.search(r"falou:\s*[\"“]?([^\"”]{25,220})", bloco, flags=re.I)
    if citacao:
        return citacao.group(1).strip(" .")
    if ":" in bloco:
        apos_dois_pontos = bloco.split(":", 1)[1].strip(" \"")
        if len(apos_dois_pontos) >= 25:
            return apos_dois_pontos[:220].rstrip(" .")
    for trecho in re.findall(r"[^?]{25,220}\?", bloco):
        trecho_limpo = trecho.strip(" \"")
        if len(trecho_limpo) >= 30:
            return trecho_limpo
    return bloco[:220].rstrip(" .")


def _fechamento_reflexivo_matematica(texto: str, tema: str, formato: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "retomar o significado de incógnita, solução e verificação, conectando a resposta final à meta financeira de Marta"
    if "carro eletrico" in base and "carro hibrido" in base:
        return "sistematizar as quatro etapas de Polya e discutir quando uma equação do 1º grau é um bom modelo matemático para a situação"
    if "josue" in base and "bruna" in base:
        return "destacar que o valor da incógnita nem sempre é a resposta final e reforçar a importância de verificar cada solução no contexto"
    if "internet discada" in base and "banda larga" in base:
        return "retomar como razão entre grandezas de espécies diferentes ajuda a interpretar tempo, velocidade e unidades de medida"
    if "construcao civil" in base and "agua" in base:
        return "sintetizar como a relação entre grandezas pode ser representada por tabela e gráfico, conectando a leitura matemática ao contexto ambiental"
    if formato == "pratica_intensiva":
        return "retomar os caminhos de resolução usados pela turma e reforçar a importância de verificar se o resultado encontrado faz sentido no problema"
    return f"sistematizar as estratégias construídas pela turma para compreender e resolver situações relacionadas a {tema}"


def _aprendizagem_matematica(tema: str, tipo: str, texto: str) -> str:
    base = _normalizar(f"{tema} {texto}")
    if "marta" in base and "celular" in base:
        return "Retomar e aplicar equações do 1º grau para modelar situações do cotidiano, identificar a incógnita, resolver por operações inversas e verificar a solução encontrada."
    if tipo == "modelagem":
        return "Modelar situações-problema utilizando equações do 1º grau, aplicando estratégias de resolução, interpretação do enunciado e verificação do resultado no contexto."
    if tipo == "funcoes":
        return "Identificar relações de dependência entre grandezas e representá-las por tabelas, expressões e gráficos, interpretando o comportamento da função no contexto analisado."
    if tipo == "grandezas_medidas":
        return "Compreender e comparar relações entre grandezas de espécies diferentes, analisando razões, unidades e proporcionalidade em situações-problema."
    if tipo == "estatistica_probabilidade":
        return "Ler, organizar e interpretar dados, tabelas e gráficos para justificar conclusões e resolver situações que envolvam análise de informações."
    if tipo == "algebra":
        return "Resolver e interpretar situações-problema por meio de equações do 1º grau, identificando incógnitas, organizando procedimentos e verificando a coerência das soluções."
    return f"Compreender e aplicar conceitos relacionados a {tema}."


def _perfil_disciplina(disciplina: str) -> str:
    base = _normalizar(disciplina)
    if _contem(base, ["orientacao de estudos", "orientacao estudos", "orienestudos", "orient"]):
        return "orientacao_estudos"
    if _contem(base, ["redacao e leitura", "leitura e redacao", "redacao", "leitura"]):
        return "leitura_redacao"
    if _contem(base, ["lingua portuguesa", "portugues"]):
        if _contem(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"
    if _contem(base, ["ciencias", "cienc"]):
        return "ciencias_ef"
    if _contem(base, ["biologia", "biolog"]):
        return "biologia"
    if _contem(base, ["quimica", "quim"]):
        return "quimica"
    if _contem(base, ["fisica", "fis"]):
        return "fisica"
    if _contem(base, ["historia", "histor"]):
        return "historia"
    if _contem(base, ["geografia", "geograf"]):
        return "geografia"
    if _contem(base, ["ingles", "lingua inglesa", "ingl"]):
        return "ingles"
    if _contem(base, ["arte"]):
        return "arte"
    if _contem(base, ["projeto de vida", "projeto"]):
        return "projeto_de_vida"
    if _contem(base, ["educacao financeira", "financeir"]):
        return "educacao_financeira"
    if _contem(base, ["matematica", "matem"]):
        return "matematica"
    if _contem(base, ["tecnologia", "inovacao", "tecnolog"]):
        return "tecnologia_inovacao"
    if _contem(base, ["sociologia", "sociolog"]):
        return "sociologia"
    if _contem(base, ["lideranca", "oratoria", "lideranc", "orator"]):
        return "lideranca_oratoria"
    return "geral"


def _eh_cdp_contextual_disciplina(disciplina: str) -> bool:
    base = _normalizar(disciplina).replace(" ", "")
    return base in {
        "cdp-ensinofundamental",
        "cdpensinofundamental",
        "cdp-ensinomedio",
        "cdpensinomedio",
    }


def _disciplina_base_cdp_contextual(texto: str, tema: str, caminho_pdf: str = "") -> str:
    base = _normalizar(f"{Path(caminho_pdf).name} {tema} {texto}")
    opcoes = [
        ("Matemática", ["matematica", "matem"]),
        ("Língua Portuguesa", ["lingua portuguesa"]),
        ("Ciências", ["ciencias", "cienc"]),
        ("História", ["historia", "histor"]),
        ("Geografia", ["geografia", "geograf"]),
        ("Arte", ["arte"]),
        ("Biologia", ["biologia", "biolog"]),
        ("Física", ["fisica", "fis"]),
        ("Química", ["quimica", "quim"]),
        ("Língua Inglesa", ["ingles", "lingua inglesa"]),
        ("Sociologia", ["sociologia"]),
        ("Liderança e Oratória", ["lideranca e oratoria", "lideranca"]),
    ]
    if re.search(r"\bportugues\b", base):
        return "Língua Portuguesa"
    for nome, chaves in opcoes:
        if _contem(base, chaves):
            return nome
    return "Geral"


def _tema_cdp_seguro(texto: str, tema: str, disciplina: str, padrao: str) -> str:
    if not padrao:
        return tema or padrao
    linhas = _limpar_linhas(texto)
    idx = -1
    for i, linha in enumerate(linhas):
        if _normalizar(padrao) in _normalizar(linha):
            idx = i
            break
    if idx == -1:
        return tema or padrao
    
    partes = [linhas[idx]]
    for i in range(idx + 1, min(idx + 5, len(linhas))):
        linha_norm = _normalizar(linhas[i])
        if any(w in linha_norm for w in ["conteudo", "objetivo", "habilidade", "ef", "em", "aula", "bimestre"]):
            break
        partes.append(linhas[i])
        
    return " ".join(partes).strip()


def _limpar_tema_cdp_contextual(tema: str, disciplina_base: str) -> str:
    texto = re.sub(r"\s+", " ", str(tema or "")).strip(" -:.")
    texto = re.sub(r"^\s*AULA\s*\d+\s*[-:–—]?\s*", "", texto, flags=re.I)
    texto = re.sub(r"^\s*TEMA\s*:\s*", "", texto, flags=re.I)
    for termo in [
        disciplina_base,
        "Matemática",
        "Língua Portuguesa",
        "Português",
        "Ciências",
        "História",
        "Geografia",
        "Arte",
        "Biologia",
        "Física",
        "Química",
    ]:
        if termo:
            texto = re.sub(rf"^\s*{re.escape(termo)}\s*[-:–]?\s*", "", texto, flags=re.I)
    return texto or str(tema or "conteúdo da aula").strip() or "conteúdo da aula"


def _formatar_material_cdp_contextual(tema: str, disciplina_base: str = "") -> str:
    titulo = _limpar_tema_cdp_contextual(tema, disciplina_base).strip()
    titulo = re.sub(r"\s+", " ", titulo).strip(" -:.")
    return f"TEMA:\n{titulo}" if titulo else "TEMA:\nConteúdo da aula"


def _metodologia_cdp_contextual_obsoleta(perfil: str, tipo: str, tema: str, conceito: str) -> list[str]:
    tema_frase = _limpar_tema_cdp_contextual(tema, "")
    conceito_frase = _limpar_tema_cdp_contextual(conceito or tema_frase, "")
    base_tema = _normalizar(f"{tema_frase} {conceito_frase}")

    if perfil == "matematica":
        if _contem(base_tema, ["fracao", "divisao", "numerador", "denominador"]):
            return [
                f"A aula inicia com uma conversa sobre situações do cotidiano em que objetos, alimentos ou quantidades precisam ser divididos em partes iguais. O professor apresenta exemplos na lousa mostrando a relação entre {tema_frase} e os procedimentos de cálculo. Em seguida, os alunos realizam atividades simples no caderno, com acompanhamento durante a resolução, registro das estratégias utilizadas e correção coletiva."
            ]
        if _contem(base_tema, ["exponencial", "potencia", "crescimento"]):
            return [
                f"A aula começa com uma conversa sobre situações em que valores aumentam rapidamente ao longo do tempo, como juros, dívidas e crescimento de quantidades. O professor apresenta exemplos simples na lousa, mostrando como reconhecer padrões e resolver situações envolvendo {tema_frase}. Durante a atividade, os alunos resolvem exercícios com acompanhamento do professor e discussão coletiva dos procedimentos utilizados."
            ]
        if _contem(base_tema, ["contagem", "principio multiplicativo", "combinacao", "possibilidade"]):
            return [
                f"A aula inicia com uma conversa sobre escolhas realizadas no dia a dia, como combinações possíveis de objetos, números, letras ou outras situações da rotina. O professor apresenta exemplos simples na lousa, explicando como diferentes escolhas geram diversas possibilidades. Em seguida, os alunos realizam atividades práticas de contagem e organização das possibilidades, registrando os resultados e comparando estratégias utilizadas."
            ]
        if _contem(base_tema, ["equacao", "incognita", "valor desconhecido"]):
            return [
                f"A aula inicia com uma conversa sobre situações do cotidiano em que é necessário calcular valores desconhecidos, organizar gastos ou resolver problemas por etapas. Em seguida, o professor apresenta situações-problema envolvendo {tema_frase}, explicando a construção e a resolução passo a passo na lousa. Após a explicação, os alunos resolvem exercícios com apoio do professor, realizando registros no caderno e discutindo os procedimentos utilizados."
            ]
        return [
            f"A aula inicia com uma conversa sobre situações do cotidiano relacionadas a {tema_frase}. O professor apresenta o conteúdo na lousa com linguagem simples, exemplos próximos da realidade dos estudantes e resolução passo a passo. Em seguida, os alunos realizam exercícios no caderno com acompanhamento do professor, registrando os procedimentos utilizados e participando da correção coletiva."
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        return [
            f"A aula inicia com uma conversa breve sobre {tema_frase}, relacionando o assunto a situações de comunicação, leitura ou escrita presentes no cotidiano. O professor realiza leitura orientada do material, explica vocabulário e organiza no quadro as ideias principais. Em seguida, os alunos respondem às atividades no caderno, com apoio durante a leitura, interpretação e produção das respostas."
        ]

    return [
        f"A aula inicia com uma conversa sobre situações do cotidiano relacionadas a {tema_frase}, valorizando os conhecimentos prévios dos estudantes da EJA. Em seguida, o professor apresenta o conteúdo com explicação clara, exemplos simples e registros no quadro. Os alunos realizam atividades no caderno com acompanhamento individual quando necessário, retomada das dúvidas e correção coletiva."
    ]


def _acompanhamento_cdp_contextual(perfil: str, tema: str) -> list[str]:
    tema_frase = _limpar_tema_cdp_contextual(tema, "")
    if perfil == "matematica":
        return [
            "☑ Identificar se o aluno compreende os dados e procedimentos envolvidos na situação-problema.",
            "☑ Observar se utiliza corretamente as operações e registros necessários para resolver a atividade.",
            "☑ Verificar participação nas resoluções, justificativas e correção coletiva.",
        ]
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        return [
            "☑ Identificar se o aluno compreende as informações principais do texto ou comando.",
            "☑ Observar se organiza respostas orais e escritas de forma coerente.",
            "☑ Verificar participação durante a leitura, os registros e a correção coletiva.",
        ]
    return [
        f"☑ Identificar se o aluno compreende as ideias principais relacionadas a {tema_frase}.",
        "☑ Observar participação, registros no caderno e realização das atividades propostas.",
        "☑ Verificar dúvidas apresentadas e avanços durante a correção coletiva.",
    ]


def _acessibilidade_cdp_contextual(perfil: str, tema: str) -> list[str]:
    if perfil == "matematica":
        return [
            "☑ Explicação com linguagem simples e exemplos próximos da realidade dos estudantes.",
            "☑ Resolução gradual das atividades com acompanhamento individual quando necessário.",
            "☑ Apoio com exemplos adicionais e retomada dos cálculos básicos.",
        ]
    return [
        "☑ Utilização de exemplos concretos e próximos do cotidiano dos estudantes.",
        "☑ Explicação passo a passo, com registro das ideias principais no quadro.",
        "☑ Apoio individual, retomada de conceitos e flexibilização dos registros quando necessário.",
    ]


def _tema_truncado_cdp(texto: str) -> bool:
    normalizado = _normalizar(texto).strip(" .:-")
    if not normalizado or len(normalizado) < 12:
        return True
    return normalizado.split()[-1] in {
        "a",
        "o",
        "as",
        "os",
        "e",
        "em",
        "com",
        "de",
        "da",
        "do",
        "das",
        "dos",
        "para",
        "por",
        "ou",
    }


def _tipo_conteudo_cdp(perfil: str, tema: str, conceito: str = "") -> str:
    base = _normalizar(f"{tema} {conceito}")
    if perfil == "matematica":
        if _contem(base, ["reta numerica", "reta numerica", "localizacao na reta", "localizacao de racionais na reta"]):
            return "reta_numerica_racionais"
        if _contem(base, ["simetricos no plano cartesiano", "simetria no plano cartesiano"]):
            return "simetria_plano_cartesiano"
        if _contem(base, ["poligonos no plano cartesiano"]):
            return "poligonos_plano_cartesiano"
        if _contem(base, ["pontos no plano cartesiano", "pares ordenados", "localizacao de pontos no plano"]):
            return "pontos_plano_cartesiano"
        if _contem(base, ["malha quadriculada", "areas na malha"]):
            return "area_malha_quadriculada"
        if _contem(base, ["numeros racionais", "numeros decimais"]):
            return "operacoes_racionais"
        if _contem(base, ["representacao algebrica", "grandezas representacao algebrica"]):
            return "relacao_grandezas_algebrica"
        if _contem(base, ["representacao grafica", "grandezas representacao grafica"]):
            return "relacao_grandezas_grafica"
        if _contem(base, ["funcao logaritmica", "logaritmica", "logaritmo"]):
            return "funcao_logaritmica"
        if _contem(base, ["aula de verificacao", "verificacao", "avaliacao diagnostica"]) and _contem(base, ["funcao"]):
            return "verificacao_funcao"
        if _contem(base, ["aula de revisao", "revisao geral", "retomada geral"]) and _contem(base, ["funcao"]):
            return "revisao_funcao"
        if _contem(base, ["representacao de funcoes", "representacoes de funcoes", "tabela expressao grafico"]):
            return "representacao_funcoes"
        if _contem(base, ["relacao de dependencia entre duas grandezas", "dependencia entre duas grandezas"]):
            return "dependencia_grandezas"
        if _contem(base, ["conceito de funcao", "o conceito de funcao", "ideia de funcao"]):
            return "conceito_funcao"
        if _contem(
            base,
            [
                "valor numerico",
                "substituicao de valores",
                "substituir a letra",
                "calculo do valor numerico",
            ],
        ):
            return "algebra_valor_numerico"
        if _contem(
            base,
            [
                "variavel",
                "expressao algebrica",
                "linguagem algebrica",
                "uso de letras",
                "letras para representar numeros",
                "quantidade variavel",
            ],
        ):
            return "algebra_variavel"
        if _contem(base, ["igualdade", "balanca", "equilibrio"]):
            return "equacao_igualdade"
        if _contem(
            base,
            [
                "sistema de equacoes",
                "sistemas de equacoes",
                "metodo da substituicao",
                "metodo da adicao",
                "duas equacoes",
            ],
        ):
            return "sistema_equacoes"
        if _contem(
            base,
            [
                "duas incognitas",
                "par ordenado",
                "pares ordenados",
                "plano cartesiano",
                "malha quadriculada",
                "reta no plano",
            ],
        ):
            return "equacao_duas_incognitas"
        if _contem(
            base,
            [
                "equacao do 1 grau",
                "equacoes do 1 grau",
                "equacao de primeiro grau",
                "equacoes de primeiro grau",
            ],
        ):
            return "equacao_1_grau"
        if _contem(
            base,
            [
                "semelhanca de triangulos",
                "triangulos semelhantes",
                "lados correspondentes",
                "ampliacao e reducao",
                "proporcionalidade nos triangulos",
            ],
        ):
            return "semelhanca_triangulos"
        if _contem(base, ["teorema de pitagoras", "pitagoras", "hipotenusa", "cateto"]):
            return "teorema_pitagoras"
        if _contem(base, ["adicao e subtracao", "somar frac", "subtrair frac"]):
            return "fracao_adicao_subtracao"
        if _contem(
            base,
            [
                "multiplicacao com frac",
                "multiplicacao de frac",
                "divisao com frac",
                "divisao de frac",
                "multiplicar frac",
                "dividir frac",
            ],
        ):
            return "fracao_mult_div"
        if _contem(
            base,
            [
                "comparacao de frac",
                "comparar frac",
                "ordenacao de frac",
                "ordenar frac",
                "simplificacao",
                "simplificar",
            ],
        ):
            return "fracao_comparacao"
        if _contem(base, ["forma mista", "numero misto", "fracao impropria"]):
            return "forma_mista"
        if _contem(base, ["estrategias para calcular", "fracao de uma quantidade"]):
            return "fracao_quantidade"
        if _contem(
            base,
            [
                "fracao como resultado",
                "fracoes como resultado",
                "resultado de uma divisao",
                "numerador",
                "denominador",
                "representacao de frac",
            ],
        ):
            return "fracao_conceito"
        if _contem(base, ["fracao", "fracoes"]):
            return "fracao_conceito"
        if _contem(
            base,
            [
                "permutacao",
                "arranjo",
                "contagem",
                "principio multiplicativo",
                "combinacao",
                "possibilidade",
            ],
        ):
            return "combinatoria"
        if _contem(base, ["equacao", "incognita", "valor desconhecido", "sentenca matematica"]):
            return "equacao"
        if _contem(base, ["porcentagem", "juros", "desconto"]):
            return "porcentagem"
        if _contem(base, ["giro", "angulo", "angulo reto", "angulo agudo", "angulo obtuso"]):
            return "geometria_angulos"
        if _contem(base, ["poligono", "triangulo", "quadrilatero", "lados", "vertices", "reconhecimento"]):
            return "geometria_poligonos"
        if _contem(base, ["area", "perimetro", "medida"]):
            return "geometria_medidas"
        return "matematica_geral"
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        if _contem(base, ["relacoes logico-discursivas", "relacao logico-discursiva", "logico-discursiva"]):
            return "lp_relacoes_logico_discursivas"
        if _contem(base, ["artigo de opiniao", "artigo de opini", "textos contemporaneos na construcao da opiniao", "textos contempor", "construcao da opini", "tese", "fato e opiniao", "fato", "ponto de vista", "estrutura argumentativa", "introducao", "desenvolvimento", "conclusao", "bibliotecas publicas"]):
            return "lp_artigo_opiniao"
        if _contem(base, ["conectivo", "conjuncao", "coesao", "coerencia", "adversativa", "concessiva", "concessao", "oposicao", "finalidade", "portanto", "embora", "porque", "todavia", "contudo", "no entanto"]):
            return "lp_relacoes_logico_discursivas"
        if _contem(base, ["por dentro da cronica parte 2", "verbos que contam historias", "verbo", "modo", "subjuntivo", "indicativo", "imperativo", "tempo verbal", "concordancia", "ortografia", "pontuacao", "registro formal", "registro informal", "reescreva", "transforme"]):
            return "analise_linguistica"
        if _contem(base, ["producao", "producao textual", "produzir", "escrita", "escreva", "rascunho", "reescrita", "redacao", "paragrafo", "elabore", "crie um texto"]):
            return "producao_textual"
        if _contem(base, ["significado", "vocabulario", "palavra", "expressao", "sinonimo", "antonimo", "inferir", "o que quer dizer"]):
            return "vocabulario_inferencia"
        if _contem(base, ["genero", "cronica", "conto", "poema", "noticia", "reportagem", "caracteristicas", "estrutura", "circulacao", "publico-alvo", "por dentro da cronica parte 1"]):
            return "genero_textual"
        if _contem(base, ["argumento", "opiniao", "tese", "ponto de vista"]):
            return "argumentacao"
        if _contem(base, ["parte 2", "parte 3", "relembre", "retome", "aula anterior", "continuacao", "revisao"]):
            return "retomada_lp"
        return "leitura_interpretacao"
    if perfil in {"ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        if _contem(
            base,
            [
                "cardapio",
                "alimentacao balanceada",
                "alimentacao saudavel",
                "planejamento alimentar",
                "planejar refeicoes",
                "montar cardapio",
                "montagem de cardapio",
                "refeicao",
                "refeicoes",
                "nutricao",
                "grupo alimentar",
                "grupos alimentares",
                "grupos de alimentos",
                "classificar alimentos",
                "in natura",
                "minimamente processado",
                "ultraprocessado",
                "cafe da manha",
                "almoco",
                "lanche",
                "jantar",
            ],
        ):
            return "ciencias_alimentacao"
        if _contem(
            base,
            [
                "digestao",
                "sistema digestorio",
                "estomago",
                "intestino",
                "esofago",
                "figado",
                "pancreas",
                "absorcao",
                "enzima",
                "suco gastrico",
                "bolo alimentar",
                "quimo",
            ],
        ):
            return "ciencias_digestao"
        if _contem(
            base,
            [
                "sistema nervoso",
                "sistema endocrino",
                "hormonio",
                "neuronio",
                "cerebro",
                "glandula",
                "puberdade",
                "adolescencia",
                "desenvolvimento humano",
                "morfologico",
                "fisiologico",
            ],
        ):
            return "ciencias_nervoso_endocrino"
        if _contem(base, ["genetica", "hereditariedade", "dna", "gene", "cromossomo", "celula", "material genetico"]):
            return "ciencias_genetica"
        if _contem(
            base,
            [
                "ecologia",
                "ecossistema",
                "cadeia alimentar",
                "teia alimentar",
                "relacao ecologica",
                "seres vivos",
                "ambiente",
                "biodiversidade",
            ],
        ):
            return "ciencias_ecologia"
        if _contem(base, ["ciencia", "fenomeno natural", "observacao", "investigacao", "organismo", "saude"]):
            return "ciencias_geral"
    if perfil == "geografia":
        if _contem(
            base,
            [
                "mapa tematico",
                "cartografia tematica",
                "mapa qualitativo",
                "mapa quantitativo",
                "valor de percepcao",
                "valores de percepcao",
                "gradacao de cor",
                "simbolo proporcional",
                "representacao cartografica",
                "fenomeno geografico",
                "titulo do mapa",
                "legenda",
                "simbologia",
                "mapa-base",
                "escala",
            ],
        ):
            return "geografia_cartografia_tematica"
        if _contem(
            base,
            [
                "produzir mapa",
                "elaborar mapa",
                "construir mapa",
                "mapa-base",
                "titulo",
                "legenda",
                "simbologia",
                "representar",
                "recorte de area",
                "correlacao entre mapas",
            ],
        ):
            return "geografia_producao_cartografica"
        if _contem(
            base,
            [
                "tabela",
                "grafico",
                "dados",
                "indice",
                "porcentagem",
                "valor",
                "quantidade",
                "concentracao",
                "densidade demografica",
                "pib",
                "comparar",
                "interpretar",
                "analisar",
            ],
        ):
            return "geografia_dados_espaciais"
        if _contem(
            base,
            [
                "fenomeno",
                "distribuicao",
                "distribuicao espacial",
                "regional",
                "territorio",
                "espaco geografico",
                "urbanizacao",
                "populacao",
                "clima",
                "vegetacao",
                "bioma",
                "relevo",
                "hidrografia",
                "desigualdade",
                "planejamento",
                "politica publica",
                "infraestrutura",
            ],
        ):
            return "geografia_fenomenos"
        if _contem(base, ["mapa", "territorio", "paisagem", "regiao", "cartografia"]):
            return "geografia_geral"
    if perfil == "historia":
        if _contem(base, ["fonte historica", "documento historico", "carta", "charge", "trecho de documento", "leia o trecho", "evidencia historica", "analise de fonte"]):
            return "historia_fonte"
        if _contem(base, ["monarquia", "rei", "governo", "poder", "centralizacao", "absolutismo", "parlamento", "czar", "imperio", "coroa", "estado", "soberano", "dinastia", "trono"]):
            return "historia_poder_politico"
        if _contem(base, ["classes sociais", "nobreza", "camponeses", "escravizados", "indigenas", "desigualdade", "hierarquia", "servos", "burguesia", "proletariado", "criollos", "peninsulares", "mestic", "estrutura social"]):
            return "historia_sociedade_desigualdade"
        if _contem(base, ["guerra", "batalha", "exercito", "conflito", "derrota", "vitoria", "tropas", "invasao", "soldados", "armamento", "combate", "alianca", "tratado"]):
            return "historia_conflito"
        if _contem(base, ["independencia", "independencias", "revolucao", "colonia", "metropole", "emancipacao", "revolta", "insurreicao", "separacao", "autonomia", "movimento revolucionario", "america espanhola"]):
            return "historia_independencia_revolucao"
        if _contem(base, ["iluminismo", "ideias", "pensadores", "liberdade", "igualdade", "soberania", "direitos", "contrato social", "razao", "filosofia", "nacionalismo", "republicanismo", "liberalismo", "socialismo"]):
            return "historia_ideias"
        return "historia_geral"
    if _contem(base, ["mapa", "territorio", "paisagem", "regiao", "cartografia"]):
        return "analise_geografica"
    if _contem(base, ["fonte historica", "tempo historico", "linha do tempo", "documento"]):
        return "analise_historica"
    if _contem(base, ["ciencia", "experimento", "observacao", "seres vivos", "ambiente"]):
        return "investigacao_ciencias"
    return "geral_cdp"


def _conceito_cdp_contextual(perfil: str, tema: str, conceito: str = "") -> str:
    tema_limpo = _limpar_tema_cdp_contextual(tema, "")
    conceito_limpo = _limpar_tema_cdp_contextual(conceito or "", "")
    base = _normalizar(f"{tema_limpo} {conceito_limpo}")
    tipo = _tipo_conteudo_cdp(perfil, tema_limpo, conceito_limpo)
    conceitos = {
        "reta_numerica_racionais": "números racionais e sua localização na reta numérica",
        "operacoes_racionais": "números racionais, decimais e resolução de operações e problemas",
        "pontos_plano_cartesiano": "localização de pontos e pares ordenados no plano cartesiano",
        "poligonos_plano_cartesiano": "polígonos no plano cartesiano e leitura de coordenadas",
        "simetria_plano_cartesiano": "simetria e localização de pontos no plano cartesiano",
        "area_malha_quadriculada": "área e contagem de unidades em malha quadriculada",
        "relacao_grandezas_algebrica": "relação entre grandezas e representação algébrica",
        "relacao_grandezas_grafica": "relação entre grandezas e representação gráfica",
        "conceito_funcao": "conceito de função e dependência entre grandezas",
        "representacao_funcoes": "representações numérica, algébrica e gráfica de funções",
        "dependencia_grandezas": "função como relação de dependência entre duas grandezas",
        "verificacao_funcao": "verificação formativa dos conceitos centrais de função",
        "revisao_funcao": "revisão dos conceitos centrais de função",
        "funcao_logaritmica": "função logarítmica e relação entre potência e logaritmo",
        "algebra_variavel": "letras, variaveis e expressoes algebricas",
        "algebra_valor_numerico": "substituicao de letras e calculo do valor numerico",
        "equacao_igualdade": "igualdade e ideia de equilibrio na resolucao de equacoes",
        "equacao_1_grau": "equacoes do 1o grau e operacoes inversas",
        "equacao_duas_incognitas": "equacoes com duas incognitas, tabela de valores e plano cartesiano",
        "sistema_equacoes": "sistemas de equacoes e comparacao de duas condicoes ao mesmo tempo",
        "semelhanca_triangulos": "semelhanca de triangulos e proporcionalidade entre lados correspondentes",
        "teorema_pitagoras": "teorema de Pitagoras em triangulos retangulos",
        "fracao_adicao_subtracao": "adição e subtração de frações",
        "fracao_mult_div": "multiplicação e divisão de frações",
        "fracao_comparacao": "comparação, ordenação e simplificação de frações",
        "forma_mista": "números mistos e frações impróprias",
        "fracao_quantidade": "fração de uma quantidade",
        "fracao_conceito": "fração como parte do todo e resultado de divisão",
        "combinatoria": "contagem de possibilidades",
        "equacao": "equações e valores desconhecidos",
        "porcentagem": "porcentagem em situações cotidianas",
        "geometria_angulos": "ângulos, giros e classificações",
        "geometria_poligonos": "polígonos e suas características",
        "geometria_medidas": "medidas, área e perímetro",
        "producao_textual": "produção e revisão de textos",
        "argumentacao": "argumentação e organização de opiniões",
        "leitura_interpretacao": "leitura, interpretação e registro de ideias",
        "lp_artigo_opiniao": "artigo de opinião: estrutura, fato, opinião e conectivos",
        "lp_relacoes_logico_discursivas": "relações lógico-discursivas e conectivos na argumentação",
        "genero_textual": "leitura e características do gênero textual",
        "analise_linguistica": "análise de recursos linguísticos em contexto",
        "vocabulario_inferencia": "vocabulário e inferência de sentidos pelo contexto",
        "retomada_lp": "retomada e aprofundamento de leitura e linguagem",
        "analise_geografica": "leitura de paisagens, mapas e territórios",
        "geografia_cartografia_tematica": "cartografia temática e diferenciação entre mapas qualitativos e quantitativos",
        "geografia_fenomenos": "distribuição espacial de fenômenos geográficos",
        "geografia_dados_espaciais": "leitura e interpretação de dados espaciais em mapas, tabelas e gráficos",
        "geografia_producao_cartografica": "produção de mapa temático com título, legenda e simbologia",
        "geografia_geral": "leitura do espaço geográfico por mapas, paisagens e territórios",
        "analise_historica": "análise de fontes e relações de tempo histórico",
        "historia_poder_politico": "organização do poder político no período estudado",
        "historia_conflito": "causas, grupos envolvidos e consequências do conflito estudado",
        "historia_independencia_revolucao": "processos de independência, revolução e mudança política",
        "historia_sociedade_desigualdade": "organização social, hierarquias e desigualdades históricas",
        "historia_ideias": "ideias políticas e pensamento histórico do período estudado",
        "historia_fonte": "leitura e análise de fonte histórica",
        "historia_geral": "relações entre contexto, sujeitos e mudanças históricas",
        "ciencias_alimentacao": "alimentação balanceada, grupos alimentares e montagem de cardápio",
        "ciencias_digestao": "processo de digestão e aproveitamento dos nutrientes",
        "ciencias_nervoso_endocrino": "sistemas nervoso e endócrino no desenvolvimento humano",
        "ciencias_genetica": "hereditariedade, células e material genético",
        "ciencias_ecologia": "relações ecológicas, seres vivos e ambiente",
        "ciencias_geral": "observação e explicação de fenômenos naturais",
        "investigacao_ciencias": "observação e explicação de fenômenos naturais",
    }
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        if _contem(base, ["relacoes logico-discursivas", "relacao logico-discursiva", "logico-discursiva"]):
            return "relações lógico-discursivas e conectivos na argumentação"
        if _contem(base, ["textos contemporaneos na construcao da opiniao", "textos contempor", "construcao da opini", "artigo de opiniao", "artigo de opini", "bibliotecas publicas"]):
            return "artigo de opinião: estrutura, fato, opinião e conectivos"
        if _contem(base, ["relacoes logico-discursivas", "conectivo", "conjuncao", "coesao", "adversativa", "concessiva"]):
            return "relações lógico-discursivas e conectivos na argumentação"
        if _contem(base, ["por dentro da cronica parte 2", "modo subjuntivo", "subjuntivo"]):
            return "modo subjuntivo em textos literários"
        if _contem(base, ["por dentro da cronica parte 1", "por dentro da cronica"]):
            return "leitura e características do gênero crônica"
        if _contem(base, ["verbos que contam historias parte 1", "tempos verbais na narrativa"]):
            return "tempos verbais na narrativa"
        if _contem(base, ["verbos que contam historias parte 2", "efeitos de sentido dos tempos verbais"]):
            return "efeitos de sentido dos tempos verbais"
        if _contem(base, ["cronica"]):
            return "leitura e análise do gênero crônica"
        if _contem(base, ["verbo", "modo", "tempo verbal"]):
            return "análise de verbos e modos verbais em contexto"
    if tipo in conceitos:
        return conceitos[tipo]
    if "matematica resolucao de problemas" in base:
        return "resolução de problemas matemáticos"
    if conceito_limpo and not _tema_truncado_cdp(conceito_limpo):
        return conceito_limpo
    if tema_limpo and not _tema_truncado_cdp(tema_limpo):
        return tema_limpo
    return "conteúdo central da aula"


def _exemplo_concreto_cdp(tipo: str) -> str:
    exemplos = {
        "reta_numerica_racionais": "marcação de inteiros, frações e decimais em uma mesma reta numérica",
        "operacoes_racionais": "adição, subtração, multiplicação e divisão com frações e números decimais em situações práticas",
        "pontos_plano_cartesiano": "leitura de pares ordenados e localização de pontos em eixos desenhados no quadro",
        "poligonos_plano_cartesiano": "identificação de vértices e construção de figuras simples a partir de coordenadas",
        "simetria_plano_cartesiano": "observação de pontos simétricos em relação aos eixos no plano cartesiano",
        "area_malha_quadriculada": "contagem de quadradinhos e comparação de áreas em desenhos simples na malha",
        "relacao_grandezas_algebrica": "valor pago por quantidade de produtos, distância percorrida e produção ao longo do tempo",
        "relacao_grandezas_grafica": "organização de tabelas simples, pares ordenados e leitura de pontos no plano cartesiano",
        "conceito_funcao": "situações em que um valor de entrada gera um valor de saída, como preço e quantidade ou tempo e distância",
        "representacao_funcoes": "comparação entre tabela, expressão algébrica e gráfico para descrever a mesma relação",
        "dependencia_grandezas": "situações reais em que uma grandeza depende da outra, como salário por dias trabalhados ou consumo por quantidade",
        "verificacao_funcao": "retomada diagnóstica de relação entre grandezas, tabela, expressão e gráfico",
        "revisao_funcao": "síntese de tabela, expressão algébrica, gráfico e dependência entre variáveis",
        "funcao_logaritmica": "pH, intensidade de abalos sísmicos e outras variações em escala ligadas à ideia de potência",
        "algebra_variavel": "preco por unidade, dobro, triplo, metade e quantidades que podem variar",
        "algebra_valor_numerico": "substituicao de letras por numeros em expressoes simples",
        "equacao_igualdade": "balanca em equilibrio e comparacao entre dois lados de uma igualdade",
        "equacao_1_grau": "descoberta de um valor desconhecido por meio de operacoes inversas",
        "equacao_duas_incognitas": "organizacao de pares de valores em tabela e localizacao em malha quadriculada",
        "sistema_equacoes": "problemas com duas informacoes que precisam ser atendidas ao mesmo tempo",
        "semelhanca_triangulos": "comparacao entre rampas, sombras, paredes e objetos em tamanhos diferentes",
        "teorema_pitagoras": "escada apoiada na parede, diagonal e caminho mais curto entre dois pontos",
        "fracao_conceito": "divisão de alimentos, porções ou folhas em partes iguais",
        "fracao_quantidade": "cálculo de partes de uma quantidade total, como metade ou um quarto de objetos",
        "fracao_adicao_subtracao": "junção e retirada de partes de uma mesma quantidade",
        "fracao_mult_div": "repartição de porções e cálculo de partes sucessivas",
        "fracao_comparacao": "comparação de porções para decidir qual representa maior quantidade",
        "forma_mista": "representação de quantidades inteiras acompanhadas de partes restantes",
        "combinatoria": "combinação de escolhas simples, como letras, números ou objetos",
        "equacao": "descoberta de um valor desconhecido em uma situação organizada por etapas",
        "porcentagem": "cálculo de descontos, acréscimos e partes de 100",
        "geometria_angulos": "giros, cantos de paredes, portas e posições no espaço",
        "geometria_poligonos": "identificação de figuras por lados, vértices e formas presentes no ambiente",
        "geometria_medidas": "medição de espaços, contornos e superfícies simples",
        "leitura_interpretacao": "leitura de texto impresso e identificação das informações principais",
        "lp_artigo_opiniao": "identificação de tese, fato, opinião e argumentos em artigo de opinião",
        "lp_relacoes_logico_discursivas": "uso de conectivos para ligar ideias de causa, oposição, concessão e conclusão",
        "producao_textual": "planejamento de respostas e pequenos textos com começo, desenvolvimento e fechamento",
        "argumentacao": "organização de uma opinião com justificativa clara",
        "genero_textual": "observação de características de um texto do cotidiano",
        "analise_linguistica": "comparação de frases para perceber mudanças de sentido",
        "vocabulario_inferencia": "descoberta do sentido de palavras a partir do trecho lido",
        "retomada_lp": "ligação entre o texto já lido e o novo conceito da aula",
        "geografia_cartografia_tematica": "comparação entre mapas que mostram categorias, valores numéricos, legenda, cores e símbolos",
        "geografia_fenomenos": "análise da distribuição de população, clima, vegetação, serviços ou infraestrutura no território",
        "geografia_dados_espaciais": "leitura de mapas, tabelas ou gráficos para comparar valores entre regiões",
        "geografia_producao_cartografica": "construção de mapa-base com título, legenda, cores e símbolos adequados",
        "geografia_geral": "observação de mapas, paisagens e relações entre sociedade, natureza e território",
        "historia_poder_politico": "quem governava, como mantinha o poder e quais grupos o apoiavam",
        "historia_conflito": "oposição entre grupos, interesses e consequências de uma guerra ou conflito",
        "historia_independencia_revolucao": "insatisfação social, liderança, mudança política e resultado do movimento",
        "historia_sociedade_desigualdade": "posição de grupos sociais, direitos, obrigações e desigualdades",
        "historia_ideias": "ideias de liberdade, igualdade, soberania ou direitos em seu contexto histórico",
        "historia_fonte": "perguntas sobre quem produziu a fonte, quando, para quem e com qual objetivo",
        "historia_geral": "sequência de acontecimentos, causas e consequências do tema histórico",
        "ciencias_alimentacao": "organização de alimentos como arroz, feijão, frutas, verduras, legumes, ovos e leite em refeições equilibradas",
        "ciencias_digestao": "caminho dos alimentos pelo corpo e transformação em nutrientes aproveitados pelo organismo",
        "ciencias_nervoso_endocrino": "respostas do corpo, hormônios, cérebro e mudanças do desenvolvimento humano",
        "ciencias_genetica": "semelhanças familiares, células, genes e transmissão de características",
        "ciencias_ecologia": "relações entre seres vivos, ambiente, alimentação e equilíbrio dos ecossistemas",
        "ciencias_geral": "observação de situações naturais e explicação das causas e consequências envolvidas",
    }
    return exemplos.get(tipo, "situação concreta próxima da realidade dos estudantes")


def _limpar_texto_cdp_contextual(texto: str) -> str:
    proibidos = [
        "Virem e conversem",
        "Todo mundo escreve",
        "Com suas palavras",
        "Pause e responda",
        "Para começar",
        "Foco no conteúdo",
        "De olho no modelo",
        "recurso digital",
        "tecnologia",
        "tecnologias digitais",
        "aplicativo",
        "internet",
        "vídeo",
        "filme",
        "youtube",
        "slide",
        "slides",
        "projete",
        "projetar",
        "projetor",
        "datashow",
        "laboratório",
        "em duplas",
        "em grupos",
        "levante a mão",
        "cruze os braços",
        "mímica",
        "dramatize",
        "assistir ao vídeo",
        "pesquisar na internet",
        "acessar o link",
        "usar o celular",
        "plataforma",
        "redes sociais",
        "posts",
        "stories",
        "pnld",
        "livro didático",
        "livro didatico",
        "assista ao vídeo",
        "link para vídeo",
        "resposta pessoal",
        "você concorda",
        "voce concorda",
        "veja no livro",
        "caderno de exercícios",
        "caderno de exercicios",
        "simulador",
        "simuladores",
        "na escola",
        "sua escola",
        "colegas de escola",
        "compartilhe com os seus colegas",
        "compartilhe com seus colegas",
        "use sua criatividade",
        "sua história",
        "sua historia",
        "encontre um colega",
        "estimule a análise crítica",
        "estimule a analise critica",
        "provoque a turma",
        "relacionadas ao tema",
        "disponível em",
        "http",
        "acesse",
    ]
    saida = str(texto or "")
    for termo in proibidos:
        if termo.lower() in [
            "virem e conversem",
            "todo mundo escreve",
            "com suas palavras",
            "pause e responda",
            "para comecar",
            "para começar",
            "foco no conteudo",
            "foco no conteúdo",
            "de olho no modelo",
            "um passo de cada vez",
            "hora da leitura",
        ]:
            saida = re.sub(
                rf"(?<!t[eé]cnica\s)(?<!din[aá]mica\s)(?<!momento\s)(?<!proposta\s)(?<!estrat[eé]gia\s){re.escape(termo)}",
                "",
                saida,
                flags=re.I,
            )
        else:
            saida = re.sub(re.escape(termo), "", saida, flags=re.I)
    return re.sub(r"\s+", " ", saida).strip()


def _tipos_matematica_eja_cdp() -> set[str]:
    return {
        "reta_numerica_racionais",
        "operacoes_racionais",
        "pontos_plano_cartesiano",
        "poligonos_plano_cartesiano",
        "simetria_plano_cartesiano",
        "area_malha_quadriculada",
        "relacao_grandezas_algebrica",
        "relacao_grandezas_grafica",
        "conceito_funcao",
        "representacao_funcoes",
        "dependencia_grandezas",
        "verificacao_funcao",
        "revisao_funcao",
        "funcao_logaritmica",
        "algebra_variavel",
        "algebra_valor_numerico",
        "equacao_igualdade",
        "equacao_1_grau",
        "equacao_duas_incognitas",
        "sistema_equacoes",
        "semelhanca_triangulos",
        "teorema_pitagoras",
    }


def _metodologia_matematica_eja_cdp(tipo_cdp: str, indice_aula: int = 0) -> str:
    aberturas = {
        "reta_numerica_racionais": [
            "A proposta da aula parte da observação de uma reta numérica simples no quadro, retomando primeiro a posição dos números inteiros mais conhecidos.",
            "Como ponto de partida, desenhar no quadro uma reta numérica e convidar a turma a localizar valores como 0, 1, 2, 1/2 e 0,5.",
        ],
        "operacoes_racionais": [
            "A retomada inicial deve considerar situações em que frações e decimais aparecem em medidas, divisões e valores do cotidiano, aproximando o conteúdo da experiência dos estudantes.",
            "O trabalho pode ser iniciado com exemplos simples de números racionais escritos no quadro, mostrando como eles aparecem em contas do dia a dia e em problemas de medida.",
        ],
        "pontos_plano_cartesiano": [
            "A aula se organiza a partir do desenho dos eixos no quadro, com marcações amplas que permitam visualizar a posição de cada ponto com clareza.",
            "No primeiro momento, registrar no quadro um plano cartesiano simples e retomar com a turma a leitura da horizontal e da vertical antes de marcar os pontos.",
        ],
        "poligonos_plano_cartesiano": [
            "A atividade começa com a marcação de alguns pontos no plano cartesiano e a discussão de como eles podem ser ligados para formar figuras conhecidas.",
            "A abordagem inicial consiste em apresentar coordenadas simples no quadro e mostrar como a união entre vértices pode gerar diferentes polígonos.",
        ],
        "simetria_plano_cartesiano": [
            "A construção do conceito parte da observação de pontos em lados opostos de um eixo, para que a turma perceba o que muda e o que permanece em uma situação de simetria.",
            "Para introduzir o tema, utilizar um plano cartesiano no quadro e marcar alguns pontos, comparando suas posições em relação aos eixos para explorar a ideia de simetria.",
        ],
        "area_malha_quadriculada": [
            "A proposta da aula parte de desenhos simples em malha quadriculada, permitindo que a turma observe a área por contagem de unidades antes de formalizar procedimentos.",
            "O percurso da aula começa pela observação de figuras desenhadas em quadradinhos, favorecendo a compreensão visual da ideia de área.",
        ],
        "relacao_grandezas_algebrica": [
            "A proposta da aula parte de uma situação simples relacionada ao cotidiano dos estudantes, permitindo observar como duas grandezas podem se relacionar ao longo de uma tabela de valores.",
            "O trabalho pode ser iniciado com um exemplo em que uma quantidade depende de outra, como valor pago por produtos, distância percorrida ou produção em determinado tempo.",
        ],
        "relacao_grandezas_grafica": [
            "Como ponto de partida, apresentar no quadro uma tabela com valores simples e discutir com a turma como cada par de números pode ser representado no plano cartesiano.",
            "A aula se organiza a partir de uma tabela já conhecida pela turma, mostrando que os dados podem ser transformados em pares ordenados e visualizados em gráfico.",
        ],
        "conceito_funcao": [
            "A construção do conceito de função pode partir de exemplos em que uma quantidade depende da outra, como preço e quantidade, tempo e distância ou número de unidades e valor total.",
            "Para introduzir o tema, utilizar situações cotidianas em que um valor de entrada gera um valor de saída, organizando os exemplos no quadro com linguagem direta.",
        ],
        "representacao_funcoes": [
            "A atividade se desenvolve com a observação de uma mesma situação representada de três maneiras: por tabela, por expressão algébrica e por gráfico.",
            "O percurso da aula começa pela comparação entre registros numéricos, algébricos e gráficos, mostrando que eles descrevem a mesma relação entre grandezas.",
        ],
        "dependencia_grandezas": [
            "A retomada inicial deve considerar uma situação cotidiana, como o valor de uma compra dependendo da quantidade adquirida ou o salário variando conforme os dias trabalhados.",
            "A abordagem inicial consiste em registrar no quadro duas grandezas ligadas entre si e conduzir a turma a perceber qual delas varia e qual depende da outra.",
        ],
        "verificacao_funcao": [
            "A aula pode ser conduzida como uma verificação formativa dos conceitos trabalhados sobre função, retomando no quadro as ideias centrais antes das atividades.",
            "No primeiro momento, registrar no quadro os conceitos principais de função e organizar uma revisão curta para que a turma relembre os procedimentos já estudados.",
        ],
        "revisao_funcao": [
            "A revisão parte da organização, no quadro, dos principais pontos já estudados sobre função: relação entre grandezas, variável dependente e independente, tabela, expressão e gráfico.",
            "A proposta da aula começa pela retomada dos exemplos já trabalhados, reunindo em um mesmo esquema as diferentes formas de representar uma função.",
        ],
        "funcao_logaritmica": [
            "A abordagem inicial deve relacionar a função logarítmica a situações em que a variação acontece em escala, como pH, intensidade de abalos sísmicos ou crescimento de valores em determinados contextos.",
            "Como ponto de partida, retomar no quadro a ideia de potência e, a partir dela, apresentar o logaritmo como forma de descobrir o expoente em uma igualdade simples.",
        ],
        "algebra_variavel": [
            "A proposta da aula parte de situacoes simples em que uma quantidade pode mudar, como o preco de varias unidades de um mesmo produto, o dobro de uma medida ou a metade de um valor.",
            "Como ponto de partida, registrar no quadro exemplos em que letras representam numeros que variam, aproximando a linguagem algebrica de situacoes que os estudantes conseguem visualizar com facilidade.",
        ],
        "algebra_valor_numerico": [
            "Na retomada inicial, registrar no quadro uma expressao algebrica curta e substituir a letra por um numero conhecido, mostrando cada etapa do calculo com calma.",
            "O trabalho comeca pela leitura de expressoes simples no quadro, destacando o que muda quando a letra recebe valores diferentes e como isso altera o resultado final.",
        ],
        "equacao_igualdade": [
            "A aula se organiza a partir da ideia de equilibrio, comparando a igualdade a uma balanca em que os dois lados precisam permanecer com o mesmo valor.",
            "Para introduzir o tema, desenhar no quadro uma situacao de balanca em equilibrio e relacionar essa imagem ao sentido matematico de igualdade.",
        ],
        "equacao_1_grau": [
            "A abordagem inicial consiste em apresentar no quadro um problema curto com valor desconhecido, transformando a situacao em equacao e resolvendo uma etapa por vez.",
            "O conteudo pode ser apresentado por meio de exemplos diretos em que o estudante precisa descobrir um numero escondido, organizando a resolucao com operacoes inversas.",
        ],
        "equacao_duas_incognitas": [
            "A primeira etapa da aula propoe observar duas quantidades que variam juntas, registrando no quadro pares de valores e organizando uma tabela simples antes da representacao no plano.",
            "A construcao do conceito acontece a partir de uma tabela de valores feita no quadro, mostrando como duas grandezas podem ser relacionadas e localizadas em malha quadriculada.",
        ],
        "sistema_equacoes": [
            "A situacao inicial deve envolver um problema com duas informacoes ao mesmo tempo, para que a turma perceba a necessidade de trabalhar duas equacoes ligadas ao mesmo contexto.",
            "O professor pode abrir a aula com um problema em que duas pistas precisam ser analisadas juntas, organizando no quadro as informacoes antes de escolher o procedimento de resolucao.",
        ],
        "semelhanca_triangulos": [
            "A turma e convidada a observar no quadro dois triangulos desenhados em tamanhos diferentes, identificando o que permanece proporcional entre eles.",
            "A explicacao deve partir de um exemplo simples de ampliacao e reducao, como sombras, rampas ou paredes, para aproximar a semelhanca de triangulos de situacoes concretas.",
        ],
        "teorema_pitagoras": [
            "No primeiro momento, registrar no quadro um triangulo retangulo ligado a uma situacao concreta, como uma escada apoiada na parede ou a diagonal de um espaco.",
            "A proposta da aula parte de um triangulo retangulo desenhado no quadro, com identificacao clara de catetos e hipotenusa antes da apresentacao da relacao a2 + b2 = c2.",
        ],
    }
    desenvolvimentos = {
        "reta_numerica_racionais": "O professor retoma com a turma que os números racionais podem aparecer entre os inteiros e organiza exemplos com frações e decimais de fácil visualização, como 1/2, 0,5, 1/4 e 0,25. Em seguida, os estudantes realizam atividades graduais no caderno: primeiro localizando pontos já indicados e depois completando a reta com novos valores. Para a sala multisseriada, alguns alunos permanecem na leitura e marcação de números mais simples, enquanto outros avançam para comparações e ordenação. A correção coletiva retoma a posição dos números e a distância entre eles sem expor individualmente os erros.",
        "operacoes_racionais": "No quadro, o professor organiza a resolução passo a passo, destacando a leitura do enunciado, a escolha da operação e a escrita dos cálculos de forma ordenada no caderno. Durante a prática, os estudantes resolvem atividades em níveis: uma parte da turma trabalha com contas mais diretas e outra avança para problemas que exigem interpretação e combinação de procedimentos. O acompanhamento é próximo, com retomada de dúvidas básicas, e a correção coletiva destaca os procedimentos corretos e os erros mais frequentes na organização dos cálculos.",
        "pontos_plano_cartesiano": "A explicação avança com a leitura dos pares ordenados, mostrando qual valor deve ser observado primeiro e como localizar cada ponto sem inverter as coordenadas. Na atividade escrita, alguns estudantes trabalham com marcações já orientadas, enquanto outros registram novos pontos e interpretam sua posição no plano. O professor acompanha a prática individualmente e o fechamento acontece com correção coletiva, retomando a ordem dos pares e a leitura dos eixos.",
        "poligonos_plano_cartesiano": "Na sequência, o professor mostra como localizar os vértices, unir os pontos e reconhecer figuras a partir de suas coordenadas, sempre com desenhos grandes e claros no quadro. Os estudantes registram os pontos no caderno e realizam atividades graduais: alguns identificam vértices e ligam figuras já sugeridas, enquanto outros constroem polígonos a partir de coordenadas dadas. A correção coletiva retoma a leitura das coordenadas e as características das figuras formadas.",
        "simetria_plano_cartesiano": "O professor conduz a leitura dos pontos, mostra como identificar a posição simétrica em relação aos eixos e resolve exemplos curtos antes da atividade individual. Durante a prática, parte da turma trabalha com pontos já marcados e observação visual da simetria, enquanto outra parte avança para o registro de coordenadas e comparação entre posições. A correção coletiva destaca o eixo de referência, a mudança de sinal quando necessário e os cuidados com a leitura dos pares ordenados.",
        "area_malha_quadriculada": "No quadro, o professor orienta a contagem das unidades de área e mostra como comparar figuras simples desenhadas em quadradinhos, evitando formalismo excessivo antes da compreensão visual. Na prática, os estudantes resolvem atividades graduais no caderno: alguns contam quadradinhos inteiros e reconhecem áreas equivalentes, enquanto outros avançam para composições um pouco mais complexas. O acompanhamento acontece durante a contagem e a correção coletiva retoma estratégias de organização e comparação das figuras.",
        "relacao_grandezas_algebrica": "No quadro, o professor organiza os dados em uma tabela simples, conduz a turma na identificação do padrão e mostra como representar essa relação por meio de uma expressão algébrica, resolvendo um exemplo passo a passo. Durante a prática, os estudantes completam tabelas, observam regularidades e escrevem a regra que relaciona as grandezas. Para atender à turma multisseriada, alguns alunos realizam exercícios de retomada com padrões mais diretos, enquanto outros avançam para situações que exigem generalização. A correção coletiva destaca a passagem da tabela para a expressão algébrica e retoma os erros mais comuns.",
        "relacao_grandezas_grafica": "O professor desenha os eixos, localiza os pontos com a participação dos estudantes e mostra como o gráfico ajuda a visualizar a relação entre as grandezas. Em seguida, os alunos constroem gráficos no caderno a partir de tabelas fornecidas. Para a sala multisseriada, a atividade pode ser organizada em níveis: localização de pontos para quem precisa retomar a base e interpretação do comportamento do gráfico para quem já demonstra maior domínio. No fechamento, a correção coletiva retoma a ordem dos pares ordenados, a marcação dos pontos e a leitura do gráfico.",
        "conceito_funcao": "No quadro, o professor organiza uma pequena tabela, identifica os valores de entrada e saída e explica, com linguagem simples, que uma função relaciona duas grandezas de forma organizada. Durante a prática, os estudantes analisam situações e indicam qual grandeza depende da outra. As atividades são graduadas: primeiro com leitura de tabelas simples e depois com identificação da regra de formação. A correção coletiva retoma a diferença entre variável independente e dependente, garantindo que todos acompanhem o raciocínio.",
        "representacao_funcoes": "No quadro, o professor mostra como os dados da tabela podem gerar uma expressão e como os pares ordenados podem ser marcados no plano cartesiano, reforçando que todas essas formas descrevem a mesma relação. Na sequência, os estudantes resolvem atividades no caderno, relacionando tabelas, expressões e gráficos simples. Para atender aos diferentes níveis da turma, alguns realizam a identificação direta das representações, enquanto outros interpretam o significado dos valores em situações-problema. A correção coletiva destaca as conexões entre as formas de representação e retoma as dúvidas mais recorrentes.",
        "dependencia_grandezas": "A partir desse exemplo, o professor registra no quadro as duas grandezas envolvidas e orienta a turma a perceber qual delas depende da outra. Depois da explicação, os estudantes resolvem situações semelhantes no caderno, identificando as grandezas, montando tabelas e registrando a regra da relação quando possível. A proposta prevê atividades de retomada para quem apresenta dificuldade na identificação das grandezas e desafios de interpretação para os alunos que avançarem com mais segurança. A correção coletiva retoma a ideia central de dependência entre variáveis.",
        "verificacao_funcao": "Em seguida, o professor propõe uma sequência curta de atividades para que os estudantes demonstrem o que compreenderam sobre relação entre grandezas, tabela, expressão algébrica, gráfico e dependência entre variáveis. Durante a resolução, acompanha individualmente os registros, observa as dificuldades e orienta os alunos sem antecipar todas as respostas. Ao final, a correção coletiva é feita de forma comentada, retomando os pontos que apresentaram maior dificuldade e reorganizando no quadro os procedimentos corretos.",
        "revisao_funcao": "A turma participa retomando exemplos já trabalhados e identificando onde cada representação aparece. Em seguida, os estudantes resolvem uma sequência de exercícios mistos, com questões de leitura, preenchimento de tabela, identificação da regra e interpretação de gráfico. As atividades são organizadas em níveis para contemplar a turma multisseriada, com retomada para quem precisa consolidar a base e desafios para quem já acompanha com mais autonomia. O fechamento ocorre com correção coletiva e síntese dos cuidados mais importantes.",
        "funcao_logaritmica": "No quadro, o professor retoma a ideia de potência e apresenta o logaritmo como uma forma de descobrir o expoente em uma igualdade simples, utilizando exemplos numéricos acessíveis e sem excesso de formalismo. Na prática, os estudantes analisam situações guiadas e resolvem exercícios básicos de interpretação. Para a turma multisseriada, alguns alunos retomam potências simples e leitura de valores, enquanto outros avançam para problemas que envolvem a variação das grandezas. A correção coletiva reforça a relação entre potência e logaritmo e esclarece as dúvidas mais comuns.",
        "algebra_variavel": "A explicacao avanca com exemplos no quadro que diferenciam letra como valor desconhecido e letra como quantidade variavel, sempre com linguagem direta e registros curtos no caderno. Na pratica, os estudantes resolvem atividades graduais: alguns identificam o que a letra representa e escrevem expressoes mais diretas, enquanto outros avancam para situacoes em que precisam calcular dobro, triplo, metade ou montar pequenas expressoes. Durante a resolucao, o professor acompanha de perto, retoma duvidas sem exposicao individual e encerra com correcao coletiva, destacando os erros mais comuns na leitura e na escrita da linguagem algebrica.",
        "algebra_valor_numerico": "Depois da demonstracao inicial, a turma acompanha no quadro a substituicao de letras por numeros e a organizacao das operacoes em ordem clara, evitando saltos de raciocinio. Os exercicios no caderno sao distribuidos em niveis: uma parte da turma trabalha com substituicoes diretas e contas mais curtas, enquanto outra resolve expressoes com duas ou mais operacoes. O professor circula entre os estudantes, orienta a organizacao das etapas e finaliza com correcao coletiva, retomando especialmente erros de substituicao e de ordem de calculo.",
        "equacao_igualdade": "Com base nessa comparacao, o professor mostra no quadro que tudo o que e feito de um lado precisa ser feito do outro, resolvendo exemplos curtos com uma operacao por vez. Na atividade escrita, alguns estudantes trabalham com igualdades mais diretas para consolidar a ideia de equilibrio, enquanto outros avancam para sentencas que exigem mais passos. O acompanhamento acontece durante a pratica e a correcao coletiva retoma os procedimentos, valorizando a organizacao do raciocinio sem expor individualmente quem errou.",
        "equacao_1_grau": "A resolucao guiada destaca a organizacao dos dados, a identificacao da incognita e o uso das operacoes inversas para isolar o valor procurado. Na sequencia, os alunos resolvem atividades no caderno com niveis diferentes: uns trabalham com equacoes mais diretas e outros transformam pequenos problemas em linguagem matematica antes de resolver. O professor acompanha os registros, ajuda na montagem da sentenca matematica e fecha a aula com correcao coletiva e verificacao do resultado encontrado.",
        "equacao_duas_incognitas": "Em seguida, o professor completa com a turma alguns pares de valores, explica como localizar os pontos na malha e relaciona a tabela com a representacao grafica. Para atender ao ritmo multisseriado, uma parte dos estudantes permanece na leitura da tabela e na montagem de pares ordenados, enquanto outra avanca para a observacao da reta e da relacao entre a equacao e o grafico. A pratica e acompanhada de perto, com apoio individual quando necessario, e o fechamento ocorre por meio de correcao coletiva dos registros mais importantes.",
        "sistema_equacoes": "A partir desse ponto, o professor organiza as informacoes no quadro, nomeia as incognitas e resolve o sistema gradualmente, por substituicao ou adicao, conforme o nivel da turma. Na atividade no caderno, alguns estudantes resolvem casos mais diretos com bastante apoio na leitura dos dados, enquanto outros avancam para problemas em que precisam interpretar melhor o contexto e justificar o resultado. O acompanhamento valoriza a organizacao das etapas e a correcao coletiva retoma os erros mais comuns na comparacao das duas condicoes.",
        "semelhanca_triangulos": "Ao longo da explicacao, o professor destaca lados correspondentes, proporcao e relacao entre ampliacao e reducao, usando desenhos grandes no quadro e exemplos que possam ser copiados com clareza no caderno. Os exercicios sao organizados em dois niveis: alguns estudantes identificam pares de lados e reconhecem figuras semelhantes, enquanto outros resolvem problemas de proporcionalidade em contextos como sombras, paredes e rampas. Durante a pratica, o professor acompanha a montagem das razoes e encerra com correcao coletiva, retomando a importancia de comparar lados correspondentes.",
        "teorema_pitagoras": "Na explicacao, o professor apresenta a relacao a2 + b2 = c2, identifica cada lado do triangulo e resolve um exemplo simples em etapas curtas, deixando visivel no quadro onde entra cada valor. Depois, a turma realiza atividades graduais no caderno: alguns estudantes apenas identificam catetos e hipotenusa e aplicam a formula em casos diretos, enquanto outros avancam para problemas de aplicacao com escada, deslocamento e diagonal. O fechamento acontece com correcao coletiva e retomada dos erros mais comuns, principalmente a troca entre cateto e hipotenusa e a organizacao dos quadrados dos numeros.",
    }
    opcoes = aberturas.get(tipo_cdp)
    if not opcoes or tipo_cdp not in desenvolvimentos:
        return ""
    inicio = opcoes[indice_aula % len(opcoes)]
    return f"{inicio} {desenvolvimentos[tipo_cdp]}"


def _acompanhamento_matematica_eja_cdp(tipo_cdp: str) -> list[str]:
    bancos = {
        "reta_numerica_racionais": [
            "☑ Verificar se o aluno localiza frações e decimais na reta numérica sem inverter a posição dos valores.",
            "☑ Observar se compara corretamente números racionais a partir da posição ocupada na reta.",
            "☑ Acompanhar se registra no caderno a relação entre fração, decimal e ponto marcado.",
        ],
        "operacoes_racionais": [
            "☑ Verificar se o aluno identifica a operação necessária antes de iniciar o cálculo.",
            "☑ Observar se organiza as etapas da conta no caderno sem saltar procedimentos.",
            "☑ Acompanhar se interpreta o resultado de forma coerente com o problema resolvido.",
        ],
        "pontos_plano_cartesiano": [
            "☑ Verificar se o aluno lê os pares ordenados na sequência correta.",
            "☑ Observar se localiza os pontos no plano cartesiano sem trocar os eixos.",
            "☑ Acompanhar se registra com clareza a posição de cada ponto no caderno.",
        ],
        "poligonos_plano_cartesiano": [
            "☑ Verificar se o aluno localiza corretamente os vértices indicados pelas coordenadas.",
            "☑ Observar se reconhece o polígono formado após unir os pontos.",
            "☑ Acompanhar se relaciona coordenadas e características da figura construída.",
        ],
        "simetria_plano_cartesiano": [
            "☑ Verificar se o aluno identifica o eixo de referência na situação de simetria.",
            "☑ Observar se reconhece a posição simétrica de pontos no plano cartesiano.",
            "☑ Acompanhar se registra corretamente as coordenadas após a reflexão do ponto.",
        ],
        "area_malha_quadriculada": [
            "☑ Verificar se o aluno conta corretamente as unidades de área na malha quadriculada.",
            "☑ Observar se compara figuras simples identificando áreas equivalentes ou diferentes.",
            "☑ Acompanhar se organiza a contagem no caderno sem perder unidades da figura.",
        ],
        "relacao_grandezas_algebrica": [
            "☑ Verificar se o aluno identifica as duas grandezas envolvidas na situação proposta.",
            "☑ Observar se reconhece o padrão apresentado na tabela de valores.",
            "☑ Acompanhar se consegue representar a relação por meio de expressão algébrica simples.",
        ],
        "relacao_grandezas_grafica": [
            "☑ Verificar se o aluno organiza corretamente os pares ordenados.",
            "☑ Observar se localiza os pontos no plano cartesiano com apoio da tabela.",
            "☑ Acompanhar se interpreta o gráfico como representação da relação entre as grandezas.",
        ],
        "conceito_funcao": [
            "☑ Identificar se o aluno diferencia variável dependente e independente.",
            "☑ Observar se reconhece quando uma grandeza depende da outra.",
            "☑ Verificar se relaciona tabela, expressão ou gráfico à ideia de função.",
        ],
        "representacao_funcoes": [
            "☑ Verificar se o aluno relaciona tabela, expressão algébrica e gráfico como formas de representar a mesma situação.",
            "☑ Observar se interpreta o significado dos valores em cada forma de representação.",
            "☑ Acompanhar se organiza os registros no caderno sem perder a correspondência entre as representações.",
        ],
        "dependencia_grandezas": [
            "☑ Verificar se o aluno identifica qual grandeza varia e qual depende da outra.",
            "☑ Observar se monta tabela simples com base na situação apresentada.",
            "☑ Acompanhar se registra a regra da relação quando isso for possível na atividade proposta.",
        ],
        "verificacao_funcao": [
            "☑ Identificar quais conceitos de função o aluno já consegue retomar com autonomia.",
            "☑ Observar se relaciona tabela, expressão algébrica e gráfico durante a verificação.",
            "☑ Registrar as principais dúvidas para retomada nas próximas aulas.",
        ],
        "revisao_funcao": [
            "☑ Verificar se o aluno retoma os conceitos centrais de função sem depender apenas da cópia do quadro.",
            "☑ Observar se relaciona tabela, expressão, gráfico e dependência entre variáveis.",
            "☑ Acompanhar se identifica procedimentos que ainda precisam de reforço antes do avanço do conteúdo.",
        ],
        "funcao_logaritmica": [
            "☑ Verificar se o aluno relaciona logaritmo à ideia de potência.",
            "☑ Observar se interpreta situações simples envolvendo escalas de variação.",
            "☑ Acompanhar se resolve exercícios básicos com apoio dos exemplos do quadro.",
        ],
        "algebra_variavel": [
            "☑ Verificar se o aluno identifica o que a letra representa em cada exemplo apresentado.",
            "☑ Observar se diferencia quantidade variavel de valor desconhecido durante os registros no caderno.",
            "☑ Acompanhar se escreve expressoes simples com dobro, triplo, metade ou preco por unidade sem perder o sentido da situacao.",
        ],
        "algebra_valor_numerico": [
            "☑ Verificar se o aluno substitui corretamente o valor da letra na expressao proposta.",
            "☑ Observar se organiza as etapas do calculo antes de apresentar o resultado final.",
            "☑ Acompanhar se respeita a ordem das operacoes nos exemplos resolvidos no caderno.",
        ],
        "equacao_igualdade": [
            "☑ Verificar se o aluno compreende a igualdade como relacao de equilibrio entre dois lados.",
            "☑ Observar se registra no caderno as transformacoes feitas dos dois lados da sentenca.",
            "☑ Acompanhar se identifica erros e corrige o procedimento com apoio durante a correcao coletiva.",
        ],
        "equacao_1_grau": [
            "☑ Verificar se o aluno organiza os dados do problema antes de montar a equacao.",
            "☑ Observar se aplica operacoes inversas de forma adequada para encontrar a incognita.",
            "☑ Acompanhar se registra as etapas da resolucao e confere o resultado encontrado.",
        ],
        "equacao_duas_incognitas": [
            "☑ Verificar se o aluno monta pares de valores coerentes com a relacao apresentada.",
            "☑ Observar se localiza corretamente os pontos na malha ou no plano cartesiano.",
            "☑ Acompanhar se relaciona a tabela de valores com a representacao grafica produzida.",
        ],
        "sistema_equacoes": [
            "☑ Verificar se o aluno identifica as duas informacoes centrais do problema antes de resolver.",
            "☑ Observar se organiza as incognitas e as equacoes sem misturar os dados das duas condicoes.",
            "☑ Acompanhar se justifica o resultado final com base no contexto do problema resolvido.",
        ],
        "semelhanca_triangulos": [
            "☑ Verificar se o aluno identifica lados correspondentes nas figuras comparadas.",
            "☑ Observar se monta proporcoes coerentes ao resolver os exemplos no caderno.",
            "☑ Acompanhar se reconhece quando os triangulos sao semelhantes e explica o criterio usado.",
        ],
        "teorema_pitagoras": [
            "☑ Verificar se o aluno diferencia catetos e hipotenusa no triangulo retangulo apresentado.",
            "☑ Observar se aplica a relacao a2 + b2 = c2 sem trocar os valores de cada lado.",
            "☑ Acompanhar se registra as etapas do calculo e confere o resultado no final da resolucao.",
        ],
    }
    return bancos.get(tipo_cdp, [])


def _acessibilidade_matematica_eja_cdp(tipo_cdp: str) -> list[str]:
    bancos = {
        "reta_numerica_racionais": [
            "☑ Reta numérica desenhada em tamanho ampliado no quadro para facilitar a visualização das marcações.",
            "☑ Retomada da relação entre fração e decimal antes da localização dos pontos.",
            "☑ Tempo ampliado para copiar a reta, marcar os valores e revisar os registros.",
        ],
        "operacoes_racionais": [
            "☑ Leitura coletiva dos enunciados antes do início dos cálculos.",
            "☑ Organização das operações em linhas curtas e bem visíveis no quadro.",
            "☑ Atividades graduais, com exemplos mais diretos antes das situações-problema.",
        ],
        "pontos_plano_cartesiano": [
            "☑ Plano cartesiano desenhado de forma ampliada no quadro para facilitar a leitura dos eixos.",
            "☑ Marcação guiada dos primeiros pares ordenados antes da atividade individual.",
            "☑ Apoio individual para estudantes com dificuldade na leitura da horizontal e da vertical.",
        ],
        "poligonos_plano_cartesiano": [
            "☑ Vértices e coordenadas destacados no quadro antes da construção das figuras.",
            "☑ Atividade em etapas: primeiro localizar pontos, depois unir vértices e por fim identificar a figura.",
            "☑ Tempo ampliado para copiar o plano e concluir a construção dos polígonos no caderno.",
        ],
        "simetria_plano_cartesiano": [
            "☑ Uso de exemplos simples com poucos pontos antes de avançar para situações mais completas.",
            "☑ Destaque visual do eixo de simetria no quadro durante toda a atividade.",
            "☑ Correção coletiva sem exposição individual, retomando a leitura das coordenadas quando necessário.",
        ],
        "area_malha_quadriculada": [
            "☑ Figuras desenhadas de forma clara e ampliada para facilitar a contagem dos quadradinhos.",
            "☑ Retomada da ideia de unidade de área antes da comparação entre as figuras.",
            "☑ Flexibilização do registro, permitindo anotar contagens parciais para organizar o raciocínio.",
        ],
        "relacao_grandezas_algebrica": [
            "☑ Uso de tabelas simples para facilitar a identificação de padrões.",
            "☑ Retomada da ideia de variável antes da escrita da expressão algébrica.",
            "☑ Atividades graduais, com exemplos diretos antes das situações-problema.",
        ],
        "relacao_grandezas_grafica": [
            "☑ Plano cartesiano desenhado em tamanho ampliado no quadro.",
            "☑ Marcação guiada dos primeiros pontos antes da atividade individual.",
            "☑ Tempo ampliado para copiar a tabela e construir o gráfico.",
        ],
        "conceito_funcao": [
            "☑ Explicação com exemplos próximos do cotidiano dos estudantes.",
            "☑ Organização dos dados em entrada e saída para facilitar a compreensão.",
            "☑ Apoio individual para diferenciar grandeza dependente e independente.",
        ],
        "representacao_funcoes": [
            "☑ Comparação guiada entre tabela, expressão e gráfico com um exemplo já resolvido no quadro.",
            "☑ Organização visual das três formas de representação para facilitar a leitura.",
            "☑ Flexibilização do registro, permitindo completar primeiro a tabela antes de avançar para a expressão ou o gráfico.",
        ],
        "dependencia_grandezas": [
            "☑ Leitura coletiva dos enunciados para destacar as duas grandezas envolvidas.",
            "☑ Tabelas curtas e exemplos concretos antes da generalização da regra.",
            "☑ Apoio individual para estudantes com dificuldade na identificação da variável dependente.",
        ],
        "verificacao_funcao": [
            "☑ Atividades em níveis, contemplando retomada e aprofundamento.",
            "☑ Correção coletiva sem exposição individual dos erros.",
            "☑ Flexibilização do registro para alunos com maior dificuldade de escrita ou organização.",
        ],
        "revisao_funcao": [
            "☑ Retomada dos conceitos básicos antes dos exercícios mistos de revisão.",
            "☑ Organização visual no quadro com tabela, expressão e gráfico do mesmo exemplo.",
            "☑ Atividades graduais para contemplar diferentes ritmos da turma multisseriada.",
        ],
        "funcao_logaritmica": [
            "☑ Retomada de potências simples antes da introdução do logaritmo.",
            "☑ Uso de exemplos interpretativos, evitando excesso de formalismo.",
            "☑ Resolução em etapas curtas, com apoio do quadro durante os cálculos.",
        ],
        "algebra_variavel": [
            "☑ Explicacao com exemplos simples no quadro antes das atividades autonomas.",
            "☑ Atividades graduais, com exercicios de retomada para quem ainda consolida a base e propostas de avancar para quem ja demonstra maior dominio.",
            "☑ Correcao coletiva sem exposicao individual, retomando o significado das letras em cada situacao.",
        ],
        "algebra_valor_numerico": [
            "☑ Organizacao do calculo em etapas curtas no quadro para facilitar a substituicao da letra por numeros.",
            "☑ Retomada da ordem das operacoes sempre que necessario durante a pratica.",
            "☑ Apoio individual para estudantes com dificuldade em registrar o passo a passo no caderno.",
        ],
        "equacao_igualdade": [
            "☑ Uso de desenho simples de balanca no quadro para apoiar a compreensao da igualdade.",
            "☑ Resolucao em etapas curtas, mantendo visivel o que foi feito em cada lado da sentenca.",
            "☑ Tempo ampliado para copiar, testar procedimentos e corrigir os registros com apoio.",
        ],
        "equacao_1_grau": [
            "☑ Retomada das operacoes inversas antes da resolucao dos exercicios.",
            "☑ Organizacao da equacao em etapas curtas no quadro, com um exemplo completo como referencia.",
            "☑ Apoio individual para estudantes com dificuldade na montagem da sentenca matematica.",
        ],
        "equacao_duas_incognitas": [
            "☑ Tabela simples desenhada no quadro para apoiar a leitura dos pares de valores.",
            "☑ Malha ou esquema amplo para facilitar a localizacao dos pontos e a visualizacao da reta.",
            "☑ Possibilidade de permanecer primeiro na tabela antes de avancar para o plano cartesiano, conforme o ritmo de cada estudante.",
        ],
        "sistema_equacoes": [
            "☑ Separacao visual das duas equacoes no quadro para evitar mistura de informacoes.",
            "☑ Leitura coletiva do problema, destacando cada condicao antes da resolucao algebrica.",
            "☑ Apoio individual na escolha e na organizacao do metodo de resolucao mais acessivel para o estudante.",
        ],
        "semelhanca_triangulos": [
            "☑ Desenhos grandes e bem espacos no quadro para facilitar a visualizacao dos lados correspondentes.",
            "☑ Marcacoes simples para indicar quais lados devem ser comparados em cada triangulo.",
            "☑ Tempo ampliado para copiar as figuras e concluir os registros de proporcionalidade.",
        ],
        "teorema_pitagoras": [
            "☑ Identificacao visual de catetos e hipotenusa com marcacoes claras no quadro.",
            "☑ Aplicacao da formula em exemplos curtos antes de avancar para problemas mais completos.",
            "☑ Apoio individual para estudantes com dificuldade na organizacao dos quadrados e das etapas do calculo.",
        ],
    }
    return bancos.get(tipo_cdp, [])


def _metodologia_cdp_contextual(
    perfil: str,
    tipo: str,
    tema: str,
    conceito: str,
    indice_aula: int = 0,
    texto_pdf: str = None,
    extracao_pdf: dict = None,
    disciplina_base: str = "",
) -> list[str]:
    conceito_frase = _conceito_cdp_contextual(perfil, tema, conceito)
    tipo_cdp = _tipo_conteudo_cdp(perfil, tema, conceito)
    exemplo = _exemplo_concreto_cdp(tipo_cdp)

    if perfil == "matematica" and tipo_cdp in _tipos_matematica_eja_cdp():
        texto_especifico = _metodologia_matematica_eja_cdp(tipo_cdp, indice_aula)
        if texto_especifico:
            return [_limpar_texto_cdp_contextual(texto_especifico)]

    matematicas = {
        "fracao_conceito": [
            f"O professor inicia a aula apresentando no quadro uma situação simples de {exemplo}. Em seguida, explica a relação entre numerador, denominador e divisão, resolvendo exemplos passo a passo. Os alunos registram no caderno as representações trabalhadas e resolvem exercícios de identificação e escrita de frações, com acompanhamento próximo e correção coletiva.",
            f"A aula começa com a retomada da ideia de parte e todo, usando exemplos de {exemplo}. O professor organiza no quadro os principais registros de {conceito_frase} e orienta a turma na resolução de atividades graduais. Ao final, a correção coletiva destaca a leitura correta das frações e os erros mais frequentes.",
        ],
        "fracao_quantidade": [
            f"O professor propõe no quadro uma situação de {exemplo} e conduz a turma na identificação do total e da parte solicitada. Depois, resolve exemplos de {conceito_frase} mostrando os cálculos por etapas. Os alunos praticam no caderno, conferem os registros com o professor e participam da correção coletiva.",
            f"A aula inicia com um problema simples envolvendo {conceito_frase}. O professor mostra no quadro como dividir a quantidade total e calcular a parte indicada, usando números acessíveis. Em seguida, os alunos resolvem exercícios semelhantes, com apoio individual quando necessário e síntese final no quadro.",
        ],
        "fracao_adicao_subtracao": [
            f"O professor retoma a ideia de fração e apresenta no quadro exemplos de {conceito_frase}, primeiro com denominadores iguais e depois com denominadores diferentes. A turma acompanha a resolução passo a passo, registrando o procedimento no caderno. Os exercícios são corrigidos coletivamente, com atenção aos erros de equivalência e cálculo.",
            f"A aula começa com dois exemplos escritos no quadro: um de soma e outro de subtração de partes. O professor explica quando é necessário igualar denominadores e orienta os alunos na resolução gradual. Durante a prática, verifica os cadernos, retoma dúvidas pontuais e encerra com correção no quadro.",
        ],
        "fracao_mult_div": [
            f"O professor apresenta no quadro o procedimento de {conceito_frase}, usando exemplos curtos e resolvidos por etapas. A turma registra os passos no caderno antes de resolver novas atividades. Durante a prática, o professor acompanha individualmente e finaliza com correção coletiva e síntese dos procedimentos.",
            f"A aula inicia com a retomada de numerador e denominador para preparar a resolução de {conceito_frase}. O professor demonstra os cálculos no quadro, destaca os cuidados com inverso e simplificação quando necessário, e propõe exercícios graduais. A correção final organiza os passos principais para consulta.",
        ],
        "fracao_comparacao": [
            f"Para introduzir a aula, o professor escreve no quadro duas frações e pergunta qual representa maior quantidade. A partir das respostas, apresenta procedimentos de {conceito_frase}, usando equivalência e comparação por etapas. Os alunos resolvem exercícios no caderno e a correção coletiva retoma os critérios usados.",
            f"O professor inicia com representações simples de partes do todo e conduz a comparação entre elas. Depois, explica no quadro como simplificar ou ordenar frações sem depender apenas da observação visual. A turma realiza atividades graduais, com verificação dos registros e fechamento coletivo.",
        ],
        "forma_mista": [
            f"O professor escreve no quadro uma fração imprópria e questiona a turma sobre o que ela representa. Em seguida, explica a conversão entre fração imprópria e número misto com exemplos resolvidos. Os alunos registram o procedimento, resolvem atividades de conversão e acompanham a correção coletiva.",
        ],
        "combinatoria": [
            f"A aula inicia com uma situação de {exemplo}. O professor organiza as escolhas no quadro, mostrando como contar possibilidades sem repetir ou esquecer casos. Os alunos resolvem atividades de contagem no caderno, comparando estratégias simples, e a correção coletiva registra o procedimento mais organizado.",
            f"O professor apresenta no quadro um problema de escolhas sucessivas e conduz a turma na separação das etapas. Depois, demonstra como multiplicar as possibilidades para chegar ao total. Os alunos praticam com exemplos semelhantes e finalizam com uma síntese do raciocínio de contagem.",
        ],
        "equacao": [
            f"A aula começa com uma situação em que é preciso descobrir um valor desconhecido. O professor representa a situação no quadro, explica a montagem da equação e resolve o exemplo passo a passo. Os alunos resolvem exercícios no caderno, com acompanhamento durante as tentativas e correção coletiva ao final.",
        ],
        "porcentagem": [
            f"O professor inicia com exemplos de {exemplo}, relacionando porcentagem à ideia de parte de um total. Em seguida, apresenta cálculos simples no quadro e orienta a resolução de atividades no caderno. A correção coletiva reforça a leitura de porcentagens e a organização dos cálculos.",
        ],
        "geometria_angulos": [
            f"A aula começa com a observação de {exemplo}. O professor desenha no quadro diferentes aberturas e giros, nomeando os tipos de ângulo com linguagem direta. Os alunos registram os exemplos, classificam novas figuras no caderno e participam da correção coletiva.",
            f"O professor apresenta no quadro desenhos simples de ângulos e conduz a turma na comparação entre suas aberturas. Depois, explica os critérios de classificação e propõe exercícios de identificação. Durante a atividade, acompanha os registros e retoma as dúvidas antes do fechamento.",
        ],
        "geometria_poligonos": [
            f"O professor inicia desenhando figuras no quadro e perguntando o que muda entre elas. Em seguida, apresenta {conceito_frase}, destacando lados, vértices e formas mais comuns. Os alunos classificam figuras no caderno, justificam suas respostas oralmente e acompanham a correção coletiva.",
        ],
        "geometria_medidas": [
            f"A aula começa com uma situação de {exemplo}. O professor mostra no quadro como identificar as medidas necessárias e organizar o cálculo. Os alunos resolvem atividades no caderno, registrando unidades e procedimentos, com fechamento coletivo dos principais cuidados.",
        ],
        "matematica_geral": [
            f"O professor inicia com um problema simples envolvendo {conceito_frase}, escrito no quadro. A turma identifica os dados e o que precisa ser resolvido antes da explicação. Em seguida, os alunos realizam exercícios no caderno, com acompanhamento do professor, retomada das dúvidas e correção coletiva.",
        ],
    }

    portugues = {
        "lp_artigo_opiniao": [
            f"O professor retoma brevemente o conceito de artigo de opinião, registrando no quadro a diferença entre fato e opinião. Em seguida, apresenta o tema do texto e realiza a leitura em voz alta, pausando para explicar vocabulário e trechos mais densos. Na lousa, organiza o esquema do artigo: tese, argumentos e conclusão. Os alunos respondem no caderno às atividades de identificação, e a correção coletiva retoma os trechos que comprovam cada resposta.",
            f"O professor escreve no quadro uma pergunta objetiva: como distinguir uma informação verificável de um ponto de vista? A partir das respostas, apresenta {conceito_frase} e lê o artigo em voz alta, orientando os alunos a localizar tese, argumentos e conclusão. Depois, os alunos classificam trechos como fato ou opinião no caderno, com acompanhamento individual e correção coletiva na lousa.",
            f"A aula começa com a retomada do conteúdo anterior sobre textos de opinião. O professor apresenta o foco da aula: reconhecer tese, argumentos, fatos, opiniões e conectivos que organizam o texto. Realiza a leitura orientada do artigo, registra exemplos no quadro e propõe atividade individual no caderno. O fechamento retoma os critérios usados para justificar as respostas com base no texto.",
        ],
        "lp_relacoes_logico_discursivas": [
            f"O professor escreve na lousa duas frases com conectivos diferentes e pergunta oralmente que mudança de sentido ocorre entre elas. Em seguida, apresenta {conceito_frase}, organizando no quadro uma tabela simples com relações de adição, oposição, causa, finalidade, concessão e conclusão. Os alunos copiam os exemplos no caderno e associam trechos do texto às relações correspondentes, com correção coletiva ao final.",
            f"O professor retoma o artigo lido e destaca no quadro conectivos presentes no texto. Explica como cada conectivo ajuda a organizar o argumento, diferenciando causa, oposição, concessão e conclusão. Os alunos realizam atividade de associação no caderno e, durante a correção coletiva, o professor esclarece os casos de maior dúvida, especialmente adversativa e concessiva.",
            f"A aula inicia com exemplos curtos escritos no quadro para mostrar como uma palavra de ligação muda o sentido da frase. O professor apresenta os principais conectivos e suas funções no texto argumentativo. Em seguida, os alunos identificam relações lógico-discursivas em trechos do artigo, registram no caderno e revisam as respostas na correção coletiva.",
        ],
        "leitura_interpretacao": [
            f"O professor escreve no quadro o título do texto e o conceito central da aula: {conceito_frase}. Em seguida, realiza a leitura em voz alta, pausando para explicar palavras que possam dificultar a compreensão. Os alunos respondem às questões no caderno, com orientação para localizar trechos que justifiquem as respostas, e a correção coletiva é feita no quadro.",
            f"O professor apresenta o texto impresso e lê em voz alta os trechos principais, verificando oralmente a compreensão da turma. Depois, orienta os alunos a responderem individualmente no caderno, retomando título, assunto e informações centrais. Ao final, corrige no quadro as questões, destacando as passagens do texto que fundamentam cada resposta.",
            f"O professor inicia escrevendo no quadro uma pergunta simples ligada ao tema do texto. Após breve troca oral, lê o texto em voz alta e orienta os alunos a acompanharem a leitura no material. Em seguida, propõe atividade de interpretação no caderno e realiza correção coletiva, diferenciando opinião pessoal de informação presente no texto.",
        ],
        "genero_textual": [
            f"O professor apresenta no quadro as características do gênero estudado, relacionando-as a {conceito_frase}. Explica cada uma com exemplos retirados do texto lido. Em seguida, propõe atividade no caderno para que os alunos identifiquem essas características no material. A correção coletiva retoma os trechos que comprovam cada resposta e registra a síntese no quadro.",
            f"O professor inicia perguntando oralmente o que os alunos reconhecem em textos do cotidiano. Registra as respostas no quadro e apresenta {conceito_frase}, destacando finalidade, linguagem e características do gênero. Depois, os alunos realizam atividade de identificação no caderno, com acompanhamento individual e correção coletiva.",
            f"O professor escreve no quadro dois pequenos trechos para comparação e orienta os alunos a observarem diferenças de linguagem e finalidade. A partir dessas observações, explica {conceito_frase} com exemplos do material. Os alunos registram as características no caderno e corrigem coletivamente as atividades propostas.",
        ],
        "analise_linguistica": [
            f"O professor retoma o texto da aula e escreve no quadro exemplos que mostram o conceito de {conceito_frase}. Explica a diferença de sentido entre as formas analisadas, usando linguagem simples e exemplos do próprio material. Em seguida, propõe atividade no caderno para identificar e reescrever trechos, com acompanhamento individual e correção coletiva no quadro.",
            f"O professor escreve no quadro duas frases do texto e pergunta oralmente o que muda no sentido entre elas. Registra as respostas e apresenta o conceito de {conceito_frase} de forma gradual, relacionando regra e uso no texto. Os alunos resolvem exercícios de identificação e transformação no caderno; ao final, a correção coletiva retoma os erros mais frequentes.",
            f"O professor relê em voz alta um trecho do texto e destaca no quadro as palavras ou formas linguísticas que serão analisadas. Explica o conceito de {conceito_frase} a partir desses exemplos e solicita atividade escrita no caderno. Durante a resolução, acompanha os alunos com maior dificuldade e encerra com síntese no quadro.",
        ],
        "vocabulario_inferencia": [
            f"O professor escreve no quadro as palavras retiradas do texto e lê em voz alta os trechos em que elas aparecem. Antes de explicar, solicita que os alunos tentem inferir o significado pelo contexto. Registra hipóteses no quadro, apresenta os significados com exemplos concretos e propõe atividade no caderno usando as palavras estudadas.",
            f"O professor inicia relendo os trechos que apresentam vocabulário novo ou expressões importantes. Pausa em cada palavra para orientar a inferência pelo contexto e, depois, explica o sentido com linguagem direta. Os alunos registram os significados no caderno e produzem frases simples, com correção coletiva ao final.",
        ],
        "producao_textual": [
            f"O professor apresenta no quadro a proposta de produção textual e retoma as características do gênero que servirá de modelo. Orienta os alunos a planejarem o texto no caderno, definindo tema, organização das ideias e objetivo da escrita. Durante a produção, acompanha individualmente e encerra com orientações de revisão e reescrita.",
            f"O professor analisa com a turma um modelo curto escrito no quadro ou no material impresso, destacando estrutura, linguagem e finalidade. Depois, orienta a escrita individual no caderno, com roteiro simples para início, desenvolvimento e fechamento. Ao final, retoma critérios de revisão sem expor publicamente os erros dos alunos.",
        ],
        "argumentacao": [
            f"O professor escreve no quadro uma pergunta relacionada a {conceito_frase}. Em seguida, orienta os alunos a diferenciar opinião, justificativa e exemplo, registrando um modelo curto. Os alunos produzem respostas no caderno e a correção coletiva verifica se as ideias estão claras e sustentadas por argumentos.",
        ],
        "retomada_lp": [
            f"O professor inicia retomando no quadro os pontos principais da aula anterior. Relê em voz alta o trecho mais importante do texto já trabalhado e conecta esse material ao novo foco da aula: {conceito_frase}. Depois, propõe atividade no caderno, acompanha individualmente e encerra com correção coletiva e síntese dos conteúdos conectados.",
            f"O professor escreve no quadro uma frase direta: na aula anterior estudamos um ponto do texto; hoje vamos aprofundar {conceito_frase}. Retoma dois exemplos já vistos, apresenta o novo conteúdo com apoio no texto e orienta atividade no caderno. A correção coletiva registra no quadro o que foi retomado e o que avançou.",
        ],
    }

    historicas = {
        "historia_poder_politico": [
            f"O professor registra no quadro uma pergunta direta sobre {conceito_frase}: quem governava, como esse poder era mantido e quais grupos o apoiavam. Em seguida, apresenta o contexto histórico em etapas, usando linguagem simples e explicando os termos novos antes de avançar. Os alunos registram no caderno um esquema com os elementos centrais e respondem a uma questão escrita; a correção coletiva retoma os pontos principais na lousa.",
            f"A aula começa com uma linha do tempo simples no quadro para situar o período estudado. O professor explica a organização do poder, destacando governantes, grupos sociais e formas de controle. Depois, os alunos completam um esquema no caderno e a correção coletiva compara as respostas, esclarecendo dúvidas sobre os conceitos históricos.",
            f"O professor apresenta no quadro os grupos envolvidos no governo estudado e explica a função de cada um. Em seguida, contextualiza {conceito_frase}, mostrando causas, interesses e consequências políticas. Os alunos respondem a duas perguntas objetivas no caderno, com acompanhamento individual e correção coletiva ao final.",
        ],
        "historia_conflito": [
            f"O professor apresenta no quadro os lados envolvidos no conflito, indicando quem eram, o que queriam e por que entraram em disputa. Explica as causas em sequência, usando setas para ligar acontecimentos e consequências. Os alunos registram um esquema de causas e resultados no caderno; depois, a correção coletiva retoma os grupos envolvidos e o impacto histórico.",
            f"A aula começa com a descrição oral de uma cena do conflito, usando linguagem simples e direta. Em seguida, o professor organiza na lousa o contexto, os interesses em jogo e as principais consequências. Os alunos respondem a uma questão de interpretação no caderno e a correção no quadro destaca os pontos centrais.",
            f"O professor registra no quadro os principais grupos do conflito e seus objetivos. Desenvolve o conteúdo em etapas numeradas, explicando início, desenvolvimento e resultado. Os alunos completam uma tabela simples no caderno e o professor verifica os registros antes da correção coletiva.",
        ],
        "historia_independencia_revolucao": [
            f"O professor inicia registrando no quadro quem estava insatisfeito, por qual motivo e o que desejava mudar. Explica o processo histórico em etapas, destacando grupos sociais, lideranças, ideias e consequências. Os alunos registram a sequência no caderno e respondem a uma questão de análise; a correção coletiva retoma causas e resultados.",
            f"A aula começa com a leitura em voz alta de um trecho curto ligado a {conceito_frase}. O professor explica o contexto e traduz termos desconhecidos antes de apresentar na lousa os elementos centrais do movimento. Os alunos respondem no caderno e a correção coletiva destaca a relação entre ideias, ações e mudanças políticas.",
            f"O professor apresenta no quadro os grupos sociais envolvidos e seus interesses. Em seguida, explica como o movimento se desenvolveu, marcando momentos de tensão e resultados. Os alunos elaboram um resumo guiado no caderno, com acompanhamento individual e correção coletiva ao final.",
        ],
        "historia_sociedade_desigualdade": [
            f"O professor inicia desenhando no quadro uma pirâmide social simples com os grupos da sociedade estudada. Explica quem estava em cada posição, quais eram seus direitos, obrigações e limitações. Os alunos registram a estrutura social no caderno e respondem a uma questão de análise; a correção coletiva destaca as desigualdades e suas causas.",
            f"A aula começa com a descrição histórica do dia a dia de pessoas de diferentes grupos sociais, sem pedir relatos pessoais dos alunos. Em seguida, o professor organiza no quadro a hierarquia social e explica como ela influenciava os acontecimentos do período. Os alunos completam um esquema no caderno e a correção coletiva retoma as diferenças entre os grupos.",
            f"O professor registra na lousa os principais grupos sociais e suas características. Explica como essa organização produzia desigualdades e influenciava conflitos ou mudanças históricas. Os alunos respondem a perguntas objetivas no caderno, com apoio individual e síntese coletiva no quadro.",
        ],
        "historia_ideias": [
            f"O professor apresenta no quadro as ideias centrais do período estudado e explica cada uma com linguagem direta. Em seguida, conecta essas ideias aos acontecimentos históricos, mostrando quem as defendia e quais mudanças buscava. Os alunos registram uma lista comentada no caderno e respondem a uma questão de verificação, corrigida coletivamente.",
            f"A aula começa com uma frase histórica ou ideia central escrita no quadro. O professor explica seu significado na época, quem a defendia e quem se opunha a ela. Depois, relaciona essas ideias aos eventos estudados. Os alunos completam um esquema no caderno e a correção coletiva retoma os conceitos.",
            f"O professor registra no quadro ideias, defensores e consequências. Explica como essas ideias circularam e foram usadas para justificar ações políticas. Os alunos respondem a uma questão escrita, e o fechamento organiza no quadro a relação entre pensamento e mudança histórica.",
        ],
        "historia_fonte": [
            f"O professor apresenta um trecho curto de fonte histórica na lousa ou no material impresso. Lê o trecho em voz alta, pausando para explicar termos e situar o contexto. Em seguida, propõe perguntas de análise: quem produziu, quando, para quem e com qual objetivo. Os alunos respondem no caderno e a correção coletiva destaca as evidências presentes no texto.",
            f"A aula começa com a explicação simples do que é uma fonte histórica. O professor lê o documento em voz alta e registra no quadro o contexto de produção. Depois, orienta perguntas progressivas, começando pelo que o texto diz e avançando para o que o autor queria defender. A correção coletiva retoma a ideia principal da fonte.",
            f"O professor apresenta a origem e a importância da fonte antes da leitura. Lê o trecho pausadamente e explica cada parte relevante. Os alunos respondem no caderno a uma questão de síntese sobre a ideia principal do documento, e o professor corrige coletivamente retomando contexto, autor e objetivo.",
        ],
        "historia_geral": [
            f"O professor situa o tema no tempo e no espaço, registrando no quadro os acontecimentos principais. Em seguida, explica {conceito_frase} com linguagem direta, destacando causas, sujeitos históricos e consequências. Os alunos registram um esquema no caderno e respondem a uma questão de verificação, com correção coletiva no quadro.",
        ],
    }

    ciencias = {
        "ciencias_alimentacao": [
            "O professor retoma na lousa os grupos alimentares, como cereais, proteínas, frutas, verduras, legumes e laticínios, usando exemplos acessíveis como arroz, feijão, ovo, leite e frutas comuns. Em seguida, explica o que caracteriza uma alimentação balanceada e registra no quadro os critérios de variedade, equilíbrio e presença de alimentos in natura ou minimamente processados. Os alunos recebem ou copiam uma tabela de cardápio e preenchem as refeições com base na lista apresentada, com acompanhamento individual e correção coletiva dos principais ajustes.",
            "A aula começa com uma lista de alimentos escrita no quadro, organizada entre alimentos in natura, minimamente processados, processados e ultraprocessados. O professor explica cada categoria com linguagem simples e mostra como essa classificação ajuda a montar refeições mais equilibradas. Depois, os alunos classificam os alimentos no caderno e indicam quais escolhas fortalecem um cardápio saudável; a correção coletiva retoma os critérios usados, sem exigir relatos pessoais sobre alimentação.",
            "O professor apresenta no quadro um cardápio com desequilíbrios propositais, como ausência de frutas e verduras, repetição excessiva de alimentos ou presença frequente de ultraprocessados. A turma analisa os problemas com mediação do professor e registra no caderno sugestões de melhoria. Em seguida, os alunos reorganizam uma refeição ou um dia de cardápio, considerando grupos alimentares, variedade e função dos nutrientes no organismo.",
        ],
        "ciencias_digestao": [
            "O professor inicia registrando na lousa o caminho percorrido pelo alimento no corpo, destacando boca, esôfago, estômago e intestinos. Em seguida, explica o processo de digestão em etapas, relacionando transformação dos alimentos, absorção de nutrientes e saúde do organismo. Os alunos copiam um esquema simples, completam informações no caderno e participam da correção coletiva dos pontos principais.",
            "A aula começa com uma pergunta objetiva no quadro: o que acontece com o alimento depois da mastigação? A partir das respostas, o professor organiza uma sequência do sistema digestório e explica cada etapa com exemplos simples. Os alunos completam um quadro com órgão, função e transformação realizada, com acompanhamento individual e fechamento coletivo.",
        ],
        "ciencias_nervoso_endocrino": [
            "O professor apresenta na lousa a relação entre sistema nervoso, sistema endócrino e mudanças do desenvolvimento humano. Explica, em etapas, como cérebro, glândulas e hormônios participam de respostas do corpo e de transformações fisiológicas. Os alunos registram um esquema com palavras-chave e respondem a questões objetivas, com correção coletiva e retomada dos termos mais difíceis.",
            "A aula inicia com exemplos neutros de respostas do corpo, como crescimento, sono, fome, emoções e mudanças corporais. O professor relaciona esses exemplos aos sistemas nervoso e endócrino, diferenciando comando nervoso e ação hormonal. Os alunos completam uma tabela simples no caderno e o fechamento retoma a função de cada sistema.",
        ],
        "ciencias_genetica": [
            "O professor introduz o tema registrando na lousa palavras-chave como célula, gene, DNA, cromossomo e hereditariedade. Em seguida, explica como características podem ser transmitidas entre gerações, usando exemplos neutros e sem exposição pessoal. Os alunos copiam um esquema organizado, respondem a questões de identificação e participam da correção coletiva.",
            "A aula começa com um esquema simples no quadro sobre célula e material genético. O professor explica a função dos genes e dos cromossomos, relacionando-os à hereditariedade. Depois, os alunos completam frases e classificam conceitos no caderno, com apoio individual e síntese final na lousa.",
        ],
        "ciencias_ecologia": [
            "O professor registra no quadro seres vivos, ambiente e relações ecológicas, explicando como energia, alimentação e equilíbrio aparecem nos ecossistemas. Em seguida, apresenta exemplos simples de cadeia alimentar ou interação entre organismos. Os alunos organizam um esquema no caderno e respondem a uma questão de análise, com correção coletiva dos conceitos centrais.",
            "A aula inicia com a observação orientada de uma situação ambiental descrita pelo professor no quadro. A partir dela, são identificados seres vivos, recursos do ambiente e relações de dependência. Os alunos completam uma tabela simples, registram conclusões e revisam coletivamente as relações entre causa, consequência e equilíbrio ambiental.",
        ],
        "ciencias_geral": [
            f"O professor introduz {conceito_frase} por meio de uma situação concreta descrita na lousa. Em seguida, organiza as ideias principais em esquema, diferenciando observação, explicação e consequência. Os alunos registram no caderno os conceitos essenciais, resolvem atividades orientadas e participam da correção coletiva com retomada dos pontos de maior dificuldade.",
        ],
    }

    geografia = {
        "geografia_cartografia_tematica": [
            "O professor apresenta na lousa ou em material impresso um mapa temático do Brasil e solicita que os alunos observem título, cores, legenda e distribuição do fenômeno representado. Em seguida, escreve no quadro a diferença entre mapa qualitativo, que mostra categorias, e mapa quantitativo, que mostra valores numéricos. Os alunos registram um esquema comparativo no caderno, respondem a uma questão objetiva sobre legenda e representação cartográfica, e a correção coletiva retoma os elementos essenciais do mapa.",
            "A aula começa com uma situação concreta: representar, em um mapa, quais estados ou regiões apresentam maior acesso a determinado serviço básico. O professor registra no quadro as respostas iniciais e explica que a cartografia temática serve para representar fenômenos específicos do espaço geográfico. Depois, compara exemplos de mapas qualitativos e quantitativos na lousa, orienta atividades de identificação no caderno e acompanha individualmente os alunos com maior dificuldade de leitura cartográfica.",
            "O professor desenha na lousa um esboço simples de mapa com uma legenda de cores e pergunta oralmente o que aquela legenda indica. A partir das respostas, explica os valores de percepção cartográfica, como gradação de cor, símbolo proporcional e destaque de categorias. Os alunos registram os exemplos no caderno, classificam situações como qualitativas ou quantitativas e corrigem coletivamente as respostas no quadro.",
        ],
        "geografia_fenomenos": [
            f"O professor apresenta no quadro um fenômeno geográfico relacionado a {conceito_frase} e orienta a turma a observar onde ele ocorre com maior ou menor intensidade. Em seguida, explica os fatores que influenciam essa distribuição espacial, como condições naturais, infraestrutura, população ou organização econômica. Os alunos registram um esquema no caderno, respondem a perguntas de interpretação e participam da correção coletiva.",
            "A aula inicia com a descrição oral de um fenômeno geográfico brasileiro, como urbanização, vegetação, clima, acesso a serviços ou desigualdades regionais. O professor organiza no quadro causas, áreas de ocorrência e consequências. Depois, os alunos analisam um mapa, tabela ou texto curto em material impresso, registram conclusões no caderno e revisam coletivamente os pontos centrais.",
        ],
        "geografia_dados_espaciais": [
            "O professor apresenta no quadro ou em material impresso dados espaciais organizados em mapa, tabela ou gráfico. Explica como comparar valores entre regiões, identificar concentração e interpretar diferenças numéricas. Os alunos respondem a questões no caderno, justificando as respostas com base nos dados apresentados, e a correção coletiva retoma os procedimentos de leitura.",
            "A aula começa com dois dados simples sobre regiões brasileiras, registrados no quadro. O professor orienta a leitura dos valores, mostra como transformar números em interpretação geográfica e relaciona os dados ao território. Os alunos completam uma tabela de análise no caderno, com apoio individual e síntese final no quadro.",
        ],
        "geografia_producao_cartografica": [
            "O professor apresenta na lousa os elementos essenciais de um mapa temático: título, legenda, simbologia, orientação e escala quando necessário. Em seguida, demonstra como construir uma representação simples a partir de um mapa-base, escolhendo um fenômeno e definindo cores ou símbolos. Os alunos produzem no caderno ou em material impresso um mapa com título e legenda, enquanto o professor acompanha individualmente e orienta correções.",
            "A aula inicia com a análise de um mapa temático simples, destacando como título e legenda orientam a leitura. Depois, o professor propõe que os alunos representem um fenômeno geográfico em mapa-base impresso ou copiado da lousa. A atividade prioriza clareza da legenda, coerência dos símbolos e relação entre o fenômeno escolhido e o território representado.",
        ],
        "geografia_geral": [
            f"O professor introduz {conceito_frase} por meio de um mapa, desenho na lousa ou descrição de uma situação geográfica concreta. Em seguida, organiza no quadro os conceitos centrais e orienta os alunos na leitura das informações espaciais. A turma registra as ideias no caderno, responde a atividades objetivas e participa da correção coletiva.",
        ],
    }

    gerais = {
        "analise_geografica": f"O professor inicia com uma situação concreta ligada a {conceito_frase}, registrando no quadro palavras-chave do tema. Em seguida, apresenta exemplos simples e orienta a leitura de informações, imagens ou mapas impressos quando houver. Os alunos respondem às atividades no caderno, com retomada das dúvidas e correção coletiva.",
        "analise_historica": f"A aula começa com a retomada de uma questão central sobre {conceito_frase}. O professor apresenta o conteúdo no quadro, relacionando fatos, tempo e mudanças sociais com linguagem direta. Os alunos realizam registros e respondem às atividades, com correção coletiva dos pontos principais.",
        "investigacao_ciencias": f"O professor introduz {conceito_frase} por meio de observações simples e perguntas sobre situações do cotidiano. Depois, organiza no quadro as explicações principais e orienta os alunos na resolução das atividades. A aula encerra com retomada das respostas e síntese coletiva.",
        "geral_cdp": f"A aula inicia com uma conversa breve para levantar o que os alunos já sabem sobre {conceito_frase}. Em seguida, o professor explica o conteúdo no quadro, usando exemplos simples e linguagem direta. Os alunos realizam atividades no caderno, com acompanhamento individual quando necessário e correção coletiva ao final.",
    }

    if perfil == "matematica":
        opcoes = matematicas.get(tipo_cdp, matematicas["matematica_geral"])
    elif perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        opcoes = portugues.get(tipo_cdp, portugues["leitura_interpretacao"])
    elif perfil == "historia":
        opcoes = historicas.get(tipo_cdp, historicas["historia_geral"])
    elif perfil in {"ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        opcoes = ciencias.get(tipo_cdp, ciencias["ciencias_geral"])
    elif perfil == "geografia":
        opcoes = geografia.get(tipo_cdp, geografia["geografia_geral"])
    elif perfil == "sociologia":
        opcoes = [
            f"A aula inicia com uma conversa breve para levantar o que os alunos já sabem sobre {conceito_frase}, introduzindo um conceito sociológico relevante para o tema. Em seguida, o professor explica o conteúdo no quadro, destacando as relações sociais e desigualdades associadas. Os alunos realizam atividades de reflexão e análise no caderno, com acompanhamento individual do professor e síntese final coletiva."
        ]
    elif perfil == "lideranca_oratoria":
        opcoes = [
            f"O professor inicia a aula convidando os alunos a refletirem sobre a persuasão ética e a responsabilidade discursiva na comunicação. Em seguida, explica conceitos de análise de discurso, mostrando como as escolhas de linguagem constroem argumentos no debate público. Os alunos realizam exercícios práticos no caderno sobre {conceito_frase}, com mediação do professor e fechamento coletivo."
        ]
    else:
        opcoes = [gerais.get(tipo_cdp, gerais["geral_cdp"])]

    texto = opcoes[indice_aula % len(opcoes)]
    texto = _expandir_metodologia_cdp_contextual(
        perfil=perfil,
        tipo_cdp=tipo_cdp,
        conceito_frase=conceito_frase,
        exemplo=exemplo,
        texto=texto,
    )
    
    tecnicas = []
    if texto_pdf:
        tecnicas = _detectar_tecnicas_lemov(texto_pdf, tema)
    elif extracao_pdf and extracao_pdf.get("texto_prioritario"):
        tecnicas = _detectar_tecnicas_lemov(extracao_pdf["texto_prioritario"], tema)

    if tecnicas:
        metodologia_temp = [{"titulo": "Abertura", "texto": texto}]
        metodologia_temp = _garantir_tecnicas_lemov_na_metodologia(metodologia_temp, tecnicas)
        texto = metodologia_temp[0]["texto"]

    return [_limpar_texto_cdp_contextual(texto)]


def _expandir_metodologia_cdp_contextual(
    perfil: str,
    tipo_cdp: str,
    conceito_frase: str,
    exemplo: str,
    texto: str,
) -> str:
    base = str(texto or "").strip()
    if not base:
        return base

    if perfil == "matematica":
        complementos = {
            "fracao_adicao_subtracao": (
                " Em seguida, introduz situacoes com denominadores diferentes, explicando a necessidade "
                "de encontrar fracoes equivalentes antes de realizar as operacoes e organizando os "
                "calculos em etapas visiveis no quadro. Ao final, os alunos registram os procedimentos "
                "no caderno e acompanham a correcao coletiva, com destaque para os erros mais comuns "
                "ligados a equivalencia, simplificacao e organizacao do calculo."
            ),
            "fracao_comparacao": (
                " Depois, o professor registra no quadro os criterios usados para comparar as fracoes, "
                "mostrando como observar equivalencia, ordenacao e relacao entre numerador e denominador. "
                "Os alunos anotam os exemplos no caderno e acompanham a correcao coletiva, retomando os "
                "procedimentos que ajudam a justificar qual fracao representa maior ou menor quantidade."
            ),
            "fracao_mult_div": (
                " Em seguida, organiza no quadro cada etapa do procedimento, reforcando quando simplificar, "
                "como identificar o inverso e quais cuidados evitam trocas indevidas nas operacoes. "
                "Os alunos registram os passos no caderno, resolvem novas atividades e acompanham a "
                "correcao coletiva com retomada dos erros mais frequentes."
            ),
            "fracao_conceito": (
                " Depois, retoma no quadro a relacao entre representacao, leitura e escrita das fracoes, "
                "explorando novos exemplos simples para consolidar a ideia de parte e todo. "
                "Os alunos registram os esquemas no caderno e acompanham a correcao coletiva das "
                "atividades, com revisao dos erros mais recorrentes."
            ),
            "fracao_quantidade": (
                " Em seguida, mostra como organizar os dados do problema no quadro, identificando total, "
                "parte pedida e operacao necessaria para chegar ao resultado. Os alunos registram os "
                "procedimentos no caderno e acompanham a correcao coletiva, com retomada das estrategias "
                "que ajudam a interpretar cada situacao."
            ),
            "forma_mista": (
                " Depois, registra no quadro novas situacoes de conversao para que a turma observe o que "
                "permanece e o que muda entre fracao impropria e numero misto. Os alunos anotam os passos "
                "no caderno e acompanham a correcao coletiva, retomando a leitura correta e a organizacao "
                "dos calculos."
            ),
            "geometria_angulos": (
                " Em seguida, organiza no quadro exemplos com diferentes aberturas e reforca a relacao "
                "entre giro, inclinacao e classificacao. Os alunos registram os criterios no caderno e "
                "acompanham a correcao coletiva, retomando as duvidas sobre identificacao e nomeacao "
                "dos angulos."
            ),
            "geometria_poligonos": (
                " Depois, retoma no quadro os criterios de classificacao, destacando numero de lados, "
                "vertices e diferencas entre figuras semelhantes. Os alunos organizam os registros no "
                "caderno e acompanham a correcao coletiva, com revisao das justificativas apresentadas."
            ),
            "matematica_geral": (
                " Em seguida, organiza no quadro os dados do problema e os passos de resolucao, "
                "destacando o raciocinio necessario em cada etapa. Os alunos registram os procedimentos "
                "no caderno e acompanham a correcao coletiva, retomando as duvidas e os erros mais comuns."
            ),
        }
        extra = complementos.get(tipo_cdp)
        if extra and _normalizar(extra.strip()) not in _normalizar(base):
            return f"{base}{extra}"

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        if "correcao coletiva" not in _normalizar(base):
            return (
                f"{base} Ao final, os alunos registram as respostas no caderno e acompanham a correcao "
                "coletiva, com retomada dos trechos do texto e esclarecimento das duvidas mais frequentes."
            )

    if perfil in {"historia", "geografia", "ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        if "correcao coletiva" not in _normalizar(base) and "fechamento coletivo" not in _normalizar(base):
            return (
                f"{base} Ao final, os alunos registram as ideias principais no caderno e acompanham um "
                "fechamento coletivo, com retomada dos conceitos centrais e esclarecimento das duvidas "
                "mais recorrentes."
            )

    return base


def _selecionar_itens_cdp(opcoes: list[str], partes: list[str], quantidade: int = 3) -> list[str]:
    if not opcoes:
        return []
    inicio = _indice_variacao(partes, len(opcoes))
    selecionados = []
    for deslocamento in range(len(opcoes)):
        item = opcoes[(inicio + deslocamento) % len(opcoes)]
        if item not in selecionados:
            selecionados.append(item)
        if len(selecionados) >= quantidade:
            break
    return selecionados


def _acompanhamento_cdp_contextual(perfil: str, tema: str, conceito: str = "", indice_aula: int = 0) -> list[str]:
    conceito_frase = _conceito_cdp_contextual(perfil, tema, conceito)
    tipo_cdp = _tipo_conteudo_cdp(perfil, tema, conceito)
    if perfil == "matematica" and tipo_cdp in _tipos_matematica_eja_cdp():
        itens = _acompanhamento_matematica_eja_cdp(tipo_cdp)
        if itens:
            return itens[:3]
    bancos = {
        "fracao_conceito": [
            "☑ Verificar se o aluno identifica numerador, denominador e a ideia de parte do todo.",
            "☑ Observar se representa frações por desenhos, registros numéricos ou exemplos simples.",
            "☑ Acompanhar a leitura correta das frações durante a correção coletiva.",
            "☑ Identificar dúvidas na relação entre fração e divisão.",
        ],
        "fracao_quantidade": [
            "☑ Verificar se o aluno reconhece o total e a parte solicitada no problema.",
            "☑ Observar se organiza a divisão da quantidade antes de calcular o resultado.",
            "☑ Acompanhar os registros para identificar erros de procedimento.",
            "☑ Retomar individualmente os casos em que o aluno confunde parte e todo.",
        ],
        "fracao_adicao_subtracao": [
            "☑ Identificar se o aluno reconhece quando os denominadores precisam ser igualados.",
            "☑ Observar se realiza corretamente os cálculos de soma e subtração de frações.",
            "☑ Verificar se registra as etapas intermediárias, não apenas o resultado final.",
            "☑ Acompanhar a correção dos erros de equivalência e simplificação.",
        ],
        "fracao_mult_div": [
            "☑ Verificar se o aluno aplica corretamente o procedimento de multiplicação ou divisão de frações.",
            "☑ Observar se identifica quando deve usar o inverso na divisão.",
            "☑ Acompanhar os registros de cálculo e a organização das etapas.",
            "☑ Retomar dúvidas sobre simplificação durante a prática.",
        ],
        "fracao_comparacao": [
            "☑ Identificar se o aluno compara frações usando equivalência, desenho ou cálculo.",
            "☑ Observar se justifica qual fração representa maior ou menor quantidade.",
            "☑ Verificar se ordena as frações mantendo coerência nos registros.",
            "☑ Acompanhar dúvidas sobre simplificação e comparação cruzada.",
        ],
        "forma_mista": [
            "☑ Verificar se o aluno converte fração imprópria em número misto e faz o caminho inverso.",
            "☑ Observar se compreende a parte inteira e a parte fracionária do registro.",
            "☑ Acompanhar os cálculos de divisão usados na conversão.",
        ],
        "combinatoria": [
            "☑ Verificar se o aluno separa corretamente as etapas de escolha.",
            "☑ Observar se conta possibilidades sem repetir ou omitir casos.",
            "☑ Acompanhar o uso de listas, esquemas ou multiplicação para organizar a contagem.",
            "☑ Identificar se consegue explicar oralmente a estratégia usada.",
        ],
        "equacao": [
            "☑ Identificar se o aluno reconhece a incógnita na situação proposta.",
            "☑ Observar se organiza os dados antes de montar a equação.",
            "☑ Verificar se aplica operações inversas de forma adequada.",
            "☑ Acompanhar a justificativa do resultado encontrado.",
        ],
        "geometria_angulos": [
            "☑ Verificar se o aluno diferencia os tipos de ângulo apresentados.",
            "☑ Observar se relaciona giros e aberturas aos desenhos feitos no quadro.",
            "☑ Acompanhar a classificação das figuras durante a atividade.",
            "☑ Retomar os critérios quando houver confusão entre ângulo reto, agudo e obtuso.",
        ],
        "geometria_poligonos": [
            "☑ Identificar se o aluno reconhece lados e vértices nas figuras.",
            "☑ Observar se classifica polígonos a partir de suas características.",
            "☑ Verificar se registra justificativas simples para cada classificação.",
            "☑ Acompanhar dúvidas na diferenciação entre figuras semelhantes.",
        ],
        "leitura_interpretacao": [
            "☑ Identificar se o aluno localiza informações explícitas no texto.",
            "☑ Observar se consegue explicar oralmente a ideia principal.",
            "☑ Verificar se as respostas escritas mantêm relação com o texto lido.",
            "☑ Acompanhar dificuldades de vocabulário e retomá-las durante a correção.",
        ],
        "lp_artigo_opiniao": [
            "☑ Verificar se o aluno identifica corretamente a tese do autor no artigo lido.",
            "☑ Observar se distingue trechos de fato e trechos de opinião com justificativa.",
            "☑ Acompanhar se reconhece introdução, desenvolvimento e conclusão na estrutura argumentativa.",
            "☑ Conferir se responde às questões com base no texto, sem se limitar a opinião pessoal.",
        ],
        "lp_relacoes_logico_discursivas": [
            "☑ Verificar se o aluno associa corretamente conectivos às relações de sentido.",
            "☑ Observar se identifica a função dos conectivos na construção do argumento.",
            "☑ Acompanhar se distingue relação adversativa de relação concessiva em contexto.",
            "☑ Conferir se aplica conectivos adequados em frases próprias.",
        ],
        "genero_textual": [
            "☑ Verificar se o aluno identifica corretamente as características do gênero estudado.",
            "☑ Observar se justifica as respostas com trechos do texto.",
            "☑ Acompanhar se distingue o gênero trabalhado de outros gêneros apresentados.",
            "☑ Verificar se os registros no caderno demonstram compreensão, não apenas cópia.",
        ],
        "analise_linguistica": [
            "☑ Verificar se o aluno identifica corretamente o recurso linguístico nos trechos indicados.",
            "☑ Observar se explica a diferença de sentido entre as formas analisadas.",
            "☑ Acompanhar individualmente os alunos com dificuldade nas atividades de reescrita.",
            "☑ Registrar os erros mais frequentes para orientar a retomada do conteúdo.",
        ],
        "vocabulario_inferencia": [
            "☑ Verificar se o aluno infere o significado das palavras pelo contexto.",
            "☑ Observar se as frases criadas demonstram compreensão do vocabulário trabalhado.",
            "☑ Acompanhar individualmente os alunos com maior dificuldade de leitura e vocabulário.",
            "☑ Retomar oralmente os sentidos das palavras durante a correção coletiva.",
        ],
        "producao_textual": [
            "☑ Verificar se o aluno organiza as ideias antes de escrever.",
            "☑ Observar clareza, sequência e coerência nos registros produzidos.",
            "☑ Acompanhar a revisão do texto com foco em melhoria, não em exposição do erro.",
        ],
        "retomada_lp": [
            "☑ Verificar se o aluno retém o conteúdo da aula anterior antes de avançar.",
            "☑ Observar se conecta o conteúdo novo ao que já foi estudado.",
            "☑ Registrar alunos que demonstram lacunas para retomada individual.",
            "☑ Acompanhar a participação durante a correção coletiva e a síntese no quadro.",
        ],
        "historia_poder_politico": [
            "☑ Verificar se o aluno identifica as características principais do governo estudado.",
            "☑ Observar se compreende a relação entre poder político e grupos sociais.",
            "☑ Analisar se consegue explicar como o poder era mantido no período estudado.",
            "☑ Conferir se registra corretamente os conceitos históricos no esquema do caderno.",
        ],
        "historia_conflito": [
            "☑ Verificar se o aluno identifica causas e consequências do conflito estudado.",
            "☑ Observar se distingue os grupos envolvidos e seus interesses.",
            "☑ Conferir se compreende o resultado do conflito e seu impacto histórico.",
            "☑ Acompanhar a organização do esquema de causas e consequências no caderno.",
        ],
        "historia_independencia_revolucao": [
            "☑ Verificar se o aluno identifica os grupos do movimento e suas motivações.",
            "☑ Observar se compreende as etapas do processo histórico estudado.",
            "☑ Analisar se relaciona ideias do período com ações políticas e mudanças históricas.",
            "☑ Registrar dúvidas sobre causas e consequências para retomada posterior.",
        ],
        "historia_sociedade_desigualdade": [
            "☑ Verificar se o aluno identifica grupos sociais e suas posições na hierarquia.",
            "☑ Observar se compreende diferenças de direitos e obrigações entre os grupos.",
            "☑ Conferir se relaciona a estrutura social aos eventos históricos do período.",
            "☑ Acompanhar se o esquema no caderno representa corretamente a organização social.",
        ],
        "historia_ideias": [
            "☑ Verificar se o aluno identifica as principais ideias do período e seus defensores.",
            "☑ Observar se compreende como essas ideias influenciaram ações históricas.",
            "☑ Analisar se explica a relação entre pensamento, política e mudança histórica.",
            "☑ Acompanhar a compreensão de termos abstratos durante a correção coletiva.",
        ],
        "historia_fonte": [
            "☑ Verificar se o aluno identifica origem, contexto e objetivo da fonte histórica.",
            "☑ Observar se compreende a ideia principal do documento analisado.",
            "☑ Conferir se relaciona a fonte com o conteúdo histórico estudado.",
            "☑ Acompanhar se utiliza evidências do texto para justificar as respostas.",
        ],
        "geografia_cartografia_tematica": [
            "☑ Verificar se o aluno diferencia mapa qualitativo de mapa quantitativo com exemplos.",
            "☑ Observar se identifica título, legenda e simbologia em um mapa temático.",
            "☑ Analisar se interpreta a legenda e relaciona as cores ou símbolos ao fenômeno representado.",
            "☑ Conferir se reconhece quando um mapa mostra categorias ou valores numéricos.",
        ],
        "geografia_fenomenos": [
            "☑ Identificar se o aluno reconhece onde o fenômeno geográfico ocorre com maior ou menor intensidade.",
            "☑ Observar se relaciona o fenômeno estudado a fatores naturais, sociais ou econômicos.",
            "☑ Verificar se interpreta corretamente informações apresentadas em mapas, tabelas ou textos.",
            "☑ Acompanhar se registra causas e consequências de forma organizada no caderno.",
        ],
        "geografia_dados_espaciais": [
            "☑ Verificar se o aluno compara valores entre regiões a partir de mapas, tabelas ou gráficos.",
            "☑ Observar se identifica concentração, distribuição e diferenças numéricas nos dados.",
            "☑ Conferir se justifica a resposta usando as informações apresentadas.",
            "☑ Acompanhar dúvidas na leitura de porcentagens, índices e quantidades.",
        ],
        "geografia_producao_cartografica": [
            "☑ Analisar se o mapa produzido contém título, legenda e simbologia adequados.",
            "☑ Verificar se o aluno aplica corretamente representação qualitativa ou quantitativa ao fenômeno escolhido.",
            "☑ Observar se consegue explicar oralmente o que seu mapa representa.",
            "☑ Acompanhar o uso de cores, símbolos e organização visual durante a produção.",
        ],
        "geografia_geral": [
            "☑ Verificar se o aluno compreende as informações geográficas apresentadas no mapa ou esquema.",
            "☑ Observar se relaciona paisagem, território, região ou fenômeno ao conteúdo estudado.",
            "☑ Acompanhar registros no caderno e participação durante a correção coletiva.",
            "☑ Retomar conceitos básicos de leitura espacial quando houver dificuldade.",
        ],
        "ciencias_alimentacao": [
            "☑ Verificar se o aluno identifica grupos alimentares a partir de exemplos concretos.",
            "☑ Observar se distingue alimentos in natura, minimamente processados e ultraprocessados.",
            "☑ Conferir se o cardápio ou a refeição organizada apresenta variedade e equilíbrio.",
            "☑ Acompanhar se o aluno justifica escolhas alimentares com base nos critérios estudados.",
        ],
        "ciencias_digestao": [
            "☑ Verificar se o aluno reconhece os principais órgãos do sistema digestório.",
            "☑ Observar se compreende a transformação dos alimentos e a absorção de nutrientes.",
            "☑ Acompanhar se registra a sequência da digestão de forma coerente.",
            "☑ Retomar dúvidas sobre função dos órgãos durante a correção coletiva.",
        ],
        "ciencias_nervoso_endocrino": [
            "☑ Verificar se o aluno diferencia sistema nervoso e sistema endócrino.",
            "☑ Observar se relaciona hormônios, glândulas e respostas do corpo ao desenvolvimento humano.",
            "☑ Acompanhar se utiliza corretamente os termos centrais no registro do caderno.",
            "☑ Retomar conceitos abstratos por meio de exemplos simples durante a correção.",
        ],
        "ciencias_genetica": [
            "☑ Verificar se o aluno identifica célula, gene, DNA e cromossomo como conceitos relacionados.",
            "☑ Observar se compreende a ideia de hereditariedade sem recorrer a relatos pessoais.",
            "☑ Acompanhar a organização dos conceitos no esquema do caderno.",
            "☑ Retomar diferenças entre característica, gene e material genético quando necessário.",
        ],
        "ciencias_ecologia": [
            "☑ Verificar se o aluno identifica seres vivos, ambiente e relações ecológicas no exemplo estudado.",
            "☑ Observar se compreende relações de alimentação, dependência e equilíbrio ambiental.",
            "☑ Acompanhar se organiza corretamente cadeia alimentar ou tabela de relações.",
            "☑ Retomar causas e consequências quando houver confusão entre os elementos do ecossistema.",
        ],
        "ciencias_geral": [
            "☑ Identificar se o aluno compreende o fenômeno natural ou conceito científico trabalhado.",
            "☑ Observar se registra observações, explicações e consequências de forma organizada.",
            "☑ Acompanhar dúvidas de vocabulário científico durante a correção coletiva.",
            "☑ Verificar se relaciona o conteúdo aos exemplos apresentados na lousa.",
        ],
    }
    padrao = [
        f"☑ Identificar se o aluno compreende as ideias principais relacionadas a {conceito_frase}.",
        "☑ Observar participação, registros no caderno e realização das atividades propostas.",
        "☑ Verificar dúvidas apresentadas e avanços durante a correção coletiva.",
        "☑ Acompanhar individualmente os estudantes que apresentarem maior dificuldade.",
    ]
    return _selecionar_itens_cdp(bancos.get(tipo_cdp, padrao), [perfil, tema, conceito, indice_aula], 3)


def _acessibilidade_cdp_contextual(perfil: str, tema: str, conceito: str = "", indice_aula: int = 0) -> list[str]:
    tipo_cdp = _tipo_conteudo_cdp(perfil, tema, conceito)
    if perfil == "matematica" and tipo_cdp in _tipos_matematica_eja_cdp():
        itens = _acessibilidade_matematica_eja_cdp(tipo_cdp)
        if itens:
            return itens[:3]
    bancos = {
        "fracao_conceito": [
            "☑ Uso de desenhos simples no quadro para representar partes iguais.",
            "☑ Retomada de numerador e denominador sempre que necessário.",
            "☑ Atividades graduais, começando por frações com números pequenos.",
            "☑ Tempo ampliado para copiar e concluir os registros.",
        ],
        "fracao_quantidade": [
            "☑ Leitura pausada do enunciado, destacando total e parte solicitada.",
            "☑ Resolução passo a passo com exemplos numéricos simples.",
            "☑ Apoio individual para alunos com dificuldade em divisão.",
            "☑ Registro no quadro dos passos principais para consulta durante a atividade.",
        ],
        "fracao_adicao_subtracao": [
            "☑ Retomada de múltiplos e denominadores antes dos exercícios.",
            "☑ Organização dos cálculos em etapas visíveis no quadro.",
            "☑ Exemplos adicionais para alunos que confundirem equivalência.",
            "☑ Correção sem exposição individual dos erros.",
        ],
        "fracao_mult_div": [
            "☑ Demonstração gradual do procedimento, com poucos números por vez.",
            "☑ Destaque no quadro para o uso do inverso na divisão.",
            "☑ Apoio individual durante os cálculos mais longos.",
            "☑ Retomada de simplificação apenas quando ela ajudar a compreensão.",
        ],
        "fracao_comparacao": [
            "☑ Uso de desenhos e retas simples para apoiar a comparação.",
            "☑ Exemplos com frações de denominadores pequenos antes de avançar.",
            "☑ Repetição dos critérios de comparação no quadro.",
            "☑ Atendimento individual para revisar equivalência quando necessário.",
        ],
        "combinatoria": [
            "☑ Organização das possibilidades por listas ou esquemas no quadro.",
            "☑ Problemas com poucas etapas antes de situações mais longas.",
            "☑ Apoio na leitura do enunciado e separação das escolhas.",
            "☑ Correção coletiva com valorização de estratégias diferentes.",
        ],
        "equacao": [
            "☑ Uso de linguagem simples para explicar incógnita como valor desconhecido.",
            "☑ Resolução em etapas curtas, uma operação por vez.",
            "☑ Retomada das operações inversas quando houver dificuldade.",
            "☑ Apoio individual durante a montagem da sentença matemática.",
        ],
        "geometria_angulos": [
            "☑ Desenhos grandes e claros no quadro para facilitar a visualização.",
            "☑ Comparação entre exemplos parecidos para diferenciar os tipos de ângulo.",
            "☑ Registro dos nomes e critérios de classificação para consulta.",
            "☑ Tempo ampliado para copiar figuras e responder às atividades.",
        ],
        "geometria_poligonos": [
            "☑ Figuras desenhadas no quadro com lados e vértices destacados.",
            "☑ Classificação feita por comparação entre exemplos simples.",
            "☑ Apoio individual para alunos com dificuldade de visualização.",
            "☑ Retomada dos critérios antes da correção coletiva.",
        ],
        "leitura_interpretacao": [
            "☑ Leitura pausada dos textos e comandos, com retomada de palavras difíceis.",
            "☑ Destaque no quadro das informações principais antes das respostas.",
            "☑ Possibilidade de resposta oral antes do registro escrito.",
            "☑ Apoio individual na localização de trechos do texto.",
        ],
        "lp_artigo_opiniao": [
            "☑ Realizar a leitura do artigo em voz alta, pausando nos trechos mais densos.",
            "☑ Retomar os conceitos de fato e opinião com exemplos simples antes da atividade.",
            "☑ Oferecer um modelo de resposta na lousa para orientar o padrão esperado.",
            "☑ Acompanhar individualmente alunos com dificuldade para localizar argumentos no texto.",
        ],
        "lp_relacoes_logico_discursivas": [
            "☑ Apresentar uma tabela de conectivos na lousa antes das atividades.",
            "☑ Trabalhar cada relação de sentido com frase curta antes de aplicar ao artigo.",
            "☑ Reduzir a quantidade de relações para alunos com maior defasagem, priorizando adição, oposição e causa.",
            "☑ Permitir consulta à tabela da lousa durante a realização das atividades.",
        ],
        "genero_textual": [
            "☑ Manter as características do gênero escritas no quadro durante a atividade.",
            "☑ Usar exemplos do cotidiano adulto para explicar o conceito trabalhado.",
            "☑ Oferecer apoio individual para localizar características no texto.",
            "☑ Permitir resposta oral quando houver dificuldade de escrita.",
        ],
        "analise_linguistica": [
            "☑ Manter os exemplos no quadro durante toda a atividade como referência.",
            "☑ Explicar o conceito gramatical com linguagem simples, sem terminologia excessiva.",
            "☑ Oferecer exemplos adicionais com frases próximas do cotidiano adulto.",
            "☑ Permitir tempo ampliado para as atividades de identificação e reescrita.",
        ],
        "vocabulario_inferencia": [
            "☑ Explicar o significado das palavras com exemplos concretos do cotidiano.",
            "☑ Escrever as palavras e seus significados no quadro durante a atividade.",
            "☑ Aceitar paráfrases nas respostas, valorizando a compreensão sobre a forma.",
            "☑ Oferecer apoio individual para alunos com vocabulário mais restrito.",
        ],
        "producao_textual": [
            "☑ Roteiro simples no quadro para orientar a escrita.",
            "☑ Possibilidade de revisar o texto em etapas menores.",
            "☑ Apoio individual na organização das ideias e frases.",
            "☑ Valorização do avanço do aluno sem exposição pública dos erros.",
        ],
        "retomada_lp": [
            "☑ Retomar oralmente o conteúdo anterior antes de propor a nova atividade.",
            "☑ Manter no quadro a ligação entre o que já foi estudado e o novo conceito.",
            "☑ Oferecer apoio individual para alunos que não acompanharam a aula anterior.",
            "☑ Ampliar o tempo de registro para completar a síntese no caderno.",
        ],
        "historia_poder_politico": [
            "☑ Apresentar o esquema de poder em forma de pirâmide, tabela ou lista simples na lousa.",
            "☑ Explicar termos como governo, centralização e absolutismo antes de usá-los na atividade.",
            "☑ Oferecer apoio individual para alunos com dificuldade de leitura dos registros.",
            "☑ Manter o esquema no quadro durante toda a resolução.",
        ],
        "historia_conflito": [
            "☑ Apresentar as causas do conflito em lista numerada na lousa.",
            "☑ Usar linguagem simples para descrever grupos, interesses e consequências.",
            "☑ Oferecer tempo ampliado para alunos com dificuldade de escrita.",
            "☑ Organizar no quadro uma tabela com causa, acontecimento e consequência.",
        ],
        "historia_independencia_revolucao": [
            "☑ Apresentar as etapas do movimento em sequência numerada na lousa.",
            "☑ Explicar termos históricos novos antes de utilizá-los no texto.",
            "☑ Oferecer apoio individual para alunos com dificuldade de compreensão.",
            "☑ Retomar oralmente a relação entre insatisfação, ação política e resultado.",
        ],
        "historia_sociedade_desigualdade": [
            "☑ Apresentar a estrutura social em esquema visual simples na lousa.",
            "☑ Explicar as diferenças entre os grupos com exemplos históricos concretos.",
            "☑ Oferecer atividade com menor número de questões quando houver dificuldade de escrita.",
            "☑ Evitar perguntas pessoais e manter a análise no contexto histórico estudado.",
        ],
        "historia_ideias": [
            "☑ Apresentar as ideias em lista simples na lousa, com definições curtas.",
            "☑ Usar exemplos concretos antes de apresentar conceitos mais abstratos.",
            "☑ Oferecer apoio individual para alunos com dificuldade de abstração.",
            "☑ Repetir os termos centrais com linguagem simples durante a correção.",
        ],
        "historia_fonte": [
            "☑ Ler a fonte em voz alta, pausando para explicar cada parte.",
            "☑ Apresentar perguntas de análise em ordem progressiva, do mais simples ao mais complexo.",
            "☑ Oferecer um roteiro de análise escrito no quadro para orientar as respostas.",
            "☑ Destacar no quadro autor, contexto, objetivo e ideia principal da fonte.",
        ],
        "geografia_cartografia_tematica": [
            "☑ Retomar conceitos básicos de leitura de mapas, como título, legenda, cores e símbolos.",
            "☑ Utilizar mapa impresso ampliado ou desenho simples na lousa para apoiar a observação.",
            "☑ Explicar qualitativo e quantitativo com exemplos concretos antes das atividades.",
            "☑ Permitir resposta oral quando houver dificuldade de escrita.",
        ],
        "geografia_fenomenos": [
            "☑ Apresentar exemplos concretos de distribuição de população, serviços, clima ou vegetação.",
            "☑ Organizar causas e consequências em lista simples no quadro.",
            "☑ Oferecer material impresso com mapas ou textos curtos para facilitar a leitura.",
            "☑ Realizar correção passo a passo, retomando o vocabulário geográfico necessário.",
        ],
        "geografia_dados_espaciais": [
            "☑ Destacar no quadro os dados que precisam ser comparados antes da atividade.",
            "☑ Explicar termos como índice, porcentagem, concentração e distribuição com exemplos simples.",
            "☑ Reduzir a quantidade de dados para alunos com maior dificuldade de leitura.",
            "☑ Permitir consulta ao esquema da lousa durante as respostas.",
        ],
        "geografia_producao_cartografica": [
            "☑ Oferecer mapa-base impresso ou contorno desenhado na lousa para orientar a produção.",
            "☑ Permitir uso de símbolos simples, como círculos, traços, cores e hachuras.",
            "☑ Acompanhar individualmente a construção de título, legenda e simbologia.",
            "☑ Valorizar clareza e organização do mapa sem exigir desenho elaborado.",
        ],
        "geografia_geral": [
            "☑ Utilizar linguagem simples e direta, explicando termos geográficos antes da atividade.",
            "☑ Trabalhar com mapas, esquemas ou descrições curtas que possam ser copiados no caderno.",
            "☑ Oferecer apoio individual durante a leitura das informações espaciais.",
            "☑ Realizar a correção das atividades passo a passo no quadro.",
        ],
        "ciencias_alimentacao": [
            "☑ Apresentar os grupos alimentares com exemplos escritos no quadro.",
            "☑ Oferecer lista de alimentos organizada por grupos para consulta durante a atividade.",
            "☑ Disponibilizar tabela de cardápio impressa ou copiada na lousa, reduzindo a demanda de organização visual.",
            "☑ Permitir que o aluno com maior dificuldade organize apenas uma refeição ou um dia de cardápio.",
        ],
        "ciencias_digestao": [
            "☑ Usar esquema simples do sistema digestório na lousa, com setas indicando a sequência.",
            "☑ Explicar cada órgão com frases curtas e exemplos objetivos.",
            "☑ Manter a lista de órgãos e funções visível durante a atividade.",
            "☑ Oferecer apoio individual para completar a sequência da digestão.",
        ],
        "ciencias_nervoso_endocrino": [
            "☑ Apresentar uma tabela simples diferenciando sistema nervoso e sistema endócrino.",
            "☑ Explicar hormônios, glândulas e respostas do corpo com linguagem direta.",
            "☑ Reduzir a quantidade de termos científicos para alunos com maior defasagem.",
            "☑ Permitir consulta ao esquema da lousa durante as respostas.",
        ],
        "ciencias_genetica": [
            "☑ Apresentar os termos célula, gene, DNA e cromossomo em esquema progressivo.",
            "☑ Evitar perguntas pessoais e trabalhar a hereditariedade por exemplos neutros.",
            "☑ Oferecer frases-modelo para orientar registros curtos no caderno.",
            "☑ Retomar oralmente cada conceito antes da correção coletiva.",
        ],
        "ciencias_ecologia": [
            "☑ Organizar seres vivos, ambiente e relações em tabela ou esquema na lousa.",
            "☑ Usar exemplos concretos antes de avançar para conceitos mais abstratos.",
            "☑ Oferecer apoio individual na montagem de cadeia alimentar ou relação ecológica.",
            "☑ Manter palavras-chave visíveis para consulta durante a atividade.",
        ],
        "ciencias_geral": [
            "☑ Utilizar exemplos concretos e esquemas simples na lousa.",
            "☑ Explicar vocabulário científico com linguagem simples antes da atividade.",
            "☑ Dividir o registro em etapas menores para facilitar a cópia e a compreensão.",
            "☑ Acompanhar individualmente os alunos com maior dificuldade de leitura ou escrita.",
        ],
    }
    padrao = [
        "☑ Utilização de exemplos concretos e próximos do cotidiano dos estudantes.",
        "☑ Explicação passo a passo, com registro das ideias principais no quadro.",
        "☑ Apoio individual, retomada de conceitos e flexibilização dos registros quando necessário.",
        "☑ Tempo ampliado para leitura, cópia e conclusão das atividades.",
    ]
    return _selecionar_itens_cdp(bancos.get(tipo_cdp, padrao), [perfil, tema, conceito, indice_aula, "acessibilidade"], 3)


def _detectar_tipo_aula(texto: str, tema: str, disciplina: str = "") -> str:
    base = _normalizar(f"{disciplina} {tema} {texto}")
    perfil = _perfil_disciplina(disciplina)
    tema_base = _normalizar(tema)

    if perfil == "educacao_financeira":
        mapa_tema = [
            ("instituicoes_financeiras", ["onde guardamos o dinheiro", "guardar dinheiro", "onde guardar o dinheiro", "guardamos o dinheiro"]),
            ("investimento_poupanca", ["por que poupamos", "porque poupamos", "reserva de emergencia", "poupamos"]),
            ("orcamento_planejamento", ["objetivos em familia ou em grupo", "objetivos em familia", "objetivos em grupo", "planejamento financeiro"]),
            ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias"]),
            ("governo_economia", ["papel do governo na economia", "governo na economia"]),
            ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas"]),
        ]
        for tipo, termos in mapa_tema:
            if _contem(tema_base, termos):
                return tipo
        if _contem(tema_base, ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]):
            return "credito_endividamento"
        if _contem(tema_base, ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]):
            return "empreendedorismo"
        if _contem(tema_base, ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]):
            return "cidadania_financeira"
        if _contem(tema_base, ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]):
            return "instituicoes_financeiras"
        if _contem(tema_base, ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]):
            return "investimento_poupanca"
        if _contem(tema_base, ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]):
            return "orcamento_planejamento"
        if _contem(tema_base, ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias", "manchetes", "noticias", "percentual", "porcentagem"]):
            return "analise_percentuais_noticias"
        if _contem(tema_base, ["papel do governo na economia", "governo na economia", "estado na economia", "politicas publicas", "impostos", "arrecadacao"]):
            return "governo_economia"
        if _contem(tema_base, ["impacto das decisoes economicas", "decisoes economicas em nossas vidas", "impacto das escolhas economicas", "escolhas economicas"]):
            return "impacto_decisoes_economicas"
        if _contem(tema_base, ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]):
            return "consumo_consciente"
        if _contem(base, ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]):
            return "credito_endividamento"
        if _contem(base, ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]):
            return "empreendedorismo"
        if _contem(base, ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]):
            return "cidadania_financeira"
        if _contem(base, ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]):
            return "instituicoes_financeiras"
        if _contem(base, ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]):
            return "investimento_poupanca"
        if _contem(base, ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]):
            return "orcamento_planejamento"
        if _contem(base, ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]):
            return "consumo_consciente"
        return "decisao_financeira"

    if perfil == "matematica":
        if _contem(base, ["aula khan", "pratica na khan", "atividade khan"]) and _contem(
            base,
            ["revisao", "conceito de funcao", "relacoes proporcionais", "grandezas diretamente proporcionais"],
        ):
            return "revisao_khan_funcao"
        if _contem(
            base,
            [
                "modelagem",
                "modelar situacoes",
                "modelar situacoes-problema",
                "metodo de polya",
                "polya",
                "representar matematicamente",
                "sentenca matematica",
            ],
        ):
            return "modelagem"
        if _contem(tema_base, ["grandeza", "razao", "proporcao"]):
            return "grandezas_medidas"
        if _contem(base, ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]):
            return "algebra"
        if _contem(base, ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]):
            return "funcoes"
        if _contem(base, ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha"]):
            return "combinatoria"
        if _contem(base, ["grandeza", "razao", "proporcao", "velocidade media", "mbps", "kbps"]):
            return "grandezas_medidas"
        if _contem(base, ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "frequencia", "censo", "pesquisa"]):
            return "estatistica_probabilidade"
        if _contem(base, ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]):
            return "geometria"
        if _contem(base, ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]):
            return "numeros_operacoes"
        return "resolucao_problemas"

    if _contem(base, ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]):
        return "producao"
    if _contem(base, ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]):
        return "argumentacao"
    if _contem(base, ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]):
        return "fonte_historica"
    if _contem(base, ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]):
        return "analise_geografica"
    if _contem(base, ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]):
        return "investigacao"
    if _contem(base, ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]):
        return "resolucao_problemas"
    if _contem(base, ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue"]):
        return "lingua_estrangeira"
    if _contem(base, ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]):
        return "arte_pratica"
    if _contem(base, ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]):
        return "reflexiva"
    if _contem(
        base,
        [
            "leitura",
            "leia",
            "texto",
            "interpreta",
            "genero textual",
            "conto",
            "cronica",
            "anuncio",
            "publicidade",
            "publicitario",
            "slogan",
            "observe",
        ],
    ):
        return "leitura"
    return "geral"


def _metodologia_fixa_pdf_especial(texto: str, disciplina: str, tema: str) -> list[dict] | None:
    perfil = _perfil_disciplina(disciplina)
    base = _normalizar(f"{disciplina} {tema} {texto}")

    if perfil == "matematica" and _contem(base, ["aula khan", "pratica na khan", "atividade khan"]) and _contem(
        base,
        ["revisao", "conceito de funcao", "relacoes proporcionais", "grandezas diretamente proporcionais"],
    ):
        return [
            {
                "titulo": "Para comecar",
                "texto": (
                    "Retomar com a turma os conceitos principais da aula, relacionando o conteudo a situacoes "
                    "do cotidiano e levantando conhecimentos previos dos alunos sobre funcao, proporcionalidade "
                    "e relacoes entre grandezas."
                ),
            },
            {
                "titulo": "Foco no conteudo",
                "texto": (
                    "Revisar os conceitos trabalhados em sala por meio de exemplos no quadro, leitura de graficos, "
                    "analise de tabelas e pequenas situacoes-problema, destacando como uma grandeza pode depender "
                    "da outra e como essa relacao pode ser representada matematicamente."
                ),
            },
            {
                "titulo": "Pratica e consolidacao",
                "texto": (
                    "Orientar os alunos na resolucao de atividades no caderno e, em seguida, encaminha-los para "
                    "a pratica no aplicativo, reforcando que o objetivo e revisar, testar hipoteses, aprender com "
                    "os erros e repetir a atividade sempre que necessario ate dominar a habilidade."
                ),
            },
            {
                "titulo": "Fechamento",
                "texto": (
                    "Retomar coletivamente as principais duvidas percebidas durante a atividade, socializar "
                    "estrategias de resolucao e registrar os pontos que precisarao ser reforcados nas proximas "
                    "aulas, utilizando o desempenho dos alunos no aplicativo como apoio para o acompanhamento "
                    "da aprendizagem."
                ),
            },
        ]

    return None


def _conceito_principal(linhas: list[str], tema: str) -> str:
    marcadores_ignorar = {
        "para comecar",
        "contextualizacao",
        "leitura analitica",
        "leitura e construcao do conteudo",
        "exploracao",
        "foco no conteudo",
        "formalizacao",
        "pause e responda",
        "na pratica",
        "revisao e reescrita",
        "relembre",
        "encerramento",
        "sistematizacao",
        "todo mundo escreve",
        "virem e conversem",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "listen and repeat",
        "write and share",
        "say it in english",
    }
    candidatos = []
    for linha in linhas[:12]:
        normalizada = _normalizar(linha)
        if normalizada in marcadores_ignorar:
            continue
        if _linha_com_marcador_metodologico(linha):
            continue
        linha_limpa = _limpar_linha_metodologica(linha)
        if not linha_limpa:
            continue
        if _linha_instrucao_matematica(linha_limpa):
            continue
        if 8 <= len(linha_limpa) <= 120:
            candidatos.append(linha_limpa)
    return candidatos[0] if candidatos else tema


def _linha_com_marcador_metodologico(linha: str) -> bool:
    normalizada = _normalizar(linha)
    marcadores = [
        "virem e conversem",
        "todo mundo escreve",
        "com suas palavras",
        "hora da leitura",
        "de olho no modelo",
        "um passo de cada vez",
        "pause e responda",
        "para comecar",
        "foco no conteudo",
        "na pratica",
        "encerramento",
    ]
    quantidade = sum(1 for marcador in marcadores if marcador in normalizada)
    if quantidade >= 2:
        return True
    return any(normalizada.startswith(marcador) for marcador in marcadores)


def _limpar_linha_metodologica(linha: str) -> str:
    limpa = re.sub(r"\s+", " ", str(linha or "")).strip(" -:;•\t")
    padroes = [
        r"\bVIREM\s+E\s+CONVERSEM\b",
        r"\bTODO\s+MUNDO\s+ESCREVE\b",
        r"\bCOM\s+SUAS\s+PALAVRAS\b",
        r"\bHORA\s+DA\s+LEITURA\b",
        r"\bDE\s+OLHO\s+NO\s+MODELO\b",
        r"\bUM\s+PASSO\s+DE\s+CADA\s+VEZ\b",
    ]
    for padrao in padroes:
        limpa = re.sub(padrao, "", limpa, flags=re.I)
    limpa = re.sub(r"\s+", " ", limpa).strip(" -:;•\t")
    return limpa


def _linha_instrucao_matematica(linha: str) -> bool:
    normalizada = _normalizar(linha)
    inicios_instrucao = (
        "resolva",
        "calcule",
        "determine",
        "registre",
        "complete",
        "observe",
        "assinale",
        "responda",
        "explique",
        "justifique",
        "copie",
        "escreva",
        "analise",
    )
    return normalizada.startswith(inicios_instrucao)


def _perguntas_orientadoras(tipo: str, tema: str, conceito: str) -> str:
    perguntas = {
        "algebra": [
            "Quais grandezas estao envolvidas na situacao?",
            "Como representar matematicamente essa relacao?",
            "O resultado encontrado faz sentido no contexto?",
        ],
        "funcoes": [
            "Que relacao de dependencia existe entre as grandezas?",
            "Como a tabela e o grafico representam essa variacao?",
            "O comportamento e crescente ou decrescente? Por quê?",
        ],
        "geometria": [
            "Que propriedades da figura ajudam na resolucao?",
            "Que medidas precisam ser observadas ou calculadas?",
            "Como justificar o procedimento utilizado?",
        ],
        "grandezas_medidas": [
            "Quais sao as grandezas envolvidas e suas unidades?",
            "A relacao e direta ou inversamente proporcional?",
            "Como interpretar o valor obtido no contexto?",
        ],
        "estatistica_probabilidade": [
            "Que dados ou eventos precisam ser analisados?",
            "Como organizar essas informacoes para interpretar melhor?",
            "O resultado pode ser expresso em fracao, decimal e porcentagem?",
        ],
        "combinatoria": [
            "A ordem dos elementos importa nesta situacao?",
            "Como listar ou contar os casos possiveis de modo organizado?",
            "O total encontrado faz sentido no contexto?",
        ],
        "modelagem": [
            "Que grandezas e relacoes aparecem na situacao?",
            "Como traduzir o problema para linguagem matematica?",
            "Como interpretar a resposta no contexto original?",
        ],
        "verificacao": [
            "Que conceito ou procedimento precisa ser retomado?",
            "Qual estrategia e mais adequada para resolver cada item?",
            "Como verificar se a resposta final esta coerente?",
        ],
        "leitura": [
            f"O que o titulo {tema} antecipa sobre o texto?",
            "Quais informacoes ajudam a compreender a finalidade do material?",
            "Que pistas do texto ou da imagem justificam as respostas?",
        ],
        "argumentacao": [
            "Qual opiniao ou ponto de vista aparece no material?",
            "Que argumentos sustentam essa ideia?",
            "Que recursos tornam a mensagem mais convincente?",
        ],
        "producao": [
            "Para quem o texto sera escrito?",
            "Qual finalidade deve orientar a producao?",
            "Que criterios precisam ser observados na revisao?",
        ],
        "investigacao": [
            "Que fenomeno ou problema esta sendo investigado?",
            "Quais evidencias aparecem no material?",
            "Como podemos explicar o processo com nossas palavras?",
        ],
        "fonte_historica": [
            "Quem produziu essa fonte e em que contexto?",
            "Que informacoes ela revela sobre o periodo estudado?",
            "Que relacao podemos fazer com o presente?",
        ],
        "analise_geografica": [
            "Que elementos da paisagem, mapa ou grafico precisam ser observados?",
            "Que relacoes existem entre espaco, sociedade e natureza?",
            "Que exemplos do cotidiano ajudam a entender o tema?",
        ],
        "resolucao_problemas": [
            "Quais dados o problema apresenta?",
            "Que estrategia de resolucao pode ser usada?",
            "Como verificar se o resultado faz sentido?",
        ],
        "lingua_estrangeira": [
            "Quais palavras ou expressoes ja conhecemos?",
            "Em que situacao real podemos usar esse vocabulario?",
            "Como pronunciar e empregar as estruturas trabalhadas?",
        ],
        "arte_pratica": [
            "Que sensacoes, ideias ou referencias a obra/material provoca?",
            "Que elementos visuais, sonoros ou corporais podemos perceber?",
            "Como transformar essa observacao em criacao ou registro?",
        ],
        "reflexiva": [
            "Como esse tema aparece na vida escolar ou pessoal?",
            "Que escolhas ou atitudes podem ser observadas nessa situacao?",
            "Que compromisso simples pode ser assumido a partir da aula?",
        ],
    }
    escolhidas = perguntas.get(tipo) or [
        f"O que ja sabemos sobre {tema}?",
        f"Quais ideias principais aparecem em {conceito}?",
        "Como registrar e aplicar o que foi discutido?",
    ]
    return "Perguntas orientadoras: " + " ".join(f"- {p}" for p in escolhidas)


def _tecnica_por_perfil(perfil: str) -> dict[str, str]:
    tecnicas = {
        "lingua_portuguesa_ef": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa_em": {
            "discussao": "DEBATE ORIENTADO",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "leitura_redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao_estudos": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "ciencias_ef": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "biologia": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "quimica": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM PROCEDIMENTOS E RESULTADOS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "fisica": {
            "discussao": "OBSERVEM E LEVANTEM HIPOTESES",
            "registro": "REGISTREM MEDIDAS E RELACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "historia": {
            "discussao": "ANALISEM AS FONTES",
            "registro": "REGISTREM A CRONOLOGIA",
            "sintese": "COM SUAS PALAVRAS",
        },
        "geografia": {
            "discussao": "OBSERVEM O MAPA/IMAGEM",
            "registro": "REGISTREM AS RELACOES ESPACIAIS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "ingles": {
            "discussao": "LISTEN AND REPEAT",
            "registro": "WRITE AND SHARE",
            "sintese": "SAY IT IN ENGLISH",
        },
        "arte": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "REGISTRO NO DIARIO DE BORDO",
            "sintese": "APRECIACAO COMPARTILHADA",
        },
        "projeto_de_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
        "educacao_financeira": {
            "discussao": "analise orientada de caso",
            "registro": "registro de calculos, criterios e decisoes",
            "sintese": "planejamento de aplicacao",
        },
        "matematica": {
            "discussao": "uma conversa em duplas",
            "registro": "um registro individual no caderno",
            "sintese": "síntese com as próprias palavras",
        },
        "tecnologia_inovacao": {
            "discussao": "PENSEM EM SOLUCOES",
            "registro": "REGISTREM O PROTOTIPO OU ALGORITMO",
            "sintese": "APRESENTEM A SOLUCAO",
        },
        "sociologia": {
            "discussao": "DEBATAM O FENOMENO SOCIAL",
            "registro": "REGISTREM ARGUMENTOS E EVIDENCIAS",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lideranca_oratoria": {
            "discussao": "PRATIQUEM EM DUPLAS OU GRUPOS",
            "registro": "REGISTREM FEEDBACKS E AVANCOS",
            "sintese": "AUTOAVALIACAO BREVE",
        },
        "ciencias": {
            "discussao": "FORMULEM HIPOTESES",
            "registro": "REGISTREM OBSERVACOES",
            "sintese": "COM SUAS PALAVRAS",
        },
        "lingua_portuguesa": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "redacao": {
            "discussao": "VIREM E CONVERSEM",
            "registro": "TODO MUNDO ESCREVE",
            "sintese": "COM SUAS PALAVRAS",
        },
        "orientacao": {
            "discussao": "discussao em duplas sobre estrategias de estudo",
            "registro": "registro de estrategia no caderno",
            "sintese": "autoavaliacao breve",
        },
        "projeto_vida": {
            "discussao": "roda de conversa acolhedora",
            "registro": "registro pessoal sem exposicao obrigatoria",
            "sintese": "compromisso para a semana",
        },
    }
    return tecnicas.get(perfil, tecnicas["lingua_portuguesa_ef"])


def _frases_por_contexto(perfil: str, tipo: str, tema: str, conceito: str, turma: str, texto_base: str = "") -> dict[str, str]:
    tecnicas = _tecnica_por_perfil(perfil)
    tecnicas_pdf = _detectar_tecnicas_matematica(texto=texto_base, tema=tema) if perfil == "matematica" else set()

    base = {
        "para_comecar": (
            f"Retomar conhecimentos previos da turma sobre {tema}. Propor {tecnicas['discussao']} "
            "para levantar hipoteses, exemplos e duvidas iniciais."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informacoes relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situacoes do cotidiano, repertorios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteudo e relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analitica do texto, imagem, dado ou situacao apresentada, destacando escolhas de "
            "linguagem, organizacao das ideias, pistas visuais e informacoes que sustentam a compreensao."
        ),
        "exploracao": (
            "Estimular os estudantes a levantar estrategias, testar caminhos e comparar representacoes antes da "
            "sistematizacao, valorizando diferentes formas de pensar e justificar o raciocinio."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteudo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relacoes entre conceito, exemplo e atividade."
        ),
        "formalizacao": (
            "Sistematizar no quadro os conceitos, propriedades, procedimentos e registros essenciais da aula, "
            "nomeando cada etapa da resolucao e retomando criterios para validar as respostas."
        ),
        "pratica": (
            f"Orientar a resolucao das atividades propostas, usando {tecnicas['registro']} para garantir registro "
            "individual. Circular pela sala, mediar duvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            "Socializar algumas respostas e realizar correcao dialogada, retomando trechos do material, registros "
            "dos estudantes e duvidas comuns antes de avancar."
        ),
        "encerramento": (
            f"Finalizar com {tecnicas['sintese']}, retomando os aprendizados sobre {tema} e registrando uma sintese "
            "curta no quadro ou no caderno."
        ),
    }

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "lingua_portuguesa", "leitura_redacao", "redacao"}:
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de producao e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, genero textual e criterios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as caracteristicas do genero relacionado a {tema}, observando estrutura, linguagem, "
                "organizacao das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                "Orientar o planejamento, a escrita do rascunho e a revisao. Solicitar que os estudantes confiram "
                "se o texto atende a finalidade, ao publico e aos criterios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opiniao, argumentos e estrategias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando genero, finalidade, publico-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensao."
            )

    elif perfil == "orientacao_estudos" or perfil == "orientacao":
        base["foco"] = (
            f"Trabalhar {conceito} como oportunidade para ensinar uma estrategia de estudo: localizar informacoes, "
            "interpretar comandos, justificar respostas e revisar registros."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades explicitando o passo a passo de estudo: ler o comando, marcar "
            "palavras-chave, buscar evidencias, responder e revisar a resposta."
        )
        base["encerramento"] = (
            f"Finalizar com autoavaliacao breve sobre qual estrategia ajudou mais a compreender {tema} e como ela "
            "pode ser usada em outras disciplinas."
        )

    elif perfil in {"ciencias_ef", "ciencias", "biologia", "quimica", "fisica"}:
        base["para_comecar"] = (
            f"Contextualizar {tema} com uma situacao-problema, imagem, dado ou exemplo do cotidiano. Propor "
            f"{tecnicas['discussao']} para que os estudantes antecipem explicacoes e levantem evidencias."
        )
        base["foco"] = (
            f"Explicar {conceito} de forma progressiva, relacionando fenomeno, causa, consequencia e exemplos. "
            "Usar esquemas no quadro para diferenciar observacao, hipotese e conceito cientifico."
        )
        base["pratica"] = (
            f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {tecnicas['registro']}. "
            "Retomar as evidencias usadas pelos estudantes para justificar as respostas."
        )

    elif perfil == "historia":
        base["foco"] = (
            f"Apresentar o contexto historico de {conceito}, situando sujeitos, tempo, espaco e conflitos envolvidos. "
            "Relacionar as ideias iniciais da turma com os conceitos historicos em estudo."
        )
        base["pratica"] = (
            "Orientar a analise de fontes, imagens, mapas, linhas do tempo ou textos do material. Solicitar registro "
            "das evidencias encontradas e mediacao para diferenciar fato, interpretacao e contexto."
        )

    elif perfil == "geografia":
        base["foco"] = (
            f"Analisar {conceito} considerando paisagem, territorio, escala, localizacao e relacoes entre sociedade "
            "e natureza. Usar mapa, imagem, tabela ou grafico como apoio para a explicacao."
        )
        base["pratica"] = (
            "Orientar leitura de mapas, imagens, graficos ou situacoes-problema, solicitando que os estudantes "
            "identifiquem elementos espaciais e expliquem relacoes de causa e consequencia."
        )

    elif perfil == "ingles":
        base["para_comecar"] = (
            f"Retomar vocabulario conhecido relacionado a {tema} com repeticao oral breve e exemplos no quadro. "
            "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematizacao."
        )
        base["leitura"] = (
            "Apresentar o texto, dialogo, imagem ou situacao comunicativa, alternando leitura em voz alta, escuta "
            "e repeticao. Destacar vocabulario-chave e estruturas em ingles com apoio em exemplos."
        )
        base["foco"] = (
            f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressoes estudadas. "
            "Registrar no quadro exemplos curtos em ingles e seus sentidos em contexto."
        )
        base["pratica"] = (
            "Organizar pratica oral e escrita em pares, com repeticao, preenchimento, pequenas respostas ou dialogos. "
            "Acompanhar pronuncia, compreensao e uso funcional das expressoes."
        )

    elif perfil == "arte":
        base["foco"] = (
            f"Apresentar referencias artisticas relacionadas a {conceito}, orientando apreciacao de elementos visuais, "
            "sonoros, corporais ou culturais. Valorizar percepcoes diferentes sem reduzir a aula a explicacao teorica."
        )
        base["pratica"] = (
            "Propor experimentacao, criacao ou apreciacao orientada, com registro no diario de bordo. Acompanhar "
            "processos criativos, escolhas dos estudantes e socializacao das producoes ou percepcoes."
        )

    elif perfil == "projeto_de_vida" or perfil == "projeto_vida":
        conceito_seguro = tema if _conceito_generico_ou_quebrado_projeto_vida(conceito) else conceito
        base["para_comecar"] = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
        )
        base["foco"] = (
            f"Construir a reflexao sobre {conceito_seguro} por meio de exemplos escolares e cotidianos, ajudando a turma a "
            "relacionar sentir, pensar e agir de forma respeitosa."
        )
        base["pratica"] = (
            "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
            "que a socializacao seja opcional ou mediada, evitando exposicao de experiencias intimas."
        )
        base["encerramento"] = (
            f"Encerrar com um compromisso simples ou observacao para a semana, relacionado a {tema}, reforcando "
            "autonomia, respeito e cuidado nas relacoes."
        )

    elif perfil == "educacao_financeira":
        conceito_seguro = tema if _normalizar(conceito) in {"educacao financeira", "financeira"} else conceito

        situacoes = {
            "orcamento_planejamento": "uma situacao de organizacao de renda, gastos e prioridades para cumprir uma meta simples",
            "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preco, durabilidade e impacto da escolha",
            "investimento_poupanca": "uma situacao de poupanca ou reserva de emergencia em que pequenos valores acumulados ajudam a lidar com imprevistos",
            "credito_endividamento": "uma compra parcelada ou oferta de credito em que seja necessario comparar valor a vista, juros, parcelas e custo total",
            "empreendedorismo": "um pequeno projeto de venda, servico ou solucao para a comunidade escolar, analisando custos, preco e viabilidade",
            "analise_percentuais_noticias": "uma noticia, manchete ou grafico em que a turma precise interpretar percentuais e relacionar os dados a uma situacao real",
            "governo_economia": "uma situacao cotidiana sobre como a acao do governo influencia precos, servicos, impostos e a vida economica da populacao",
            "impacto_decisoes_economicas": "uma situacao do cotidiano em que escolhas economicas afetam consumo, planejamento, prioridades e bem-estar",
            "cidadania_financeira": "uma situacao de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de servicos financeiros",
            "instituicoes_financeiras": "uma situacao cotidiana sobre onde guardar, movimentar e proteger o dinheiro com seguranca",
        }
        situacao = situacoes.get(tipo, f"uma situacao financeira real relacionada a {tema}")

        base["para_comecar"] = (
            f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre habitos financeiros familiares. "
            "Convidar os estudantes a levantar hipoteses sobre escolhas, riscos, prioridades e consequencias antes da sistematizacao."
        )
        base["analise_caso"] = (
            f"Conduzir a analise do caso ligado a {tema}, identificando dados importantes, alternativas possiveis, "
            "criterios de decisao e consequencias de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
        )
        base["foco"] = (
            f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situacoes reais de consumo, "
            "planejamento, poupanca, credito ou organizacao de recursos. Explicar o vocabulario financeiro necessario e construir criterios claros para a tomada de decisao."
        )
        base["pause"] = (
            "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
            "retomando dados do material e duvidas comuns antes de seguir para a aplicacao."
        )
        base["calculos"] = (
            "Orientar calculos financeiros de forma guiada, destacando dados, operacoes, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
            "Relacionar cada resultado numerico a uma decisao possivel, evitando que a atividade fique apenas mecanica."
        )
        base["planejamento"] = (
            "Orientar a elaboracao ou analise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
            "Acompanhar os registros para que os estudantes expliquem os criterios usados nas escolhas."
        )
        base["simulacao"] = (
            "Organizar uma simulacao financeira ou analise de alternativas, aplicando os criterios construidos na aula para escolher, comparar, planejar ou revisar uma decisao. "
            "Solicitar registro de calculos, justificativas e possiveis consequencias."
        )
        base["projeto"] = (
            "Orientar a organizacao de um projeto empreendedor simples, levantando recursos necessarios, custos, preco, publico, viabilidade e cuidados eticos. "
            "Solicitar que os estudantes justifiquem as decisoes tomadas no planejamento."
        )
        base["pratica"] = (
            "Orientar a resolucao das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparacao de alternativas e justificativa das decisoes. "
            "Retomar vocabulario financeiro e criterios de escolha sempre que surgirem duvidas."
        )

        if tipo == "orcamento_planejamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} como estrategia de organizacao financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                "Construir com a turma criterios para controlar recursos e ajustar escolhas conforme limites e objetivos."
            )
            base["pratica"] = base["planejamento"]
        elif tipo == "consumo_consciente":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} a partir de criterios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-beneficio e impacto da escolha. "
                "Evitar tom moralista e conduzir a analise com base em argumentos, dados e consequencias."
            )
        elif tipo == "investimento_poupanca":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando poupanca, reserva, rendimento, constancia e planejamento de metas. "
                "Mostrar como a organizacao dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "credito_endividamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} com foco no uso responsavel do credito, analisando juros, parcelas, custo total, riscos de endividamento e criterios para decidir. "
                "Comparar alternativas sem estimular consumo, priorizando avaliacao critica e planejamento."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "empreendedorismo":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou servico, custos, preco, lucro e viabilidade. "
                "Relacionar a proposta a planejamento, responsabilidade e analise do contexto."
            )
            base["pratica"] = base["projeto"]
        elif tipo == "analise_percentuais_noticias":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio da leitura de noticias, manchetes, tabelas e graficos, ajudando a turma a interpretar percentuais, "
                "comparar dados e perceber como os numeros influenciam a compreensao dos fatos."
            )
            base["calculos"] = (
                "Orientar calculos de porcentagem e comparacao de variacoes com apoio do quadro, destacando o significado de cada dado antes do procedimento numerico. "
                "Retomar passo a passo como localizar o valor de referencia, calcular percentuais e interpretar o resultado no contexto da noticia analisada."
            )
            base["pratica"] = (
                "Propor leitura guiada de noticias ou situacoes semelhantes, seguida de registros no caderno com interpretacao dos percentuais, comparacao de informacoes "
                "e justificativa sobre o que os dados revelam."
            )
        elif tipo == "governo_economia":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando arrecadacao, servicos publicos, regulacao e impactos economicos no cotidiano. "
                "Conduzir a turma a perceber como decisoes do governo interferem em precos, circulacao de dinheiro e acesso a direitos."
            )
            base["pratica"] = (
                "Orientar a analise de exemplos concretos, comparando situacoes em que a acao do governo influencia consumo, trabalho, precos ou servicos. "
                "Solicitar registros curtos com explicacao das relacoes observadas."
            )
        elif tipo == "impacto_decisoes_economicas":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} por meio de escolhas economicas do cotidiano, relacionando recursos disponiveis, prioridades, consumo e consequencias de curto e longo prazo. "
                "Estimular a turma a comparar alternativas com base em criterios claros e realistas."
            )
            base["pratica"] = (
                "Propor situacoes-problema simples para que os estudantes comparem escolhas, antecipem impactos e justifiquem decisoes com base nos dados apresentados. "
                "Retomar o vocabulario financeiro necessario sempre que surgirem duvidas."
            )
        elif tipo == "cidadania_financeira":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, seguranca, comprovantes, garantias e autonomia nas decisoes financeiras. "
                "Orientar a turma a identificar formas de protecao e uso consciente de servicos financeiros."
            )
        elif tipo == "instituicoes_financeiras":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} explicando a funcao das instituicoes financeiras na guarda, movimentacao, controle e protecao do dinheiro. "
                "Comparar exemplos como banco, conta digital, poupanca e outros servicos, destacando seguranca e planejamento."
            )

        base["encerramento"] = (
            f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando criterios de decisao, organizacao e responsabilidade. "
            "Propor um fechamento com planejamento de aplicacao no cotidiano, sem solicitar exposicao de informacoes financeiras pessoais."
        )

    elif perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        contexto = _resumo_contexto_matematica(texto_base, tema)
        pratica = _resumo_pratica_matematica(texto_base, tema)
        pergunta_pause = _pergunta_pause_matematica(texto_base)
        tecnica_inicio = "uma conversa em duplas" if "virem_conversem" in tecnicas_pdf else "uma discussão coletiva inicial"
        tecnica_registro = "um registro individual no caderno" if "todo_mundo_escreve" in tecnicas_pdf else tecnicas["registro"]

        if formato == "verificacao":
            base["para_comecar"] = (
                f"Retomar com a turma os procedimentos essenciais relacionados a {tema}, recuperando "
                "criterios de resolucao, organizacao dos registros e verificacao das respostas antes das atividades."
            )
        elif formato == "pratica_intensiva":
            base["para_comecar"] = (
                "Retomar brevemente as estrategias discutidas na aula anterior e combinar com a turma como registrar "
                "equacao, resolucao e verificacao em cada situacao proposta."
            )
        else:
            base["para_comecar"] = (
                f"Apresentar {contexto} e propor {tecnica_inicio} para que os estudantes mobilizem conhecimentos "
                "previos, levantem hipoteses e identifiquem o que precisa ser descoberto na situacao."
            )

        if tipo == "algebra":
            base["foco"] = (
                f"Conduzir a construcao de {conceito}, identificando a incognita, organizando os dados do problema e "
                "mostrando como as propriedades da igualdade ajudam a transformar e validar cada passo da resolucao."
            )
        elif tipo == "funcoes":
            base["foco"] = (
                f"Conduzir a leitura de {conceito} articulando tabela, pares ordenados, representacao grafica e "
                "interpretacao da dependencia entre as grandezas envolvidas no contexto estudado."
            )
        elif tipo == "grandezas_medidas":
            base["foco"] = (
                f"Desenvolver {conceito} relacionando unidades, razoes e comparacoes entre grandezas, destacando como "
                "as variacoes do contexto ajudam a construir significado para os calculos."
            )
        elif tipo == "estatistica_probabilidade":
            base["foco"] = (
                f"Desenvolver {conceito} por meio da leitura de dados, tabelas e graficos, orientando a turma a "
                "organizar informacoes, justificar conclusoes e conferir a coerencia das interpretacoes."
            )
        elif tipo == "combinatoria":
            base["foco"] = (
                f"Desenvolver {conceito} discutindo criterios de contagem, verificando se a ordem importa e escolhendo "
                "a estrategia mais adequada antes de iniciar os calculos."
            )
        elif tipo == "modelagem":
            base["foco"] = (
                f"Conduzir a modelagem da situacao apresentada em {tema}, traduzindo os dados para linguagem "
                "matematica, construindo a equacao e interpretando a solucao no contexto original."
            )
        else:
            base["foco"] = (
                f"Explorar {conceito} com exemplos guiados, destacando dados, relacoes, procedimentos e criterios para "
                "verificar se o resultado encontrado faz sentido na situacao estudada."
            )

        if "hora_leitura" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Integrar leitura orientada para explicitar como interpretar o enunciado, selecionar informações "
                "relevantes e planejar o caminho de resolução."
            )
        if "um_passo" in tecnicas_pdf or "um passo de cada vez" in _normalizar(texto_base):
            base["foco"] = (
                base["foco"]
                + " Construir a estratégia de forma gradual, nomeando cada etapa do procedimento."
            )
        if "de_olho_modelo" in tecnicas_pdf:
            base["foco"] = (
                base["foco"]
                + " Apoiar a explicação com um exemplo resolvido, comentando por que a solução encontrada é válida."
            )

        base["formalizacao"] = ""
        if pergunta_pause:
            base["pause"] = (
                f"Propor a questao do material: {pergunta_pause} Socializar as respostas e realizar correcao "
                "dialogada, retomando as justificativas matematicas construidas pela turma."
            )
        else:
            base["pause"] = (
                "Socializar algumas estrategias, comparar caminhos de resolucao e retomar com a turma os criterios "
                "usados para validar cada resposta."
            )

        if formato == "verificacao":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com atividades de retomada e verificacao, solicitando resolucao "
                "completa, comparacao de estrategias e conferência cuidadosa da coerencia dos resultados."
            )
        elif formato == "pratica_intensiva":
            base["pratica"] = (
                f"Organizar {tecnica_registro} com {pratica}, solicitando que cada estudante registre equacao, "
                "resolucao, justificativa e verificacao da resposta em todas as atividades propostas."
            )
        else:
            base["pratica"] = (
                f"Orientar {tecnica_registro} com {pratica}, acompanhando a interpretacao dos enunciados, a "
                "organizacao dos calculos e a validacao das solucoes construidas pela turma."
            )

        fechamento = _fechamento_reflexivo_matematica(texto_base, tema, formato)
        base["encerramento"] = (
            f"Encerrar com {tecnicas['sintese']}, para {fechamento} e registrar uma sintese coletiva do que "
            "foi aprendido na aula."
        )

    elif perfil == "tecnologia_inovacao":
        base["para_comecar"] = (
            f"Apresentar um problema real relacionado a {tema}, incentivando observacao do contexto e levantamento "
            "de necessidades antes da construcao de solucoes."
        )
        base["pratica"] = (
            "Orientar criacao, programacao, prototipagem ou teste de solucao, acompanhando escolhas tecnicas, "
            "iteracoes e registros do processo."
        )

    elif perfil == "sociologia":
        base["para_comecar"] = (
            f"Apresentar um fenomeno social ligado a {tema} por meio de situacao, imagem, dado ou relato, "
            "provocando estranhamento e questionamentos iniciais."
        )
        base["foco"] = (
            f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
            "para superar leituras baseadas apenas no senso comum."
        )

    elif perfil == "lideranca_oratoria":
        base["para_comecar"] = (
            f"Realizar aquecimento vocal, corporal ou mental relacionado a {tema}, criando um ambiente acolhedor "
            "para a pratica de comunicacao e reduzindo a ansiedade de exposicao."
        )
        base["foco"] = (
            f"Apresentar tecnicas e conceitos ligados a {conceito}, demonstrando aplicacoes em fala publica, "
            "argumentacao, escuta ativa ou lideranca colaborativa."
        )
        base["pause"] = (
            "Promover pratica oral breve com feedback positivo sobre avancos observados antes de sugerir ajustes, "
            "fortalecendo confianca e progressao da turma."
        )
        base["pratica"] = (
            "Orientar exercicios, miniapresentacoes, debates ou dinamicas de lideranca de forma progressiva, "
            "sem expor estudantes abruptamente e valorizando preparo, escuta e cooperacao."
        )
        base["encerramento"] = (
            "Encerrar com autoavaliacao breve sobre comunicacao, postura e participacao, registrando um proximo "
            "passo de desenvolvimento para a turma."
        )

    return base


def _obra_literaria_redacao(tema: str, texto_base: str = "") -> str:
    fonte = " ".join([str(tema or ""), str(texto_base or "")[:800]])
    match = re.search(r"[\"“”']([^\"“”']{3,80})[\"“”']", fonte)
    if match:
        return match.group(1).strip()
    texto = re.sub(r"^\s*aula\s*\d+\s*[-:–—]?\s*", "", str(tema or ""), flags=re.I).strip(" -:–—")
    texto = re.sub(r"^trilha\s*", "", texto, flags=re.I).strip(" -:–—")
    return texto or "a obra literaria em estudo"


def _eh_producao_final_redacao(texto_base: str, tema: str = "") -> bool:
    # Check top lines of the text_base for reading indicators
    linhas_topo = _limpar_linhas(texto_base)[:6]
    texto_topo = _normalizar(" ".join(linhas_topo))
    texto_topo_limpo = re.sub(r"[^\w\s]", " ", texto_topo)
    texto_topo_limpo = re.sub(r"\s+", " ", texto_topo_limpo).strip()
    if "pratica de linguagem leitura" in texto_topo_limpo or "praticas de leitura" in texto_topo_limpo or "praticas de linguagem leitura" in texto_topo_limpo:
        if "producao de textos" not in texto_topo_limpo and "pratica de linguagem producao" not in texto_topo_limpo:
            return False

    base = _normalizar(f"{tema} {texto_base}")
    if "pratica de linguagem" in base and "leitura" in base and not any(
        termo in base
        for termo in [
            "producao de textos",
            "versao final",
            "revisao orientada",
            "redacao paulista",
            "submissao",
            "reescrita",
            "rascunho",
        ]
    ):
        return False
    return any(
        termo in base
        for termo in [
            "producao de textos",
            "versao final",
            "revisao orientada",
            "redacao paulista",
            "submissao",
            "reescrita",
            "rascunho",
        ]
    )


def _metodologia_leitura_redacao_modelo_obsoleta(texto_base: str, tema: str) -> list[dict]:
    if _eh_producao_final_redacao(texto_base, tema):
        return [
            {
                "titulo": "Para comecar",
                "texto": (
                    "Explicar aos estudantes que a aula sera dedicada a finalizacao da producao textual, destacando a importancia "
                    "da revisao e da passagem do rascunho para a versao final. Retomar o percurso de escrita realizado nas aulas "
                    "anteriores e apresentar o roteiro da aula no quadro: revisao final, escrita da versao final e envio na plataforma Redacao Paulista."
                ),
            },
            {
                "titulo": "Revisao orientada",
                "texto": (
                    "Orientar os estudantes a relerem seus textos com atencao, observando organizacao das ideias, sequencia dos "
                    "acontecimentos, clareza das informacoes e adequacao ao genero trabalhado. Utilizar um checklist simples para "
                    "auxiliar na revisao da estrutura do texto, pontuacao, conectivos e linguagem utilizada."
                ),
            },
            {
                "titulo": "Escrita da versao final",
                "texto": (
                    "Solicitar que os estudantes produzam a versao final do texto, incorporando as melhorias identificadas durante "
                    "a revisao. Incentivar a atencao a organizacao dos paragrafos, a clareza das ideias e a apresentacao do texto antes da entrega final."
                ),
            },
            {
                "titulo": "Submissao e socializacao",
                "texto": (
                    "Orientar os estudantes no envio da producao textual para a plataforma Redacao Paulista, oferecendo suporte sempre que necessario. "
                    "Apos o envio, promover um breve momento de socializacao sobre as dificuldades e avancos percebidos durante o processo de escrita e revisao."
                ),
            },
            {
                "titulo": "Encerramento",
                "texto": (
                    "Finalizar a aula valorizando o percurso de escrita desenvolvido pelos estudantes, reforcando a importancia da revisao textual "
                    "para melhorar a clareza, organizacao e qualidade da producao escrita."
                ),
            },
        ]

    obra = _obra_literaria_redacao(tema, texto_base)
    return [
        {
            "titulo": "Para comecar",
            "texto": (
                f"Retomar os acontecimentos ja lidos da obra {obra}, incentivando os estudantes a relembrarem personagens, "
                "situacoes marcantes, momentos engraçados ou acontecimentos inesperados da narrativa. Promover o compartilhamento "
                "de lembrancas e opinioes para ampliar o envolvimento da turma com a leitura."
            ),
        },
        {
            "titulo": "Predicao guiada",
            "texto": (
                f"Conduzir uma conversa sobre os pensamentos das personagens e as situacoes apresentadas em {obra}, incentivando "
                "os estudantes a levantarem hipoteses sobre os proximos acontecimentos da historia. Estimular comentarios pessoais "
                "e afetivos sobre atitudes, desafios e possiveis mudancas no percurso narrativo."
            ),
        },
        {
            "titulo": "Leitura compartilhada ou individual",
            "texto": (
                "Realizar a leitura do trecho selecionado de forma compartilhada ou individual, orientando os estudantes a identificarem "
                "personagens, espaco e acontecimentos principais. Durante a leitura, promover pausas para comentarios e impressoes sobre "
                "a narrativa, incentivando a participacao da turma e a expressao de opinioes despertadas pelo texto."
            ),
        },
        {
            "titulo": "Conexao com a producao textual",
            "texto": (
                "Destacar que as historias literarias possuem sequencia de acontecimentos e organizacao narrativa. Orientar os estudantes "
                "a perceberem como os fatos se conectam na historia para apoiar futuras producoes textuais criativas, com começo, desenvolvimento e desfecho."
            ),
        },
    ]


def _genero_textual_redacao(texto_base: str, tema: str = "") -> str:
    base = _normalizar(f"{tema} {texto_base}")
    if "resenha" in base:
        return "resenha"
    if "cronica" in base or "crônica" in base:
        return "cronica"
    if "sinopse" in base:
        return "sinopse"
    if _eh_producao_final_redacao(texto_base, tema):
        return "producao textual"
    return "narrativa"


def _objetivo_pedagogico_redacao(texto_base: str, tema: str, genero: str) -> str:
    base = _normalizar(f"{tema} {texto_base}")
    habilidade = "interpretar, analisar e produzir textos"
    if genero == "producao textual" or "revis" in base:
        habilidade = "planejar, revisar, reescrever e aprimorar textos"
    elif genero == "resenha":
        habilidade = "analisar, argumentar e sustentar opinioes sobre uma obra"

    finalidade = "compartilhar leitura, impressoes e posicionamentos com clareza"
    if genero == "resenha":
        finalidade = "recomendar ou nao a obra a leitores da escola, justificando a opiniao"
    elif genero == "cronica":
        finalidade = "relatar uma situacao do cotidiano para provocar identificacao e reflexao"
    elif genero == "sinopse":
        finalidade = "apresentar a obra a leitores da escola de forma objetiva e convidativa"
    elif genero == "producao textual":
        finalidade = "produzir a versao final do texto para circulacao escolar ou envio na plataforma"

    return (
        f"Desenvolver a capacidade de {habilidade}, considerando o genero {genero}, "
        f"escrevendo para os colegas da turma com o objetivo de {finalidade}."
    )


def _perguntas_analise_redacao(genero: str, tema: str) -> list[str]:
    if genero == "resenha":
        return [
            "O que a obra apresentada mostra de mais importante ao leitor?",
            "Que opiniao sobre a obra aparece no texto e como ela foi justificada?",
            "Que elementos fazem esse texto convencer ou nao o leitor a buscar a obra?",
        ]
    if genero == "cronica":
        return [
            "Que situacao cotidiana aparece no texto e como ela se desenvolve?",
            "Como o narrador apresenta o conflito ou desafio vivido?",
            "Que reflexao sobre o cotidiano o texto provoca no leitor?",
        ]
    return [
        f"Quais acontecimentos, informacoes ou ideias centrais aparecem em {tema}?",
        "Como as escolhas de linguagem ajudam o leitor a compreender o texto e seus sentidos?",
        "Que reflexoes, opinioes ou relacoes com o cotidiano essa leitura desperta?",
    ]


def _sistematizacao_redacao(genero: str) -> str:
    if genero == "resenha":
        return (
            "Organizar coletivamente uma lista com os elementos essenciais da resenha: apresentacao da obra, tipo de historia, "
            "opiniao fundamentada, pontos positivos e/ou negativos e recomendacao final."
        )
    if genero == "cronica":
        return (
            "Registrar em esquema os elementos da cronica: narrador, situacao cotidiana, conflito ou desafio, desenvolvimento da narrativa e reflexao final."
        )
    if genero == "sinopse":
        return (
            "Retomar em passo a passo os elementos da sinopse: apresentacao da obra, personagens ou situacao central, tema principal e convite para a leitura."
        )
    return (
        "Organizar coletivamente um esquema com genero textual, finalidade, leitor previsto, estrutura basica e recursos de linguagem que poderao apoiar a escrita."
    )


def _extrair_tema_redacao_leitura(texto: str) -> str | None:
    linhas = _limpar_linhas(texto)
    if not linhas:
        return None
        
    texto_topo = " ".join(linhas[:20])
    
    # 1. Trilha with quotes
    match_trilha = re.search(r'(Trilha\s+[“"\'\u201c][^”"\'\u201d]+[”"\'\u201d])', texto_topo, flags=re.I)
    if match_trilha:
        return match_trilha.group(1).strip()
        
    # 2. Elaboração do Projeto/Rascunho/Texto
    match_elab = re.search(r'(Elaboração\s+(?:do|de|)\s*(?:Projeto\s+de\s+Texto\s+\d+|rascunho|texto\s+\d+))', texto_topo, flags=re.I)
    if match_elab:
        return match_elab.group(1).strip()
        
    # 3. Versão final do Texto / Rascunho
    match_versao = re.search(r'(Versão\s+final\s+do\s+Texto\s+\d+|Versão\s+final\s+do\s+rascunho)', texto_topo, flags=re.I)
    if match_versao:
        return match_versao.group(1).strip()

    # 4. Devolutiva do Texto
    match_devolutiva = re.search(r'(Devolutiva\s+do\s+Texto\s+\d+)', texto_topo, flags=re.I)
    if match_devolutiva:
        return match_devolutiva.group(1).strip()
        
    # Fallback to line-by-line matches if not found in joined format
    for linha in linhas[:20]:
        match = re.search(r'(Trilha\s+[“"[][^”"\]]+[”"\]])', linha, flags=re.I)
        if match:
            return match.group(1).strip()
        
        match_v = re.search(r'(Versão\s+final\s+do\s+Texto\s+\d+)', linha, flags=re.I)
        if match_v:
            return match_v.group(1).strip()

        match_d = re.search(r'(Devolutiva\s+do\s+Texto\s+\d+)', linha, flags=re.I)
        if match_d:
            return match_d.group(1).strip()

    # Generic Trilha/Versão final/Devolutiva matches
    for linha in linhas[:20]:
        linha_lower = linha.lower()
        if "trilha" in linha_lower:
            match = re.search(r'(Trilha\s+.+)', linha, flags=re.I)
            if match:
                t = match.group(1).split('|')[0].strip()
                t = re.sub(r'^(Trilha\s+[^-\n]+).*$', r'\1', t).strip()
                return t
        if "versao final" in _normalizar(linha):
            match = re.search(r'(Versão\s+final\s+.+)', linha, flags=re.I)
            if match:
                return match.group(1).split('|')[0].strip()
        if "devolutiva" in _normalizar(linha):
            match = re.search(r'(Devolutiva\s+.+)', linha, flags=re.I)
            if match:
                return match.group(1).split('|')[0].strip()
                
    return None


def _seccionar_texto_por_tema(texto: str, tema: str) -> str:
    linhas = texto.splitlines()
    tema_norm = _normalizar(tema)
    tema_norm_limpo = re.sub(r'[“"”\'\[\]]', '', tema_norm).strip()
    
    idx_inicio = 0
    for i, linha in enumerate(linhas):
        linha_norm = _normalizar(linha)
        linha_norm_limpo = re.sub(r'[“"”\'\[\]]', '', linha_norm).strip()
        if tema_norm_limpo in linha_norm_limpo or (len(tema_norm_limpo) > 5 and tema_norm_limpo[:15] in linha_norm_limpo):
            idx_inicio = i
            break
            
    idx_fim = len(linhas)
    for i in range(idx_inicio + 1, len(linhas)):
        linha_norm = _normalizar(linhas[i])
        if "trilha " in linha_norm or "versao final " in linha_norm or "devolutiva " in linha_norm:
            linha_norm_limpo = re.sub(r'[“"”\'\[\]]', '', linha_norm).strip()
            if tema_norm_limpo not in linha_norm_limpo:
                idx_fim = i
                break
                
    return "\n".join(linhas[idx_inicio:idx_fim])


def _extrair_etapas_redacao_leitura(texto: str) -> list[dict]:
    linhas = texto.splitlines()
    etapas = []
    secao_atual = None
    linhas_secao = []
    
    for linha in linhas:
        linha_clean = linha.strip()
        match = re.match(r"^\s*(\d+)\.\s*(.+)$", linha_clean)
        if match:
            if secao_atual:
                etapas.append({
                    "numero": secao_atual["numero"],
                    "titulo": secao_atual["titulo"],
                    "texto": "\n".join(linhas_secao).strip()
                })
            secao_atual = {
                "numero": int(match.group(1)),
                "titulo": match.group(2).strip(),
            }
            linhas_secao = []
        else:
            if secao_atual is not None:
                if linha_clean.isdigit() and len(linha_clean) <= 2:
                    continue
                linhas_secao.append(linha_clean)
                
    if secao_atual:
        etapas.append({
            "numero": secao_atual["numero"],
            "titulo": secao_atual["titulo"],
            "texto": "\n".join(linhas_secao).strip()
        })
        
    return etapas


def _metodologia_leitura_redacao_modelo(texto_base: str, tema: str) -> list[dict]:
    genero = _genero_textual_redacao(texto_base, tema)
    objetivo = _objetivo_pedagogico_redacao(texto_base, tema, genero)
    perguntas = _perguntas_analise_redacao(genero, tema)

    # 1. Tentar extrair as etapas do PDF
    etapas_pdf = []
    if texto_base:
        secao = _seccionar_texto_por_tema(texto_base, tema)
        etapas_pdf = _extrair_etapas_redacao_leitura(secao)

    # 2. Gerar a estrutura padrão
    if _eh_producao_final_redacao(texto_base, tema):
        metodologia = [
            {
                "titulo": "Disparo inicial / contextualizacao",
                "texto": (
                    f"Apresentar o tema da aula e explicar que o trabalho sera voltado a finalizacao da producao textual. "
                    f"Retomar o percurso ja vivido pela turma e explicitar o objetivo da aula: {objetivo}"
                ),
            },
            {
                "titulo": "Leitura ou exploracao inicial",
                "texto": (
                    "Orientar releitura guiada do proprio rascunho, com instrucoes claras para observar tema, organizacao das ideias, "
                    "clareza das informacoes, adequacao ao genero textual e dialogo com o leitor."
                ),
            },
            {
                "titulo": "Analise guiada",
                "texto": (
                    "Conduzir perguntas orientadoras para revisar o texto: 1) O texto comunica com clareza a ideia principal? "
                    "2) A organizacao das partes ajuda o leitor a acompanhar a escrita? 3) O que pode ser melhorado para tornar a producao mais completa e adequada ao genero?"
                ),
            },
            {
                "titulo": "Sistematizacao",
                "texto": (
                    "Organizar no quadro um checklist de revisao com criterios obrigatorios: atendimento ao tema, estrutura do genero, paragrafos organizados, pontuacao, conectivos, ortografia e efeito pretendido no leitor."
                ),
            },
            {
                "titulo": "Producao textual",
                "texto": (
                    "Solicitar a escrita da versao final do texto em contexto real de circulacao, como mural da escola, pasta da turma ou plataforma Redacao Paulista. "
                    "Explicar o que escrever, para quem escrever e com qual objetivo, orientando os estudantes a incorporar as melhorias feitas durante a revisao."
                ),
            },
            {
                "titulo": "Revisao e fechamento",
                "texto": (
                    "Finalizar com revisao final em dupla ou individual, retomando o checklist e incentivando adjustments antes da entrega. "
                    "Encerrar com reflexao sobre o que melhorou do rascunho para a versao final e por que revisar faz parte do processo de escrita."
                ),
            },
        ]
    else:
        obra = _obra_literaria_redacao(tema, texto_base)
        metodologia = [
            {
                "titulo": "Disparo inicial / contextualizacao",
                "texto": (
                    f"Apresentar a aula a partir da obra {obra}, conectando o tema ao cotidiano, as experiencias leitoras da turma e o repertorio dos estudantes. "
                    f"Explicar o proposito da atividade e explicitar o objetivo pedagogico: {objetivo}"
                ),
            },
            {
                "titulo": "Leitura ou exploracao inicial",
                "texto": (
                    f"Propor leitura guiada ou exploracao inicial de trechos de {obra}, com foco no genero {genero}, nas personagens, nos acontecimentos e na forma como o texto busca envolver o leitor."
                ),
            },
            {
                "titulo": "Analise guiada",
                "texto": (
                    f"Conduzir perguntas interpretativas e reflexivas: 1) {perguntas[0]} 2) {perguntas[1]} 3) {perguntas[2]}"
                ),
            },
            {
                "titulo": "Sistematizacao",
                "texto": _sistematizacao_redacao(genero),
            },
            {
                "titulo": "Producao textual",
                "texto": (
                    f"Propor uma atividade de escrita em contexto real, como recomendacao para colegas, texto para mural da escola, diario de leitura ou publicacao da turma. "
                    f"Explicar o que escrever, para quem escrever e com qual objetivo, garantindo integracao entre leitura e escrita, incentivando producoes textuais criativas e deixando claros os criterios obrigatorios do genero {genero}."
                ),
            },
            {
                "titulo": "Revisao e fechamento",
                "texto": (
                    "Orientar revisao com checklist de clareza, organizacao, adequacao ao genero, justificativa das opinioes e efeito no leitor. "
                    "Encerrar com socializacao breve e reflexao sobre como a leitura ajudou a produzir um texto mais consciente e melhor elaborado."
                ),
            },
        ]

    # 3. Se houver etapas extraídas, mapeá-las para enriquecer cada bloco
    if etapas_pdf:
        mapa_etapas = {i: [] for i in range(6)}
        
        for idx_e, e in enumerate(etapas_pdf):
            t_norm = _normalizar(e["titulo"])
            texto_completo = f"Condução prática sugerida: {e['titulo']}. {e['texto']}"
            
            mapped = False
            if any(k in t_norm for k in ["retomada", "prepara", "abertura", "context", "introducao", "disparo"]):
                mapa_etapas[0].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["leitura", "exploracao", "ler"]):
                mapa_etapas[1].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["analise", "pergunta", "discussao", "positivo", "revisao guiada"]):
                mapa_etapas[2].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["sistematizacao", "registro", "roteiro", "esquema", "oportunidade", "melhoria"]):
                mapa_etapas[3].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["producao", "escrita", "escrever", "submissao", "plataforma", "redacao"]):
                mapa_etapas[4].append(texto_completo)
                mapped = True
            if any(k in t_norm for k in ["fechamento", "revisao", "conclusao", "socializacao", "encerramento"]):
                mapa_etapas[5].append(texto_completo)
                mapped = True
                
            if not mapped:
                total = len(etapas_pdf)
                if total <= 3:
                    seq_map = {0: [0], 1: [1], 2: [1], 3: [2], 4: [2], 5: [2]}
                elif total == 4:
                    seq_map = {0: [0], 1: [1], 2: [1], 3: [2], 4: [2], 5: [3]}
                else:
                    seq_map = {0: [0], 1: [1], 2: [2], 3: [3], 4: [3], 5: [4]}
                
                for b_idx, e_idxs in seq_map.items():
                    if idx_e in e_idxs:
                        mapa_etapas[b_idx].append(texto_completo)

        for i in range(6):
            if mapa_etapas[i]:
                etapas_unidas = "\n\n".join(mapa_etapas[i])
                metodologia[i]["texto"] = f"{metodologia[i]['texto']}\n\n{etapas_unidas}"

    return metodologia


def _etapas_por_perfil(perfil: str, tipo: str, texto_base: str = "", tema: str = "") -> list[tuple[str, str]]:
    if perfil == "matematica":
        formato = _detectar_formato_aula_matematica(texto_base, tema)
        if formato == "verificacao":
            return [
                ("Relembre", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        if formato == "pratica_intensiva":
            return [
                ("Para comecar", "para_comecar"),
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]

        etapas = [
            ("Para comecar", "para_comecar"),
            ("Foco no conteudo", "foco"),
        ]
        if _tem_secao_matematica(texto_base, "pause e responda"):
            etapas.append(("Pause e responda", "pause"))
        etapas.extend(
            [
                ("Na pratica", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        )
        return etapas

    if perfil == "lingua_portuguesa_em":
        return [
            ("Para comecar", "para_comecar"),
            ("Contextualizacao", "contextualizacao"),
            ("Leitura analitica", "leitura_analitica"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "leitura_redacao" and tipo == "producao":
        return [
            ("Para comecar", "para_comecar"),
            ("Leitura e construcao do conteudo", "leitura"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
            ("Na pratica", "pratica"),
            ("Revisao e reescrita", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        etapas = [
            ("Para comecar", "para_comecar"),
            ("Analise de caso", "analise_caso"),
            ("Foco no conteudo", "foco"),
            ("Pause e responda", "pause"),
        ]
        base = _normalizar(f"{texto_base} {tema}")
        if tipo in {"credito_endividamento", "investimento_poupanca", "analise_percentuais_noticias"} or _contem(base, ["juros", "porcentagem", "parcela", "rendimento", "calculo"]):
            etapas.append(("Calculos financeiros", "calculos"))
        if tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orcamentario", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na pratica", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    return [
        ("Para comecar", "para_comecar"),
        ("Leitura e construcao do conteudo", "leitura"),
        ("Foco no conteudo", "foco"),
        ("Pause e responda", "pause"),
        ("Na pratica", "pratica"),
        ("Encerramento", "encerramento"),
    ]


def _remover_abertura_generica(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    padroes = [
        r"^Retomar conhecimentos previos da turma sobre [^.]+\.?\s*",
        r"^Retomar conhecimentos pr[eÃ©]vios da turma sobre [^.]+\.?\s*",
        r"^Promover discuss[aÃ£]o inicial sobre [^.]+\.?\s*",
        r"^Apresentar [^.]+ e propor [^.]+ para que os estudantes mobilizem conhecimentos previos, levantem hipoteses e identifiquem o que precisa ser descoberto na situacao\.?\s*",
    ]
    for padrao in padroes:
        texto = re.sub(padrao, "", texto, count=1, flags=re.I).strip()
    return texto


def _anexar_orientacao_unica(texto: str, orientacao: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    orientacao = re.sub(r"\s+", " ", str(orientacao or "")).strip()
    if not orientacao:
        return texto
    if _normalizar(orientacao[:80]) in _normalizar(texto):
        return texto
    if texto and not texto.endswith((".", "!", "?")):
        texto += "."
    return f"{texto} {orientacao}".strip() if texto else orientacao


def _ajustar_texto_por_sequencia(
    texto: str,
    chave: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
    tema: str = "",
) -> str:
    """Diferencia metodologia quando varios PDFs compoem uma sequencia."""
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if total_aulas <= 1 or not texto:
        return texto

    indice_aula = max(0, min(indice_aula, total_aulas - 1))
    ultima = indice_aula == total_aulas - 1
    primeira = indice_aula == 0

    if chave == "para_comecar" and not primeira:
        resto = _remover_abertura_generica(texto)
        if ultima:
            opcoes_abertura = [
                (
                    f"Retomar o percurso das aulas anteriores sobre {tema}, destacando os registros, "
                    "duvidas e estrategias ja construidos pela turma."
                ),
                (
                    f"Revisitar o percurso das aulas anteriores sobre {tema}, retomando os registros, "
                    "duvidas e estrategias construidos ate aqui."
                ),
                (
                    f"Dar continuidade ao estudo de {tema}, recuperando o percurso das aulas anteriores "
                    "e os registros produzidos pela turma."
                ),
            ]
        else:
            opcoes_abertura = [
                (
                    f"Retomar a aula anterior sobre {tema} e conectar os registros ja produzidos "
                    "ao novo foco do dia."
                ),
                (
                    f"Recuperar aprendizagens da aula anterior sobre {tema}, articulando os registros "
                    "ja produzidos ao novo foco do dia."
                ),
                (
                    f"Revisitar os registros da aula anterior sobre {tema} e relacionar essas anotacoes "
                    "ao encaminhamento do dia."
                ),
                (
                    f"Dar continuidade ao estudo de {tema}, retomando o que foi registrado anteriormente "
                    "e conectando ao foco da aula."
                ),
                (
                    f"Reativar os conhecimentos construidos na aula anterior sobre {tema}, conectando "
                    "os registros ja produzidos ao novo foco do dia."
                ),
            ]
        abertura = _escolher_variacao(opcoes_abertura, [tema, chave, str(indice_aula), str(total_aulas), resto[:120]])
        return f"{abertura} {resto}".strip()

    if chave in {"leitura", "contextualizacao", "leitura_analitica", "foco"} and not primeira:
        orientacao = (
            "Retomar registros anteriores quando necessario, ajudando a turma a perceber a continuidade do estudo."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave in {"pratica", "calculos", "planejamento", "projeto"} and not primeira:
        orientacao = (
            "Solicitar que os estudantes comparem as respostas de hoje com as estrategias usadas anteriormente, "
            "identificando avancos, ajustes e duvidas persistentes."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave == "pause" and not primeira:
        orientacao = (
            "Usar a pausa tambem para verificar quais aprendizagens da sequencia ja estao consolidadas "
            "e quais ainda precisam de retomada."
        )
        return _anexar_orientacao_unica(texto, orientacao)

    if chave == "encerramento":
        if ultima:
            orientacao = (
                "Fechar a sequencia com uma sintese final, retomando o percurso completo e registrando "
                "o que a turma consegue fazer com mais autonomia."
            )
        elif not primeira:
            orientacao = (
                "Registrar uma sintese parcial e uma pergunta para orientar a proxima aula da sequencia."
            )
        else:
            orientacao = (
                "Indicar que os registros desta aula serao retomados na continuidade da sequencia."
            )
        return _anexar_orientacao_unica(texto, orientacao)

    return texto


def _ajustar_metodologia_por_sequencia(
    metodologia,
    indice_aula: int = 0,
    total_aulas: int = 1,
    tema: str = "",
):
    if total_aulas <= 1:
        return metodologia

    mapa_titulos = {
        "para comecar": "para_comecar",
        "relembre": "para_comecar",
        "contextualizacao": "contextualizacao",
        "leitura analitica": "leitura_analitica",
        "leitura e construcao do conteudo": "leitura",
        "foco no conteudo": "foco",
        "pause e responda": "pause",
        "na pratica": "pratica",
        "calculos financeiros": "calculos",
        "planejamento orcamentario": "planejamento",
        "projeto empreendedor": "projeto",
        "encerramento": "encerramento",
        "revisao e reescrita": "encerramento",
    }

    ajustada = []
    for item in metodologia or []:
        if not isinstance(item, dict):
            ajustada.append(item)
            continue
        novo_item = dict(item)
        titulo = _normalizar(novo_item.get("titulo", ""))
        chave = mapa_titulos.get(titulo, "")
        if chave:
            novo_item["texto"] = _ajustar_texto_por_sequencia(
                novo_item.get("texto", ""),
                chave,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
        ajustada.append(novo_item)
    return ajustada


def _montar_etapas_metodologia(
    texto: str,
    disciplina: str,
    turma: str,
    tema: str,
    indice_aula: int = 0,
    total_aulas: int = 1,
) -> list[dict]:
    perfil = _perfil_disciplina(disciplina)
    if perfil == "leitura_redacao":
        return _metodologia_leitura_redacao_modelo(texto, tema)

    metodologia = _motor_metodologico.gerar(
        texto_pdf=texto,
        disciplina=disciplina,
        turma=turma,
        tema=tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
    )
    mapa_titulos = {
        "para comecar": "Para comecar",
        "relembre": "Relembre",
        "contextualizacao": "Contextualizacao",
        "leitura analitica": "Leitura analitica",
        "leitura e construcao do conteudo": "Leitura e construcao do conteudo",
        "foco no conteudo": "Foco no conteudo",
        "pause e responda": "Pause e responda",
        "na pratica": "Na pratica",
        "analise de caso": "Analise de caso",
        "calculos financeiros": "Calculos financeiros",
        "planejamento orcamentario": "Planejamento orcamentario",
        "projeto empreendedor": "Projeto empreendedor",
        "revisao e reescrita": "Revisao e reescrita",
        "encerramento": "Encerramento",
    }
    harmonizada = []
    for item in metodologia or []:
        if not isinstance(item, dict):
            harmonizada.append(item)
            continue
        novo_item = dict(item)
        titulo_norm = _normalizar(novo_item.get("titulo", ""))
        if titulo_norm in mapa_titulos:
            novo_item["titulo"] = mapa_titulos[titulo_norm]
        harmonizada.append(novo_item)
    return harmonizada


def _tema_por_texto(texto: str, caminho_pdf: str, disciplina: str) -> str:
    if _perfil_disciplina(disciplina) == "orientacao_estudos":
        titulo_catalogado = _titulo_catalogado_orientacao_estudos(caminho_pdf, texto)
        if titulo_catalogado:
            return titulo_catalogado

    def limpar_prefixo_disciplina(titulo: str) -> str:
        palavras_titulo = str(titulo or "").split()
        palavras_disciplina = str(disciplina or "").split()
        if not palavras_titulo or not palavras_disciplina:
            return str(titulo or "").strip()

        prefixo_titulo = [_normalizar(p) for p in palavras_titulo[: len(palavras_disciplina)]]
        prefixo_disciplina = [_normalizar(p) for p in palavras_disciplina]
        if prefixo_titulo == prefixo_disciplina:
            return " ".join(palavras_titulo[len(palavras_disciplina) :]).strip()

        primeiro_titulo = _normalizar(palavras_titulo[0])
        primeiro_disciplina = _normalizar(palavras_disciplina[0])
        if primeiro_titulo and primeiro_disciplina and primeiro_titulo[:5] == primeiro_disciplina[:5]:
            return " ".join(palavras_titulo[1:]).strip()

        return str(titulo or "").strip()

    linhas = _limpar_linhas(texto)
    for linha in linhas[:12]:
        titulo_aula = limpar_prefixo_disciplina(_limpar_titulo_material(_titulo_em_linha_aula(linha), disciplina))
        if len(titulo_aula) >= 6:
            titulo_aula_norm = _normalizar(titulo_aula).replace(" ", "").replace("\ufffd", "")
            if not ("sugestoes" in titulo_aula_norm and "condu" in titulo_aula_norm):
                return titulo_aula[:120]

    if _perfil_disciplina(disciplina) == "leitura_redacao":
        tema_leitura = _extrair_tema_redacao_leitura(texto)
        if tema_leitura:
            return tema_leitura

    candidatos = []
    disciplina_norm = _normalizar(disciplina)
    disciplina_base = disciplina_norm.split()[0] if disciplina_norm else ""
    for linha in linhas[:8]:
        linha_norm = _normalizar(linha)
        if linha_norm == disciplina_norm:
            continue
        if disciplina_base and len(linha.split()) <= max(2, len(str(disciplina or "").split())) and linha_norm.startswith(disciplina_base[:5]):
            continue
        titulo = _limpar_titulo_material(linha, disciplina)
        normalizada = _normalizar(titulo)
        if len(titulo) < 4 or not titulo:
            continue
        if any(token in normalizada for token in ["bimestre", "ensino medio", "ensino fundamental"]):
            break
        if _linha_generica(titulo, disciplina):
            continue
        if _linha_rotulo_aula(normalizada) or normalizada.startswith(("slide ", "pagina ", "página ")):
            if candidatos:
                break
            continue
        candidatos.append(titulo)
        if len(candidatos) >= 4:
            break

    if candidatos:
        titulo = _juntar_partes_titulo(candidatos)
        titulo = limpar_prefixo_disciplina(titulo)
        if len(titulo) >= 6:
            return titulo[:120]

    titulo_multilinha = limpar_prefixo_disciplina(_extrair_titulo_multilinha(texto, disciplina))
    if len(titulo_multilinha) >= 6:
        return titulo_multilinha[:120]
    for linha in _limpar_linhas(texto):
        titulo = limpar_prefixo_disciplina(_limpar_titulo_material(linha, disciplina))
        titulo_norm = _normalizar(titulo)
        if len(titulo) >= 6 and not _linha_generica(titulo, disciplina) and not (_linha_rotulo_aula(titulo_norm) or titulo_norm.startswith("slide ")):
            return titulo[:120]
    return Path(caminho_pdf).stem.replace("_", " ").replace("-", " ").title()


def _rotulo_aula_material(texto: str, caminho_pdf: str) -> str:
    padrao_texto = re.compile(r"\baula\s*(?:n[.o]?\s*)?(\d{1,3})\b", flags=re.I)
    for linha in _limpar_linhas(texto)[:30]:
        match = padrao_texto.search(linha)
        if match:
            return f"AULA {match.group(1)}"

    match = re.search(r"\baula[_\s-]*(\d{1,3})\b", Path(caminho_pdf).stem, flags=re.I)
    if match:
        return f"AULA {match.group(1)}"
    return ""


def _material_digital_por_texto(texto: str, caminho_pdf: str, disciplina: str, tema: str = "") -> str:
    rotulo = _rotulo_aula_material(texto, caminho_pdf)
    titulo = (tema or _tema_por_texto(texto, caminho_pdf, disciplina)).strip()
    if _perfil_disciplina(disciplina) == "orientacao_estudos" and _titulo_ja_rotulado_orientacao_estudos(titulo):
        return titulo
    if rotulo and titulo:
        return f"{rotulo} - {titulo}"
    return rotulo or titulo


def _texto_metodologia(metodologia) -> str:
    blocos = []
    for item in metodologia or []:
        if isinstance(item, dict):
            titulo = str(item.get("titulo", "") or "").strip()
            texto = str(item.get("texto", "") or "").strip()
            blocos.append(f"{titulo}:\n{texto}".strip() if titulo else texto)
        else:
            blocos.append(str(item))
    return "\n\n".join(blocos)


def _metodologia_em_blocos_por_texto(texto: str) -> list[dict]:
    titulos_validos = {
        "para comecar",
        "disparo inicial / contextualizacao",
        "disparo inicial / contextualização",
        "leitura ou exploracao inicial",
        "leitura ou exploração inicial",
        "leitura compartilhada ou individual",
        "predicao guiada",
        "predição guiada",
        "analise guiada",
        "análise guiada",
        "sistematizacao",
        "sistematização",
        "foco no conteudo",
        "foco no conteúdo",
        "pause e responda",
        "na pratica",
        "na prática",
        "producao textual",
        "produção textual",
        "revisao orientada",
        "revisão orientada",
        "escrita da versao final",
        "escrita da versão final",
        "submissao e socializacao",
        "submissão e socialização",
        "revisao e fechamento",
        "revisão e fechamento",
        "encerramento",
    }
    linhas = [linha.rstrip() for linha in str(texto or "").splitlines()]
    blocos = []
    atual = None

    for linha in linhas:
        limpa = linha.strip()
        if not limpa:
            continue

        match = re.match(r"^([^:]{2,90}):\s*(.*)$", limpa)
        titulo_chave = _normalizar(match.group(1)) if match else ""
        if match and titulo_chave in {_normalizar(t) for t in titulos_validos}:
            titulo = match.group(1).strip()
            corpo = match.group(2).strip()
            if atual:
                atual["texto"] = " ".join(atual["texto"]).strip()
                blocos.append(atual)
            atual = {"titulo": titulo, "texto": [corpo] if corpo else []}
            continue

        if atual:
            atual["texto"].append(limpa)
        else:
            atual = {"titulo": "Desenvolvimento", "texto": [limpa]}

    if atual:
        atual["texto"] = " ".join(atual["texto"]).strip()
        blocos.append(atual)

    return [bloco for bloco in blocos if bloco.get("texto")]


_PADRAO_CODIGO_APRENDIZAGEM = re.compile(r"\(?((?:EM|EF)\d{2}[A-Z]{2,4}\d{0,3}[A-Z]?)\)?", flags=re.I)
_PADRAO_TURMA_METODOLOGIA = re.compile(
    r"\b(da turma|com a turma)\s+\d{1,2}\s*[º°oªa?]?\s*(?:ano|s[ée]rie|em|ef)?\s*[A-Z]?\b",
    flags=re.I,
)
_FINS_INCOMPLETOS_APRENDIZAGEM = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "em",
    "e",
    "com",
    "para",
    "por",
    "que",
}


_MARCADORES_INCOMPATIVEIS_TEMA = {
    "parasitoses": {
        "tema": [
            "esquistossomose",
            "platelminto",
            "platelmintos",
            "nematodeo",
            "nematodeos",
            "lombriga",
            "amarelao",
            "ascaris",
            "ancylostoma",
            "schistosoma",
            "parasita",
            "parasitos",
            "parasitologia",
        ],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "som",
            "sistema visual",
            "visao",
            "olho humano",
            "retina",
        ],
    },
    "virologia": {
        "tema": ["virus", "viral", "virais", "virologia", "vacina", "vacinal"],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "platelminto",
            "nematodeo",
            "lombriga",
            "esquistossomose",
        ],
    },
    "genetica_biotecnologia": {
        "tema": [
            "hereditariedade",
            "heredograma",
            "mendel",
            "dna",
            "gene",
            "genes",
            "genetica",
            "genetico",
            "biotecnologia",
            "clonagem",
            "bioetica",
            "biosseguranca",
        ],
        "bloqueados": [
            "audicao",
            "auditivo",
            "decibeis",
            "poluicao sonora",
            "caminho do som",
            "sistema digestorio",
            "digestao",
            "grupos alimentares",
            "cardapio",
        ],
    },
}


def _trecho_incompleto_aprendizagem(texto: str) -> bool:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return True
    normalizado = _normalizar(texto)
    if any(marcador in texto for marcador in ["⬅", "←", "→"]):
        return True
    if "http" in normalizado or "disponivel em" in normalizado:
        return True
    if texto.endswith((",", ";", ":", "/", "-")):
        return True
    if texto.count("(") > texto.count(")") or texto.count("[") > texto.count("]"):
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and _normalizar(palavras[-1]) in _FINS_INCOMPLETOS_APRENDIZAGEM:
        return True
    if texto.count("?") >= 2 or re.match(r"^(?:o que|como|por que|qual)\b", normalizado):
        return True
    return len(texto) > 700


def _texto_incompativel_com_tema(texto: str, tema: str, conceito: str = "") -> bool:
    base_tema = _normalizar(f"{tema} {conceito}")
    base_texto = _normalizar(texto)
    if not base_texto or not base_tema:
        return False
    if _texto_tem_dominio_visao(base_texto) and not _tema_permite_dominio_visao(base_tema):
        return True
    if _texto_tem_dominio_audicao(base_texto) and not _tema_permite_dominio_audicao(base_tema):
        return True
    if _texto_tem_anatomia_especifica(base_texto) and not _tema_permite_anatomia_especifica(base_tema):
        return True
    if _tema_virus_celulas(base_tema) and _texto_tem_vacinacao(base_texto):
        return True
    for regra in _MARCADORES_INCOMPATIVEIS_TEMA.values():
        if any(marcador in base_tema for marcador in regra["tema"]):
            return any(marcador in base_texto for marcador in regra["bloqueados"])
    return False


def _texto_tem_dominio_visao(texto_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|olhos|retina|cornea|pupila|cristalino|sistema visual|caminho da luz|formacao da imagem|estruturas do olho|visao)\b",
            texto_normalizado,
            flags=re.I,
        )
    )


def _tema_permite_dominio_visao(tema_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:olho|olhos|retina|cornea|pupila|cristalino|sistema visual|caminho da luz|formacao da imagem|visao)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _texto_tem_dominio_audicao(texto_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:audicao|ouvido|ouvidos|decibel|decibeis|poluicao sonora|caminho do som|sistema auditivo|protecao auditiva)\b",
            texto_normalizado,
            flags=re.I,
        )
    )


def _tema_permite_dominio_audicao(tema_normalizado: str) -> bool:
    return bool(
        re.search(
            r"\b(?:audicao|ouvido|ouvidos|decibel|decibeis|poluicao sonora|som|sistema auditivo|auditiva)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _texto_tem_anatomia_especifica(texto_normalizado: str) -> bool:
    return any(
        marcador in texto_normalizado
        for marcador in [
            "esquema anatomico",
            "nomear oralmente cada estrutura",
            "nomes das estruturas",
            "legenda",
        ]
    )


def _tema_permite_anatomia_especifica(tema_normalizado: str) -> bool:
    return bool(
        _tema_permite_dominio_visao(tema_normalizado)
        or _tema_permite_dominio_audicao(tema_normalizado)
        or re.search(
            r"\b(?:sistema respiratorio|pulmao|pulmoes|hematose|ventilacao pulmonar|sistema digestorio|corpo humano|anatomia|fisiologico|fisiologicos)\b",
            tema_normalizado,
            flags=re.I,
        )
    )


def _tema_virus_celulas(tema_normalizado: str) -> bool:
    return "virus" in tema_normalizado and any(
        termo in tema_normalizado
        for termo in ["celula", "celulas", "capsideo", "metabolismo", "intracelular", "bacteriofago"]
    )


def _texto_tem_vacinacao(texto_normalizado: str) -> bool:
    return any(termo in texto_normalizado for termo in ["vacinacao", "vacina", "vacinal", "cobertura vacinal", "mutacao"])


def _foco_limpo_aprendizagem(tema: str, conceito: str = "") -> str:
    for candidato in [tema, conceito, "o tema da aula"]:
        texto = re.sub(r"\s+", " ", str(candidato or "")).strip(" .:-")
        if texto and not _trecho_incompleto_aprendizagem(texto):
            return texto[:140]
    return "o tema da aula"


def _conceito_generico_ou_quebrado_projeto_vida(conceito: str) -> bool:
    base = _normalizar(conceito)
    if not base:
        return True
    if any(
        marcador in base
        for marcador in [
            "questao essencial",
            "habilidade",
            "competencia",
            "competencias",
            "tema da aula",
            "conteudo da aula",
        ]
    ):
        return True
    ultimo = base.split()[-1]
    return ultimo in {"a", "as", "o", "os", "de", "da", "do", "e", "em", "com", "para", "por"}


def _aprendizagem_padrao_projeto_vida(tema: str) -> str:
    foco = _foco_limpo_aprendizagem(tema, tema)
    if _normalizar(foco) == "o tema da aula":
        foco = re.sub(r"\s+", " ", str(tema or "")).strip(" .:-") or "o ambiente digital"
    base = _normalizar(foco)
    if any(termo in base for termo in ["post", "postar", "public", "print", "rede", "digital", "internet", "online"]):
        return (
            f"Refletir sobre {foco}, analisando escolhas, exposicao, respeito, responsabilidade e "
            "consequencias das acoes no ambiente digital."
        )
    return (
        f"Refletir sobre {foco}, relacionando o tema a escolhas, atitudes, convivencia respeitosa, "
        "autoconhecimento e tomada de decisao responsavel."
    )


def _remover_residuos_aprendizagem(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    padroes_corte = [
        r"\bTrilha\b",
        r"\bPr[aá]tica de linguagem\b",
        r"\bSUGEST[OÕ]ES PARA CONDU[ÇC][AÃ]O\b",
        r"\bAULA\s+\d+\b",
        r"\b\d+\.\s+(?:Disparo inicial|Leitura|Formula[çc][aã]o|An[aá]lise|Sistematiza[çc][aã]o|Produ[çc][aã]o|Revis[aã]o)\b",
        r"\s[●•]\s",
    ]
    for padrao in padroes_corte:
        match = re.search(padrao, texto, flags=re.I)
        if match and match.start() > 20:
            return texto[:match.start()].strip(" .;:-")
    return texto


def _sanitizar_aprendizagem(aprendizagem: str, tema: str, conceito: str = "", perfil: str = "") -> str:
    texto = _remover_residuos_aprendizagem(aprendizagem)
    texto = re.sub(
        r"^(?:C\d+\s*:\s*)?(?:Habilidades?\s+BNCC\s+e\s+Curr[ií]culo\s+Paulista|Habilidades?|Aprendizagem essencial|Compet[eê]ncia)\s*:\s*",
        "",
        texto,
        flags=re.I,
    ).strip()
    texto = re.sub(
        r"^(?:Habilidades?\s+BNCC\s+e\s+Curr[ií]culo\s+Paulista)\s*",
        "",
        texto,
        flags=re.I,
    ).strip()
    texto = re.sub(r"^(?:Habilidades?)\s*:\s*", "", texto, flags=re.I).strip()
    match = _PADRAO_CODIGO_APRENDIZAGEM.search(texto)
    codigo = f"({match.group(1).upper()})" if match else ""

    if (
        perfil in {"projeto_de_vida", "lideranca_oratoria"}
        and (
            _trecho_incompleto_aprendizagem(texto)
            or _texto_incompativel_com_tema(texto, tema, conceito)
            or "desenvolver habilidades relacionadas ao tema da aula" in _normalizar(texto)
        )
    ):
        if codigo:
            return f"Habilidade: {codigo} {_aprendizagem_padrao_projeto_vida(tema)}"
        return _aprendizagem_padrao_projeto_vida(tema)

    if _trecho_incompleto_aprendizagem(texto) or _texto_incompativel_com_tema(texto, tema, conceito):
        foco = _foco_limpo_aprendizagem(tema, conceito)
        if codigo:
            return f"Habilidade: {codigo} Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."
        return f"Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."

    if codigo and not texto.lower().startswith("habilidade:"):
        texto = f"Habilidade: {texto}"
    return texto


def _texto_habilidade_invalido_ou_truncado(texto: str) -> bool:
    base = _normalizar(texto)
    if not base:
        return True

    texto_limpo = re.sub(r"^habilidade:\s*", "", texto.strip(), flags=re.I)
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto_limpo)
    if not palavras:
        return True

    ultimo = _normalizar(palavras[-1])
    if ultimo in {"a", "as", "o", "os", "de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "que"}:
        return True

    if len(texto_limpo) < 30:
        return True

    if texto_limpo[:1].islower():
        return True

    if _trecho_incompleto_aprendizagem(texto_limpo):
        return True

    return False


def _sintetizar_objetivos_e_conteudos_para_aprendizagem(
    tema: str,
    objetivos: list[str] | None = None,
    conteudos: list[str] | None = None,
    perfil: str = "",
) -> str:
    objetivos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (objetivos or []) if str(x or "").strip()]
    conteudos = [re.sub(r"\s+", " ", str(x or "")).strip(" .;:-") for x in (conteudos or []) if str(x or "").strip()]

    foco_tema = _foco_limpo_aprendizagem(tema, " ".join(conteudos[:2]))

    if perfil == "geografia":
        if objetivos:
            verbo_base = objetivos[0]
            verbo_base = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar)\s+", lambda m: m.group(1).capitalize() + " ", verbo_base, flags=re.I)
            complemento = ""
            if len(objetivos) > 1:
                complemento = objetivos[1]
                complemento = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar)\s+", "", complemento, flags=re.I)
                complemento = complemento[:180].rstrip(" .;:-")
                if complemento:
                    return f"{verbo_base.rstrip(' .;:-')}, {complemento}."
            return verbo_base.rstrip(" .;:-") + "."

        if conteudos:
            return f"Analisar criticamente aspectos relacionados a {foco_tema}, com base nos conteúdos e discussões propostos no material."

        return f"Analisar criticamente aspectos relacionados a {foco_tema}, relacionando o tema aos conceitos centrais da aula."

    if objetivos:
        base = objetivos[0].rstrip(" .;:-")
        if len(objetivos) > 1:
            segundo = re.sub(r"^(identificar|analisar|reconhecer|interpretar|comparar|avaliar|explicar|aplicar|justificar)\s+", "", objetivos[1], flags=re.I).rstrip(" .;:-")
            if segundo:
                return f"{base}, {segundo}."
        return base + "."

    if conteudos:
        return f"Compreender e analisar conceitos relacionados a {foco_tema}, articulando os conteúdos trabalhados no material."

    return f"Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco_tema}."


def _montar_aprendizagem_inteligente(
    habilidade_pdf: str,
    tema: str,
    conceito: str,
    perfil: str,
    objetivos_secao: list[str] | None = None,
    conteudos_secao: list[str] | None = None,
) -> str:
    habilidade_pdf = re.sub(r"\s+", " ", str(habilidade_pdf or "")).strip()

    if habilidade_pdf and not _texto_habilidade_invalido_ou_truncado(habilidade_pdf):
        return _sanitizar_aprendizagem(habilidade_pdf, tema, conceito, perfil=perfil)

    fallback = _sintetizar_objetivos_e_conteudos_para_aprendizagem(
        tema=tema,
        objetivos=objetivos_secao,
        conteudos=conteudos_secao,
        perfil=perfil,
    )
    return _sanitizar_aprendizagem(fallback, tema, conceito, perfil=perfil)


def _fallback_acompanhamento_tema(tema: str, perfil: str) -> list[str]:
    base = _normalizar(tema)
    if any(termo in base for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]):
        return [
            "☑ Verificar se os estudantes identificam agente causador, ciclo de vida, formas de transmissão e principais sintomas da parasitose estudada.",
            "☑ Observar se relacionam saneamento básico, prevenção e promoção da saúde às medidas de controle da doença.",
            "☑ Conferir se os registros utilizam vocabulário científico adequado e organizam relações entre hospedeiro, ambiente e profilaxia.",
        ]
    if _tema_virus_celulas(base):
        return [
            "☑ Verificar se os estudantes comparam vírus e células, identificando capsídeo, material genético, organelas e metabolismo.",
            "☑ Observar se interpretam imagens, esquemas ou tabelas para diferenciar seres vivos, células e vírus.",
            "☑ Conferir se os registros justificam por que os vírus dependem de células para se multiplicar.",
        ]
    if any(termo in base for termo in ["virus", "viral", "virais", "virologia", "vacina", "vacinal"]):
        return [
            "☑ Verificar se os estudantes relacionam vírus, mutações, vacinação e prevenção com base nos exemplos discutidos.",
            "☑ Observar se interpretam imagens, dados ou situações-problema para explicar a importância da cobertura vacinal.",
            "☑ Conferir se os registros usam vocabulário científico adequado e justificam relações entre saúde individual e coletiva.",
        ]
    if any(termo in base for termo in ["hereditariedade", "heredograma", "mendel", "dna", "gene", "genes", "genetica", "biotecnologia", "clonagem", "bioetica", "biosseguranca"]):
        return [
            f"☑ Verificar se os estudantes relacionam {tema} aos conceitos de hereditariedade, variabilidade genética ou biotecnologia trabalhados na aula.",
            "☑ Observar se utilizam evidências, esquemas, cruzamentos ou dados do material para justificar as respostas.",
            "☑ Conferir se os registros apresentam vocabulário científico adequado e conexões coerentes entre conceito, exemplo e conclusão.",
        ]
    if perfil in {"biologia", "ciencias_ef"}:
        return [
            f"☑ Verificar se os estudantes compreendem os conceitos biológicos relacionados a {tema}.",
            "☑ Observar participação, registros, interpretação de imagens ou esquemas e uso de evidências durante a aula.",
            "☑ Conferir se as respostas apresentam vocabulário científico e medidas coerentes de prevenção, cuidado ou análise.",
        ]
    return [
        f"☑ Verificar se os estudantes compreendem os conceitos centrais relacionados a {tema}.",
        "☑ Observar a participação, os registros e a forma como justificam respostas durante as atividades propostas.",
        "☑ Conferir se as produções finais retomam o tema da aula com clareza, coerência e autonomia progressiva.",
    ]


def _fallback_acessibilidade_tema(tema: str, perfil: str) -> list[str]:
    base = _normalizar(tema)
    if any(termo in base for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]):
        return [
            "☑ Utilizar esquema ampliado do ciclo de vida do parasita, destacando agente causador, hospedeiro, transmissão e prevenção.",
            "☑ Disponibilizar banco de palavras com termos como saneamento, profilaxia, hospedeiro, contaminação e tratamento.",
            "☑ Conduzir leitura guiada das imagens e comandos, permitindo registro por tópicos, setas ou desenho esquemático.",
        ]
    if _tema_virus_celulas(base):
        return [
            "☑ Ampliar esquemas comparativos entre vírus e células, destacando capsídeo, material genético, organelas e metabolismo.",
            "☑ Disponibilizar banco de palavras com termos como vírus, célula, capsídeo, material genético, organela e metabolismo.",
            "☑ Organizar a comparação em tabela ou tópicos, com leitura mediada dos comandos e retomada coletiva das diferenças.",
        ]
    if any(termo in base for termo in ["virus", "viral", "virais", "virologia", "vacina", "vacinal"]):
        return [
            "☑ Apresentar imagens e esquemas simples sobre vírus, mutações e vacinação antes da atividade individual.",
            "☑ Disponibilizar banco de palavras com termos como vírus, vacina, mutação, imunização e cobertura vacinal.",
            "☑ Organizar as respostas em etapas curtas, com leitura mediada dos comandos e síntese coletiva no quadro.",
        ]
    if any(termo in base for termo in ["hereditariedade", "heredograma", "mendel", "dna", "gene", "genes", "genetica", "biotecnologia", "clonagem", "bioetica", "biosseguranca"]):
        return [
            "â˜‘ Disponibilizar esquemas ampliados, quadros de cruzamento ou roteiros visuais para apoiar a leitura dos conceitos genÃ©ticos.",
            "â˜‘ Oferecer banco de palavras com termos como DNA, gene, alelo, heredograma, hereditariedade, biotecnologia e evidÃªncia.",
            "â˜‘ Permitir registro por desenho, tabela, setas ou frases curtas, com mediaÃ§Ã£o na interpretaÃ§Ã£o dos comandos.",
        ]
    if perfil in {"biologia", "ciencias_ef"}:
        return [
            "☑ Utilizar imagens, esquemas e exemplos do cotidiano para apoiar a compreensão dos conceitos científicos.",
            "☑ Destacar palavras-chave no quadro e orientar registros por tópicos, setas ou frases curtas.",
            "☑ Oferecer mediação individual e retomada coletiva dos comandos antes da atividade principal.",
        ]
    return [
        "☑ Disponibilizar roteiro, palavras-chave ou perguntas orientadoras para apoiar a compreensão da atividade.",
        "☑ Permitir diferentes formas de registro, como tópicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        "☑ Realizar retomadas coletivas dos comandos e oferecer mediação individual conforme as necessidades observadas.",
    ]


def _normalizar_itens_contextuais(
    acompanhamento: list[str],
    acessibilidade: list[str],
    tema: str,
    perfil: str,
) -> tuple[list[str], list[str]]:
    acomp = list(acompanhamento or [])
    acess = list(acessibilidade or [])
    base_tema = _normalizar(tema)
    tema_parasitologia = any(
        termo in base_tema
        for termo in ["esquistossomose", "platelminto", "nematodeo", "lombriga", "amarelao", "parasita"]
    )
    termos_parasitologia = ["parasita", "parasit", "saneamento", "profilax", "hospedeiro", "transmissao", "doenca"]
    if any(_texto_incompativel_com_tema(item, tema) for item in acomp):
        fallback = _fallback_acompanhamento_tema(tema, perfil)
        if fallback:
            acomp = fallback
    if any(_texto_incompativel_com_tema(item, tema) for item in acess):
        fallback = _fallback_acessibilidade_tema(tema, perfil)
        if fallback:
            acess = fallback
    if tema_parasitologia:
        texto_acomp = _normalizar(" ".join(acomp))
        texto_acess = _normalizar(" ".join(acess))
        if texto_acomp and not any(termo in texto_acomp for termo in termos_parasitologia):
            fallback = _fallback_acompanhamento_tema(tema, perfil)
            if fallback:
                acomp = fallback
        if texto_acess and not any(termo in texto_acess for termo in termos_parasitologia):
            fallback = _fallback_acessibilidade_tema(tema, perfil)
            if fallback:
                acess = fallback
    return acomp, acess


def _remover_turma_metodologia(texto: str) -> str:
    return _PADRAO_TURMA_METODOLOGIA.sub(lambda m: m.group(1), str(texto or ""))


def _indice_variacao(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(parte or "") for parte in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


def _escolher_variacao(opcoes: list[str], partes: list[str]) -> str:
    return opcoes[_indice_variacao(partes, len(opcoes))]


_VARIACOES_INICIO_METODOLOGIA = [
    (
        r"^Retomar conhecimentos previos",
        [
            "Retomar conhecimentos previos",
            "Mobilizar conhecimentos previos",
            "Ativar conhecimentos previos",
            "Iniciar pela retomada dos conhecimentos previos",
        ],
    ),
    (
        r"^Retomar conhecimentos prévios",
        [
            "Retomar conhecimentos prévios",
            "Mobilizar conhecimentos prévios",
            "Ativar conhecimentos prévios",
            "Iniciar pela retomada dos conhecimentos prévios",
        ],
    ),
    (
        r"^Promover discussao",
        [
            "Promover discussao",
            "Abrir dialogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Promover discussão",
        [
            "Promover discussão",
            "Abrir diálogo",
            "Conduzir conversa",
            "Organizar troca de ideias",
        ],
    ),
    (
        r"^Apresentar",
        [
            "Apresentar",
            "Introduzir",
            "Explorar",
            "Contextualizar",
        ],
    ),
    (
        r"^Realizar leitura guiada",
        [
            "Realizar leitura guiada",
            "Conduzir leitura guiada",
            "Mediar a leitura guiada",
            "Organizar leitura orientada",
        ],
    ),
    (
        r"^Conduzir leitura",
        [
            "Conduzir leitura",
            "Mediar leitura",
            "Organizar leitura",
            "Orientar leitura",
        ],
    ),
    (
        r"^Analisar",
        [
            "Analisar",
            "Explorar",
            "Examinar",
            "Investigar com a turma",
        ],
    ),
    (
        r"^Explicar",
        [
            "Explicar",
            "Desenvolver a explicacao sobre",
            "Construir a explicacao de",
            "Apresentar de forma progressiva",
        ],
    ),
    (
        r"^Orientar",
        [
            "Orientar",
            "Acompanhar",
            "Conduzir",
            "Mediar",
        ],
    ),
    (
        r"^Socializar",
        [
            "Socializar",
            "Compartilhar coletivamente",
            "Promover a socializacao de",
            "Retomar com a turma",
        ],
    ),
    (
        r"^Sistematizar",
        [
            "Sistematizar",
            "Organizar",
            "Registrar de forma coletiva",
            "Consolidar",
        ],
    ),
    (
        r"^Finalizar com",
        [
            "Finalizar com",
            "Concluir com",
            "Encaminhar o fechamento com",
            "Organizar uma sintese final com",
        ],
    ),
    (
        r"^Encerrar com",
        [
            "Encerrar com",
            "Fechar a aula com",
            "Concluir com",
            "Promover o encerramento com",
        ],
    ),
    (
        r"^Retomar a importancia",
        [
            "Retomar a importancia",
            "Destacar, no fechamento, a importancia",
            "Conduzir uma sintese sobre a importancia",
            "Fechar a aula reforcando a importancia",
        ],
    ),
    (
        r"^Retomar a importância",
        [
            "Retomar a importância",
            "Destacar, no fechamento, a importância",
            "Conduzir uma síntese sobre a importância",
            "Fechar a aula reforçando a importância",
        ],
    ),
]


def _variar_inicio_etapa(texto: str, partes_seed: list[str]) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return ""

    for padrao, opcoes in _VARIACOES_INICIO_METODOLOGIA:
        if re.search(padrao, texto, flags=re.IGNORECASE):
            escolha = _escolher_variacao(opcoes, partes_seed + [padrao, texto[:160]])
            return re.sub(padrao, escolha, texto, count=1, flags=re.IGNORECASE)
    return texto


def _colocar_aspas_no_titulo(texto: str, titulo: str) -> str:
    texto_final = str(texto or "")
    titulo = str(titulo or "").strip()
    if len(titulo) < 4:
        return texto_final

    padrao = re.compile(rf'(?<!["“]){re.escape(titulo)}(?!["”])', flags=re.I)
    return padrao.sub(lambda match: f'"{match.group(0)}"', texto_final)


def _variar_linguagem_metodologia(metodologia, disciplina: str, turma: str, tema: str):
    """Aplica variacao linguistica controlada sem alterar a estrutura pedagogica."""
    variadas = []
    for idx, item in enumerate(metodologia or []):
        if not isinstance(item, dict):
            variadas.append(item)
            continue

        titulo = str(item.get("titulo", "")).strip()
        texto = str(item.get("texto", "")).strip()
        texto_variado = _variar_inicio_etapa(
            texto,
            [disciplina, turma, tema, titulo, str(idx)],
        )
        texto_variado = _remover_turma_metodologia(texto_variado)
        texto_variado = _colocar_aspas_no_titulo(texto_variado, tema)
        texto_variado = ajustar_verbos_para_infinitivo(texto_variado)
        novo_item = dict(item)
        novo_item["texto"] = texto_variado
        variadas.append(novo_item)
    return variadas


def _acompanhamento_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        f"Verificar se os estudantes compreendem os conceitos centrais relacionados a {tema} durante as discussões e atividades propostas.",
        "Observar a participação, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
        "Acompanhar se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
    ]

    if perfil == "matematica":
        return [
            f"Verificar se os estudantes identificam corretamente os elementos matemáticos envolvidos em {tema} e organizam estratégias coerentes de resolução.",
            "Observar se os estudantes utilizam adequadamente procedimentos, propriedades e registros matemáticos durante as resoluções.",
            "Acompanhar se os estudantes interpretam os resultados encontrados e conseguem justificar os caminhos escolhidos ao longo das atividades.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            f"Verificar se os estudantes compreendem as ideias centrais de {tema} e identificam os elementos textuais trabalhados na aula.",
            "Observar a participação nas leituras, discussões e registros, considerando a capacidade de argumentar, interpretar e revisar as respostas.",
            "Acompanhar se os estudantes aplicam as estratégias de leitura, análise ou produção textual com progressiva autonomia.",
        ]

    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return [
            f"Verificar se os estudantes relacionam {tema} aos conceitos científicos trabalhados e utilizam evidências para sustentar suas respostas.",
            "Observar a participação nas investigações, registros e socializações, considerando a clareza das hipóteses e explicações apresentadas.",
            "Acompanhar se os estudantes conseguem interpretar fenômenos, dados ou experimentos com base nos conceitos desenvolvidos na aula.",
        ]

    return base


def _acessibilidade_por_contexto(perfil: str, tipo: str, tema: str) -> list[str]:
    base = [
        "Disponibilizar mediação individualizada durante as atividades, adequando explicações, tempo e forma de resposta conforme as necessidades da turma.",
        "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensão dos conceitos trabalhados.",
        "Organizar intervenções com exemplos comentados e acompanhamento próximo para apoiar estudantes com dificuldades de leitura, interpretação ou organização das tarefas.",
    ]

    if perfil == "matematica":
        return [
            "Disponibilizar resolução comentada e exemplos passo a passo para favorecer a compreensão dos procedimentos matemáticos.",
            "Utilizar apoio visual e retomadas coletivas para auxiliar estudantes com dificuldades na interpretação dos problemas.",
            "Realizar acompanhamento individualizado durante as atividades, auxiliando na organização dos cálculos e identificação das operações necessárias.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            "Oferecer apoio à leitura com destaque para palavras-chave, trechos importantes e orientações passo a passo para a realização das atividades.",
            "Utilizar mediação oral, retomadas coletivas e exemplos comentados para favorecer a compreensão dos textos e comandos.",
            "Adaptar tempo, forma de registro e acompanhamento das produções conforme as necessidades observadas na turma.",
        ]

    return base


def _acompanhamento_dinamico_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acompanhamento_dinamico(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


def _acessibilidade_dinamica_contexto(
    perfil: str,
    tipo: str,
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str,
) -> list[str]:
    return gerar_acessibilidade_dinamica(
        tema=tema,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
        perfil=perfil,
        tipo=tipo,
    )


from core.inteligencia_local import SistemaGeracaoMetodologica
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.extrator_pdf import ExtratorPDF
from core.lib.metodologia import MotorMetodologico
from core.validador_plano import validar_aula_final

gerador_inteligente = SistemaGeracaoMetodologica()
_extrator_lib = ExtratorPDF()
_motor_metodologico = MotorMetodologico()


def _perfil_gerador_colunas_habilitado(perfil: str) -> bool:
    return perfil not in {"projeto_de_vida", "lideranca_oratoria", "leitura_redacao", "orientacao_estudos"}


def _tentar_gerador_colunas_pedagogicas(
    texto: str,
    titulo_aula: str,
    disciplina: str,
    turma: str,
    tema: str,
    perfil: str,
    contexto_metodologico: str,
    indice_aula: int,
    total_aulas: int,
    modalidade_eja_ativa: bool,
) -> dict | None:
    if not _perfil_gerador_colunas_habilitado(perfil):
        return None

    try:
        colunas = montar_colunas_pedagogicas(texto_pdf=texto, titulo_aula=titulo_aula)
        metodologia = list(colunas.get("metodologia_blocos") or [])
        acompanhamento = list(colunas.get("acompanhamento_aprendizagem") or [])
        acessibilidade = list(colunas.get("acessibilidade") or [])
        if not metodologia or len(acompanhamento) < 2 or len(acessibilidade) < 2:
            return None

        metodologia = _ajustar_metodologia_por_sequencia(
            metodologia,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
            tema=tema,
        )
        metodologia, _ = revisar_metodologia(
            metodologia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia = naturalizar_metodologia_professor(metodologia)
        if modalidade_eja_ativa:
            tecnicas_pdf = _detectar_tecnicas_lemov(texto, tema)
            metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_pdf)

        return {
            "metodologia": metodologia,
            "acompanhamento": acompanhamento,
            "acessibilidade": acessibilidade,
            "pistas_pdf": colunas.get("pistas"),
        }
    except Exception:
        return None


def _aula_por_pdf(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    usar_ia: bool,
    provedor_ia: str,
    modelo_ia: str = "",
    indice_aula: int = 0,
    total_aulas: int = 1,
    modalidade_eja: bool = False,
) -> dict:
    texto = _extrair_texto_pdf(caminho_pdf)
    tema = _tema_por_texto(texto, caminho_pdf, disciplina)
    material_digital = _material_digital_por_texto(texto, caminho_pdf, disciplina, tema)
    numero_aula = _rotulo_aula_material(texto, caminho_pdf).replace("AULA", "", 1).strip()
    cdp_contextual = _eh_cdp_contextual_disciplina(disciplina)
    disciplina_base = _disciplina_base_cdp_contextual(texto, tema, caminho_pdf) if cdp_contextual else disciplina
    perfil = _perfil_disciplina(disciplina_base)
    if perfil == "orientacao_estudos":
        etapas_orientacao = _extrair_etapas_orientacao_estudos(texto)
        if etapas_orientacao:
            idx_etapa = min(max(indice_aula, 0), len(etapas_orientacao) - 1)
            etapa_atual = etapas_orientacao[idx_etapa]
            texto = etapa_atual["texto"]
            rotulo_etapa = etapa_atual["titulo"].upper()
            tema = rotulo_etapa
            material_digital = rotulo_etapa
    extracao_pdf = _extrator_lib.extrair(texto, tema)
    texto_prioritario_pdf = extracao_pdf.get("texto_prioritario") or texto
    tipo = _detectar_tipo_aula(texto_prioritario_pdf, tema, disciplina_base)
    metodologia_fixa_pdf = _metodologia_fixa_pdf_especial(texto, disciplina_base, tema)
    modalidade_eja_ativa = bool(modalidade_eja and _perfil_suporta_eja(perfil))
    contexto_metodologico = "eja_regular" if modalidade_eja_ativa else detectar_contexto_metodologico(texto, caminho_pdf, disciplina_base, turma)
    escopo_pv = buscar_item_projeto_vida(turma, bimestre, numero_aula) if perfil == "projeto_de_vida" else {}
    aprendizagem_pv = montar_aprendizagem_projeto_vida(escopo_pv) if escopo_pv else ""
    if escopo_pv.get("titulo"):
        tema = escopo_pv["titulo"]
        material_digital = f"AULA {int(numero_aula)} - {tema}" if numero_aula.isdigit() else tema

    if cdp_contextual:
        extracao_cdp = extracao_pdf
        conceito_cdp = extracao_cdp.get("conceito_extraido", tema)
        habilidade_cdp = extracao_cdp.get("habilidade", "")
        if habilidade_cdp and len(habilidade_cdp) > 15:
            aprendizagem_cdp = habilidade_cdp
        else:
            foco_cdp = _foco_limpo_aprendizagem(
                _limpar_tema_cdp_contextual(tema, disciplina_base),
                _limpar_tema_cdp_contextual(conceito_cdp, disciplina_base),
            )
            aprendizagem_cdp = f"Compreender e aplicar conceitos relacionados a {foco_cdp}, realizando registros e resoluções com apoio do professor."
        return {
            "disciplina": disciplina_base,
            "tema": tema,
            "material": _formatar_material_cdp_contextual(tema, disciplina_base),
            "numero_aula": numero_aula,
            "aprendizagem": _sanitizar_aprendizagem(aprendizagem_cdp, tema, conceito_cdp, perfil=perfil),
            "metodologia": _metodologia_cdp_contextual(
                perfil,
                tipo,
                tema,
                conceito_cdp,
                indice_aula,
                texto_pdf=texto,
                extracao_pdf=extracao_pdf,
                disciplina_base=disciplina_base,
            ),
            "acompanhamento": _acompanhamento_cdp_contextual(perfil, tema, conceito_cdp, indice_aula),
            "acessibilidade": _acessibilidade_cdp_contextual(perfil, tema, conceito_cdp, indice_aula),
            "ia_usada": False,
            "ia_provedor": "",
            "ia_erro": "",
        }
    
    ia_usada = False
    ia_erro = ""
    
    # 1. Tentar processar com IA
    if usar_ia:
        try:
            from core.ia import processar_plano_ia
            plano_ia = processar_plano_ia(texto, disciplina, turma, provedor_ia, modelo_ia, modalidade_eja=modalidade_eja_ativa)
            tema = tema if escopo_pv.get("titulo") else plano_ia.get("tema") or tema
            extracao = _extrator_lib.extrair(texto, tema)
            tipo = _detectar_tipo_aula(extracao.get("texto_prioritario") or texto, tema, disciplina_base)
            habilidade_pdf = extracao.get("habilidade", "")
            objetivos_secao = extracao.get("objetivos_secao") or []
            conteudos_secao = extracao.get("conteudos_secao") or []
            if aprendizagem_pv:
                aprendizagem = aprendizagem_pv
            else:
                aprendizagem = _montar_aprendizagem_inteligente(
                    habilidade_pdf=habilidade_pdf or plano_ia.get("aprendizagem", ""),
                    tema=tema,
                    conceito=extracao.get("conceito_extraido", tema),
                    perfil=perfil,
                    objetivos_secao=objetivos_secao,
                    conteudos_secao=conteudos_secao,
                )
            colunas_planejamento = _tentar_gerador_colunas_pedagogicas(
                texto=texto,
                titulo_aula=material_digital or tema,
                disciplina=disciplina_base,
                turma=turma,
                tema=tema,
                perfil=perfil,
                contexto_metodologico=contexto_metodologico,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                modalidade_eja_ativa=modalidade_eja_ativa,
            )

            if metodologia_fixa_pdf:
                metodologia = metodologia_fixa_pdf
                desenvolvimento = _texto_metodologia(metodologia)
                etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
                acompanhamento = gerar_acompanhamento_aprimorado(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    habilidade=habilidade_pdf, etapas_metodologia=etapas_titulos,
                )
                acessibilidade = gerar_acessibilidade_aprimorada(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    recursos_detectados=extracao.get("recursos_detectados"),
                )
                acompanhamento, acessibilidade = _normalizar_itens_contextuais(
                    acompanhamento,
                    acessibilidade,
                    tema,
                    perfil,
                )
            elif colunas_planejamento:
                metodologia = colunas_planejamento["metodologia"]
                if modalidade_eja_ativa:
                    tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
                    metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf)
                desenvolvimento = _texto_metodologia(metodologia)
                acompanhamento = colunas_planejamento["acompanhamento"]
                acessibilidade = colunas_planejamento["acessibilidade"]
                acompanhamento, acessibilidade = _normalizar_itens_contextuais(
                    acompanhamento,
                    acessibilidade,
                    tema,
                    perfil,
                )
            else:
                metodologia = plano_ia.get("metodologia", [])
                tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
                if perfil == "leitura_redacao":
                    metodologia = _metodologia_leitura_redacao_modelo(texto, tema)
                if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
                    metodologia = _garantir_tecnicas_lemov_na_metodologia(metodologia, tecnicas_lemov_pdf)
                metodologia = _variar_linguagem_metodologia(metodologia, disciplina_base, turma, tema)
                if perfil != "leitura_redacao":
                    metodologia = _ajustar_metodologia_por_sequencia(
                        metodologia,
                        indice_aula=indice_aula,
                        total_aulas=total_aulas,
                        tema=tema,
                    )
                metodologia, _ = revisar_metodologia(
                    metodologia,
                    perfil=perfil,
                    tema=tema,
                    contexto=contexto_metodologico,
                )
                metodologia = naturalizar_metodologia_professor(metodologia)
                metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf) if modalidade_eja_ativa else metodologia

                desenvolvimento = _texto_metodologia(metodologia)
                etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
                acompanhamento = gerar_acompanhamento_aprimorado(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    habilidade=habilidade_pdf,
                    etapas_metodologia=etapas_titulos,
                )
                acessibilidade = gerar_acessibilidade_aprimorada(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    recursos_detectados=extracao.get("recursos_detectados"),
                )
                acompanhamento, acessibilidade = _normalizar_itens_contextuais(
                    acompanhamento,
                    acessibilidade,
                    tema,
                    perfil,
                )
            
            aula_gerada = {
                "disciplina": disciplina_base,
                "tema": tema,
                "material": material_digital,
                "numero_aula": numero_aula,
                "aprendizagem": aprendizagem,
                "metodologia": metodologia,
                "acompanhamento": acompanhamento,
                "acessibilidade": acessibilidade,
                "ia_usada": True,
                "ia_provedor": provedor_ia,
                "ia_erro": "",
            }
            aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
            return aula_gerada
        except Exception as e:
            ia_erro = f"Falha na IA ({provedor_ia}): {str(e)[:150]}. Usando motor heurístico local."
    
    # 2. Fallback heurístico — usa o motor sofisticado do lote.py
    #    em vez do motor fraco do inteligencia_local.py
    # Extrair dados estruturados do PDF
    extracao = _extrator_lib.extrair(texto, tema)
    tipo = _detectar_tipo_aula(extracao.get("texto_prioritario") or texto, tema, disciplina_base)
    conceito = extracao.get("conceito_extraido", tema)
    habilidade = extracao.get("habilidade", "")
    recursos = extracao.get("recursos_detectados", [])
    objetivos_secao = extracao.get("objetivos_secao") or []
    conteudos_secao = extracao.get("conteudos_secao") or []
    
    # Se o extrator encontrou uma habilidade/BNCC no PDF, usa ela diretamente
    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
        habilidade = aprendizagem_pv
    else:
        aprendizagem = _montar_aprendizagem_inteligente(
            habilidade_pdf=habilidade,
            tema=tema,
            conceito=conceito,
            perfil=perfil,
            objetivos_secao=objetivos_secao,
            conteudos_secao=conteudos_secao,
        )
    if perfil == "orientacao_estudos" and re.match(r"(?i)^etapa\s+(\d+|final)\b", str(tema or "").strip()):
        aprendizagem = (
            f"Desenvolver estratégias de leitura, interpretação e registro na {tema}, "
            "com foco em autonomia de estudo e resolução orientada das atividades."
        )

    colunas_planejamento = _tentar_gerador_colunas_pedagogicas(
        texto=texto,
        titulo_aula=material_digital or tema,
        disciplina=disciplina_base,
        turma=turma,
        tema=tema,
        perfil=perfil,
        contexto_metodologico=contexto_metodologico,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
        modalidade_eja_ativa=modalidade_eja_ativa,
    )

    if metodologia_fixa_pdf:
        metodologia = metodologia_fixa_pdf
        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    elif colunas_planejamento:
        metodologia = colunas_planejamento["metodologia"]
        if modalidade_eja_ativa:
            tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
            metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf)
        desenvolvimento = _texto_metodologia(metodologia)
        acompanhamento = colunas_planejamento["acompanhamento"]
        acessibilidade = colunas_planejamento["acessibilidade"]
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    else:
        metodologia = _montar_etapas_metodologia(
            texto,
            disciplina_base,
            turma,
            tema,
            indice_aula=indice_aula,
            total_aulas=total_aulas,
        )
        tecnicas_lemov_pdf = _detectar_tecnicas_lemov(texto, tema)
        if perfil not in {"projeto_de_vida", "lideranca_oratoria"}:
            metodologia = _garantir_tecnicas_lemov_na_metodologia(metodologia, tecnicas_lemov_pdf)
        metodologia = _variar_linguagem_metodologia(metodologia, disciplina_base, turma, tema)
        metodologia, _ = revisar_metodologia(
            metodologia,
            perfil=perfil,
            tema=tema,
            contexto=contexto_metodologico,
        )
        metodologia = naturalizar_metodologia_professor(metodologia)
        metodologia = _adaptar_metodologia_eja(metodologia, perfil, tema, texto, tecnicas_lemov_pdf) if modalidade_eja_ativa else metodologia

        desenvolvimento = _texto_metodologia(metodologia)
        etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
        acompanhamento = gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        )
        acessibilidade = gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        )
        acompanhamento, acessibilidade = _normalizar_itens_contextuais(
            acompanhamento,
            acessibilidade,
            tema,
            perfil,
        )
    
    aula_gerada = {
        "disciplina": disciplina_base,
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": acompanhamento,
        "acessibilidade": acessibilidade,
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro,
    }
    aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
    return aula_gerada


def processar_varios_pdfs(
    caminhos_pdf,
    disciplina: str,
    turma: str,
    bimestre: str = "",
    usar_ia: bool = False,
    provedor_ia: str = "",
    modelo_ia: str = "",
    dividir_metodologia: bool = False,
    dividir_por_pdf: list[bool] | None = None,
    modalidade_eja: bool = False,
) -> list[dict]:
    aulas = []
    total_aulas = len(caminhos_pdf or [])
    for idx, caminho in enumerate(caminhos_pdf or []):
        aula = _aula_por_pdf(
            caminho,
            disciplina,
            turma,
            bimestre,
            usar_ia,
            provedor_ia,
            modelo_ia,
            indice_aula=idx,
            total_aulas=total_aulas,
            modalidade_eja=modalidade_eja,
        )
        dividir_aula_atual = bool(dividir_por_pdf[idx]) if dividir_por_pdf and idx < len(dividir_por_pdf) else dividir_metodologia
        if dividir_aula_atual:
            texto = _texto_metodologia(aula["metodologia"])
            parte1, parte2 = processar_pdf_e_dividir_metodologia(texto)
            aula_primeiro = dict(aula)
            aula_primeiro["metodologia"] = _metodologia_em_blocos_por_texto(parte1)

            aula_segundo = dict(aula)
            aula_segundo["tema"] = f"{aula['tema']} - continuidade"
            aula_segundo["metodologia"] = _metodologia_em_blocos_por_texto(parte2)

            aulas.extend([aula_primeiro, aula_segundo])
        else:
            aulas.append(aula)
    return aulas
