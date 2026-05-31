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
    tem_noticia: bool = False
    tem_imagem_inicial: bool = False
    tem_mapa: bool = False
    tem_leitura_guiada: bool = False
    tem_construcao_conceito: bool = False

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

PALAVRAS_GRAFICO = ["grafico", "gráfico", "coluna", "linha", "eixo", "fluxo de refugiados"]
PALAVRAS_TABELA = ["tabela", "quadro", "comparativo"]
PALAVRAS_CALCULO = ["juros", "porcentagem", "percentual", "cálculo", "calculo", "rendimento"]
PALAVRAS_COMPARACAO = ["comparar", "comparação", "comparacao", "diferença", "diferenca", "sinônimos", "sinonimos"]
PALAVRAS_ESTUDO_CASO = ["situação", "situacao", "caso", "estudante de 25 anos", "um rapaz se mudou"]
PALAVRAS_NOTICIA = ["leia a notícia", "leia a noticia", "notícia", "noticia", "uol", "g1", "cnn", "bbc", "veja"]
PALAVRAS_IMAGEM = ["observe as imagens", "observe a imagem", "imagem de satélite", "imagem de satelite"]
PALAVRAS_MAPA = ["mapa interativo", "fluxo de migração", "fluxo de migracao", "legenda", "países ou regiões", "paises ou regioes"]
PALAVRAS_LEITURA = ["leia", "leitura", "hora da leitura"]
PALAVRAS_CONSTRUCAO_CONCEITO = ["construindo o conceito"]
PALAVRAS_DEBATE = ["virem e conversem", "com suas palavras", "para refletir"]


def extrair_bullets_secao(texto: str, marcador_secao: str) -> List[str]:
    linhas = [l.strip() for l in texto.replace("●", "\n● ").splitlines() if l.strip()]
    secao = False
    itens = []

    for linha in linhas:
        n = norm(linha)
        if marcador_secao in n:
            secao = True
            continue

        if secao and any(rot in n for rot in ["objetivos", "conteudos", "conteúdos", "habilidades", "recursos didaticos", "duração da aula", "duracao da aula"]) and marcador_secao not in n:
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


def classificar_perfil(texto: str, titulo: str, conteudos: List[str], objetivos: List[str], blocos: Dict[str, str]) -> str:
    base = " ".join([texto, titulo] + conteudos + objetivos)
    n = norm(base)

    tem_noticia = any(p in n for p in [norm(x) for x in PALAVRAS_NOTICIA])
    tem_imagem = any(p in n for p in [norm(x) for x in PALAVRAS_IMAGEM])
    tem_mapa = any(p in n for p in [norm(x) for x in PALAVRAS_MAPA])
    tem_comparacao = any(p in n for p in [norm(x) for x in PALAVRAS_COMPARACAO])
    tem_grafico = any(p in n for p in [norm(x) for x in PALAVRAS_GRAFICO])
    tem_estado = any(t in n for t in ["estado", "documentos internacionais", "direitos", "restrições", "restricoes", "soberania", "fronteiras"])
    tem_xenofobia = "xenofobia" in n
    tem_refugiado = "refugiado" in n or "refugiados" in n
    tem_migracao_legal_ilegal = "migracao legal e ilegal" in n or ("migrante legal" in n and "migrante ilegal" in n)

    if tem_xenofobia and tem_noticia:
        return "noticia_leitura_critica"
    if tem_migracao_legal_ilegal and (tem_imagem or "virem e conversem" in n) and tem_estado:
        return "imagem_debate_direitos"
    if tem_refugiado and tem_comparacao:
        return "comparacao_conceitual"
    if tem_mapa and "migracao" in n:
        return "mapa_fluxos_migratorios"
    if tem_grafico and tem_refugiado:
        return "grafico_fluxos_refugiados"
    if tem_comparacao:
        return "comparacao_conceitual"
    if tem_noticia:
        return "noticia_leitura_critica"
    if tem_imagem:
        return "imagem_debate"
    if "construindo o conceito" in n or blocos.get("Construindo o conceito"):
        return "conceito_reflexivo"
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

        tem_para_comecar=bool(blocos.get("Para comecar")) or ("para comecar" in n) or bool(blocos.get("Ponto de partida")),
        tem_relembre=bool(blocos.get("Relembre")) or ("relembre" in n),
        tem_foco_conteudo=bool(blocos.get("Foco no conteudo")) or ("foco no conteudo" in n) or bool(blocos.get("Construindo o conceito")),
        tem_pause_responda=bool(blocos.get("Pause e responda")) or ("pause e responda" in n),
        tem_atividade_final=bool(blocos.get("Na pratica")) or ("na pratica" in n or "desafio" in n),
        tem_video=("link para video" in n or "assista ao video" in n),

        tem_grafico=any(p in n for p in [norm(x) for x in PALAVRAS_GRAFICO]),
        tem_tabela=any(p in n for p in [norm(x) for x in PALAVRAS_TABELA]),
        tem_calculo=any(p in n for p in [norm(x) for x in PALAVRAS_CALCULO]),
        tem_comparacao=any(p in n for p in [norm(x) for x in PALAVRAS_COMPARACAO]),
        tem_estudo_caso=any(p in n for p in [norm(x) for x in PALAVRAS_ESTUDO_CASO]),
        tem_situacao_problema=("problema" in n or "questoes abaixo" in n or "responda às perguntas" in texto_pdf.lower() or "responda as perguntas" in n),
        tem_noticia=any(p in n for p in [norm(x) for x in PALAVRAS_NOTICIA]),
        tem_imagem_inicial=any(p in n for p in [norm(x) for x in PALAVRAS_IMAGEM]),
        tem_mapa=any(p in n for p in [norm(x) for x in PALAVRAS_MAPA]),
        tem_leitura_guiada=any(p in n for p in [norm(x) for x in PALAVRAS_LEITURA]),
        tem_construcao_conceito=any(p in n for p in [norm(x) for x in PALAVRAS_CONSTRUCAO_CONCEITO]),
        tecnicas_lemov=detectar_tecnicas(texto_pdf),
    )

    pistas.perfil = classificar_perfil(texto_pdf, titulo_aula, conteudos, objetivos, blocos)
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

    if pistas.perfil in {
        "noticia_leitura_critica",
        "imagem_debate",
        "imagem_debate_direitos",
        "comparacao_conceitual",
        "conceito_reflexivo",
        "mapa_fluxos_migratorios",
    } and not pistas.tem_grafico and not pistas.tem_tabela:
        for termo in [
            "graficos, tabelas ou dados",
            "gráficos, tabelas ou dados",
            "eixos, valores",
            "localizar dados relevantes",
        ]:
            if norm(termo) in n:
                return ""
    return texto


def frase_inicial(p: PistasPedagogicas) -> str:
    opcoes = []

    if p.tem_noticia:
        opcoes.append("Iniciar a aula com leitura guiada da notícia apresentada no material, mobilizando conhecimentos prévios e incentivando a turma a identificar o problema central discutido.")
    if p.tem_imagem_inicial:
        opcoes.append("Iniciar a aula com observação orientada das imagens do material, estimulando os estudantes a levantar hipóteses, identificar elementos importantes e relacioná-los ao tema.")
    if p.tem_mapa:
        opcoes.append("Iniciar a aula com exploração do mapa apresentado no material, orientando a turma a observar fluxos, regiões e possíveis explicações para os deslocamentos identificados.")
    if p.tem_estudo_caso or p.tem_situacao_problema:
        opcoes.append("Iniciar com a situação-problema do material, incentivando a turma a levantar hipóteses e antecipar possíveis caminhos de análise.")
    opcoes.append("Iniciar a aula apresentando o tema central e incentivando os estudantes a relacioná-lo a situações do cotidiano.")

    return deterministic_choice(opcoes, p.titulo + "|inicio")


def frase_foco(p: PistasPedagogicas) -> str:
    frase = ""
    if p.perfil == "noticia_leitura_critica":
        frase = "Conduzir a leitura orientada da notícia e das perguntas propostas, destacando informações principais, pontos de vista, formas de preconceito ou conflito e relações com o conceito central da aula."
    elif p.perfil == "imagem_debate":
        frase = "Explorar as imagens e questões iniciais do material, promovendo debate orientado e análise crítica das situações apresentadas antes da sistematização dos conceitos."
    elif p.perfil == "imagem_debate_direitos":
        frase = "Explorar as imagens, os questionamentos iniciais e os conceitos do material, destacando diferenças entre situações analisadas, riscos envolvidos, direitos, restrições e o papel do Estado."
    elif p.perfil == "comparacao_conceitual":
        frase = "Sistematizar os conceitos centrais da aula por meio de comparação orientada, ajudando a turma a distinguir termos próximos, reconhecer critérios e justificar diferenças com clareza."
    elif p.perfil == "mapa_fluxos_migratorios":
        frase = "Conduzir a leitura orientada do mapa e dos conceitos do material, destacando fluxos migratórios, causas dos deslocamentos e relações entre globalização, trabalho e qualidade de vida."
    elif p.perfil == "grafico_fluxos_refugiados":
        frase = "Conduzir a leitura orientada de gráficos, quadros ou informações visuais do material, ajudando a turma a interpretar os fluxos de refugiados e relacioná-los às causas do deslocamento forçado."
    elif p.perfil == "conceito_reflexivo":
        frase = "Sistematizar os conceitos centrais da aula com explicações claras, exemplos próximos da realidade dos estudantes e retomada do vocabulário principal."
    else:
        if p.tem_grafico and p.tem_tabela:
            frase = "Desenvolver o conteúdo central da aula por meio da análise orientada de gráficos e tabelas explicativas presentes no material."
        elif p.tem_grafico:
            frase = "Desenvolver o conteúdo central da aula por meio da leitura e interpretação orientada de gráficos e informações visuais do material."
        elif p.tem_tabela:
            frase = "Desenvolver o conteúdo central da aula por meio da análise de tabelas ou quadros comparativos do material."
        else:
            frase = "Desenvolver o conteúdo central da aula com explicação dialogada, exemplos do material e participação orientada da turma."

    if p.tem_grafico or p.tem_tabela:
        f_norm = norm(frase)
        if "grafico" not in f_norm and "tabela" not in f_norm and "quadro" not in f_norm:
            if p.tem_grafico and p.tem_tabela:
                frase += " Orientar a leitura e interpretação dos gráficos e tabelas presentes no material para fundamentar a análise."
            elif p.tem_grafico:
                frase += " Orientar a leitura e interpretação dos gráficos presentes no material."
            elif p.tem_tabela:
                frase += " Orientar a análise das tabelas ou quadros explicativos do material."

    return frase


def frase_pause(p: PistasPedagogicas) -> str:
    if p.tem_pause_responda:
        return "Realizar uma pausa de verificação da aprendizagem para que os estudantes justifiquem respostas, retomem conceitos e revisem o raciocínio antes de avançar."
    return ""


def frase_pratica(p: PistasPedagogicas) -> str:
    if p.perfil == "noticia_leitura_critica":
        return "Propor atividade de análise e registro em que os estudantes retomem a notícia, respondam às questões e relacionem o caso discutido aos conceitos trabalhados na aula."
    if p.perfil == "imagem_debate":
        return "Encaminhar atividade de debate e registro para que a turma organize observações, formule respostas e relacione as imagens às ideias centrais estudadas."
    if p.perfil == "imagem_debate_direitos":
        return "Organizar atividade em que os estudantes comparem situações, registrem diferenças e justifiquem respostas com base nos conceitos, direitos e restrições discutidos."
    if p.perfil == "comparacao_conceitual":
        return "Propor atividade de comparação conceitual para que os estudantes organizem critérios, registrem diferenças e expliquem os conceitos com maior precisão."
    if p.perfil == "mapa_fluxos_migratorios":
        return "Propor atividade em que os estudantes interpretem o mapa, relacionem fluxos e causas das migrações e registrem conclusões com base nas discussões realizadas."
    if p.perfil == "grafico_fluxos_refugiados":
        return "Propor atividade de interpretação de informações visuais para que a turma relacione os fluxos de refugiados às causas e aos contextos geopolíticos estudados."
    return "Propor atividade de aplicação para que os estudantes retomem o conteúdo, organizem ideias principais e consolidem a aprendizagem."


def frase_encerramento(p: PistasPedagogicas) -> str:
    destaque = ", ".join(p.vocabulario_chave[:3])
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


def _blocos_metodologia(p: PistasPedagogicas) -> List[Dict[str, str]]:
    blocos = []
    blocos.append({"titulo": "Para comecar", "texto": frase_inicial(p)})

    if "Virem e conversem" in p.tecnicas_lemov:
        comp = complemento_tecnica("Virem e conversem", "inicio")
        if comp:
            blocos.append({"titulo": "Interacao inicial", "texto": comp})

    blocos.append({"titulo": "Foco no conteudo", "texto": frase_foco(p)})

    for tecnica in ("Um passo de cada vez", "De olho no modelo", "Hora da leitura"):
        if tecnica in p.tecnicas_lemov:
            comp = complemento_tecnica(tecnica, "foco")
            if comp:
                blocos.append({"titulo": tecnica, "texto": comp})
                break

    pause = frase_pause(p)
    if pause:
        blocos.append({"titulo": "Pause e responda", "texto": pause})
        if "Pausa produtiva" in p.tecnicas_lemov:
            comp = complemento_tecnica("Pausa produtiva", "pause")
            if comp:
                blocos.append({"titulo": "Pausa produtiva", "texto": comp})

    blocos.append({"titulo": "Na pratica", "texto": frase_pratica(p)})

    if "Todo mundo escreve" in p.tecnicas_lemov:
        comp = complemento_tecnica("Todo mundo escreve", "pratica")
        if comp:
            blocos.append({"titulo": "Registro individual", "texto": comp})

    blocos.append({"titulo": "Encerramento", "texto": frase_encerramento(p)})

    if "Com suas palavras" in p.tecnicas_lemov:
        comp = complemento_tecnica("Com suas palavras", "encerramento")
        if comp:
            blocos.append({"titulo": "Com suas palavras", "texto": comp})

    saida = []
    for bloco in blocos:
        texto = bloquear_contaminacao_tematica(sanitizar_texto_pedagogico(bloco.get("texto", "")), p)
        if texto:
            saida.append({"titulo": bloco["titulo"], "texto": texto})

    uniq = []
    seen = set()
    for bloco in saida:
        chave = norm(bloco["titulo"] + " " + bloco["texto"])
        if chave and chave not in seen:
            seen.add(chave)
            uniq.append(bloco)

    if len(uniq) > 6:
        for idx in range(5, len(uniq)):
            if uniq[idx]["titulo"] in {"Encerramento", "Com suas palavras"}:
                return uniq[:5] + [uniq[idx]]
    return uniq[:6]


def gerar_metodologia(pistas: PistasPedagogicas) -> str:
    blocos = _blocos_metodologia(pistas)
    return "\n".join(f"{i+1}. {bloco['texto']}" for i, bloco in enumerate(blocos))


BANCO_ACOMPANHAMENTO = {
    "noticia_leitura_critica": [
        "Verificar se os estudantes identificam informações principais, problema central e posicionamentos presentes na notícia analisada.",
        "Observar se relacionam o caso discutido aos conceitos trabalhados na aula, utilizando argumentos coerentes nas respostas orais e escritas.",
        "Conferir se os registros finais apresentam interpretação crítica, clareza na exposição das ideias e retomada do vocabulário principal.",
        "Acompanhar se a turma diferencia fatos do caso apresentado e interpretações construídas durante o debate."
    ],
    "imagem_debate": [
        "Verificar se os estudantes observam elementos relevantes das imagens e conseguem relacioná-los ao tema discutido na aula.",
        "Observar a participação nas discussões iniciais e a capacidade de formular hipóteses, perguntas e respostas com progressiva autonomia.",
        "Conferir se os registros finais retomam as ideias centrais construídas a partir da observação e do debate orientado.",
        "Acompanhar se a turma articula imagem, contexto e conceito de forma coerente."
    ],
    "imagem_debate_direitos": [
        "Verificar se os estudantes identificam diferenças entre as situações analisadas e compreendem os riscos, direitos e restrições envolvidos.",
        "Observar se justificam respostas com base nas imagens, nos conceitos trabalhados e nas discussões sobre o papel do Estado.",
        "Conferir se os registros finais apresentam comparação coerente, uso do vocabulário central e argumentação progressivamente mais precisa.",
        "Acompanhar se a turma reconhece relações entre migração, direitos humanos e políticas migratórias."
    ],
    "comparacao_conceitual": [
        "Verificar se os estudantes distinguem corretamente os conceitos trabalhados, evitando tratá-los como sinônimos.",
        "Observar se utilizam critérios de comparação para justificar respostas e explicar diferenças com maior precisão.",
        "Conferir se os registros finais evidenciam compreensão conceitual, organização das ideias e uso do vocabulário principal.",
        "Acompanhar se a turma relaciona os conceitos comparados aos exemplos e situações apresentados no material."
    ],
    "mapa_fluxos_migratorios": [
        "Verificar se os estudantes interpretam o mapa apresentado e identificam fluxos, entradas, saídas e possíveis explicações para os deslocamentos observados.",
        "Observar se relacionam as informações do material às causas das migrações e às discussões sobre globalização, trabalho e qualidade de vida.",
        "Conferir se os registros finais apresentam leitura coerente do mapa, justificativas plausíveis e retomada dos conceitos principais.",
        "Acompanhar se a turma utiliza a legenda e os elementos do mapa para sustentar suas respostas."
    ],
    "grafico_fluxos_refugiados": [
        "Verificar se os estudantes interpretam corretamente gráficos, quadros ou informações visuais sobre fluxos de refugiados.",
        "Observar se relacionam os dados analisados às causas do deslocamento forçado e aos contextos geopolíticos discutidos.",
        "Conferir se os registros finais articulam leitura visual, explicação conceitual e conclusão coerente.",
        "Acompanhar se a turma utiliza evidências do material para sustentar respostas e comparações."
    ],
    "conceito_reflexivo": [
        "Verificar se os estudantes compreendem os conceitos centrais da aula e conseguem explicá-los com suas próprias palavras.",
        "Observar a participação nas discussões e a retomada do vocabulário principal durante as intervenções orais e escritas.",
        "Conferir se os registros finais apresentam ideias organizadas, exemplos coerentes e compreensão progressiva do tema.",
        "Acompanhar se a turma diferencia corretamente os conceitos trabalhados, evitando confusões entre noções próximas."
    ],
    "geral": [
        "Verificar se os estudantes compreendem o tema central da aula e reconhecem as ideias principais trabalhadas.",
        "Observar a participação, os registros e a forma como justificam respostas ao longo das atividades propostas.",
        "Conferir se as produções finais apresentam clareza, coerência e retomada dos conceitos estudados.",
        "Acompanhar se os estudantes utilizam o vocabulário da aula de forma progressivamente mais autônoma."
    ],
}


def gerar_acompanhamento(pistas: PistasPedagogicas) -> List[str]:
    base = BANCO_ACOMPANHAMENTO.get(pistas.perfil, BANCO_ACOMPANHAMENTO["geral"])[:]
    rng = random.Random(pistas.titulo + "|acompanhamento|" + pistas.perfil)
    rng.shuffle(base)
    return [sentenca(item) for item in dedup(base)[:3]]


BANCO_ACESSIBILIDADE = {
    "noticia_leitura_critica": [
        "Oferecer leitura guiada da notícia com destaque para título, informações principais, personagens envolvidos e problema central discutido.",
        "Disponibilizar palavras-chave e perguntas orientadoras para apoiar a interpretação do texto e a organização das respostas.",
        "Permitir registro em tópicos, frases curtas ou resposta oral mediada, conforme as necessidades observadas na turma.",
        "Retomar coletivamente o sentido de trechos importantes antes do trabalho individual."
    ],
    "imagem_debate": [
        "Organizar observação orientada das imagens com perguntas curtas que ajudem a turma a identificar elementos relevantes antes da discussão.",
        "Utilizar apoio visual e retomadas coletivas para favorecer a relação entre imagem, contexto e conceito central da aula.",
        "Permitir diferentes formas de registro, como tópicos, frases curtas, esquema ou resposta oral mediada.",
        "Oferecer mediação individual na organização das ideias e na formulação das respostas."
    ],
    "imagem_debate_direitos": [
        "Apresentar comandos curtos e objetivos, com retomada coletiva das perguntas antes do registro individual.",
        "Organizar quadro comparativo simples para apoiar a distinção entre situações, riscos, direitos e restrições discutidos no material.",
        "Permitir registro em tópicos, frases curtas, esquema comparativo ou resposta oral mediada, conforme as necessidades observadas.",
        "Destacar visualmente conceitos centrais ligados a migração, documentação, direitos e papel do Estado."
    ],
    "comparacao_conceitual": [
        "Organizar quadro comparativo ou esquema visual para apoiar a distinção entre os conceitos trabalhados na aula.",
        "Retomar oralmente os critérios de comparação com exemplos simples antes da atividade autônoma.",
        "Permitir registro em tópicos, tabela simples, frases curtas ou resposta oral mediada, conforme as necessidades observadas.",
        "Destacar visualmente semelhanças e diferenças para apoiar a compreensão conceitual."
    ],
    "mapa_fluxos_migratorios": [
        "Disponibilizar leitura guiada do mapa com destaque para legenda, fluxos, regiões de entrada e saída e elementos visuais relevantes.",
        "Oferecer perguntas orientadoras para ajudar os estudantes a relacionar o mapa às causas das migrações e aos contextos discutidos na aula.",
        "Permitir diferentes formas de registro, como tópicos, setas, esquema simples ou resposta oral mediada.",
        "Retomar coletivamente como localizar informações essenciais no mapa antes do trabalho individual."
    ],
    "grafico_fluxos_refugiados": [
        "Disponibilizar leitura guiada de gráficos, quadros ou informações visuais, destacando título, categorias e comparação entre os dados apresentados.",
        "Oferecer apoio visual com palavras-chave e perguntas orientadoras para ajudar na interpretação das informações do material.",
        "Permitir diferentes formas de registro, como tópicos, respostas curtas, marcações no gráfico ou explicação oral mediada.",
        "Retomar coletivamente como localizar dados relevantes antes do trabalho individual."
    ],
    "conceito_reflexivo": [
        "Disponibilizar glossário com palavras-chave e exemplos simples para apoiar a compreensão do vocabulário da aula.",
        "Retomar oralmente os conceitos principais com apoio de esquema, quadro ou síntese visual construída com a turma.",
        "Permitir diferentes formas de expressão do entendimento, como tópicos, frases curtas, desenho explicativo ou resposta oral mediada.",
        "Utilizar exemplos concretos do cotidiano para apoiar a compreensão de termos mais abstratos."
    ],
    "geral": [
        "Disponibilizar roteiro com palavras-chave e perguntas orientadoras para apoiar a compreensão da atividade.",
        "Realizar retomadas coletivas dos comandos e oferecer mediação individual conforme as necessidades observadas.",
        "Permitir diferentes formas de registro, como tópicos, frases curtas, esquema, desenho ou resposta oral mediada.",
        "Organizar momentos de apoio em duplas para favorecer compreensão e participação."
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
