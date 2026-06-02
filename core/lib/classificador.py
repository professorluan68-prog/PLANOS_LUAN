"""
Classificador unificado de perfil disciplinar, tipo de aula e recursos.

Centraliza a logica que tambem aparece em lote.py para que os modulos de
metodologia, acompanhamento, acessibilidade e extracao usem a mesma base.
"""

from __future__ import annotations

import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza espacos para comparacao."""
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    return re.sub(r"\s+", " ", texto).strip().lower()


def contem_termos(base: str, termos: list[str] | tuple[str, ...]) -> bool:
    """Verifica se algum dos termos aparece na string base."""
    base_normalizada = normalizar_texto(base)
    return any(normalizar_texto(termo) in base_normalizada for termo in termos)


def contem_termo_exato(base: str, termos: list[str] | tuple[str, ...]) -> bool:
    """Verifica correspondencia por palavra ou expressao inteira."""
    base_normalizada = normalizar_texto(base)
    for termo in termos:
        termo_normalizado = normalizar_texto(termo)
        if not termo_normalizado:
            continue
        if re.search(rf"(?<!\w){re.escape(termo_normalizado)}(?!\w)", base_normalizada):
            return True
    return False


def perfil_disciplina(disciplina: str) -> str:
    """Retorna o perfil pedagogico da disciplina."""
    base = normalizar_texto(disciplina)

    if ("orient" in base and "estud" in base) or "orienestudos" in base:
        return "orientacao_estudos"
    if contem_termo_exato(base, ["orientacao de estudos", "orientacao estudos", "orienestudos"]):
        return "orientacao_estudos"
    if contem_termo_exato(base, ["redacao e leitura", "leitura e redacao"]):
        return "leitura_redacao"
    if contem_termo_exato(base, ["lingua portuguesa", "portugues"]):
        if contem_termo_exato(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"
    if contem_termo_exato(base, ["ciencias"]):
        return "ciencias_ef"
    if contem_termo_exato(base, ["biologia"]):
        return "biologia"
    if contem_termo_exato(base, ["quimica"]):
        return "quimica"
    if contem_termo_exato(base, ["fisica"]):
        return "fisica"
    if contem_termo_exato(base, ["historia"]):
        return "historia"
    if contem_termo_exato(base, ["geografia"]):
        return "geografia"
    if contem_termo_exato(base, ["ingles", "lingua inglesa"]):
        return "ingles"
    if contem_termo_exato(base, ["arte"]):
        return "arte"
    if contem_termo_exato(base, ["projeto de vida"]):
        return "projeto_de_vida"
    if contem_termo_exato(base, ["educacao financeira"]):
        return "educacao_financeira"
    if contem_termo_exato(base, ["matematica"]):
        return "matematica"
    if contem_termo_exato(base, ["tecnologia e inovacao", "tecnologia", "inovacao"]):
        return "tecnologia_inovacao"
    if contem_termo_exato(base, ["sociologia"]):
        return "sociologia"
    if contem_termo_exato(base, ["lideranca e oratoria", "lideranca", "oratoria"]):
        return "lideranca_oratoria"
    return "geral"


# ── Palavras-chave e função de classificação para Língua Portuguesa ────────

_LP_LEITURA_LITERARIA = [
    "cronica", "conto", "poema", "poesia", "narrativa", "leitura literaria",
    "genero literario", "eu lirico", "narrador", "enredo", "personagem",
    "metafora", "figuras de linguagem", "fruicao", "apreciacao",
    "machado de assis", "clarice lispector", "rubem braga", "carlos drummond",
    "marina colasanti", "conto indigena", "literatura",
]

_LP_GRAMATICA_CONTEXTUALIZADA = [
    "modo subjuntivo", "modo indicativo", "tempos verbais", "preterito",
    "futuro", "gerundio", "coesao", "elementos coesivos", "conjuncoes",
    "pronomes", "regencia verbal", "regencia nominal", "oracoes subordinadas",
    "adverbiais", "adjetivas", "modalizacao", "polissemia", "intertextualidade",
    "conectores", "anafora", "catafora",
]

_LP_LEITURA_JORNALISTICA = [
    "noticia", "editorial", "artigo de opiniao", "carta do leitor",
    "reportagem", "manchete", "lide", "tema central", "subtemas",
    "fato", "opiniao", "parcialidade", "imparcialidade", "veiculo",
    "jornalismo", "midia", "fonte", "intencionalidade",
    "resenha critica",
]

_LP_PRODUCAO_TEXTUAL = [
    "produza", "escreva uma carta", "redija", "elabore",
    "carta do leitor", "resenha", "artigo", "producao",
    "estrutura do genero", "publico-alvo", "suporte", "circulacao",
]

_LP_PESQUISA = [
    "scielo", "curadoria", "artigo cientifico", "plagio",
    "base de dados", "google academico", "fontes confiaveis",
    "divulgacao cientifica", "direitos autorais",
]


def _tipo_aula_lingua_portuguesa(titulo: str, texto: str) -> str:
    """
    Classifica o tipo de aula de Língua Portuguesa com base no título e texto.

    Retorna:
        'leitura_literaria', 'gramatica_contextualizada',
        'leitura_jornalistica', 'producao_textual' ou 'pesquisa'.

    Regra especial: se o título contém 'Parte 2', 'Parte 3' ou 'Parte 4'
    e o conteúdo traz termos de gramática contextualizada, retorna
    'gramatica_contextualizada'.
    """
    titulo_norm = normalizar_texto(titulo)
    texto_norm = normalizar_texto(texto)

    # Regra especial: aula de continuidade com foco gramatical
    if any(p in titulo_norm for p in ["parte 2", "parte 3", "parte 4"]):
        if contem_termos(texto_norm, _LP_GRAMATICA_CONTEXTUALIZADA):
            return "gramatica_contextualizada"

    # Pesquisa acadêmica
    if contem_termos(texto_norm, _LP_PESQUISA):
        return "pesquisa"

    # Produção textual
    if contem_termos(texto_norm, _LP_PRODUCAO_TEXTUAL):
        return "producao_textual"

    # Leitura jornalística
    if contem_termos(texto_norm, _LP_LEITURA_JORNALISTICA):
        if contem_termos(texto_norm, ["fato", "opiniao", "parcialidade", "veiculo", "intencionalidade", "manchete"]):
            return "leitura_jornalistica"

    # Gramática contextualizada
    if contem_termos(texto_norm, _LP_GRAMATICA_CONTEXTUALIZADA):
        return "gramatica_contextualizada"

    # Leitura literária (padrão para LP)
    return "leitura_literaria"


_TIPOS_MATEMATICA = [
    ("modelagem", ["modelagem", "modelar situacoes", "metodo de polya", "polya", "representar matematicamente", "sentenca matematica"]),
    ("grandezas_medidas", ["grandeza", "razao", "proporcao", "velocidade media", "mbps", "kbps"]),
    ("algebra", ["equac", "equa", "variavel", "incognita", "express", "polinom", "sistema", "inequac", "logarit", "1 grau", "2 grau", "modulo"]),
    ("funcoes", ["func", "f(x)", "lei de formacao", "dominio", "imagem", "grafico de funcao", "taxa de variacao"]),
    ("combinatoria", ["combinat", "permut", "arranjo", "fatorial", "contagem", "ordem importa", "anagrama", "comissao", "placa", "senha"]),
    ("estatistica_probabilidade", ["estatist", "probab", "media", "mediana", "moda", "amostra", "espaco amostral", "evento", "frequencia", "censo", "pesquisa"]),
    ("geometria", ["geometr", "area", "perimetro", "volume", "angulo", "triangulo", "figura", "solido", "pitagoras", "malha", "trigonom"]),
    ("numeros_operacoes", ["numero", "fracao", "decimal", "porcentagem", "potencia", "raiz", "divisibilidade", "operacao", "mmc", "mdc", "primo"]),
]

_TIPOS_EDUCACAO_FINANCEIRA = [
    ("credito_endividamento", ["credito", "divida", "emprestimo", "financiamento", "parcela", "endividamento", "inadimplencia"]),
    ("empreendedorismo", ["empreendedorismo", "empreendedor", "negocio", "empresa", "produto", "servico", "mercado", "lucro", "viabilidade"]),
    ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias", "manchetes", "noticias", "percentual", "porcentagem"]),
    ("governo_economia", ["papel do governo na economia", "governo na economia", "estado na economia", "politicas publicas", "impostos", "arrecadacao"]),
    ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas", "impacto das escolhas economicas", "escolhas economicas"]),
    ("cidadania_financeira", ["direito do consumidor", "direitos do consumidor", "consumidor", "reclamacao", "garantia", "nota fiscal", "cidadania financeira"]),
    ("instituicoes_financeiras", ["instituicao financeira", "instituicoes financeiras", "banco", "conta digital", "guardar dinheiro", "onde guardamos", "movimentar dinheiro"]),
    ("investimento_poupanca", ["investimento", "poupanca", "rendimento", "juros", "aplicacao", "reserva", "patrimonio", "rentabilidade", "reserva de emergencia"]),
    ("orcamento_planejamento", ["orcamento", "planejamento", "receita", "despesa", "gasto", "renda", "controle", "organizacao financeira"]),
    ("consumo_consciente", ["consumo", "compra", "decisao", "necessidade", "desejo", "prioridade", "escolha", "custo-beneficio", "consumo consciente"]),
]

_TIPOS_TECNOLOGIA_INOVACAO = [
    ("programacao_inicial", ["startlab", "bloco diga", "bandeira verde", "blocos de eventos", "aparencia", "algoritmo", "programacao", "mensagens interativas", "criando com teclado"]),
    ("cultura_digital", ["cultura digital", "interacoes digitais", "forum", "emocoes", "etica", "respeito", "comportamentos respeitosos", "convivencia online"]),
    ("comunicacao_digital", ["perguntas claras", "duvidas corretamente", "fazer perguntas", "mensagem", "forum", "pedido de ajuda", "comunicacao clara", "perguntas inadequadas"]),
    ("consumo_tecnologia", ["obsolescencia", "lixo eletronico", "consumo excessivo", "consumo consciente", "descarte", "sustentabilidade", "impactos ambientais"]),
    ("dispositivos_entrada_saida", ["entrada e saida", "dispositivo de entrada", "dispositivo de saida", "teclado", "mouse", "monitor", "impressora", "microfone", "camera", "projetor", "caixa de som"]),
]

_TIPOS_GERAIS = [
    ("producao", ["producao textual", "produzir", "rascunho", "revisao", "reescrita", "redacao", "planejamento do texto"]),
    ("argumentacao", ["debate", "argumento", "opiniao", "tese", "ponto de vista", "carta de leitor"]),
    ("fonte_historica", ["fonte historica", "documento historico", "linha do tempo", "periodo historico", "cronologia"]),
    ("analise_geografica", ["mapa", "paisagem", "territorio", "regiao", "grafico", "escala", "cartografia"]),
    ("investigacao", ["experimento", "investigacao", "hipotese", "modelo", "observacao", "processo natural"]),
    ("resolucao_problemas", ["calculo", "problema", "porcentagem", "juros", "orcamento", "tabela", "grafico"]),
    ("lingua_estrangeira", ["vocabulary", "listen", "repeat", "speaking", "reading", "writing", "dialogue", "vocabulario", "escutar", "repetir", "falar", "ler", "escrever", "dialogo"]),
    ("arte_pratica", ["apreciacao", "criacao", "experimentacao", "musica", "imagem", "obra", "performance"]),
    ("reflexiva", ["autoconhecimento", "convivencia", "projeto de vida", "escolha", "respeito", "planejamento pessoal"]),
    ("leitura", ["leitura", "leia", "texto", "interpreta", "genero textual", "conto", "cronica", "anuncio", "publicidade", "publicitario", "slogan", "observe"]),
]

_MARCADORES_RECURSOS_PRIORITARIOS = {
    "analise_grafico": [
        "analise o grafico",
        "observe o grafico",
        "leia o grafico",
        "com base no grafico",
        "analise a tabela",
        "observe a tabela",
        "preencha a tabela",
        "complete a tabela",
        "com base na tabela",
    ],
    "analise_geografica": [
        "observe o mapa",
        "analise o mapa",
        "com base no mapa",
        "leia o mapa",
        "localize no mapa",
    ],
    "analise_imagem": [
        "observe a imagem",
        "analise a imagem",
        "leitura da imagem",
        "observe a charge",
        "analise a charge",
    ],
    "producao_textual": [
        "produza um texto",
        "escreva um texto",
        "produza uma resenha",
        "produza uma cronica",
        "produza uma carta",
        "rascunho",
        "revisao",
        "reescrita",
    ],
    "calculo_resolucao": [
        "resolva os calculos",
        "resolva as questoes",
        "calcule",
        "efetue",
        "determine o valor",
    ],
    "experimentacao": [
        "realize o experimento",
        "observe o experimento",
        "hipotese",
        "procedimento",
        "conclusao do experimento",
    ],
}


def _detectar_tipo_educacao_financeira_por_tema(tema_base: str) -> str | None:
    """Prioriza o titulo/tema para evitar contaminacao por texto auxiliar."""
    mapa_prioritario = [
        ("instituicoes_financeiras", ["onde guardamos o dinheiro", "guardar dinheiro", "onde guardar o dinheiro", "guardamos o dinheiro"]),
        ("investimento_poupanca", ["por que poupamos", "porque poupamos", "reserva de emergencia", "poupamos"]),
        ("orcamento_planejamento", ["objetivos em familia ou em grupo", "objetivos em familia", "objetivos em grupo", "planejamento financeiro"]),
        ("analise_percentuais_noticias", ["percentuais na midia", "porcentagens na midia", "analisando noticias", "analise de noticias"]),
        ("governo_economia", ["papel do governo na economia", "governo na economia"]),
        ("impacto_decisoes_economicas", ["impacto das decisoes economicas", "decisoes economicas em nossas vidas"]),
    ]
    for tipo, termos in mapa_prioritario:
        if contem_termos(tema_base, termos):
            return tipo
    return None


def _detectar_tipo_por_catalogo(
    tema_base: str,
    texto_base: str,
    catalogo: list[tuple[str, list[str]]],
    default: str,
) -> str:
    for tipo, termos in catalogo:
        if contem_termo_exato(tema_base, termos) or contem_termos(tema_base, termos):
            return tipo
    for tipo, termos in catalogo:
        if contem_termo_exato(texto_base, termos) or contem_termos(texto_base, termos):
            return tipo
    return default


def detectar_tipo_aula(texto: str, tema: str, disciplina: str = "") -> str:
    """Classifica o tipo de aula a partir do conteudo."""
    base = normalizar_texto(f"{disciplina} {tema} {texto}")
    tema_base = normalizar_texto(tema)
    perfil = perfil_disciplina(disciplina)

    if perfil == "educacao_financeira":
        tipo_por_tema = _detectar_tipo_educacao_financeira_por_tema(tema_base)
        if tipo_por_tema:
            return tipo_por_tema
        return _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_EDUCACAO_FINANCEIRA, "decisao_financeira")

    if perfil == "matematica":
        return _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_MATEMATICA, "resolucao_problemas")

    if perfil == "tecnologia_inovacao":
        return _detectar_tipo_por_catalogo(tema_base, base, _TIPOS_TECNOLOGIA_INOVACAO, "tecnologia_geral")

    # Língua Portuguesa — classificador especializado
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return _tipo_aula_lingua_portuguesa(tema, texto)

    for tipo, termos in _TIPOS_GERAIS:
        if contem_termo_exato(tema_base, termos) or contem_termos(tema_base, termos):
            return tipo
    for tipo, termos in _TIPOS_GERAIS:
        if contem_termo_exato(base, termos) or contem_termos(base, termos):
            return tipo

    return "geral"


_RECURSOS_DETECTAVEIS = {
    "leitura_texto": ["leitura", "leia", "texto", "trecho", "conto", "cronica", "poema", "artigo", "noticia"],
    "analise_imagem": ["imagem", "ilustracao", "foto", "fotografia", "pintura", "obra", "charge"],
    "analise_grafico": ["grafico", "tabela", "dados", "infografico", "mapa"],
    "calculo_resolucao": ["calcule", "resolva", "operacao", "equacao", "formula", "expressao"],
    "producao_textual": ["producao", "escreva", "redija", "rascunho", "reescrita", "revisao"],
    "experimentacao": ["experimento", "observacao", "laboratorio", "material", "procedimento"],
    "debate_oral": ["debate", "discussao", "opiniao", "argumento", "apresentacao", "oralidade"],
    "escuta_audio": ["audio", "musica", "som", "podcast", "video", "assista"],
}


def detectar_recursos(texto: str, tema: str = "") -> list[str]:
    """Detecta tipos de recursos/atividades presentes no conteudo."""
    base = normalizar_texto(f"{tema} {texto}")
    recursos = [
        recurso
        for recurso, marcadores in _MARCADORES_RECURSOS_PRIORITARIOS.items()
        if any(marcador in base for marcador in marcadores)
    ]
    if recursos:
        return recursos
    recursos = [
        recurso
        for recurso, termos in _RECURSOS_DETECTAVEIS.items()
        if contem_termo_exato(base, termos) or contem_termos(base, termos)
    ]
    return recursos or ["leitura_texto"]
