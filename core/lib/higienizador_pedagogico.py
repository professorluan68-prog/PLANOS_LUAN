# -*- coding: utf-8 -*-
"""
Higienizador Pedagógico e de Contaminação Metodológica.

Detecta e remove termos incoerentes (como "notícia" em aulas de literatura,
"tabela/gráfico" em aulas sem dados) em desenvolvimento, acompanhamento
e acessibilidade dos planos de aula gerados pelo sistema.
"""

import re
import unicodedata

# Keywords de detecção de recursos reais (procuradas apenas no texto sem fontes/links)
RECURSOS_KEYWORDS = {
    "noticia": ["notícia", "manchete", "lide", "lead", "jornalístico", "jornal", "fato noticioso"],
    "reportagem": ["reportagem", "repórter", "jornalismo investigativo", "matéria jornalística"],
    "editorial": ["editorial", "opinião do jornal", "linha editorial"],
    "cronica": ["crônica", "cronista", "cotidiano", "voz narrativa", "olhar do cotidiano"],
    "tabela": ["tabela", "dados tabulados", "preencha a tabela", "tabelas"],
    "grafico": ["gráfico", "eixo x", "eixo y", "histograma", "gráfico de barras", "gráfico de linhas", "gráfico de pizza", "gráfico de setores", "gráficos"],
    "mapa": ["mapa", "cartográfico", "coordenadas geográficas", "mapa-múndi", "mapa do brasil", "mapas"],
    "experimento": ["experimento", "laboratório", "procedimento experimental", "materiais e métodos", "experimentos"],
}

# Fontes comuns e termos de créditos que causam falsos positivos
FONTES_NAO_RECURSO = [
    r"g1\.globo\.com", r"uol\.com\.br", r"bbc\.com", r"cnn", r"folha", r"estadao",
    r"dispon[ií]vel em\b", r"acesso em\b", r"adaptado de\b", r"fonte:\b",
    r"reprodu[cç][aã]o\b", r"imagem:\b", r"foto:\b", r"cr[eé]dito:\b"
]

# Termos de notícia/jornalísticos e suas substituições por contexto
REGRAS_SUBSTITUICAO = {
    "literatura": [
        (r"\ba not[ií]cia apresentada\b", "a obra apresentada"),
        (r"\ba not[ií]cia analisada\b", "a obra analisada"),
        (r"\ba not[ií]cia\b", "a obra"),
        (r"\bas not[ií]cias\b", "as obras"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada da obra apresentada"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada da obra apresentada"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura da obra apresentada"),
        (r"\bnot[ií]cia apresentada\b", "obra apresentada"),
        (r"\bnot[ií]cia analisada\b", "obra analisada"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do texto literário"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do texto literário"),
        (r"\bleitura da not[ií]cia\b", "leitura do texto literário"),
        (r"\bna not[ií]cia\b", "no texto literário"),
        (r"\bda not[ií]cia\b", "do texto literário"),
        (r"\bnot[ií]cia\b", "texto literário"),
        (r"\bnot[ií]cias\b", "textos literários"),
        (r"\bmanchete\b", "título do texto"),
        (r"\bmanchetes\b", "títulos"),
        (r"\blide\b", "parágrafo inicial"),
        (r"\blead\b", "introdução do texto"),
        (r"\bjornal[ií]stico\b", "literário"),
        (r"\bjornal[ií]stica\b", "literária"),
        (r"\bjornal[ií]sticos\b", "literários"),
        (r"\bjornal[ií]sticas\b", "literárias"),
        (r"\breportagem\b", "obra de referência"),
        (r"\breportagens\b", "obras de referência"),
        (r"\beditorial\b", "texto literário"),
        (r"\beditoriais\b", "textos literários"),
    ],
    "cronica": [
        (r"\ba not[ií]cia apresentada\b", "a crônica apresentada"),
        (r"\ba not[ií]cia analisada\b", "a crônica analisada"),
        (r"\ba not[ií]cia\b", "a crônica"),
        (r"\bas not[ií]cias\b", "as crônicas"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada da crônica apresentada"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada da crônica apresentada"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura da crônica apresentada"),
        (r"\bnot[ií]cia apresentada\b", "crônica apresentada"),
        (r"\bnot[ií]cia analisada\b", "crônica analisada"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada da crônica"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada da crônica"),
        (r"\bleitura da not[ií]cia\b", "leitura da crônica"),
        (r"\bna not[ií]cia\b", "na crônica"),
        (r"\bda not[ií]cia\b", "da crônica"),
        (r"\bnot[ií]cia\b", "crônica"),
        (r"\bnot[ií]cias\b", "crônicas"),
        (r"\bmanchete\b", "título da crônica"),
        (r"\bmanchetes\b", "títulos"),
        (r"\blide\b", "parágrafo inicial"),
        (r"\blead\b", "introdução da crônica"),
        (r"\bjornal[ií]stico\b", "narrativo"),
        (r"\bjornal[ií]stica\b", "narrativa"),
        (r"\bjornal[ií]sticos\b", "narrativos"),
        (r"\bjornal[ií]sticas\b", "narrativas"),
        (r"\breportagem\b", "crônica"),
        (r"\breportagens\b", "crônicas"),
        (r"\beditorial\b", "crônica"),
        (r"\beditoriais\b", "crônicas"),
    ],
    "texto_normativo": [
        (r"\ba not[ií]cia apresentada\b", "a lei apresentada"),
        (r"\ba not[ií]cia analisada\b", "a lei analisada"),
        (r"\ba not[ií]cia\b", "o texto legal"),
        (r"\bas not[ií]cias\b", "os textos legais"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do texto legal apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do texto legal apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do texto legal apresentado"),
        (r"\bnot[ií]cia apresentada\b", "lei apresentada"),
        (r"\bnot[ií]cia analisada\b", "lei analisada"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do texto legal"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do texto legal"),
        (r"\bleitura da not[ií]cia\b", "leitura do texto legal"),
        (r"\bna not[ií]cia\b", "no texto legal"),
        (r"\bda not[ií]cia\b", "do texto legal"),
        (r"\bnot[ií]cia\b", "lei ou estatuto"),
        (r"\bnot[ií]cias\b", "normas ou leis"),
        (r"\bmanchete\b", "título do artigo"),
        (r"\bmanchetes\b", "artigos"),
        (r"\blide\b", "preâmbulo da lei"),
        (r"\blead\b", "introdução do texto normativo"),
        (r"\bjornal[ií]stico\b", "legal"),
        (r"\bjornal[ií]stica\b", "legal"),
        (r"\bjornal[ií]sticos\b", "legais"),
        (r"\bjornal[ií]sticas\b", "legais"),
        (r"\breportagem\b", "legislação"),
        (r"\breportagens\b", "legislações"),
        (r"\beditorial\b", "artigo de lei"),
        (r"\beditoriais\b", "artigos de lei"),
    ],
    "artigo_opiniao": [
        (r"\ba not[ií]cia apresentada\b", "o artigo de opinião apresentado"),
        (r"\ba not[ií]cia analisada\b", "o artigo de opinião analisado"),
        (r"\ba not[ií]cia\b", "o artigo de opinião"),
        (r"\bas not[ií]cias\b", "os artigos de opinião"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do artigo de opinião apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do artigo de opinião apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do artigo de opinião apresentado"),
        (r"\bnot[ií]cia apresentada\b", "artigo de opinião apresentado"),
        (r"\bnot[ií]cia analisada\b", "artigo de opinião analisado"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do artigo de opinião"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do artigo de opinião"),
        (r"\bleitura da not[ií]cia\b", "leitura do artigo de opinião"),
        (r"\bna not[ií]cia\b", "no artigo de opinião"),
        (r"\bda not[ií]cia\b", "do artigo de opinião"),
        (r"\bnot[ií]cia\b", "artigo de opinião"),
        (r"\bnot[ií]cias\b", "artigos de opinião"),
        (r"\bmanchete\b", "título do artigo"),
        (r"\bmanchetes\b", "títulos dos artigos"),
        (r"\blide\b", "introdução do artigo"),
        (r"\blead\b", "introdução do artigo"),
        (r"\breportagem\b", "artigo de opinião"),
        (r"\breportagens\b", "artigos de opinião"),
    ],
    "editorial": [
        (r"\ba not[ií]cia apresentada\b", "o editorial apresentado"),
        (r"\ba not[ií]cia analisada\b", "o editorial analisado"),
        (r"\ba not[ií]cia\b", "o editorial"),
        (r"\bas not[ií]cias\b", "os editoriais"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do editorial apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do editorial apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do editorial apresentado"),
        (r"\bnot[ií]cia apresentada\b", "editorial apresentado"),
        (r"\bnot[ií]cia analisada\b", "editorial analisado"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do editorial"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do editorial"),
        (r"\bleitura da not[ií]cia\b", "leitura do editorial"),
        (r"\bna not[ií]cia\b", "no editorial"),
        (r"\bda not[ií]cia\b", "do editorial"),
        (r"\bnot[ií]cia\b", "editorial"),
        (r"\bnot[ií]cias\b", "editoriais"),
        (r"\bmanchete\b", "título do editorial"),
        (r"\bmanchetes\b", "títulos dos editoriais"),
        (r"\blide\b", "introdução do editorial"),
        (r"\blead\b", "introdução do editorial"),
        (r"\breportagem\b", "editorial"),
        (r"\breportagens\b", "editoriais"),
    ],
    "entrevista": [
        (r"\ba not[ií]cia apresentada\b", "a entrevista apresentada"),
        (r"\ba not[ií]cia analisada\b", "a entrevista analisada"),
        (r"\ba not[ií]cia\b", "a entrevista"),
        (r"\bas not[ií]cias\b", "as entrevistas"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada da entrevista apresentada"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada da entrevista apresentada"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura da entrevista apresentada"),
        (r"\bnot[ií]cia apresentada\b", "entrevista apresentada"),
        (r"\bnot[ií]cia analisada\b", "entrevista analisada"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada da entrevista"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada da entrevista"),
        (r"\bleitura da not[ií]cia\b", "leitura da entrevista"),
        (r"\bna not[ií]cia\b", "na entrevista"),
        (r"\bda not[ií]cia\b", "da entrevista"),
        (r"\bnot[ií]cia\b", "entrevista"),
        (r"\bnot[ií]cias\b", "entrevistas"),
        (r"\bmanchete\b", "título da entrevista"),
        (r"\bmanchetes\b", "títulos das entrevistas"),
        (r"\blide\b", "introdução da entrevista"),
        (r"\blead\b", "introdução da entrevista"),
        (r"\breportagem\b", "entrevista"),
        (r"\breportagens\b", "entrevistas"),
    ],
    "geral_nao_jornalistica": [
        (r"\ba not[ií]cia apresentada\b", "o material apresentado"),
        (r"\ba not[ií]cia analisada\b", "o conteúdo analisado"),
        (r"\ba not[ií]cia\b", "o material"),
        (r"\bas not[ií]cias\b", "os materiais"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do material apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do material apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do material apresentado"),
        (r"\bnot[ií]cia apresentada\b", "material apresentado"),
        (r"\bnot[ií]cia analisada\b", "conteúdo analisado"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do material"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do material"),
        (r"\bleitura da not[ií]cia\b", "leitura do material"),
        (r"\bna not[ií]cia\b", "no material"),
        (r"\bda not[ií]cia\b", "do material"),
        (r"\bnot[ií]cia\b", "conteúdo da aula"),
        (r"\bnot[ií]cias\b", "conteúdos da aula"),
        (r"\bmanchete\b", "título do material"),
        (r"\bmanchetes\b", "títulos do material"),
        (r"\blide\b", "introdução do tema"),
        (r"\blead\b", "introdução do tema"),
        (r"\bjornal[ií]stico\b", "didático"),
        (r"\bjornal[ií]stica\b", "didática"),
        (r"\bjornal[ií]sticos\b", "didáticos"),
        (r"\bjornal[ií]sticas\b", "didáticas"),
        (r"\breportagem\b", "material de estudo"),
        (r"\breportagens\b", "materiais de estudo"),
        (r"\beditorial\b", "material de estudo"),
        (r"\beditoriais\b", "materiais de estudo"),
    ],
}

# Recursos que exigem consistência (ordenados do mais específico ao mais genérico)
REGRAS_RECURSOS = {
    "tabela": [
        (r"\banalizar tabelas e gr[aá]ficos\b", "analisar as informações do material"),
        (r"\banalizar tabelas\b", "analisar as informações do material"),
        (r"\binterpreta[cç][aã]o de tabelas\b", "interpretação das informações"),
        (r"\bpreenchimento de tabelas\b", "registro das informações"),
        (r"\btabela real\b", "informações do material"),
        (r"\btabelas\b", "informações do material"),
        (r"\btabela\b", "informação do material"),
    ],
    "grafico": [
        (r"\banalizar tabelas e gr[aá]ficos\b", "analisar as informações do material"),
        (r"\banalizar gr[aá]ficos\b", "analisar as informações do material"),
        (r"\bgr[aá]fico real\b", "dados do material"),
        (r"\bleitura de gr[aá]fico\b", "leitura das informações"),
        (r"\bgr[aá]ficos\b", "informações do material"),
        (r"\bgr[aá]fico\b", "informação do material"),
        (r"\beixo x\b", "eixo de análise"),
        (r"\beixo y\b", "eixo de análise"),
        (r"\beixos\b", "dados de análise"),
    ],
    "mapa": [
        (r"\banalizar mapa\b", "analisar a imagem do material"),
        (r"\bleitura de mapa\b", "leitura das informações"),
        (r"\bmapa real\b", "imagem do material"),
        (r"\bmapas\b", "informações do material"),
        (r"\bmapa\b", "informação do material"),
        (r"\ban[aá]lise cartogr[aá]fica\b", "análise de informações"),
    ],
    "experimento": [
        (r"\brealizar experimento\b", "realizar a atividade prática"),
        (r"\bprocedimento experimental\b", "etapas da atividade"),
        (r"\bexperimento de laborat[oó]rio\b", "atividade do material"),
        (r"\bexperimentos\b", "atividades práticas"),
        (r"\bexperimento\b", "atividade prática"),
        (r"\blaborat[oó]rio\b", "sala de aula"),
    ]
}


def normalizar_para_busca(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def limpar_falsos_positivos_texto(texto: str) -> str:
    """Remove links, URLs e citações de fontes que acionam falsos positivos."""
    if not texto:
        return ""
    # Remover URLs como http://, https://, www., g1.globo.com...
    texto_limpo = re.sub(r'https?://\S+|www\.\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?', '', texto)
    
    # Remover linhas inteiras ou frases que parecem citações bibliográficas/créditos
    linhas = texto_limpo.split('\n')
    linhas_filtradas = []
    for linha in linhas:
        linha_norm = normalizar_para_busca(linha)
        # Se contiver marcadores de fonte
        if any(re.search(pat, linha_norm) for pat in FONTES_NAO_RECURSO):
            continue
        linhas_filtradas.append(linha)
        
    return '\n'.join(linhas_filtradas)


def detectar_recursos_reais(texto_pdf: str) -> dict:
    """Detecta a presença real de recursos no texto limpo do PDF."""
    texto_limpo = limpar_falsos_positivos_texto(texto_pdf)
    texto_norm = normalizar_para_busca(texto_limpo)
    
    recursos_detectados = {}
    for recurso, keywords in RECURSOS_KEYWORDS.items():
        presente = False
        for kw in keywords:
            kw_norm = normalizar_para_busca(kw)
            if kw_norm in texto_norm:
                presente = True
                break
        recursos_detectados[recurso] = presente
        
    return recursos_detectados


def detectar_perfil_pedagogico_real(tema: str, disciplina: str) -> str:
    """Detecta de forma estrita o perfil da aula para aplicar higienização."""
    tema_norm = normalizar_para_busca(tema)
    disc_norm = normalizar_para_busca(disciplina)
    
    # Se for Língua Portuguesa
    if "portuguesa" in disc_norm or "portugues" in disc_norm or "redacao" in disc_norm:
        if any(t in tema_norm for t in ["cronica", "cronista"]):
            return "cronica"
        if any(t in tema_norm for t in ["editorial", "editoria", "editoriais"]):
            return "editorial"
        if any(t in tema_norm for t in ["artigo de opiniao", "artigo opiniao", "construcao da opiniao"]):
            return "artigo_opiniao"
        if any(t in tema_norm for t in ["entrevista", "oralidade"]):
            return "entrevista"
        if any(t in tema_norm for t in [
            "modernismo", "modernista", "literatura", "conto", "poema", "poesia", "romance", "prosa",
            "lirico", "obra", "autor", "vanguardas", "semana de arte moderna", "primeira geracao",
            "segunda geracao", "movimentos da literatura", "o que o texto revela", "poesia da decada",
            "mario de andrade", "oswald de andrade", "drummond", "manuel bandeira",
        ]):
            return "literatura"
        if any(t in tema_norm for t in ["norma", "normas", "normativo", "legal", "constituicao", "estatuto", "lei", "decreto", "direito", "regra"]):
            return "texto_normativo"
        # Somente notícia e reportagem ficam liberadas para manter linguagem de notícia.
        if any(t in tema_norm for t in ["noticia", "reportagem", "manchete", "lide", "jornalistico"]):
            return "jornalistico_valido"
        
        # Padrão para português se não for explicitamente jornalístico é considerado literário/geral
        return "literatura"
        
    return "geral"


def higienizar_string(texto: str, perfil_pedagogico: str, recursos_reais: dict) -> str:
    """Higieniza uma string de texto usando as regras de substituição."""
    if not texto:
        return ""
        
    texto_final = texto
    
    # 1. Primeiro resolvemos a combinação "tabelas e gráficos" se ambos estiverem ausentes
    if not recursos_reais.get("tabela", False) and not recursos_reais.get("grafico", False):
        texto_final = re.sub(r"\btabelas e gr[aá]ficos\b", "as informações do material", texto_final, flags=re.I)
        texto_final = re.sub(r"\bgr[aá]ficos e tabelas\b", "as informações do material", texto_final, flags=re.I)
    
    # 2. Higienizar termos jornalísticos/notícias se o perfil não for jornalístico válido
    if perfil_pedagogico != "jornalistico_valido":
        regras = REGRAS_SUBSTITUICAO.get(perfil_pedagogico, REGRAS_SUBSTITUICAO["geral_nao_jornalistica"])
        for padrao, subst in regras:
            def substituir(match):
                match_text = match.group(0)
                if match_text.isupper():
                    return subst.upper()
                if match_text[0].isupper():
                    return subst[0].upper() + subst[1:]
                return subst
            texto_final = re.sub(padrao, substituir, texto_final, flags=re.I)
        substituto_caso = {
            "literatura": "a obra discutida",
            "cronica": "a crônica discutida",
            "texto_normativo": "o texto legal discutido",
            "artigo_opiniao": "o tema discutido",
            "editorial": "o tema discutido",
            "entrevista": "a entrevista discutida",
        }.get(perfil_pedagogico, "o tema discutido")
        texto_final = re.sub(r"\bo caso discutido\b", substituto_caso, texto_final, flags=re.I)
            
    # 3. Higienizar recursos ausentes (tabela, gráfico, mapa, experimento)
    for recurso, regras in REGRAS_RECURSOS.items():
        # Se o recurso foi marcado como ausente (ou não declarado presente)
        if not recursos_reais.get(recurso, False):
            for padrao, subst in regras:
                def substituir(match):
                    match_text = match.group(0)
                    if match_text.isupper():
                        return subst.upper()
                    if match_text[0].isupper():
                        return subst[0].upper() + subst[1:]
                    return subst
                texto_final = re.sub(padrao, substituir, texto_final, flags=re.I)
                
    return texto_final


def higienizar_plano(
    desenvolvimento: str | list,
    acompanhamento: list,
    acessibilidade: list,
    perfil: str,
    disciplina: str,
    tema: str,
    recursos_reais: dict = None
) -> tuple[str | list, list, list]:
    """
    Higieniza desenvolvimento, acompanhamento e acessibilidade de forma coerente.
    """
    if recursos_reais is None:
        recursos_reais = {}
        
    perfil_pedagogico = detectar_perfil_pedagogico_real(tema, disciplina)
    
    # Higienizar Desenvolvimento
    if isinstance(desenvolvimento, list):
        desenv_higienizado = []
        for etapa in desenvolvimento:
            if isinstance(etapa, dict):
                etapa_nova = dict(etapa)
                etapa_nova["texto"] = higienizar_string(etapa_nova.get("texto", ""), perfil_pedagogico, recursos_reais)
                desenv_higienizado.append(etapa_nova)
            else:
                desenv_higienizado.append(higienizar_string(str(etapa), perfil_pedagogico, recursos_reais))
    else:
        desenv_higienizado = higienizar_string(str(desenvolvimento), perfil_pedagogico, recursos_reais)
        
    # Higienizar Acompanhamento
    acomp_higienizado = []
    for item in acompanhamento:
        acomp_higienizado.append(higienizar_string(str(item), perfil_pedagogico, recursos_reais))
        
    # Higienizar Acessibilidade
    acess_higienizado = []
    for item in acessibilidade:
        acess_higienizado.append(higienizar_string(str(item), perfil_pedagogico, recursos_reais))
        
    return desenv_higienizado, acomp_higienizado, acess_higienizado
