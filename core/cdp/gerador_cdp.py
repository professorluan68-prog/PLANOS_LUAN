import hashlib
import re
import unicodedata
from pathlib import Path

def _limpar_linhas(texto: str) -> list[str]:
    linhas = []
    for linha in (texto or "").splitlines():
        linha = re.sub(r"\s+", " ", linha).strip()
        if linha:
            linhas.append(linha)
    return linhas

from core.lib.classificador import contem_termos as _contem
from core.lib.classificador import normalizar_texto as _normalizar

def _eh_cdp_contextual_disciplina(disciplina: str) -> bool:
    base = _normalizar(disciplina).replace(" ", "")
    return base in {
        "cdp-ensinofundamental",
        "cdpensinofundamental",
        "cdp-ensinomedio",
        "cdpensinomedio",
    } or (
        "cdp" in base
        and (
            "ensinomedio" in base
            or "ensinofundamental" in base
            or base.endswith("cdpem")
            or base.endswith("cdpef")
        )
    )

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
        if _contem(base, ["sistema de numeracao decimal", "composicao e decomposicao", "composição e decomposição"]):
            return "decimal_composicao_decomposicao"
        if _contem(base, ["resolucao de problemas com sistema de numeracao decimal", "problemas com sistema de numeracao decimal"]):
            return "problemas_sistema_decimal"
        if _contem(base, ["comparacao e ordenacao de numeros naturais", "comparação e ordenação de números naturais"]):
            return "comparacao_ordenacao_naturais"
        if _contem(base, ["calculos mentais com numeros naturais", "cálculos mentais com números naturais"]):
            return "calculo_mental_naturais"
        if _contem(base, ["procedimentos de adicao com numeros naturais", "adição com números naturais", "procedimentos de adição com números naturais"]):
            return "adicao_naturais"
        if _contem(base, ["resolucao de problemas de adicao e subtracao", "resolução de problemas com adição e subtração de naturais", "resolução de problemas com adição e subtração"]):
            return "problemas_adicao_subtracao_naturais"
        if _contem(base, ["estrategias de multiplicacao com numeros naturais", "estratégias de multiplicação com números naturais", "multiplicacao de naturais"]):
            return "multiplicacao_naturais"
        if _contem(base, ["resolucao de problemas com multiplicacoes e divisoes", "resolução de problemas com multiplicação", "resolução de problemas com operações fundamentais", "operacoes fundamentais", "operações fundamentais"]):
            return "problemas_operacoes_naturais"
        if _contem(base, ["padroes e regularidades com multiplos", "padrões e regularidades com múltiplos", "explorando os multiplos", "explorando os múltiplos", "multiplos de um numero natural", "múltiplos de um número natural"]):
            return "multiplos_regularidades"
        if _contem(base, ["aula de verificacao operacoes fundamentais", "aula de verificação", "verificacao operacoes fundamentais", "verificação operações fundamentais"]):
            return "verificacao_operacoes_fundamentais"
        if _contem(base, ["adicao e subtracao com numeros inteiros", "adição e subtração com números inteiros", "divisao com numeros inteiros", "divisão com números inteiros"]):
            return "numeros_inteiros"
        if _contem(base, ["resolucao de problemas com adicao e subtracao de inteiros", "resolução de problemas com adição e subtração de inteiros"]):
            return "problemas_numeros_inteiros"
        if _contem(base, ["o que e uma fracao", "o que é uma fração", "ampliacao da compreensao sobre fracoes", "ampliação da compreensão sobre frações"]):
            return "fracao_introducao_fundamental"
        if _contem(base, ["resolucao de problemas com fracoes", "resolução de problemas com frações"]):
            return "problemas_fracoes_fundamental"
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

def _tipos_matematica_fundamental_cdp() -> set[str]:
    return {
        "decimal_composicao_decomposicao",
        "problemas_sistema_decimal",
        "comparacao_ordenacao_naturais",
        "calculo_mental_naturais",
        "adicao_naturais",
        "problemas_adicao_subtracao_naturais",
        "multiplicacao_naturais",
        "problemas_operacoes_naturais",
        "multiplos_regularidades",
        "verificacao_operacoes_fundamentais",
        "numeros_inteiros",
        "problemas_numeros_inteiros",
        "fracao_introducao_fundamental",
        "problemas_fracoes_fundamental",
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

def _metodologia_matematica_fundamental_cdp(tipo_cdp: str, indice_aula: int = 0) -> str:
    aberturas = {
        "decimal_composicao_decomposicao": [
            "A aula começa com a escrita de um número na lousa para que a turma retome oralmente valor posicional, ordens e classes antes da explicação formal.",
            "O professor inicia a aula retomando a leitura de um número natural e perguntando como ele pode ser separado em partes menores na lousa.",
        ],
        "problemas_sistema_decimal": [
            "O professor apresenta um problema simples com números naturais e retoma oralmente o que deve ser observado primeiro no enunciado.",
        ],
        "comparacao_ordenacao_naturais": [
            "A aula começa com dois ou três números escritos na lousa para que a turma compare qual é maior, menor ou vem antes na sequência.",
        ],
        "calculo_mental_naturais": [
            "O professor inicia com cálculos orais curtos, retomando estratégias simples de adição, subtração ou decomposição antes dos registros no caderno.",
        ],
        "adicao_naturais": [
            "A abertura retoma uma soma simples no quadro, destacando unidades, dezenas e a organização do algoritmo antes da atividade escrita.",
        ],
        "problemas_adicao_subtracao_naturais": [
            "O professor lê um problema curto em voz alta e pergunta à turma quais dados já aparecem e o que precisa ser descoberto.",
        ],
        "multiplicacao_naturais": [
            "A aula começa com uma situação concreta de grupos iguais, quantidades repetidas ou tabuadas conhecidas para retomar o sentido da multiplicação.",
        ],
        "problemas_operacoes_naturais": [
            "O professor apresenta um enunciado matemático simples e conduz oralmente a identificação da operação mais adequada antes da resolução.",
        ],
        "multiplos_regularidades": [
            "A abertura retoma oralmente o que é múltiplo e propõe uma sequência simples na lousa para a turma continuar com apoio do professor.",
        ],
        "verificacao_operacoes_fundamentais": [
            "O professor retoma rapidamente na lousa os procedimentos principais de adição, subtração, multiplicação e divisão antes da verificação guiada.",
        ],
        "numeros_inteiros": [
            "A aula começa com um exemplo do cotidiano, como temperatura, saldo ou pontuação, para retomar o significado dos números positivos e negativos.",
        ],
        "problemas_numeros_inteiros": [
            "O professor lê em voz alta um problema com números inteiros e pergunta à turma como identificar o que aumenta, diminui ou muda de posição na reta numérica.",
        ],
        "fracao_introducao_fundamental": [
            "A abertura retoma oralmente o significado de numerador, denominador e parte do todo com um desenho simples na lousa.",
        ],
        "problemas_fracoes_fundamental": [
            "O professor apresenta uma situação com fração no cotidiano e retoma o que representa o todo antes de iniciar a resolução.",
        ],
    }
    desenvolvimentos = {
        "decimal_composicao_decomposicao": "Em seguida, o professor desenha ou organiza na lousa um quadro de ordens e classes, explica a composição e a decomposição do número passo a passo e resolve um exemplo completo antes da prática. Os estudantes copiam o modelo no caderno, realizam dois ou três exercícios graduais e acompanham a correção coletiva com retomada dos erros mais frequentes.",
        "problemas_sistema_decimal": "Depois da leitura do enunciado, o professor identifica com a turma quais números são importantes, resolve o primeiro problema na lousa verbalizando cada passo e orienta a escrita organizada no caderno. Na prática, os estudantes resolvem um problema por vez, com acompanhamento individual e correção coletiva antes de avançar.",
        "comparacao_ordenacao_naturais": "O professor registra na lousa os critérios de comparação, mostra como observar quantidade de algarismos e valor posicional e resolve exemplos simples antes da atividade. Os estudantes ordenam números no caderno, justificam oralmente algumas respostas e a correção coletiva retoma a leitura correta das ordens.",
        "calculo_mental_naturais": "Na explicação guiada, o professor mostra estratégias curtas de cálculo mental, como decomposição, compensação e agrupamento, sempre com exemplos escritos na lousa e linguagem simples. Os estudantes resolvem cálculos no caderno, com pausas para conferência oral e correção passo a passo no quadro.",
        "adicao_naturais": "O professor apresenta o algoritmo na lousa, organiza unidades, dezenas e centenas em colunas e verbaliza cada etapa da soma antes de pedir o registro no caderno. A turma resolve exercícios graduais e acompanha a correção coletiva, com atenção à organização do cálculo e ao transporte quando necessário.",
        "problemas_adicao_subtracao_naturais": "Na lousa, o professor destaca dados, pergunta o que o problema quer descobrir e explica como escolher entre somar ou subtrair sem deixar a turma resolver sozinha desde o início. Os estudantes registram a operação e a resposta no caderno, com acompanhamento individual e correção coletiva de cada item.",
        "multiplicacao_naturais": "O professor mostra na lousa a multiplicação como adição de parcelas iguais e resolve exemplos concretos antes de apresentar o algoritmo ou a estratégia principal da aula. Os estudantes acompanham um segundo exemplo, registram no caderno e resolvem atividades graduais com correção coletiva ao final.",
        "problemas_operacoes_naturais": "O professor lê cada problema em voz alta, orienta a identificação dos dados e indica qual operação deve ser usada, evitando deixar todas as questões para resolução autônoma de uma vez. A prática acontece no caderno, com um problema por vez, acompanhamento individual e correção coletiva passo a passo na lousa.",
        "multiplos_regularidades": "Em seguida, o professor constrói sequências na lousa, mostra como identificar regularidades e explica o que significa um número ser múltiplo de outro usando exemplos simples. Os estudantes completam sequências no caderno, identificam múltiplos e acompanham a correção coletiva com retomada do raciocínio usado.",
        "verificacao_operacoes_fundamentais": "Depois da retomada inicial, a turma realiza atividades curtas de verificação no caderno, sempre com leitura oral do enunciado e orientação sobre o que observar em cada questão. O professor acompanha de perto, identifica quem precisa de mais apoio e corrige coletivamente os procedimentos principais antes do fechamento.",
        "numeros_inteiros": "O professor desenha uma reta numérica na lousa, marca positivos e negativos e explica a regra principal com exemplos de temperatura, saldo ou deslocamento antes da atividade. Os estudantes registram a reta no caderno, resolvem exemplos guiados e acompanham a correção coletiva com retomada da regra de sinais quando necessário.",
        "problemas_numeros_inteiros": "Na explicação, o professor retoma a reta numérica ou a regra de sinais, lê cada enunciado em voz alta e mostra como transformar a situação concreta em cálculo. Os estudantes resolvem um problema por vez no caderno, com acompanhamento individual e correção coletiva que retoma o significado do resultado.",
        "fracao_introducao_fundamental": "O professor desenha figuras simples na lousa, mostra a divisão em partes iguais e explica a função do numerador e do denominador com exemplos concretos antes da atividade. Os estudantes copiam os desenhos, identificam frações e acompanham a correção coletiva com apoio visual na lousa.",
        "problemas_fracoes_fundamental": "O professor lê o problema em voz alta, retoma a ideia de todo e parte e resolve um exemplo com desenho simples antes de liberar a atividade. Os estudantes registram fração, desenho e resposta no caderno, enquanto o professor acompanha individualmente e conduz a correção coletiva passo a passo.",
    }
    opcoes = aberturas.get(tipo_cdp)
    if not opcoes or tipo_cdp not in desenvolvimentos:
        return ""
    inicio = opcoes[indice_aula % len(opcoes)]
    return f"{inicio} {desenvolvimentos[tipo_cdp]} O fechamento da aula acontece com uma pergunta oral de síntese, seguida de breve retomada na lousa do que foi aprendido."

def _acompanhamento_matematica_fundamental_cdp(tipo_cdp: str) -> list[str]:
    bancos = {
        "decimal_composicao_decomposicao": [
            "☑ Verificar se o estudante identifica ordens, classes e valor posicional ao compor e decompor números naturais.",
            "☑ Observar se registra corretamente a decomposição no caderno sem trocar a posição dos algarismos.",
            "☑ Acompanhar se relaciona a escrita numérica ao que foi organizado no quadro durante a explicação.",
        ],
        "problemas_sistema_decimal": [
            "☑ Verificar se o estudante localiza os dados principais do enunciado antes de iniciar a conta.",
            "☑ Observar se utiliza a composição ou decomposição do número para apoiar a resolução do problema.",
            "☑ Acompanhar se registra a resposta final com coerência em relação ao que foi perguntado.",
        ],
        "comparacao_ordenacao_naturais": [
            "☑ Verificar se o estudante compara números naturais observando quantidade de algarismos e valor posicional.",
            "☑ Observar se organiza corretamente a ordem crescente ou decrescente nas atividades do caderno.",
            "☑ Acompanhar as justificativas orais durante a correção coletiva para identificar dúvidas recorrentes.",
        ],
        "calculo_mental_naturais": [
            "☑ Verificar se o estudante utiliza estratégias simples de cálculo mental sem depender apenas da contagem direta.",
            "☑ Observar se explica oralmente como pensou para chegar ao resultado quando solicitado pelo professor.",
            "☑ Acompanhar se os registros no caderno mantêm coerência com a estratégia trabalhada na lousa.",
        ],
        "adicao_naturais": [
            "☑ Verificar se o estudante organiza corretamente as parcelas em colunas antes de somar.",
            "☑ Observar se acompanha o algoritmo passo a passo sem perder unidades, dezenas e centenas.",
            "☑ Acompanhar se registra o procedimento completo no caderno e não apenas o resultado final.",
        ],
        "problemas_adicao_subtracao_naturais": [
            "☑ Verificar se o estudante identifica quando o problema pede adição ou subtração.",
            "☑ Observar se separa os dados do enunciado antes de montar a operação no caderno.",
            "☑ Acompanhar se relaciona a resposta ao contexto do problema na correção coletiva.",
        ],
        "multiplicacao_naturais": [
            "☑ Verificar se o estudante compreende a multiplicação como adição de parcelas iguais ou agrupamento.",
            "☑ Observar se aplica corretamente a estratégia principal apresentada na lousa.",
            "☑ Acompanhar se os registros no caderno mostram organização do cálculo e compreensão do resultado.",
        ],
        "problemas_operacoes_naturais": [
            "☑ Verificar se o estudante identifica a operação adequada em cada problema antes de começar a conta.",
            "☑ Observar se resolve uma atividade por vez com atenção aos dados e ao que se quer descobrir.",
            "☑ Acompanhar se corrige os próprios procedimentos após a resolução coletiva na lousa.",
        ],
        "multiplos_regularidades": [
            "☑ Verificar se o estudante identifica padrões em sequências e reconhece múltiplos de um número natural.",
            "☑ Observar se completa sequências no caderno sem perder a regularidade trabalhada na aula.",
            "☑ Acompanhar se consegue explicar oralmente por que um número é múltiplo de outro.",
        ],
        "verificacao_operacoes_fundamentais": [
            "☑ Verificar quais procedimentos de adição, subtração, multiplicação e divisão o estudante já realiza com mais autonomia.",
            "☑ Observar se há dúvidas recorrentes na leitura do enunciado, escolha da operação ou organização dos registros.",
            "☑ Acompanhar quais conteúdos precisam de retomada individual ou coletiva após a verificação guiada.",
        ],
        "numeros_inteiros": [
            "☑ Verificar se o estudante compreende o significado de números positivos e negativos em situações concretas.",
            "☑ Observar se utiliza a reta numérica ou a regra de sinais para justificar a resposta.",
            "☑ Acompanhar se registra corretamente cálculos e comparações com números inteiros no caderno.",
        ],
        "problemas_numeros_inteiros": [
            "☑ Verificar se o estudante identifica, no enunciado, quando a situação representa aumento, diminuição ou deslocamento na reta numérica.",
            "☑ Observar se escolhe a operação adequada antes de iniciar o cálculo com números inteiros.",
            "☑ Acompanhar se a resposta final faz sentido em relação ao contexto trabalhado pelo professor.",
        ],
        "fracao_introducao_fundamental": [
            "☑ Verificar se o estudante identifica numerador, denominador e a ideia de parte do todo nas representações feitas na lousa.",
            "☑ Observar se consegue relacionar desenho e escrita numérica da fração no caderno.",
            "☑ Acompanhar se responde às perguntas de correção coletiva compreendendo o significado da divisão em partes iguais.",
        ],
        "problemas_fracoes_fundamental": [
            "☑ Verificar se o estudante reconhece o todo e a parte indicada antes de resolver o problema com frações.",
            "☑ Observar se usa desenho, escrita fracionária ou cálculo simples para organizar a resolução no caderno.",
            "☑ Acompanhar se a resposta final está coerente com a situação concreta apresentada pelo professor.",
        ],
    }
    return bancos.get(tipo_cdp, [])

def _acessibilidade_matematica_fundamental_cdp(tipo_cdp: str) -> list[str]:
    bancos = {
        "decimal_composicao_decomposicao": [
            "☑ Organizar quadro de ordens e classes de forma ampliada na lousa para facilitar a leitura dos valores posicionais.",
            "☑ Trabalhar um número por vez, com exemplos simples antes de ampliar a quantidade de algarismos.",
            "☑ Oferecer tempo ampliado para copiar o esquema e concluir a decomposição no caderno.",
        ],
        "problemas_sistema_decimal": [
            "☑ Ler o enunciado em voz alta e destacar oralmente os dados principais antes da resolução individual.",
            "☑ Reescrever na lousa apenas as informações essenciais do problema para reduzir a sobrecarga de leitura.",
            "☑ Apoiar individualmente estudantes com dificuldade de organizar a conta a partir do enunciado.",
        ],
        "comparacao_ordenacao_naturais": [
            "☑ Escrever os números com espaçamento e alinhamento claros na lousa para facilitar a comparação visual.",
            "☑ Utilizar exemplos com poucos números antes de ampliar a atividade de ordenação.",
            "☑ Permitir registro por setas, sinais de maior e menor ou lista simples no caderno.",
        ],
        "calculo_mental_naturais": [
            "☑ Apresentar uma estratégia de cada vez na lousa, evitando múltiplos caminhos simultâneos para o mesmo cálculo.",
            "☑ Retomar oralmente o raciocínio passo a passo antes de pedir o registro no caderno.",
            "☑ Oferecer exemplos extras para estudantes que ainda dependem da contagem direta.",
        ],
        "adicao_naturais": [
            "☑ Organizar o algoritmo em colunas bem visíveis na lousa, com destaque para unidades, dezenas e centenas.",
            "☑ Resolver um exemplo completo antes da atividade individual, mantendo o modelo no quadro durante a prática.",
            "☑ Acompanhar individualmente estudantes com dificuldade de alinhamento e transporte no cálculo.",
        ],
        "problemas_adicao_subtracao_naturais": [
            "☑ Explicar com palavras simples o que o problema está pedindo antes que os estudantes iniciem a resolução.",
            "☑ Destacar na lousa palavras do enunciado que indicam juntar, tirar, comparar ou completar.",
            "☑ Permitir que o estudante registre primeiro a operação e só depois produza a resposta final por escrito.",
        ],
        "multiplicacao_naturais": [
            "☑ Utilizar exemplos concretos de grupos iguais na lousa antes do algoritmo formal.",
            "☑ Resolver em etapas curtas, mantendo visível a relação entre adição repetida e multiplicação.",
            "☑ Oferecer apoio individual na organização do cálculo e no uso da tabuada quando necessário.",
        ],
        "problemas_operacoes_naturais": [
            "☑ Apresentar um problema por vez, com leitura mediada e orientação inicial antes da resolução no caderno.",
            "☑ Registrar na lousa os dados e a pergunta principal de cada atividade para apoiar a compreensão.",
            "☑ Realizar correção coletiva passo a passo antes de avançar para o próximo problema.",
        ],
        "multiplos_regularidades": [
            "☑ Construir a sequência na lousa de forma ampliada para facilitar a identificação do padrão.",
            "☑ Retomar oralmente o significado de múltiplo antes da atividade individual.",
            "☑ Permitir completar sequências com apoio visual e registro parcial no caderno.",
        ],
        "verificacao_operacoes_fundamentais": [
            "☑ Retomar oralmente os procedimentos principais antes da atividade de verificação, sem tratá-la como prova formal.",
            "☑ Organizar as questões em etapas curtas, com acompanhamento individual de quem apresentar mais dificuldade.",
            "☑ Corrigir coletivamente na lousa, valorizando o procedimento e não apenas o resultado final.",
        ],
        "numeros_inteiros": [
            "☑ Desenhar reta numérica ampliada na lousa, com positivos e negativos destacados por cores ou marcações simples.",
            "☑ Relacionar cada exemplo a situações concretas, como temperatura ou saldo, antes do cálculo abstrato.",
            "☑ Permitir registro por seta, desenho ou marcação na reta antes da escrita formal da conta.",
        ],
        "problemas_numeros_inteiros": [
            "☑ Ler cada problema em voz alta e explicar o contexto com linguagem simples antes da resolução.",
            "☑ Reproduzir na lousa a reta numérica ou a regra de sinais como apoio durante a atividade.",
            "☑ Oferecer tempo ampliado para organizar o raciocínio e registrar o cálculo no caderno.",
        ],
        "fracao_introducao_fundamental": [
            "☑ Utilizar desenhos simples e ampliados na lousa para representar partes iguais e facilitar a visualização da fração.",
            "☑ Retomar numerador e denominador com linguagem direta sempre que necessário durante a atividade.",
            "☑ Permitir que o estudante responda primeiro pelo desenho e depois pela escrita numérica da fração.",
        ],
        "problemas_fracoes_fundamental": [
            "☑ Ler o problema em voz alta e destacar o que representa o todo antes de trabalhar a parte solicitada.",
            "☑ Resolver um exemplo com desenho na lousa para orientar estudantes com maior dificuldade de abstração.",
            "☑ Acompanhar individualmente a passagem do desenho para o registro numérico no caderno.",
        ],
    }
    return bancos.get(tipo_cdp, [])

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

    if perfil == "matematica" and tipo_cdp in _tipos_matematica_fundamental_cdp():
        texto_especifico = _metodologia_matematica_fundamental_cdp(tipo_cdp, indice_aula)
        if texto_especifico:
            return [_limpar_texto_cdp_contextual(texto_especifico)]

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

def _indice_variacao(partes: list[str], total: int) -> int:
    if total <= 1:
        return 0
    chave = "|".join(str(parte or "") for parte in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total

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
    if perfil == "matematica" and tipo_cdp in _tipos_matematica_fundamental_cdp():
        itens = _acompanhamento_matematica_fundamental_cdp(tipo_cdp)
        if itens:
            return itens[:3]
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
    if perfil == "matematica" and tipo_cdp in _tipos_matematica_fundamental_cdp():
        itens = _acessibilidade_matematica_fundamental_cdp(tipo_cdp)
        if itens:
            return itens[:3]
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

eh_cdp_contextual_disciplina = _eh_cdp_contextual_disciplina
disciplina_base_cdp_contextual = _disciplina_base_cdp_contextual
limpar_tema_cdp_contextual = _limpar_tema_cdp_contextual
formatar_material_cdp_contextual = _formatar_material_cdp_contextual
metodologia_cdp_contextual = _metodologia_cdp_contextual
acompanhamento_cdp_contextual = _acompanhamento_cdp_contextual
acessibilidade_cdp_contextual = _acessibilidade_cdp_contextual
tipo_conteudo_cdp = _tipo_conteudo_cdp
tema_cdp_seguro = _tema_cdp_seguro
limpar_texto_cdp_contextual = _limpar_texto_cdp_contextual
conceito_cdp_contextual = _conceito_cdp_contextual

__all__ = [
    "eh_cdp_contextual_disciplina",
    "disciplina_base_cdp_contextual",
    "limpar_tema_cdp_contextual",
    "formatar_material_cdp_contextual",
    "metodologia_cdp_contextual",
    "acompanhamento_cdp_contextual",
    "acessibilidade_cdp_contextual",
    "tipo_conteudo_cdp",
    "tema_cdp_seguro",
    "limpar_texto_cdp_contextual",
    "conceito_cdp_contextual",
]
