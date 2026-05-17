import os
import re
import unicodedata
import hashlib
from pathlib import Path

import pdfplumber

from config import PDF_TEXTO_LIMITE_CHARS
from core.avaliacao import gerar_acessibilidade_dinamica, gerar_acompanhamento_dinamico
from core.projeto_vida_escopo import buscar_item_projeto_vida, montar_aprendizagem_projeto_vida
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
    titulo = re.sub(r"\s+", " ", linha or "").strip(" -–—:")
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
    return titulo.strip(" -–—:")


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
    if _linha_periodo_ensino(texto):
        return True
    return bool(re.fullmatch(r"(?:[1-4][oº°]?\s*)?bimestre", texto))


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
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
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
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
            if partes:
                break
            continue
        partes.append(titulo)
        if len(partes) >= 2:
            break

    if not partes:
        return ""

    if len(partes) == 1:
        return _limpar_titulo_material(partes[0], disciplina)

    primeira = partes[0].rstrip(" -:")
    if primeira.lower().endswith((" de", " da", " do", " das", " dos", " e")) or len(primeira) <= 28:
        return _limpar_titulo_material(f"{primeira} {partes[1].lstrip('-: ')}".strip(), disciplina)
    return _limpar_titulo_material(primeira, disciplina)


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
    return base in {"cdp-ensinofundamental", "cdpensinofundamental"}


def _disciplina_base_cdp_contextual(texto: str, tema: str, caminho_pdf: str = "") -> str:
    base = _normalizar(f"{Path(caminho_pdf).name} {tema} {texto}")
    opcoes = [
        ("Matemática", ["matematica", "matem"]),
        ("Língua Portuguesa", ["lingua portuguesa", "portugues"]),
        ("Ciências", ["ciencias", "cienc"]),
        ("História", ["historia", "histor"]),
        ("Geografia", ["geografia", "geograf"]),
        ("Arte", ["arte"]),
        ("Biologia", ["biologia", "biolog"]),
        ("Física", ["fisica", "fis"]),
        ("Química", ["quimica", "quim"]),
        ("Língua Inglesa", ["ingles", "lingua inglesa"]),
    ]
    for nome, chaves in opcoes:
        if _contem(base, chaves):
            return nome
    return "Geral"


def _limpar_tema_cdp_contextual(tema: str, disciplina_base: str) -> str:
    texto = re.sub(r"\s+", " ", str(tema or "")).strip(" -:.")
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


def _metodologia_cdp_contextual(perfil: str, tipo: str, tema: str, conceito: str) -> list[str]:
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
        "aplicativo",
        "internet",
        "vídeo",
        "filme",
        "youtube",
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
        "disponível em",
        "http",
        "acesse",
    ]
    saida = str(texto or "")
    for termo in proibidos:
        saida = re.sub(re.escape(termo), "", saida, flags=re.I)
    return re.sub(r"\s+", " ", saida).strip()


def _metodologia_cdp_contextual(perfil: str, tipo: str, tema: str, conceito: str, indice_aula: int = 0) -> list[str]:
    conceito_frase = _conceito_cdp_contextual(perfil, tema, conceito)
    tipo_cdp = _tipo_conteudo_cdp(perfil, tema, conceito)
    exemplo = _exemplo_concreto_cdp(tipo_cdp)

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
    else:
        opcoes = [gerais.get(tipo_cdp, gerais["geral_cdp"])]

    texto = opcoes[indice_aula % len(opcoes)]
    return [_limpar_texto_cdp_contextual(texto)]


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

    if perfil == "educacao_financeira":
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
        tema_base = _normalizar(tema)
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
        base["para_comecar"] = (
            f"Abrir a aula com uma situacao acolhedora relacionada a {tema}, sem exigir exposicao pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participacao."
        )
        base["foco"] = (
            f"Construir o conceito de {conceito} por meio de exemplos escolares e cotidianos, ajudando a turma a "
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
        if tipo in {"credito_endividamento", "investimento_poupanca"} or _contem(base, ["juros", "porcentagem", "parcela", "rendimento", "calculo"]):
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
            abertura = (
                f"Retomar o percurso das aulas anteriores sobre {tema}, destacando os registros, "
                "duvidas e estrategias ja construidos pela turma."
            )
        else:
            abertura = (
                f"Retomar a aula anterior sobre {tema} e conectar os registros ja produzidos "
                "ao novo foco do dia."
            )
        return f"{abertura} {resto}".strip()

    if chave in {"leitura", "contextualizacao", "leitura_analitica", "foco"} and not primeira:
        orientacao = (
            "Relacionar a explicacao aos registros anteriores para que a turma perceba continuidade, "
            "aprofundamento e novos desafios."
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
    linhas = _linhas_relevantes(texto, disciplina, tema)
    conceito = _conceito_principal(linhas, tema)
    perfil = _perfil_disciplina(disciplina)
    if perfil == "matematica" and _normalizar(conceito) in {"matematica", "matemática"}:
        conceito = tema
    tipo = _detectar_tipo_aula(texto, tema, disciplina)
    frases = _frases_por_contexto(perfil, tipo, tema, conceito, turma, texto)
    etapas = []
    for titulo, chave in _etapas_por_perfil(perfil, tipo, texto, tema):
        texto_etapa = frases.get(chave, "").strip()
        if texto_etapa:
            texto_etapa = _ajustar_texto_por_sequencia(
                texto_etapa,
                chave,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
            etapas.append({"titulo": titulo, "texto": texto_etapa})
    return etapas


def _tema_por_texto(texto: str, caminho_pdf: str, disciplina: str) -> str:
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
        if normalizada.startswith(("aula ", "slide ", "pagina ", "página ")):
            if candidatos:
                break
            continue
        candidatos.append(titulo)
        if len(candidatos) >= 2:
            break

    if candidatos:
        titulo = candidatos[0]
        if len(candidatos) > 1 and (
            titulo.lower().endswith((" de", " da", " do", " das", " dos", " e")) or len(titulo) <= 28
        ):
            complemento = candidatos[1].lstrip("-: ").strip()
            separador = " - " if _normalizar(complemento).startswith("parte ") else " "
            titulo = f"{titulo.rstrip(' -:')}{separador}{complemento}".strip()
        titulo = limpar_prefixo_disciplina(titulo)
        if len(titulo) >= 6:
            return titulo[:120]

    titulo_multilinha = limpar_prefixo_disciplina(_extrair_titulo_multilinha(texto, disciplina))
    if len(titulo_multilinha) >= 6:
        return titulo_multilinha[:120]
    for linha in _limpar_linhas(texto):
        titulo = limpar_prefixo_disciplina(_limpar_titulo_material(linha, disciplina))
        if len(titulo) >= 6 and not _linha_generica(titulo, disciplina) and not _normalizar(titulo).startswith(("aula ", "slide ")):
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
    if rotulo and titulo:
        return f"{rotulo} - {titulo}"
    return rotulo or titulo


def _texto_metodologia(metodologia) -> str:
    blocos = []
    for item in metodologia or []:
        if isinstance(item, dict):
            blocos.append(f"{item.get('titulo', '')}\n{item.get('texto', '')}".strip())
        else:
            blocos.append(str(item))
    return "\n\n".join(blocos)


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


def _foco_limpo_aprendizagem(tema: str, conceito: str = "") -> str:
    for candidato in [tema, conceito, "o tema da aula"]:
        texto = re.sub(r"\s+", " ", str(candidato or "")).strip(" .:-")
        if texto and not _trecho_incompleto_aprendizagem(texto):
            return texto[:140]
    return "o tema da aula"


def _sanitizar_aprendizagem(aprendizagem: str, tema: str, conceito: str = "") -> str:
    texto = re.sub(r"\s+", " ", str(aprendizagem or "")).strip()
    texto = re.sub(
        r"^(?:C\d+\s*:\s*)?(?:Habilidades?|Aprendizagem essencial|Compet[eê]ncia)\s*:\s*",
        "",
        texto,
        flags=re.I,
    ).strip()
    texto = re.sub(r"^(?:Habilidades?)\s*:\s*", "", texto, flags=re.I).strip()
    match = _PADRAO_CODIGO_APRENDIZAGEM.search(texto)
    codigo = f"({match.group(1).upper()})" if match else ""

    if _trecho_incompleto_aprendizagem(texto):
        foco = _foco_limpo_aprendizagem(tema, conceito)
        if codigo:
            return f"Habilidade: {codigo} Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."
        return f"Desenvolver habilidades relacionadas ao tema da aula, com foco em {foco}."

    if codigo and not texto.lower().startswith("habilidade:"):
        texto = f"Habilidade: {texto}"
    return texto


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

gerador_inteligente = SistemaGeracaoMetodologica()
_extrator_lib = ExtratorPDF()

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
) -> dict:
    texto = _extrair_texto_pdf(caminho_pdf)
    tema = _tema_por_texto(texto, caminho_pdf, disciplina)
    material_digital = _material_digital_por_texto(texto, caminho_pdf, disciplina, tema)
    numero_aula = _rotulo_aula_material(texto, caminho_pdf).replace("AULA", "", 1).strip()
    cdp_contextual = _eh_cdp_contextual_disciplina(disciplina)
    disciplina_base = _disciplina_base_cdp_contextual(texto, tema, caminho_pdf) if cdp_contextual else disciplina
    perfil = _perfil_disciplina(disciplina_base)
    tipo = _detectar_tipo_aula(texto, tema, disciplina_base)
    escopo_pv = buscar_item_projeto_vida(turma, bimestre, numero_aula) if perfil == "projeto_de_vida" else {}
    aprendizagem_pv = montar_aprendizagem_projeto_vida(escopo_pv) if escopo_pv else ""
    if escopo_pv.get("titulo"):
        tema = escopo_pv["titulo"]
        material_digital = f"AULA {int(numero_aula)} - {tema}" if numero_aula.isdigit() else tema

    if cdp_contextual:
        extracao_cdp = _extrator_lib.extrair(texto, tema)
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
            "tema": tema,
            "material": material_digital,
            "numero_aula": numero_aula,
            "aprendizagem": _sanitizar_aprendizagem(aprendizagem_cdp, tema, conceito_cdp),
            "metodologia": _metodologia_cdp_contextual(perfil, tipo, tema, conceito_cdp, indice_aula),
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
            plano_ia = processar_plano_ia(texto, disciplina, turma, provedor_ia, modelo_ia)
            tema = tema if escopo_pv.get("titulo") else plano_ia.get("tema") or tema
            aprendizagem = aprendizagem_pv or plano_ia.get("aprendizagem", "")
            metodologia = plano_ia.get("metodologia", [])
            metodologia = _variar_linguagem_metodologia(metodologia, disciplina_base, turma, tema)
            metodologia = _ajustar_metodologia_por_sequencia(
                metodologia,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                tema=tema,
            )
            aprendizagem = _sanitizar_aprendizagem(aprendizagem, tema)
            
            desenvolvimento = _texto_metodologia(metodologia)
            
            # Extrair etapas e dados para acompanhamento enriquecido
            etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
            extracao = _extrator_lib.extrair(texto, tema)
            
            return {
                "tema": tema,
                "material": material_digital,
                "numero_aula": numero_aula,
                "aprendizagem": aprendizagem,
                "metodologia": metodologia,
                "acompanhamento": gerar_acompanhamento_aprimorado(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    habilidade=extracao.get("habilidade", ""),
                    etapas_metodologia=etapas_titulos,
                ),
                "acessibilidade": gerar_acessibilidade_aprimorada(
                    tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
                    disciplina=disciplina_base, perfil=perfil, tipo=tipo,
                    recursos_detectados=extracao.get("recursos_detectados"),
                ),
                "ia_usada": True,
                "ia_provedor": provedor_ia,
                "ia_erro": "",
            }
        except Exception as e:
            ia_erro = f"Falha na IA ({provedor_ia}): {str(e)[:150]}. Usando motor heurístico local."
    
    # 2. Fallback heurístico — usa o motor sofisticado do lote.py
    #    em vez do motor fraco do inteligencia_local.py
    metodologia = _montar_etapas_metodologia(
        texto,
        disciplina_base,
        turma,
        tema,
        indice_aula=indice_aula,
        total_aulas=total_aulas,
    )
    metodologia = _variar_linguagem_metodologia(metodologia, disciplina_base, turma, tema)
    
    # Extrair dados estruturados do PDF
    extracao = _extrator_lib.extrair(texto, tema)
    conceito = extracao.get("conceito_extraido", tema)
    habilidade = extracao.get("habilidade", "")
    recursos = extracao.get("recursos_detectados", [])
    
    # Se o extrator encontrou uma habilidade/BNCC no PDF, usa ela diretamente
    if aprendizagem_pv:
        aprendizagem = aprendizagem_pv
        habilidade = aprendizagem_pv
    elif habilidade and len(habilidade) > 15:
        aprendizagem = habilidade
    else:
        verbo = "Aplicar atividades e compreender" if tipo == "pratica" else "Compreender e analisar"
        conceito_aprendizagem = _foco_limpo_aprendizagem(tema, conceito)
        aprendizagem = f"{verbo} os conceitos relacionados a: {conceito_aprendizagem}."
    aprendizagem = _sanitizar_aprendizagem(aprendizagem, tema, conceito)
    
    desenvolvimento = _texto_metodologia(metodologia)
    etapas_titulos = [m.get("titulo", "") for m in metodologia if isinstance(m, dict)]
    
    return {
        "tema": tema,
        "material": material_digital,
        "numero_aula": numero_aula,
        "aprendizagem": aprendizagem,
        "metodologia": metodologia,
        "acompanhamento": gerar_acompanhamento_aprimorado(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            habilidade=habilidade, etapas_metodologia=etapas_titulos,
        ),
        "acessibilidade": gerar_acessibilidade_aprimorada(
            tema=tema, aprendizagem=aprendizagem, desenvolvimento=desenvolvimento,
            disciplina=disciplina_base, perfil=perfil, tipo=tipo,
            recursos_detectados=recursos,
        ),
        "ia_usada": False,
        "ia_provedor": provedor_ia if usar_ia else "",
        "ia_erro": ia_erro,
    }


def processar_varios_pdfs(
    caminhos_pdf,
    disciplina: str,
    turma: str,
    bimestre: str = "",
    usar_ia: bool = False,
    provedor_ia: str = "",
    modelo_ia: str = "",
    dividir_metodologia: bool = False,
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
        )
        if dividir_metodologia:
            texto = _texto_metodologia(aula["metodologia"])
            parte1, parte2 = processar_pdf_e_dividir_metodologia(texto)
            if idx % 2 == 0:
                aula["metodologia"] = [{"titulo": "Primeiro momento", "texto": parte1}]
            else:
                aula["tema"] = f"{aula['tema']} - continuidade"
                aula["metodologia"] = [{"titulo": "Segundo momento", "texto": parte2}]
            aulas.append(aula)
        else:
            aulas.append(aula)
    return aulas
