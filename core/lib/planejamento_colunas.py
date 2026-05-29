from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List


def _norm(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()


def _limpar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def _capitalizar_frase(texto: str) -> str:
    texto = _limpar_espacos(texto)
    if not texto:
        return ""
    return texto[0].upper() + texto[1:]


def _primeira_frase(texto: str, limite: int = 180) -> str:
    texto = _limpar_espacos(texto)
    if not texto:
        return ""
    partes = re.split(r"(?<=[.!?])\s+", texto)
    frase = partes[0] if partes else texto
    if len(frase) > limite:
        frase = frase[:limite].rsplit(" ", 1)[0] + "..."
    return frase


def _deduplicar_linhas(itens: List[str]) -> List[str]:
    vistos = set()
    saida = []
    for item in itens:
        chave = _norm(item)
        if chave and chave not in vistos:
            vistos.add(chave)
            saida.append(_limpar_espacos(item))
    return saida


@dataclass
class PistasPDF:
    titulo: str = ""
    tema_central: str = ""
    objetivos: List[str] = field(default_factory=list)
    conteudos: List[str] = field(default_factory=list)
    possui_para_comecar: bool = False
    possui_foco_conteudo: bool = False
    possui_pause_responda: bool = False
    possui_atividade_final: bool = False
    possui_grafico: bool = False
    possui_tabela: bool = False
    possui_comparacao: bool = False
    possui_calculo: bool = False
    possui_estudo_caso: bool = False
    possui_video: bool = False
    tecnicas_lemov: List[str] = field(default_factory=list)
    vocabulario_chave: List[str] = field(default_factory=list)
    perfil_aula: str = "geral"


LEMOV_MAP = {
    "virem e conversem": "Virem e conversem",
    "todo mundo escreve": "Todo mundo escreve",
    "com suas palavras": "Com suas palavras",
    "de olho no modelo": "De olho no modelo",
    "pausa produtiva": "Pausa produtiva",
    "turn and talk": "Virem e conversem",
    "everyone writes": "Todo mundo escreve",
}

PALAVRAS_GRAFICO = [
    "grafico", "grafico", "colunas", "linha", "eixo", "historico", "historico", "ipca",
]

PALAVRAS_TABELA = [
    "tabela", "quadro", "comparativo", "categoria", "percentual",
]

PALAVRAS_CALCULO = [
    "calcule", "calculo", "calculo", "juros", "porcentagem", "parcelas", "valor", "rendimento",
]

PALAVRAS_COMPARACAO = [
    "comparar", "comparativo", "diferenca", "diferenca", "vantagens", "riscos", "opcoes", "opcoes",
]

PALAVRAS_ESTUDO_CASO = [
    "ana tem", "gabriel recebeu", "joao recebeu", "carlos ganhou", "seu personagem",
]


def extrair_listas_de_conteudo(texto: str) -> Dict[str, List[str]]:
    texto_limpo = texto.replace("●", "\n● ")
    linhas = [l.strip() for l in texto_limpo.splitlines() if l.strip()]

    conteudos = []
    objetivos = []
    secao = None

    for linha in linhas:
        n = _norm(linha)

        if "conteudos" in n or "conteudos" in _norm(linha):
            secao = "conteudos"
            continue
        if "objetivos" in n:
            secao = "objetivos"
            continue

        if linha.startswith("●"):
            valor = linha.lstrip("●").strip(" ;:.")
            if secao == "conteudos":
                conteudos.append(valor)
            elif secao == "objetivos":
                objetivos.append(valor)

    return {
        "conteudos": _deduplicar_linhas(conteudos),
        "objetivos": _deduplicar_linhas(objetivos),
    }


def detectar_tecnicas_lemov(texto: str) -> List[str]:
    t = _norm(texto)
    encontradas = []
    for chave, nome in LEMOV_MAP.items():
        if chave in t:
            encontradas.append(nome)
    return _deduplicar_linhas(encontradas)


def detectar_vocabulario_chave(texto: str, conteudos: List[str], objetivos: List[str]) -> List[str]:
    candidatos = []
    base = conteudos[:]
    for obj in objetivos:
        obj_limpo = re.sub(
            r"^(explicar|reconhecer|analisar|comparar|avaliar|identificar)\s+",
            "",
            obj,
            flags=re.I,
        )
        candidatos.append(obj_limpo.strip(" ;:."))

    candidatos.extend(base)

    palavras_fortes = []
    for candidato in candidatos:
        c_limpo = _limpar_espacos(candidato)
        if 4 <= len(c_limpo) <= 80:
            palavras_fortes.append(c_limpo)

    return _deduplicar_linhas(palavras_fortes)[:6]


def classificar_perfil_aula(texto: str, titulo: str, conteudos: List[str], objetivos: List[str]) -> str:
    base = " ".join([texto, titulo] + conteudos + objetivos)
    n = _norm(base)

    if any(p in n for p in PALAVRAS_GRAFICO):
        return "grafico"
    if any(p in n for p in PALAVRAS_CALCULO):
        return "calculo"
    if any(p in n for p in PALAVRAS_COMPARACAO):
        return "comparacao"
    if any(p in n for p in PALAVRAS_ESTUDO_CASO):
        return "decisao"
    if "conceito" in n or "o que e" in n or "o que e" in _norm(base):
        return "conceitos"
    return "geral"


def extrair_pistas_pdf(texto_pdf: str, titulo_aula: str = "") -> PistasPDF:
    texto = texto_pdf or ""
    listas = extrair_listas_de_conteudo(texto)

    conteudos = listas["conteudos"]
    objetivos = listas["objetivos"]
    tecnicas = detectar_tecnicas_lemov(texto)
    texto_norm = _norm(texto)

    return PistasPDF(
        titulo=_limpar_espacos(titulo_aula),
        tema_central=_limpar_espacos(titulo_aula),
        objetivos=objetivos,
        conteudos=conteudos,
        possui_para_comecar=("para comecar" in texto_norm),
        possui_foco_conteudo=("foco no conteudo" in texto_norm),
        possui_pause_responda=("pause e responda" in texto_norm),
        possui_atividade_final=("na pratica" in texto_norm or "desafio" in texto_norm or "roda de conversa" in texto_norm),
        possui_grafico=any(p in texto_norm for p in [_norm(x) for x in PALAVRAS_GRAFICO]),
        possui_tabela=any(p in texto_norm for p in [_norm(x) for x in PALAVRAS_TABELA]),
        possui_comparacao=any(p in texto_norm for p in [_norm(x) for x in PALAVRAS_COMPARACAO]),
        possui_calculo=any(p in texto_norm for p in [_norm(x) for x in PALAVRAS_CALCULO]),
        possui_estudo_caso=any(p in texto_norm for p in [_norm(x) for x in PALAVRAS_ESTUDO_CASO]),
        possui_video=("link para video" in texto_norm or "assista ao video" in texto_norm or "assista ao video" in texto_norm),
        tecnicas_lemov=tecnicas,
        vocabulario_chave=detectar_vocabulario_chave(texto, conteudos, objetivos),
        perfil_aula=classificar_perfil_aula(texto, titulo_aula, conteudos, objetivos),
    )


def _frase_entrada(pistas: PistasPDF) -> str:
    if pistas.possui_estudo_caso:
        return "Retomar a situacao apresentada no material e levantar hipoteses com a turma sobre escolhas, consequencias e possibilidades de decisao."
    if pistas.possui_para_comecar:
        return "Iniciar com a questao disparadora do material, mobilizando conhecimentos previos e aproximando o tema do cotidiano dos estudantes."
    return "Iniciar a aula retomando o tema central e levantando conhecimentos previos da turma."


def _frase_foco(pistas: PistasPDF) -> str:
    base_conteudos = ", ".join(pistas.conteudos[:3])

    if pistas.perfil_aula == "grafico":
        return "Conduzir a leitura orientada dos dados e graficos do material, ajudando a turma a interpretar informacoes, comparar valores e relacionar os resultados ao tema estudado."
    if pistas.perfil_aula == "comparacao":
        return "Explorar comparacoes presentes no material, destacando diferencas, vantagens, limites e criterios de escolha de forma critica."
    if pistas.perfil_aula == "calculo":
        return "Desenvolver a analise dos exemplos do material com mediacao passo a passo, destacando dados, operacoes e o significado dos resultados obtidos."
    if pistas.perfil_aula == "conceitos":
        return "Sistematizar os conceitos centrais da aula com explicacoes claras, exemplos proximos da realidade dos estudantes e retomada do vocabulario principal."
    if base_conteudos:
        return f"Desenvolver o conteudo central da aula, com foco em {base_conteudos}, articulando explicacao, exemplos e participacao da turma."
    return "Desenvolver o conteudo central da aula com mediacao do professor, exemplos e participacao dos estudantes."


def _frase_pause(pistas: PistasPDF) -> str:
    if pistas.possui_pause_responda:
        return "Realizar uma pausa de verificacao para que os estudantes justifiquem respostas, comparem alternativas e revisem o raciocinio antes de avancar."
    return ""


def _frase_pratica(pistas: PistasPDF) -> str:
    if pistas.perfil_aula == "grafico":
        return "Propor uma atividade de aplicacao em que os estudantes interpretem informacoes visuais, registrem conclusoes e expliquem o que os dados revelam."
    if pistas.perfil_aula == "comparacao":
        return "Organizar uma atividade de comparacao entre alternativas, solicitando que os estudantes registrem a escolha feita e os criterios utilizados."
    if pistas.perfil_aula == "calculo":
        return "Propor aplicacao orientada com registro dos calculos e breve justificativa sobre a decisao ou conclusao construida a partir dos resultados."
    if pistas.perfil_aula == "decisao":
        return "Encaminhar uma situacao pratica para que a turma discuta possibilidades, defenda escolhas e relacione o conteudo a decisoes mais conscientes."
    return "Propor uma atividade de aplicacao para que os estudantes retomem o conteudo, registrem ideias principais e consolidem a aprendizagem."


def _frase_encerramento(pistas: PistasPDF) -> str:
    voc = ", ".join(pistas.vocabulario_chave[:3])
    if voc:
        return f"Encerrar a aula com sintese dos pontos principais, retomando especialmente {voc} e verificando o que a turma conseguiu compreender."
    return "Encerrar a aula com sintese dos pontos principais e retomada das aprendizagens construidas."


def _aplicar_tecnicas_lemov(blocos: List[Dict[str, str]], tecnicas: List[str]) -> List[Dict[str, str]]:
    if not tecnicas:
        return blocos

    ajustes = blocos[:]
    mapa = {
        "Virem e conversem": {
            "titulo": "Interacao inicial",
            "texto": "Aplicar a tecnica Virem e conversem no momento inicial para ampliar a participacao e socializar hipoteses.",
        },
        "Todo mundo escreve": {
            "titulo": "Registro individual",
            "texto": "Solicitar registro individual com a tecnica Todo mundo escreve, favorecendo organizacao do pensamento e participacao de toda a turma.",
        },
        "Com suas palavras": {
            "titulo": "Retomada autoral",
            "texto": "Retomar a explicacao com a tecnica Com suas palavras, incentivando os estudantes a reelaborarem o conteudo com autonomia.",
        },
        "De olho no modelo": {
            "titulo": "Modelagem",
            "texto": "Usar a tecnica De olho no modelo para apresentar um exemplo orientador antes da producao ou resolucao proposta.",
        },
        "Pausa produtiva": {
            "titulo": "Pausa produtiva",
            "texto": "Realizar uma Pausa produtiva para revisao breve do raciocinio e ajuste das respostas antes da continuidade da atividade.",
        },
    }

    complementos = [mapa[t] for t in tecnicas if t in mapa]
    if complementos:
        ajustes.insert(1, complementos[0])
    if len(complementos) > 1:
        ajustes.insert(3, complementos[1])
    return ajustes


def _blocos_metodologia_base(pistas: PistasPDF) -> List[Dict[str, str]]:
    blocos = [
        {"titulo": "Para comecar", "texto": _frase_entrada(pistas)},
        {"titulo": "Foco no conteudo", "texto": _frase_foco(pistas)},
        {"titulo": "Pause e responda", "texto": _frase_pause(pistas)},
        {"titulo": "Na pratica", "texto": _frase_pratica(pistas)},
        {"titulo": "Encerramento", "texto": _frase_encerramento(pistas)},
    ]
    blocos = [bloco for bloco in blocos if bloco.get("texto")]
    blocos = _aplicar_tecnicas_lemov(blocos, pistas.tecnicas_lemov)
    return blocos[:6]


def gerar_metodologia_curta(pistas: PistasPDF) -> str:
    blocos = _blocos_metodologia_base(pistas)
    return "\n".join(f"{i+1}. {_capitalizar_frase(bloco['texto'])}" for i, bloco in enumerate(blocos))


def gerar_metodologia_blocos(pistas: PistasPDF) -> List[Dict[str, str]]:
    return [
        {"titulo": bloco["titulo"], "texto": _capitalizar_frase(bloco["texto"])}
        for bloco in _blocos_metodologia_base(pistas)
        if bloco.get("texto")
    ]


def gerar_acompanhamento_3_itens(pistas: PistasPDF) -> List[str]:
    if pistas.perfil_aula == "grafico":
        itens = [
            "Verificar se os estudantes interpretam corretamente os dados, eixos, valores e informacoes apresentadas em graficos ou tabelas do material.",
            "Observar se conseguem relacionar os dados analisados ao conceito central da aula, explicando conclusoes com clareza.",
            "Conferir se os registros finais apresentam comparacao de informacoes e justificativas coerentes com a discussao realizada.",
        ]
    elif pistas.perfil_aula == "comparacao":
        itens = [
            "Verificar se os estudantes identificam diferencas, vantagens, limites e criterios de escolha entre as alternativas analisadas.",
            "Observar se justificam suas respostas com base nas informacoes do material, evitando respostas apenas intuitivas.",
            "Conferir se os registros finais evidenciam tomada de decisao com coerencia, argumentacao e uso do vocabulario trabalhado.",
        ]
    elif pistas.perfil_aula == "calculo":
        itens = [
            "Verificar se os estudantes identificam corretamente os dados necessarios e compreendem o que esta sendo pedido em cada situacao.",
            "Observar se realizam os procedimentos com apoio progressivamente menor, explicando o significado dos resultados encontrados.",
            "Conferir se os registros finais articulam calculo, interpretacao e conclusao, e nao apenas a resposta numerica.",
        ]
    elif pistas.perfil_aula == "conceitos":
        itens = [
            "Verificar se os estudantes compreendem os conceitos centrais da aula e conseguem explica-los com suas proprias palavras.",
            "Observar a participacao nas discussoes e a retomada do vocabulario principal durante as intervencoes orais e escritas.",
            "Conferir se os registros finais apresentam ideias organizadas, exemplos coerentes e compreensao progressiva do tema.",
        ]
    else:
        itens = [
            "Verificar se os estudantes compreendem o tema central da aula e reconhecem as ideias principais trabalhadas.",
            "Observar a participacao, os registros e a forma como justificam respostas ao longo das atividades propostas.",
            "Conferir se as producoes finais apresentam clareza, coerencia e retomada dos conceitos estudados.",
        ]

    return _deduplicar_linhas(itens)[:3]


def gerar_acessibilidade_3_itens(pistas: PistasPDF) -> List[str]:
    if pistas.perfil_aula == "grafico":
        itens = [
            "Disponibilizar leitura guiada de graficos e tabelas, destacando titulo, eixos, valores e comparacao entre os dados apresentados.",
            "Oferecer apoio visual com palavras-chave e perguntas orientadoras para ajudar na interpretacao das informacoes do material.",
            "Permitir diferentes formas de registro, como topicos, respostas curtas, marcacoes no grafico ou explicacao oral mediada.",
        ]
    elif pistas.perfil_aula == "comparacao":
        itens = [
            "Organizar quadro comparativo ou esquema visual para apoiar a analise entre alternativas, criterios e consequencias.",
            "Apresentar comandos curtos e objetivos, com retomada coletiva das etapas da atividade antes do registro individual.",
            "Permitir registro em topicos, frases curtas, tabela simples ou resposta oral mediada, conforme as necessidades observadas.",
        ]
    elif pistas.perfil_aula == "calculo":
        itens = [
            "Disponibilizar resolucao em etapas, com destaque visual para dados, operacao a realizar e interpretacao do resultado.",
            "Oferecer mediacao com exemplos semelhantes antes da atividade autonoma, reduzindo a sobrecarga cognitiva da tarefa.",
            "Permitir uso de esquemas, anotacoes guiadas, calculo acompanhado e explicacao oral do raciocinio como forma de registro.",
        ]
    elif pistas.perfil_aula == "conceitos":
        itens = [
            "Disponibilizar glossario com palavras-chave e exemplos simples para apoiar a compreensao do vocabulario da aula.",
            "Retomar oralmente os conceitos principais com apoio de esquema, quadro ou sintese visual construida com a turma.",
            "Permitir diferentes formas de expressao do entendimento, como topicos, frases curtas, desenho explicativo ou resposta oral mediada.",
        ]
    else:
        itens = [
            "Disponibilizar roteiro com palavras-chave e perguntas orientadoras para apoiar a compreensao da atividade.",
            "Realizar retomadas coletivas dos comandos e oferecer mediacao individual conforme as necessidades observadas.",
            "Permitir diferentes formas de registro, como topicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        ]

    return _deduplicar_linhas(itens)[:3]


def montar_tres_colunas(texto_pdf: str, titulo_aula: str = "") -> Dict[str, object]:
    pistas = extrair_pistas_pdf(texto_pdf=texto_pdf, titulo_aula=titulo_aula)
    return {
        "pistas_pdf": pistas,
        "desenvolvimento": gerar_metodologia_curta(pistas),
        "metodologia_blocos": gerar_metodologia_blocos(pistas),
        "acompanhamento": gerar_acompanhamento_3_itens(pistas),
        "acessibilidade": gerar_acessibilidade_3_itens(pistas),
    }
