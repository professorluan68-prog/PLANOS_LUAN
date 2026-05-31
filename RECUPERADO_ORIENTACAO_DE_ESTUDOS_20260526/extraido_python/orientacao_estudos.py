import re
from typing import List

from .base import PedagogicalContext


def _limpar_tema(tema: str = "") -> str:
    tema = re.sub(r"(?i)^AULA\s+\d+\s*[-–:]?\s*", "", tema or "").strip()
    return tema or "estratégias de estudo, leitura e registro"


def _normalizar(texto: str = "") -> str:
    texto = (texto or "").lower()
    trocas = {
        "á": "a", "à": "a", "â": "a", "ã": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
        "’": "i",
        "‹": "a",
    }
    for origem, destino in trocas.items():
        texto = texto.replace(origem, destino)
    return texto


def _focos_do_material(texto_total: str, tema: str) -> dict:
    texto_total = texto_total or ""
    fonte_total = _normalizar(f"{tema} {texto_total}")
    fonte = _normalizar(f"{tema} {texto_total[:5000]}")
    tema_norm = _normalizar(tema)
    focos = {
        "projeto_cultural": any(k in fonte for k in ["projeto cultural", "projetos culturais", "justificativa", "objetivo", "metodologia do projeto"]),
        "carta_leitor": any(k in fonte for k in ["carta de leitor", "cartas de leitor", "remetente", "destinatario", "tese"]),
        "argumentacao": any(k in fonte for k in ["argumento", "argumentacao", "tese", "ponto de vista", "opiniao"]),
        "coesao": any(k in fonte for k in ["coesao", "conectivo", "conectivos", "conjuncao", "conjuncoes", "pronome", "pronomes", "substituicao", "retomadas", "referente"]),
        "producao": any(k in fonte_total for k in ["produzir", "producao", "rascunho", "versao definitiva", "escrevam"]),
        "jornada": "jornada" in fonte_total,
        "saeb": "de olho no saeb" in fonte_total or bool(re.search(r"\bLP\d[A-Z]{4}\d{2}\b", texto_total, flags=re.IGNORECASE)),
        "jogos_regras": any(k in fonte for k in ["jogos com palavras", "regra de jogo", "manual de instrucoes", "como jogar"]),
        "humor_hq": any(k in fonte for k in ["humor", "tirinha", "tirinhas", "quadrinhos", "charge", "charges"]),
        "noticia_reportagem": any(k in fonte for k in ["noticia", "noticias", "reportagem", "reportagens", "jornalistico", "jornalistica"]),
        "poesia": any(k in fonte for k in ["poema", "poemas", "poesia", "versos", "estrofes", "eu lirico", "cordel"]),
        "narrativa": any(k in fonte for k in ["conto", "contos", "narrativa", "narrativas", "fabula", "fabulas", "lenda", "lendas", "personagem", "enredo"]),
        "verbete": any(k in fonte for k in ["verbete", "verbetes", "enciclopedia", "enciclopedico"]),
        "teatro": any(k in fonte for k in ["teatro", "texto teatral", "rubrica", "rubricas", "personagens em cena"]),
        "fato_opiniao": any(k in fonte for k in ["fato", "opiniao", "opinioes", "artigo de opiniao", "ponto de vista"]),
        "visual": any(k in fonte for k in ["imagem", "imagens", "linguagem verbal e nao verbal", "grafico", "tabela", "infografico"]),
    }
    if "carta" in tema_norm and "projeto" not in tema_norm:
        focos["projeto_cultural"] = False
    if "projeto" in tema_norm and "carta" not in tema_norm:
        focos["carta_leitor"] = False
    if any(
        k in tema_norm
        for k in [
            "jogos com palavras",
            "para chorar de rir",
            "da charge a noticia",
            "que tirada",
            "vamos a fundo",
            "uma palavra puxa a outra",
            "a trama do texto",
            "por dentro dos verbetes",
            "narrativas breves",
            "a voz da poesia",
            "um mergulho no cordel",
            "poema para mim",
            "lendas e narrativa",
            "qual e a moral",
            "o texto no teatro",
            "opiniao versus fato",
        ]
    ):
        focos["projeto_cultural"] = False
        focos["carta_leitor"] = False
    return focos


_PERFIS_TEMA = {
    "jogos com palavras e imagens": (
        "textos com palavras e imagens e regras de jogo",
        "relação entre palavras, imagens e regras de jogo; leitura de imagens e recursos visuais usados para construir sentido",
    ),
    "para chorar de rir": (
        "textos de humor e construção de efeitos humorísticos",
        "situações de humor, ironia, quebra de expectativa e relação entre texto verbal e visual",
    ),
    "da charge a noticia": (
        "charges, notícias e diferentes abordagens de um mesmo tema",
        "características da charge e da notícia, finalidade dos gêneros e comparação entre formas de tratar a informação",
    ),
    "que tirada": (
        "tirinhas, humor e linguagem verbo-visual",
        "efeitos de humor, falas, imagens, sequência de quadrinhos e pistas visuais que ajudam na interpretação",
    ),
    "vamos a fundo nos assuntos": (
        "reportagens e aprofundamento de informações",
        "finalidade da reportagem, título, intertítulos, imagens, legendas e organização das informações",
    ),
    "uma palavra puxa a outra": (
        "conectivos e relações entre partes do texto",
        "conectivos, conjunções e relações de sentido que ligam palavras, frases e parágrafos",
    ),
    "a trama do texto": (
        "coesão textual, retomadas e continuidade das ideias",
        "retomadas, pronomes, substituições e referentes que evitam repetições e mantêm a continuidade textual",
    ),
    "por dentro dos verbetes": (
        "verbetes enciclopédicos e organização de informações",
        "finalidade informativa, estrutura do verbete, seleção de informações e linguagem objetiva",
    ),
    "narrativas breves": (
        "narrativas breves, personagens e sequência de fatos",
        "personagens, narrador, conflito, tempo, espaço, sequência de fatos, causa e consequência e marcas de pontuação",
    ),
    "a voz da poesia": (
        "poemas, versos, eu lírico e interlocução",
        "versos, estrofes, eu lírico, interlocutor, vocativo, marcas linguísticas e efeitos de sentido",
    ),
    "um mergulho no cordel": (
        "cordel, linguagem figurada e leitura das entrelinhas",
        "versos, linguagem figurada, inferências, ilustrações e pistas textuais para compreender sentidos implícitos",
    ),
    "poema para mim e para voce": (
        "poemas, criação poética e expressão de sentimentos",
        "estrutura do poema, versos, recursos expressivos, temas possíveis e planejamento da produção poética",
    ),
    "lendas e narrativa": (
        "lendas, narrativas e tradição oral",
        "tema, personagens, tempo, espaço, sequência narrativa, pronomes e marcas culturais presentes nas lendas",
    ),
    "qual e a moral da historia": (
        "fábulas, personagens e moral da história",
        "personagens, conflito, desfecho, moral, inferência e relações de causa e consequência",
    ),
    "o texto no teatro": (
        "texto teatral, falas e rubricas",
        "falas, rubricas, personagens, cenário, pontuação expressiva e organização da cena teatral",
    ),
    "opiniao versus fato": (
        "fatos, opiniões e posicionamento argumentativo",
        "distinção entre fato e opinião, ponto de vista, argumentos e justificativas em textos opinativos",
    ),
}


def _perfil_por_tema(tema: str) -> tuple[str, str] | None:
    tema_norm = _normalizar(tema)
    for chave, perfil in _PERFIS_TEMA.items():
        if chave in tema_norm:
            return perfil
    return None


def _objeto_de_estudo(focos: dict, tema: str) -> str:
    perfil = _perfil_por_tema(tema)
    if perfil:
        return perfil[0]
    if focos["projeto_cultural"] and focos["carta_leitor"]:
        return "projetos culturais, coesão textual, cartas de leitor e argumentação"
    if focos["projeto_cultural"]:
        return "projetos culturais e coesão textual"
    if focos["carta_leitor"]:
        return "cartas de leitor, tese e argumento"
    if focos["jogos_regras"]:
        return "textos com palavras e imagens e regras de jogo"
    if focos["poesia"]:
        return "poemas, versos, eu lírico e interlocução"
    if focos["narrativa"]:
        return "narrativas, personagens, enredo e relações de causa e consequência"
    if focos["verbete"]:
        return "verbetes enciclopédicos e organização de informações"
    if focos["teatro"]:
        return "texto teatral, falas e rubricas"
    if focos["fato_opiniao"]:
        return "fatos, opiniões e posicionamento argumentativo"
    if focos["noticia_reportagem"]:
        return "notícias, reportagens e tratamento da informação"
    if focos["humor_hq"]:
        return "humor, charges, tirinhas e linguagem verbo-visual"
    return tema


def _foco_conceitual(focos: dict, tema: str = "") -> str:
    perfil = _perfil_por_tema(tema)
    if perfil:
        return perfil[1]
    partes = []
    if focos["projeto_cultural"]:
        partes.append("partes do projeto cultural, como justificativa, objetivos, metodologia e avaliação")
    if focos["coesao"]:
        partes.append("retomadas, pronomes e substituições que mantêm a coesão textual")
    if focos["carta_leitor"]:
        partes.append("função social, tese e argumentos da carta de leitor")
    elif focos["argumentacao"]:
        partes.append("tese, ponto de vista e argumentos")
    if focos["jogos_regras"]:
        partes.append("relação entre palavras, imagens e regras de jogo")
    if focos["humor_hq"]:
        partes.append("efeitos de humor, ironia e articulação entre linguagem verbal e visual")
    if focos["noticia_reportagem"]:
        partes.append("fato central, finalidade, abordagem do assunto e organização jornalística")
    if focos["poesia"]:
        partes.append("versos, estrofes, eu lírico, interlocução e efeitos de sentido")
    if focos["narrativa"]:
        partes.append("personagens, narrador, conflito, sequência de fatos e relações de causa e consequência")
    if focos["verbete"]:
        partes.append("finalidade informativa, estrutura do verbete e seleção de informações")
    if focos["teatro"]:
        partes.append("falas, rubricas, pontuação expressiva e organização da cena")
    if focos["fato_opiniao"]:
        partes.append("distinção entre fato e opinião, ponto de vista e justificativas")
    if focos["visual"]:
        partes.append("leitura de imagens, tabelas, gráficos ou outros elementos visuais do material")
    if not partes:
        partes.append("procedimentos de leitura, interpretação e organização das respostas")
    return "; ".join(partes)


def montar_desenvolvimento_orientacao_estudos(
    slides_textos: List[str],
    tema_input: str,
    habilidade: str,
    contexto: PedagogicalContext,
) -> str:
    tema = _limpar_tema(tema_input)
    texto_total = " ".join(slides_textos or [])
    focos = _focos_do_material(texto_total, tema)
    objeto = _objeto_de_estudo(focos, tema)
    foco = _foco_conceitual(focos, tema)
    aprofundamento = " com maior aprofundamento dos registros e das justificativas" if focos["jornada"] else ""

    abertura = (
        f"Para começar: Retomar conhecimentos prévios sobre {objeto} por meio de perguntas curtas e exemplos próximos da rotina escolar. "
        "Registrar no quadro as primeiras ideias da turma para orientar a leitura e a resolução das atividades."
    )

    leitura = (
        "Leitura e construção do conteúdo: Realizar a leitura guiada dos textos, comandos e enunciados, com pausas para localizar informações, "
        "marcar palavras-chave e esclarecer vocabulário. Organizar, no quadro, as ideias centrais para que os estudantes registrem o percurso de estudo."
    )

    foco_conteudo = (
        f"Foco no conteúdo: Analisar {foco}. "
        f"Transformar as questões do material em orientações de estudo, pedindo que os alunos justifiquem respostas com evidências do texto{aprofundamento}."
    )

    pratica = (
        "Na prática: Orientar a resolução das atividades passo a passo, acompanhando leitura, marcações, registros e respostas escritas. "
        "Solicitar que os estudantes comparem alternativas, revisem justificativas e ajustem as respostas antes da socialização."
    )
    if focos["producao"]:
        pratica += (
            " Nas propostas de produção, organizar planejamento, rascunho, revisão e versão final com apoio de critérios simples."
        )
    if focos["saeb"]:
        pratica += (
            " Quando aparecer o padrão DE OLHO NO SAEB, utilizar os códigos de habilidade, nível e dificuldade para orientar a resolução, "
            "priorizar intervenções e organizar a correção dialogada."
        )

    pause = (
        "Pause e responda: Socializar respostas selecionadas e realizar correção dialogada, retomando trechos, marcas no texto e caminhos de resolução. "
        "Acompanhar se os estudantes explicam como chegaram às respostas e quais estratégias de estudo utilizaram."
    )

    encerramento = (
        "Encerramento: Retomar coletivamente o conteúdo estudado e as estratégias utilizadas na aula. "
        "Registrar uma síntese final no quadro, conectando leitura atenta, análise de enunciados, justificativa de respostas e organização dos estudos."
    )

    return contexto.adaptar_texto("\n\n".join([abertura, leitura, foco_conteudo, pratica, pause, encerramento]))
