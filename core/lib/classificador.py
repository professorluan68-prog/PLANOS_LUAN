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
    return re.sub(r"\s+", " ", texto).strip().lower()


def contem_termos(base: str, termos: list[str] | tuple[str, ...]) -> bool:
    """Verifica se algum dos termos aparece na string base."""
    base_normalizada = normalizar_texto(base)
    return any(normalizar_texto(termo) in base_normalizada for termo in termos)


def perfil_disciplina(disciplina: str) -> str:
    """Retorna o perfil pedagogico da disciplina."""
    base = normalizar_texto(disciplina)

    if contem_termos(base, ["orientacao de estudos", "orientacao estudos", "orienestudos", "orient"]):
        return "orientacao_estudos"
    if contem_termos(base, ["redacao e leitura", "leitura e redacao", "redacao", "leitura"]):
        return "leitura_redacao"
    if contem_termos(base, ["lingua portuguesa", "portugues"]):
        if contem_termos(base, ["ensino medio", "medio", "1 ano", "2 ano", "3 ano", "em"]):
            return "lingua_portuguesa_em"
        return "lingua_portuguesa_ef"
    if contem_termos(base, ["ciencias", "cienc"]):
        return "ciencias_ef"
    if contem_termos(base, ["biologia", "biolog"]):
        return "biologia"
    if contem_termos(base, ["quimica", "quim"]):
        return "quimica"
    if contem_termos(base, ["fisica", "fis"]):
        return "fisica"
    if contem_termos(base, ["historia", "histor"]):
        return "historia"
    if contem_termos(base, ["geografia", "geograf"]):
        return "geografia"
    if contem_termos(base, ["ingles", "lingua inglesa", "ingl"]):
        return "ingles"
    if contem_termos(base, ["arte"]):
        return "arte"
    if contem_termos(base, ["projeto de vida", "projeto"]):
        return "projeto_de_vida"
    if contem_termos(base, ["educacao financeira", "financeir"]):
        return "educacao_financeira"
    if contem_termos(base, ["matematica", "matem"]):
        return "matematica"
    if contem_termos(base, ["tecnologia", "inovacao", "tecnolog"]):
        return "tecnologia_inovacao"
    if contem_termos(base, ["sociologia", "sociolog"]):
        return "sociologia"
    if contem_termos(base, ["lideranca", "oratoria", "lideranc", "orator"]):
        return "lideranca_oratoria"
    return "geral"


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


def detectar_tipo_aula(texto: str, tema: str, disciplina: str = "") -> str:
    """Classifica o tipo de aula a partir do conteudo."""
    base = normalizar_texto(f"{disciplina} {tema} {texto}")
    tema_base = normalizar_texto(tema)
    perfil = perfil_disciplina(disciplina)

    if perfil == "educacao_financeira":
        tipo_por_tema = _detectar_tipo_educacao_financeira_por_tema(tema_base)
        if tipo_por_tema:
            return tipo_por_tema
        for tipo, termos in _TIPOS_EDUCACAO_FINANCEIRA:
            if contem_termos(tema_base, termos):
                return tipo
        for tipo, termos in _TIPOS_EDUCACAO_FINANCEIRA:
            if contem_termos(base, termos):
                return tipo
        return "decisao_financeira"

    if perfil == "matematica":
        for tipo, termos in _TIPOS_MATEMATICA:
            if contem_termos(base, termos) or contem_termos(tema_base, termos):
                return tipo
        return "resolucao_problemas"

    if perfil == "tecnologia_inovacao":
        for tipo, termos in _TIPOS_TECNOLOGIA_INOVACAO:
            if contem_termos(base, termos) or contem_termos(tema_base, termos):
                return tipo
        return "tecnologia_geral"

    for tipo, termos in _TIPOS_GERAIS:
        if contem_termos(base, termos):
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
        for recurso, termos in _RECURSOS_DETECTAVEIS.items()
        if contem_termos(base, termos)
    ]
    return recursos or ["leitura_texto"]
