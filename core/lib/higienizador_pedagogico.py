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
    "calculo": [
        "calcule",
        "calcular",
        "operações",
        "operação",
        "equação",
        "equações",
        "função matemática",
        "função afim",
        "função quadrática",
        "juros",
        "desconto",
        "valor posicional",
        "decomposição",
    ],
    "producao_textual": ["produção textual", "produza um texto", "escreva um texto", "planejar texto", "revisar texto", "redação", "cartaz informativo"],
    "debate": ["debate", "roda de conversa", "discussão em grupo", "world café", "socialização", "conversa em duplas"],
}

# Fontes comuns e termos de créditos que causam falsos positivos
FONTES_NAO_RECURSO = [
    r"g1\.globo\.com", r"uol\.com\.br", r"bbc\.com", r"cnn", r"folha", r"estadao",
    r"dispon[ií]vel em\b", r"acesso em\b", r"adaptado de\b", r"fonte:\b",
    r"reprodu[cç][aã]o\b", r"imagem:\b", r"foto:\b", r"cr[eé]dito:\b"
]

# Termos de notícia/jornalísticos e suas substituições por contexto
REGRAS_SUBSTITUICAO = {
    "texto_publicitario": [
        (r"\ba not[ií]cia apresentada\b", "o anúncio apresentado"),
        (r"\ba not[ií]cia analisada\b", "o anúncio analisado"),
        (r"\ba not[ií]cia\b", "o anúncio"),
        (r"\bas not[ií]cias\b", "as campanhas"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do anúncio apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do anúncio apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do anúncio apresentado"),
        (r"\bnot[ií]cia apresentada\b", "anúncio apresentado"),
        (r"\bnot[ií]cia analisada\b", "anúncio analisado"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do anúncio"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do anúncio"),
        (r"\bleitura da not[ií]cia\b", "leitura do anúncio"),
        (r"\bna not[ií]cia\b", "no anúncio"),
        (r"\bda not[ií]cia\b", "do anúncio"),
        (r"\bnot[ií]cia\b", "anúncio"),
        (r"\bnot[ií]cias\b", "campanhas"),
        (r"\breportagem\b", "campanha"),
        (r"\breportagens\b", "campanhas"),
        (r"\beditorial\b", "texto publicitário"),
        (r"\beditoriais\b", "textos publicitários"),
    ],
    "biografia": [
        (r"\ba not[ií]cia apresentada\b", "a biografia apresentada"),
        (r"\ba not[ií]cia analisada\b", "a biografia analisada"),
        (r"\ba not[ií]cia\b", "a biografia"),
        (r"\bas not[ií]cias\b", "as biografias"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada da biografia apresentada"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada da biografia apresentada"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura da biografia apresentada"),
        (r"\bnot[ií]cia apresentada\b", "biografia apresentada"),
        (r"\bnot[ií]cia analisada\b", "biografia analisada"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada da biografia"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada da biografia"),
        (r"\bleitura da not[ií]cia\b", "leitura da biografia"),
        (r"\bna not[ií]cia\b", "na biografia"),
        (r"\bda not[ií]cia\b", "da biografia"),
        (r"\bnot[ií]cia\b", "biografia"),
        (r"\bnot[ií]cias\b", "biografias"),
        (r"\breportagem\b", "biografia"),
        (r"\breportagens\b", "biografias"),
    ],
    "conto_distopico": [
        (r"\ba not[ií]cia apresentada\b", "o conto apresentado"),
        (r"\ba not[ií]cia analisada\b", "o conto analisado"),
        (r"\ba not[ií]cia\b", "o conto"),
        (r"\bas not[ií]cias\b", "os contos"),
        (r"\bleitura guiada da not[ií]cia apresentada\b", "leitura guiada do conto apresentado"),
        (r"\bleitura orientada da not[ií]cia apresentada\b", "leitura guiada do conto apresentado"),
        (r"\bleitura da not[ií]cia apresentada\b", "leitura do conto apresentado"),
        (r"\bnot[ií]cia apresentada\b", "conto apresentado"),
        (r"\bnot[ií]cia analisada\b", "conto analisado"),
        (r"\bleitura guiada da not[ií]cia\b", "leitura guiada do conto"),
        (r"\bleitura orientada da not[ií]cia\b", "leitura guiada do conto"),
        (r"\bleitura da not[ií]cia\b", "leitura do conto"),
        (r"\bna not[ií]cia\b", "no conto"),
        (r"\bda not[ií]cia\b", "do conto"),
        (r"\bnot[ií]cia\b", "conto"),
        (r"\bnot[ií]cias\b", "contos"),
        (r"\breportagem\b", "conto"),
        (r"\breportagens\b", "contos"),
    ],
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
        (r"\bda reportagem lida\b", "do material de estudo lido"),
        (r"\bna reportagem lida\b", "no material de estudo lido"),
        (r"\ba reportagem lida\b", "o material de estudo lido"),
        (r"\breportagem lida\b", "material de estudo lido"),
        (r"\breportagens lidas\b", "materiais de estudo lidos"),
        (r"\buma reportagem\b", "um material de estudo"),
        (r"\bumas reportagens\b", "materiais de estudo"),
        (r"\bleitura da reportagem\b", "leitura do material de estudo"),
        (r"\bleitura orientada da reportagem\b", "leitura orientada do material de estudo"),
        (r"\bleitura mediada da reportagem\b", "leitura mediada do material de estudo"),
        (r"\bda reportagem\b", "do material de estudo"),
        (r"\bna reportagem\b", "no material de estudo"),
        (r"\bpela reportagem\b", "pelo material de estudo"),
        (r"\ba reportagem\b", "o material de estudo"),
        (r"\bas reportagens\b", "os materiais de estudo"),
        (r"\bdas reportagens\b", "dos materiais de estudo"),
        (r"\bnas reportagens\b", "nos materiais de estudo"),
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
    ],
    "calculo": [
        (r"\batividade de c[aá]lculo\b", "atividade de análise do material"),
        (r"\bresolu[cç][aã]o de c[aá]lculos\b", "resolução da atividade"),
        (r"\bc[aá]lculos\b", "registros"),
        (r"\bc[aá]lculo\b", "registro"),
        (r"\bcalcular\b", "analisar"),
        (r"\bcontas\b", "registros"),
    ],
    "producao_textual": [
        (r"\bprodu[cç][aã]o textual formal\b", "registro da atividade"),
        (r"\bprodu[cç][aã]o textual\b", "registro da atividade"),
        (r"\bproduzir um texto\b", "registrar uma resposta"),
        (r"\bescrever um texto\b", "registrar uma resposta"),
    ],
    "debate": [
        (r"\bdebate formal avaliativo\b", "conversa orientada"),
        (r"\bdebate formal\b", "conversa orientada"),
        (r"\bdebate\b", "discussão orientada"),
    ],
}


def normalizar_para_busca(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _contem_algum(texto_norm: str, termos: list[str]) -> bool:
    return any(normalizar_para_busca(termo) in texto_norm for termo in termos)


def _remover_contextos_negativos_de_recurso(texto_norm: str, keywords: list[str]) -> str:
    """Ignora trechos em que o próprio material nega a presença de um recurso."""
    if not texto_norm:
        return ""

    texto_filtrado = texto_norm
    negacoes = [
        "sem",
        "nao ha",
        "nao contem",
        "nao envolve",
        "nao apresenta",
        "sem comando de",
        "sem atividade de",
        "sem proposta de",
        "sem necessidade de",
    ]

    for keyword in keywords:
        keyword_norm = normalizar_para_busca(keyword)
        if not keyword_norm:
            continue

        for negacao in negacoes:
            negacao_norm = normalizar_para_busca(negacao)
            texto_filtrado = re.sub(
                rf"\b{re.escape(negacao_norm)}\b[^.!?\n;]*\b{re.escape(keyword_norm)}\b[^.!?\n;]*",
                " ",
                texto_filtrado,
            )

    return texto_filtrado


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
        texto_recurso = texto_norm
        if recurso in {"calculo", "producao_textual", "debate", "tabela", "grafico", "mapa", "experimento"}:
            texto_recurso = _remover_contextos_negativos_de_recurso(texto_norm, keywords)

        presente = False
        for kw in keywords:
            kw_norm = normalizar_para_busca(kw)
            if kw_norm in texto_recurso:
                presente = True
                break
        recursos_detectados[recurso] = presente

    if recursos_detectados.get("mapa") and "mapa conceitual" in texto_norm:
        termos_mapa_geografico = [
            "mapa do brasil",
            "mapa-mundi",
            "mapa mundi",
            "mapa politico",
            "mapa político",
            "mapa fisico",
            "mapa físico",
            "mapa interativo",
            "cartografico",
            "cartográfico",
            "coordenadas geograficas",
            "coordenadas geográficas",
        ]
        if not any(termo in texto_norm for termo in termos_mapa_geografico):
            recursos_detectados["mapa"] = False
            recursos_detectados["mapa_conceitual"] = True

    return recursos_detectados


def detectar_perfil_pedagogico_real(tema: str, disciplina: str) -> str:
    """Detecta de forma estrita o perfil da aula para aplicar higienização."""
    tema_norm = normalizar_para_busca(tema)
    disc_norm = normalizar_para_busca(disciplina)
    
    # Se for Língua Portuguesa
    if "portuguesa" in disc_norm or "portugues" in disc_norm or "redacao" in disc_norm:
        if _contem_algum(tema_norm, ["trilha", "alice no pais das maravilhas", "obra literaria", "personagens", "enredo"]):
            return "leitura_literaria_trilha"
        if any(t in tema_norm for t in ["anuncie aqui", "anuncio publicitario", "propaganda", "publicidade", "slogan", "jingle", "campanha", "advergame", "unboxing", "social advertising"]):
            return "texto_publicitario"
        if any(t in tema_norm for t in ["historia de uma vida", "biografia", "trajetoria", "vida de", "carreira", "nascimento", "mapa conceitual"]):
            return "biografia"
        if any(t in tema_norm for t in ["jornalismo em imagens", "fotojornalismo", "recursos visuais", "textos jornalisticos digitais"]):
            return "noticia_multimodal"
        if any(t in tema_norm for t in ["conto distopico", "narrativa distopica", "distopia", "olhos por bugalhos", "uma narrativa pode moldar uma imagem"]):
            return "conto_distopico"
        if any(t in tema_norm for t in ["cronica", "cronista"]):
            return "cronica"
        if any(t in tema_norm for t in ["editorial", "editoria", "editoriais", "vozes da redacao jornalistica"]):
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

    if "arte" in disc_norm:
        if _contem_algum(tema_norm, ["musica", "música", "samba", "forro", "forró", "repertorio musical", "escuta", "palmas", "asa branca"]):
            return "arte_musica"
        if _contem_algum(tema_norm, ["compor versos", "diario de bordo", "diário de bordo", "criacao artistica", "criação artística", "producao visual", "produção visual"]):
            return "arte_producao_criativa"
        if _contem_algum(tema_norm, ["manifestacao cultural", "manifestação cultural", "patrimonio", "patrimônio", "danca", "dança", "territorio", "território"]):
            return "arte_contexto_cultural"
        return "arte_geral"

    if "biologia" in disc_norm:
        if _contem_algum(tema_norm, ["tabela comparativa", "comparacao", "comparação", "gases", "planetas", "organismos"]):
            return "biologia_tabela_comparativa"
        if _contem_algum(tema_norm, ["efeito estufa", "aquecimento global", "atmosfera", "celula", "célula", "ecologia", "metabolismo", "saude", "saúde"]):
            return "biologia_conceitual"
        return "biologia_conceitual"

    if disc_norm == "ciencias" or "ciencias" in disc_norm:
        if _contem_algum(tema_norm, ["reciclagem", "poluicao", "poluição", "recursos naturais", "uso responsavel", "uso responsável", "impacto"]):
            return "ciencias_impacto_socioambiental"
        if _contem_algum(tema_norm, ["materiais sinteticos", "materiais sintéticos", "material natural", "materia-prima", "matéria-prima", "produto acabado"]):
            return "ciencias_conceitual"
        return "ciencias_conceitual"

    if "educacao financeira" in disc_norm or "educação financeira" in disc_norm:
        if _contem_algum(tema_norm, ["juros", "desconto", "porcentagem", "orcamento", "orçamento", "planilha"]):
            return "educacao_financeira_calculo"
        if _contem_algum(tema_norm, ["consumo", "consumo consciente", "necessidades", "desejos", "escolhas"]):
            return "educacao_financeira_consumo"
        if _contem_algum(tema_norm, ["objetivos", "metas", "prioridades", "planejamento financeiro", "definicao de objetivos", "definição de objetivos"]):
            return "educacao_financeira_planejamento"
        return "educacao_financeira_planejamento"

    if "geografia" in disc_norm:
        if _contem_algum(tema_norm, ["grafico", "gráfico", "taxa", "populacao", "população", "ibge", "serie historica", "série histórica"]):
            return "geografia_grafico_dados"
        if _contem_algum(tema_norm, ["mapa", "mancha urbana", "territorio", "território", "regiao", "região", "localizacao", "localização", "cartografia"]):
            return "geografia_mapa"
        if _contem_algum(tema_norm, ["urbanizacao", "urbanização", "rede urbana", "migracao", "migração", "paisagem"]):
            return "geografia_conceitual_espaco"
        return "geografia_conceitual_espaco"

    if "historia" in disc_norm or "história" in disc_norm:
        if _contem_algum(tema_norm, ["mapa historico", "mapa histórico", "crescente fertil", "crescente fértil"]):
            return "historia_mapa_historico"
        if _contem_algum(tema_norm, ["fonte historica", "fonte histórica", "texto de epoca", "texto de época", "imagem historica", "imagem histórica"]):
            return "historia_fonte_documental"
        if _contem_algum(tema_norm, ["periodo historico", "período histórico", "processo", "civilizacao", "civilização", "civilizacoes", "civilizações", "sociedade", "governo", "cultura"]):
            return "historia_contextual"
        return "historia_contextual"

    if "lideranca" in disc_norm or "liderança" in disc_norm or "oratoria" in disc_norm or "oratória" in disc_norm:
        if _contem_algum(tema_norm, ["voz", "ritmo", "entonacao", "entonação", "pausa", "projecao", "projeção", "leitura em voz alta", "discurso oral"]):
            return "oratoria_pratica"
        if _contem_algum(tema_norm, ["persuasao", "persuasão", "retorica", "retórica", "argumentacao oral", "argumentação oral", "defesa de ideias"]):
            return "argumentacao_oral"
        return "oratoria_pratica"

    if "ingles" in disc_norm or "inglês" in disc_norm or "lingua inglesa" in disc_norm or "língua inglesa" in disc_norm:
        if _contem_algum(tema_norm, ["listen", "audio", "áudio", "dialogue", "script", "my preferences"]):
            return "ingles_listening"
        if _contem_algum(tema_norm, ["vocabulary", "vocabulario", "vocabulário", "action verbs", "word bank", "i like to"]):
            return "ingles_vocabulario"
        if _contem_algum(tema_norm, ["talk to classmates", "ask/answer", "in pairs", "dialogue"]):
            return "ingles_interacao_oral"
        return "ingles_vocabulario"

    if "matematica" in disc_norm or "matemática" in disc_norm:
        if _contem_algum(tema_norm, ["tabela", "grafico", "gráfico", "eixos", "dados", "ibge", "populacao", "população"]):
            return "matematica_tabela_grafico"
        if _contem_algum(tema_norm, ["operacoes", "operações", "decomposicao", "decomposição", "porcentagem", "equacoes", "equações", "funcoes", "funções", "valor posicional"]):
            return "matematica_calculo"
        if _contem_algum(tema_norm, ["situacao-problema", "situação-problema", "estrategia", "estratégia", "modelagem", "justificativa"]):
            return "matematica_resolucao_problemas"
        return "matematica_calculo"

    if "orientacao de estudos" in disc_norm or "orientação de estudos" in disc_norm:
        if _contem_algum(tema_norm, ["etapa", "missao", "missão", "semana", "atividade sequenciada"]):
            return "orientacao_estudos_etapas"
        if _contem_algum(tema_norm, ["ler", "destacar", "localizar", "organizar", "responder"]):
            return "leitura_estrategia_estudo"
        return "orientacao_estudos_etapas"

    if "projeto de vida" in disc_norm:
        if _contem_algum(tema_norm, ["identidade", "autenticidade", "valores", "escolhas", "sentimentos", "quem sou"]):
            return "projeto_vida_autoconhecimento"
        if _contem_algum(tema_norm, ["convivencia", "convivência", "escuta", "empatia", "respeito", "relacoes", "relações"]):
            return "projeto_vida_convivencia"
        return "projeto_vida_reflexivo"

    if "quimica" in disc_norm or "química" in disc_norm:
        if _contem_algum(tema_norm, ["funcoes organicas", "funções orgânicas", "alcool", "álcool", "aldeido", "aldeído", "cetona", "eter", "éter", "ester", "éster", "amina", "amida", "haleto"]):
            return "quimica_funcoes_organicas"
        if _contem_algum(tema_norm, ["substancias licitas", "substâncias lícitas", "dependencia quimica", "dependência química", "ods 3", "world cafe", "world café"]):
            return "quimica_saude_discussao"
        return "quimica_conceitual"

    if "tecnologia" in disc_norm or "inovacao" in disc_norm or "inovação" in disc_norm:
        if _contem_algum(tema_norm, ["computador", "dispositivo", "entrada", "saida", "saída", "hardware", "periferico", "periférico"]):
            return "tecnologia_computacao_conceitual"
        if _contem_algum(tema_norm, ["seguranca", "segurança", "privacidade", "internet", "empatia digital"]):
            return "tecnologia_cidadania_digital"
        return "tecnologia_pratica_classificacao"

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
    if perfil_pedagogico not in {"jornalistico_valido", "noticia_multimodal"}:
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
            "texto_publicitario": "a campanha discutida",
            "biografia": "a trajetória discutida",
            "conto_distopico": "o conto discutido",
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
        item_higienizado = higienizar_string(str(item), perfil_pedagogico, recursos_reais)
        item_higienizado = _limpar_placeholders_acessibilidade(item_higienizado)
        acess_higienizado.append(item_higienizado)
        
    from core.disciplinas import eh_cdp, eh_cdp_contextual
    from core.qualidade_metodologica import sanitizar_texto_cdp_estrito

    if eh_cdp(disciplina) or eh_cdp_contextual(disciplina):
        if isinstance(desenv_higienizado, list):
            desenv_novos = []
            for etapa in desenv_higienizado:
                if isinstance(etapa, dict):
                    etapa_nova = dict(etapa)
                    etapa_nova["texto"] = sanitizar_texto_cdp_estrito(etapa_nova.get("texto", ""))
                    desenv_novos.append(etapa_nova)
                else:
                    desenv_novos.append(sanitizar_texto_cdp_estrito(str(etapa)))
            desenv_higienizado = desenv_novos
        else:
            desenv_higienizado = sanitizar_texto_cdp_estrito(str(desenv_higienizado))

        acomp_higienizado = [sanitizar_texto_cdp_estrito(item) for item in acomp_higienizado]
        acess_higienizado = [sanitizar_texto_cdp_estrito(item) for item in acess_higienizado]

    return desenv_higienizado, acomp_higienizado, acess_higienizado


_PLACEHOLDERS_ACESSIBILIDADE = {
    r"\binforma[cç][aã]o do material simples\b": "tabela simples",
    r"\binforma[cç][aã]o do material\b": "recurso do material",
    r"\bo material simples\b": "tabela simples",
}


def _limpar_placeholders_acessibilidade(texto: str) -> str:
    for padrao, substituto in _PLACEHOLDERS_ACESSIBILIDADE.items():
        texto = re.sub(padrao, substituto, texto, flags=re.IGNORECASE)
    return texto
