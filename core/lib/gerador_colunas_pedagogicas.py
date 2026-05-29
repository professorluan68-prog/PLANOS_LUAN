from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List

from core.lib.extrator_blocos_pedagogicos import extrair_blocos_pedagogicos


def norm(txt: str) -> str:
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt).strip().lower()


def clean(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "")).strip()


def sentenca(txt: str) -> str:
    txt = clean(txt)
    if not txt:
        return ""
    if txt[-1] not in ".!?":
        txt += "."
    return txt[0].upper() + txt[1:]


def dedup(seq: List[str]) -> List[str]:
    out = []
    seen = set()
    for item in seq:
        key = norm(item)
        if key and key not in seen:
            seen.add(key)
            out.append(clean(item))
    return out


def deterministic_choice(options: List[str], seed_key: str) -> str:
    if not options:
        return ""
    rng = random.Random(seed_key)
    return rng.choice(options)


@dataclass
class PistasPedagogicas:
    titulo: str = ""
    conteudos: List[str] = field(default_factory=list)
    objetivos: List[str] = field(default_factory=list)
    vocabulario_chave: List[str] = field(default_factory=list)
    tem_para_comecar: bool = False
    tem_relembre: bool = False
    tem_foco_conteudo: bool = False
    tem_pause_responda: bool = False
    tem_atividade_final: bool = False
    tem_video: bool = False
    tem_grafico: bool = False
    tem_tabela: bool = False
    tem_calculo: bool = False
    tem_comparacao: bool = False
    tem_estudo_caso: bool = False
    tem_situacao_problema: bool = False
    tecnicas_lemov: List[str] = field(default_factory=list)
    perfil: str = "geral"
    verbo_objetivo: str = "compreender"


TECNICAS_LEMOV = {
    "virem e conversem": "Virem e conversem",
    "todo mundo escreve": "Todo mundo escreve",
    "com suas palavras": "Com suas palavras",
    "um passo de cada vez": "Um passo de cada vez",
    "de olho no modelo": "De olho no modelo",
    "hora da leitura": "Hora da leitura",
    "pausa produtiva": "Pausa produtiva",
}

VERBOS_OBJETIVO = [
    "analisar", "comparar", "interpretar", "reconhecer", "explicar",
    "avaliar", "identificar", "planejar", "aplicar", "justificar",
]

PALAVRAS_GRAFICO = [
    "grafico", "gráfico", "linha", "coluna", "eixo", "dados", "ipca",
]

PALAVRAS_TABELA = [
    "tabela", "quadro", "comparativo", "categoria", "percentual",
]

PALAVRAS_CALCULO = [
    "juros", "porcentagem", "percentual", "cálculo", "calculo",
    "valor", "parcela", "saldo", "rendimento", "rentabilidade",
]

PALAVRAS_COMPARACAO = [
    "comparar", "comparação", "comparacao", "diferença",
    "diferenca", "vantagens", "riscos", "alternativas",
]

PALAVRAS_ESTUDO_CASO = [
    "ana tem", "gabriel recebeu", "joão recebeu", "joao recebeu",
    "carlos ganhou", "seu personagem", "situação", "situacao",
]


def extrair_bullets_secao(texto: str, marcador_secao: str) -> List[str]:
    linhas = [l.strip() for l in texto.replace("●", "\n● ").splitlines() if l.strip()]
    secao = False
    itens = []

    for linha in linhas:
        n = norm(linha)
        if marcador_secao in n:
            secao = True
            continue
        if secao and ("objetivos" in n or "conteudos" in n) and marcador_secao not in n:
            break
        if secao and linha.startswith("●"):
            itens.append(linha.lstrip("●").strip(" ;:."))

    return dedup(itens)


def extrair_conteudos_objetivos(texto: str) -> Dict[str, List[str]]:
    return {
        "conteudos": extrair_bullets_secao(texto, "conteudos"),
        "objetivos": extrair_bullets_secao(texto, "objetivos"),
    }


def detectar_tecnicas(texto: str) -> List[str]:
    t = norm(texto)
    achadas = []
    for chave, nome in TECNICAS_LEMOV.items():
        if chave in t:
            achadas.append(nome)
    return dedup(achadas)


def detectar_verbo_objetivo(objetivos: List[str]) -> str:
    n = norm(" ".join(objetivos))
    for verbo in VERBOS_OBJETIVO:
        if verbo in n:
            return verbo
    return "compreender"


def extrair_vocabulario_chave(conteudos: List[str], objetivos: List[str], titulo: str) -> List[str]:
    candidatos = []
    if titulo:
        titulo_limpo = re.sub(r"^\s*aula\s*\d+\s*-\s*", "", titulo, flags=re.I)
        candidatos.append(titulo_limpo)
    candidatos.extend(conteudos[:4])

    for obj in objetivos[:4]:
        obj_limpo = re.sub(
            r"^(explicar|reconhecer|analisar|comparar|avaliar|identificar|interpretar|planejar|aplicar|justificar)\s+",
            "",
            obj,
            flags=re.I,
        )
        candidatos.append(obj_limpo.strip(" ;:."))

    saida = []
    for candidato in candidatos:
        candidato = clean(candidato)
        if 4 <= len(candidato) <= 90:
            saida.append(candidato)
    return dedup(saida)[:6]


def classificar_perfil(texto: str, titulo: str, conteudos: List[str], objetivos: List[str]) -> str:
    base = " ".join([texto, titulo] + conteudos + objetivos)
    n = norm(base)
    if any(p in n for p in [norm(x) for x in PALAVRAS_GRAFICO]):
        return "grafico"
    if any(p in n for p in [norm(x) for x in PALAVRAS_CALCULO]):
        return "calculo"
    if any(p in n for p in [norm(x) for x in PALAVRAS_COMPARACAO]):
        return "comparacao"
    if any(p in n for p in [norm(x) for x in PALAVRAS_ESTUDO_CASO]):
        return "decisao"
    if "conceito" in n or "o que e" in n:
        return "conceito"
    return "geral"


def extrair_pistas(texto_pdf: str, titulo_aula: str) -> PistasPedagogicas:
    texto_pdf = texto_pdf or ""
    listas = extrair_conteudos_objetivos(texto_pdf)
    conteudos = listas["conteudos"]
    objetivos = listas["objetivos"]
    blocos = extrair_blocos_pedagogicos(texto_pdf)
    n = norm(texto_pdf)

    pistas = PistasPedagogicas(
        titulo=clean(titulo_aula),
        conteudos=conteudos,
        objetivos=objetivos,
        vocabulario_chave=extrair_vocabulario_chave(conteudos, objetivos, titulo_aula),
        tem_para_comecar=bool(blocos.get("Para comecar")) or ("para comecar" in n),
        tem_relembre=bool(blocos.get("Relembre")) or ("relembre" in n),
        tem_foco_conteudo=bool(blocos.get("Foco no conteudo")) or ("foco no conteudo" in n),
        tem_pause_responda=bool(blocos.get("Pause e responda")) or ("pause e responda" in n),
        tem_atividade_final=bool(blocos.get("Na pratica")) or ("na pratica" in n or "desafio" in n or "roda de conversa" in n),
        tem_video=("link para video" in n or "assista ao video" in n),
        tem_grafico=any(p in n for p in [norm(x) for x in PALAVRAS_GRAFICO]),
        tem_tabela=any(p in n for p in [norm(x) for x in PALAVRAS_TABELA]),
        tem_calculo=any(p in n for p in [norm(x) for x in PALAVRAS_CALCULO]),
        tem_comparacao=any(p in n for p in [norm(x) for x in PALAVRAS_COMPARACAO]),
        tem_estudo_caso=any(p in n for p in [norm(x) for x in PALAVRAS_ESTUDO_CASO]),
        tem_situacao_problema=("problema" in n or "situação" in texto_pdf.lower() or "situacao" in n),
        tecnicas_lemov=detectar_tecnicas(texto_pdf),
    )
    pistas.perfil = classificar_perfil(texto_pdf, titulo_aula, conteudos, objetivos)
    pistas.verbo_objetivo = detectar_verbo_objetivo(objetivos)
    return pistas


def sanitizar_texto_pedagogico(txt: str) -> str:
    txt = clean(txt)
    txt = txt.replace("..", ".")
    txt = re.sub(r"\s+,", ",", txt)
    txt = re.sub(r"\s+\.", ".", txt)
    txt = re.sub(r"\b2o bimestre\b", "", txt, flags=re.I)
    txt = re.sub(r"\bensino medio\b", "", txt, flags=re.I)
    txt = re.sub(r"\baula \d+\b", "", txt, flags=re.I)
    txt = txt.strip(" -:;,")
    txt = clean(txt)
    return sentenca(txt)


def bloquear_contaminacao_tematica(texto: str, pistas: PistasPedagogicas) -> str:
    n = norm(texto)
    if pistas.perfil in {"grafico", "conceito", "comparacao"} and not pistas.tem_calculo:
        for termo in ["parcelas", "endividamento", "credito", "crédito", "custo total"]:
            if norm(termo) in n:
                return ""
    return texto


def frase_inicial(pistas: PistasPedagogicas) -> str:
    opcoes = []
    if pistas.tem_para_comecar or pistas.tem_relembre:
        opcoes.append("Iniciar a aula retomando a situação apresentada no material e mobilizando conhecimentos prévios da turma sobre o tema.")
    if pistas.tem_estudo_caso or pistas.tem_situacao_problema:
        opcoes.append("Iniciar com a situação-problema do material, incentivando a turma a levantar hipóteses e antecipar possíveis caminhos de análise.")
    opcoes.append("Iniciar a aula apresentando o tema central e incentivando os estudantes a relacioná-lo a situações do cotidiano.")
    return deterministic_choice(opcoes, pistas.titulo + "|inicio")


def frase_foco(pistas: PistasPedagogicas) -> str:
    if pistas.perfil == "grafico":
        return "Conduzir a leitura orientada de gráficos, tabelas ou dados do material, ajudando a turma a interpretar informações, comparar valores e construir conclusões com base nas evidências apresentadas."
    if pistas.perfil == "calculo":
        return "Desenvolver o conteúdo com mediação passo a passo, destacando dados, operações e interpretação dos resultados, de modo que o cálculo esteja ligado à compreensão da situação estudada."
    if pistas.perfil == "comparacao":
        return "Explorar comparações presentes no material, destacando diferenças, vantagens, limites e critérios de escolha de forma crítica e contextualizada."
    if pistas.perfil == "decisao":
        return "Conduzir a análise do caso apresentado, discutindo alternativas, consequências e critérios de decisão, com foco em escolhas mais conscientes e justificadas."
    if pistas.perfil == "conceito":
        return "Sistematizar os conceitos centrais da aula com explicações claras, exemplos próximos da realidade dos estudantes e retomada do vocabulário principal."
    return "Desenvolver o conteúdo central da aula com explicação dialogada, exemplos do material e participação orientada da turma."


def frase_pause(pistas: PistasPedagogicas) -> str:
    if pistas.tem_pause_responda:
        return "Realizar uma pausa de verificação da aprendizagem para que os estudantes comparem respostas, justifiquem ideias e revisem o raciocínio antes de avançar."
    return ""


def frase_pratica(pistas: PistasPedagogicas) -> str:
    if pistas.perfil == "grafico":
        return "Propor atividade de aplicação em que os estudantes interpretem dados, registrem conclusões e expliquem o que as informações revelam sobre o tema estudado."
    if pistas.perfil == "calculo":
        return "Encaminhar atividade com registro dos cálculos e breve justificativa, reforçando a relação entre procedimento, resultado e tomada de decisão."
    if pistas.perfil == "comparacao":
        return "Organizar atividade de comparação entre alternativas, solicitando que os estudantes registrem a escolha feita e os critérios utilizados para justificá-la."
    if pistas.perfil == "decisao":
        return "Propor situação prática para que a turma discuta possibilidades, defenda escolhas e relacione o conteúdo a decisões mais responsáveis."
    return "Propor atividade de aplicação para que os estudantes retomem o conteúdo, organizem ideias principais e consolidem a aprendizagem."


def frase_encerramento(pistas: PistasPedagogicas) -> str:
    destaque = ", ".join(pistas.vocabulario_chave[:3])
    if destaque:
        return f"Encerrar a aula com síntese dos pontos principais, retomando especialmente {destaque} e verificando o que a turma conseguiu compreender."
    return "Encerrar a aula com síntese dos pontos principais e retomada das aprendizagens construídas."


def complemento_tecnica(tecnica: str, etapa: str) -> str:
    mapa = {
        ("Virem e conversem", "inicio"): "Aplicar a técnica Virem e conversem no momento inicial para ampliar a participação e socializar hipóteses.",
        ("Todo mundo escreve", "pratica"): "Utilizar a técnica Todo mundo escreve para favorecer a organização do pensamento antes da socialização das respostas.",
        ("Com suas palavras", "encerramento"): "Retomar a síntese final com a técnica Com suas palavras, incentivando os estudantes a reelaborarem o conteúdo com autonomia.",
        ("Um passo de cada vez", "foco"): "Conduzir a explicação com a técnica Um passo de cada vez, organizando o conteúdo em etapas claras e progressivas.",
        ("De olho no modelo", "foco"): "Utilizar a técnica De olho no modelo para apresentar um exemplo orientador antes da atividade principal.",
        ("Hora da leitura", "foco"): "Promover leitura orientada do material com a técnica Hora da leitura, destacando informações essenciais e pontos de atenção.",
        ("Pausa produtiva", "pause"): "Realizar uma Pausa produtiva para revisão breve do raciocínio antes da continuidade da atividade.",
    }
    return mapa.get((tecnica, etapa), "")


def _blocos_metodologia(pistas: PistasPedagogicas) -> List[Dict[str, str]]:
    blocos = []
    blocos.append({"titulo": "Para comecar", "texto": frase_inicial(pistas)})

    if "Virem e conversem" in pistas.tecnicas_lemov:
        comp = complemento_tecnica("Virem e conversem", "inicio")
        if comp:
            blocos.append({"titulo": "Interacao inicial", "texto": comp})

    blocos.append({"titulo": "Foco no conteudo", "texto": frase_foco(pistas)})

    for tecnica in ("Um passo de cada vez", "De olho no modelo", "Hora da leitura"):
        if tecnica in pistas.tecnicas_lemov:
            comp = complemento_tecnica(tecnica, "foco")
            if comp:
                blocos.append({"titulo": tecnica, "texto": comp})
                break

    pause = frase_pause(pistas)
    if pause:
        blocos.append({"titulo": "Pause e responda", "texto": pause})
        if "Pausa produtiva" in pistas.tecnicas_lemov:
            comp = complemento_tecnica("Pausa produtiva", "pause")
            if comp:
                blocos.append({"titulo": "Pausa produtiva", "texto": comp})

    blocos.append({"titulo": "Na pratica", "texto": frase_pratica(pistas)})

    if "Todo mundo escreve" in pistas.tecnicas_lemov:
        comp = complemento_tecnica("Todo mundo escreve", "pratica")
        if comp:
            blocos.append({"titulo": "Registro individual", "texto": comp})

    blocos.append({"titulo": "Encerramento", "texto": frase_encerramento(pistas)})

    if "Com suas palavras" in pistas.tecnicas_lemov:
        comp = complemento_tecnica("Com suas palavras", "encerramento")
        if comp:
            blocos.append({"titulo": "Com suas palavras", "texto": comp})

    saida = []
    for bloco in blocos:
        texto = bloquear_contaminacao_tematica(sanitizar_texto_pedagogico(bloco.get("texto", "")), pistas)
        if texto:
            saida.append({"titulo": bloco["titulo"], "texto": texto})

    uniq = []
    seen = set()
    for bloco in saida:
        chave = norm(bloco["titulo"] + " " + bloco["texto"])
        if chave and chave not in seen:
            seen.add(chave)
            uniq.append(bloco)
    return uniq[:6]


def gerar_metodologia(pistas: PistasPedagogicas) -> str:
    blocos = _blocos_metodologia(pistas)
    return "\n".join(f"{i+1}. {bloco['texto']}" for i, bloco in enumerate(blocos))


BANCO_ACOMPANHAMENTO = {
    "grafico": [
        "Verificar se os estudantes interpretam corretamente os dados, eixos, valores e informações apresentadas em gráficos ou tabelas do material.",
        "Observar se conseguem relacionar os dados analisados ao conceito central da aula, explicando conclusões com clareza.",
        "Conferir se os registros finais apresentam comparação de informações e justificativas coerentes com a discussão realizada.",
        "Acompanhar se a turma utiliza os dados do material para sustentar respostas, evitando conclusões sem evidências.",
    ],
    "calculo": [
        "Verificar se os estudantes identificam corretamente os dados necessários e compreendem o que está sendo pedido em cada situação.",
        "Observar se realizam os procedimentos com apoio progressivamente menor, explicando o significado dos resultados encontrados.",
        "Conferir se os registros finais articulam cálculo, interpretação e conclusão, e não apenas a resposta numérica.",
        "Acompanhar se a turma reconhece a relação entre resultado obtido e decisão financeira discutida na aula.",
    ],
    "comparacao": [
        "Verificar se os estudantes identificam diferenças, vantagens, limites e critérios de escolha entre as alternativas analisadas.",
        "Observar se justificam suas respostas com base nas informações do material, evitando respostas apenas intuitivas.",
        "Conferir se os registros finais evidenciam tomada de decisão com coerência, argumentação e uso do vocabulário trabalhado.",
        "Acompanhar se a turma compara alternativas sem perder de vista o objetivo central da aula.",
    ],
    "decisao": [
        "Verificar se os estudantes compreendem a situação analisada e reconhecem os elementos importantes para a tomada de decisão.",
        "Observar se conseguem defender escolhas com justificativas coerentes, considerando consequências e critérios discutidos na aula.",
        "Conferir se os registros finais expressam posicionamento claro, argumentação e retomada dos conceitos trabalhados.",
        "Acompanhar se a turma articula informações do material com decisões mais conscientes e responsáveis.",
    ],
    "conceito": [
        "Verificar se os estudantes compreendem os conceitos centrais da aula e conseguem explicá-los com suas próprias palavras.",
        "Observar a participação nas discussões e a retomada do vocabulário principal durante as intervenções orais e escritas.",
        "Conferir se os registros finais apresentam ideias organizadas, exemplos coerentes e compreensão progressiva do tema.",
        "Acompanhar se a turma diferencia corretamente os conceitos trabalhados, evitando confusões entre noções próximas.",
    ],
    "geral": [
        "Verificar se os estudantes compreendem o tema central da aula e reconhecem as ideias principais trabalhadas.",
        "Observar a participação, os registros e a forma como justificam respostas ao longo das atividades propostas.",
        "Conferir se as produções finais apresentam clareza, coerência e retomada dos conceitos estudados.",
        "Acompanhar se os estudantes utilizam o vocabulário da aula de forma progressivamente mais autônoma.",
    ],
}


def gerar_acompanhamento(pistas: PistasPedagogicas) -> List[str]:
    base = BANCO_ACOMPANHAMENTO.get(pistas.perfil, BANCO_ACOMPANHAMENTO["geral"])[:]
    rng = random.Random(pistas.titulo + "|acompanhamento|" + pistas.perfil)
    rng.shuffle(base)
    return [sentenca(item) for item in dedup(base)[:3]]


BANCO_ACESSIBILIDADE = {
    "grafico": [
        "Disponibilizar leitura guiada de gráficos e tabelas, destacando título, eixos, valores e comparação entre os dados apresentados.",
        "Oferecer apoio visual com palavras-chave e perguntas orientadoras para ajudar na interpretação das informações do material.",
        "Permitir diferentes formas de registro, como tópicos, respostas curtas, marcações no gráfico ou explicação oral mediada.",
        "Retomar coletivamente como localizar dados relevantes antes do trabalho individual.",
    ],
    "calculo": [
        "Disponibilizar resolução em etapas, com destaque visual para dados, operação a realizar e interpretação do resultado.",
        "Oferecer mediação com exemplos semelhantes antes da atividade autônoma, reduzindo a sobrecarga cognitiva da tarefa.",
        "Permitir uso de esquemas, anotações guiadas, cálculo acompanhado e explicação oral do raciocínio como forma de registro.",
        "Apresentar comandos curtos e sequenciados, com conferência coletiva de cada etapa da atividade.",
    ],
    "comparacao": [
        "Organizar quadro comparativo ou esquema visual para apoiar a análise entre alternativas, critérios e consequências.",
        "Apresentar comandos curtos e objetivos, com retomada coletiva das etapas da atividade antes do registro individual.",
        "Permitir registro em tópicos, frases curtas, tabela simples ou resposta oral mediada, conforme as necessidades observadas.",
        "Destacar visualmente semelhanças e diferenças para facilitar a tomada de decisão durante a atividade.",
    ],
    "decisao": [
        "Disponibilizar roteiro com perguntas orientadoras para apoiar a análise da situação apresentada e a justificativa das escolhas.",
        "Retomar oralmente os critérios de decisão com exemplos simples antes da produção individual ou em dupla.",
        "Permitir diferentes formas de registro, como tópicos, esquema, frases curtas ou resposta oral mediada.",
        "Oferecer apoio individual na organização das ideias, especialmente para estudantes com dificuldade em justificar respostas.",
    ],
    "conceito": [
        "Disponibilizar glossário com palavras-chave e exemplos simples para apoiar a compreensão do vocabulário da aula.",
        "Retomar oralmente os conceitos principais com apoio de esquema, quadro ou síntese visual construída com a turma.",
        "Permitir diferentes formas de expressão do entendimento, como tópicos, frases curtas, desenho explicativo ou resposta oral mediada.",
        "Utilizar exemplos concretos do cotidiano para apoiar a compreensão de termos mais abstratos.",
    ],
    "geral": [
        "Disponibilizar roteiro com palavras-chave e perguntas orientadoras para apoiar a compreensão da atividade.",
        "Realizar retomadas coletivas dos comandos e oferecer mediação individual conforme as necessidades observadas.",
        "Permitir diferentes formas de registro, como tópicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        "Organizar momentos de apoio em duplas para favorecer compreensão e participação.",
    ],
}


def gerar_acessibilidade(pistas: PistasPedagogicas) -> List[str]:
    base = BANCO_ACESSIBILIDADE.get(pistas.perfil, BANCO_ACESSIBILIDADE["geral"])[:]
    rng = random.Random(pistas.titulo + "|acessibilidade|" + pistas.perfil)
    rng.shuffle(base)
    return [sentenca(item) for item in dedup(base)[:3]]


def montar_colunas_pedagogicas(texto_pdf: str, titulo_aula: str) -> Dict[str, object]:
    pistas = extrair_pistas(texto_pdf, titulo_aula)
    return {
        "pistas": pistas,
        "desenvolvimento": gerar_metodologia(pistas),
        "metodologia_blocos": _blocos_metodologia(pistas),
        "acompanhamento_aprendizagem": gerar_acompanhamento(pistas),
        "acessibilidade": gerar_acessibilidade(pistas),
    }
