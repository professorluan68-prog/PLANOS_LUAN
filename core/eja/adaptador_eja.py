import re

from core.lib.extrator_pdf import normalizar_texto


PERFIS_EJA = frozenset({"biologia", "ingles", "lideranca_oratoria"})

_SUBSTITUICOES_LEMOV = {
    "virem e conversem": "uma conversa em duplas",
    "todo mundo escreve": "um registro individual",
    "com suas palavras": "uma explicacao com linguagem propria",
    "hora da leitura": "uma leitura orientada",
    "de olho no modelo": "a analise de um exemplo",
    "pause e responda": "uma breve verificacao de compreensao",
    "um passo de cada vez": "uma explicacao em etapas",
}


def perfil_suporta_eja(perfil: str) -> bool:
    return normalizar_texto(perfil) in PERFIS_EJA


def _anexar_orientacao_unica(texto: str, orientacao: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    orientacao = re.sub(r"\s+", " ", str(orientacao or "")).strip()
    if not orientacao:
        return texto
    if normalizar_texto(orientacao[:80]) in normalizar_texto(texto):
        return texto
    if texto and not texto.endswith((".", "!", "?")):
        texto += "."
    return f"{texto} {orientacao}".strip() if texto else orientacao


def _remover_nomes_lemov(texto: str) -> str:
    resultado = re.sub(r"\s+", " ", str(texto or "")).strip()
    for nome, substituicao in _SUBSTITUICOES_LEMOV.items():
        resultado = re.sub(
            rf"\b(?:a\s+tecnica\s+|o\s+momento\s+)?{re.escape(nome)}\b",
            substituicao,
            resultado,
            flags=re.I,
        )
    resultado = re.sub(r"\btecnicas?\s+lemov\b", "estrategias pedagogicas", resultado, flags=re.I)
    return re.sub(r"\s+", " ", resultado).strip()


def texto_tecnica_eja(tecnica: str, perfil: str, destino: str = "") -> str:
    """Traduz marcadores do material em uma acao natural, sem citar Lemov."""
    tecnica_norm = normalizar_texto(tecnica)
    if "virem e conversem" in tecnica_norm:
        return "Promover uma conversa em duplas sobre experiencias ligadas ao tema."
    if "todo mundo escreve" in tecnica_norm:
        return "Solicitar um registro individual curto e retomar as respostas na correcao."
    if "pause e responda" in tecnica_norm:
        return "Fazer uma breve verificacao de compreensao e retomar as duvidas."
    if "com suas palavras" in tecnica_norm:
        return "Pedir que os estudantes expliquem a ideia com linguagem propria e exemplos reais."
    if "de olho no modelo" in tecnica_norm:
        return "Apresentar um exemplo comentado antes da atividade."
    if "hora da leitura" in tecnica_norm:
        return "Conduzir uma leitura orientada com pausas para vocabulario e compreensao."
    if "um passo de cada vez" in tecnica_norm:
        return "Organizar a explicacao em etapas curtas e claras."
    if perfil == "ingles" and any(
        marcador in tecnica_norm
        for marcador in ("listen and repeat", "write and share", "say it in english")
    ):
        return "Trabalhar comandos curtos, repeticao orientada e uso funcional do ingles."
    return "Aplicar uma estrategia breve de participacao e verificacao da aprendizagem."


def consolidar_blocos_eja(metodologia, perfil: str = ""):
    if normalizar_texto(perfil) == "lideranca_oratoria":
        return [
            {
                **item,
                "texto": _remover_nomes_lemov(item.get("texto", "")),
            }
            if isinstance(item, dict)
            else _remover_nomes_lemov(item)
            for item in metodologia or []
        ]

    grupos = [
        ("Para comecar", {"para comecar", "relembre", "abertura", "contextualizacao"}),
        (
            "Foco no conteudo",
            {
                "foco no conteudo",
                "leitura",
                "leitura e construcao do conteudo",
                "conceituacao",
                "desenvolvimento",
            },
        ),
        (
            "Pause e responda",
            {
                "pause e responda",
                "na pratica",
                "atividade",
                "atividade principal",
                "socializacao",
                "socializacao e correcao",
            },
        ),
        ("Encerramento", {"encerramento", "fechamento", "sistematizacao"}),
    ]
    saida = {titulo: [] for titulo, _ in grupos}
    extras = []

    for item in metodologia or []:
        if not isinstance(item, dict):
            extras.append(_remover_nomes_lemov(item))
            continue
        titulo_norm = normalizar_texto(item.get("titulo", ""))
        texto = _remover_nomes_lemov(item.get("texto", ""))
        if not texto:
            continue
        encaixado = False
        for titulo, aliases in grupos:
            if titulo_norm in aliases:
                saida[titulo].append(texto)
                encaixado = True
                break
        if not encaixado:
            extras.append(texto)

    if extras:
        saida["Foco no conteudo"].extend(extras)

    return [
        {"titulo": titulo, "texto": " ".join(saida[titulo])}
        for titulo, _ in grupos
        if saida[titulo]
    ]


def adaptar_metodologia_eja(
    metodologia,
    perfil: str,
    tema: str,
    texto_pdf: str,
    tecnicas_pdf: list[str] | None = None,
    garantir_tecnicas_fn=None,
):
    if not perfil_suporta_eja(perfil):
        return metodologia

    perfil = normalizar_texto(perfil)
    tem_video = "video" in normalizar_texto(texto_pdf)
    adaptada = []

    for item in metodologia or []:
        if not isinstance(item, dict):
            adaptada.append(_remover_nomes_lemov(item))
            continue

        novo = dict(item)
        titulo = normalizar_texto(novo.get("titulo", ""))
        texto = _remover_nomes_lemov(novo.get("texto", ""))

        if titulo in {"para comecar", "relembre", "abertura", "contextualizacao"}:
            texto = _anexar_orientacao_unica(
                texto,
                f"Relacionar {tema} a experiencias dos estudantes, incluindo situacoes do cotidiano e do trabalho.",
            )

        elif titulo in {
            "foco no conteudo",
            "conceituacao",
            "desenvolvimento",
            "leitura e construcao do conteudo",
            "leitura",
        }:
            if perfil == "ingles":
                complemento = (
                    "Explorar vocabulario e estruturas com exemplos de comunicacao no trabalho, "
                    "em servicos e em outras situacoes reais."
                )
            elif perfil == "lideranca_oratoria":
                complemento = (
                    "Relacionar o conteudo a comunicacao profissional, trabalho em equipe, "
                    "resolucao de conflitos e tomada de decisao."
                )
            else:
                complemento = (
                    "Explicar o conceito com linguagem acessivel e adulta, relacionando-o a saude, "
                    "ambiente, tecnologia, comunidade e mundo do trabalho."
                )
            if tem_video:
                complemento += " Retomar de forma breve as informacoes centrais do video indicado."
            texto = _anexar_orientacao_unica(texto, complemento)

        elif titulo in {
            "pause e responda",
            "na pratica",
            "atividade",
            "atividade principal",
            "socializacao",
        }:
            texto = _anexar_orientacao_unica(
                texto,
                "Propor uma situacao pratica ligada ao cotidiano ou ao trabalho e orientar um registro curto.",
            )

        elif titulo in {"encerramento", "fechamento", "sistematizacao"}:
            texto = _anexar_orientacao_unica(
                texto,
                f"Retomar a utilidade de {tema} para a vida cotidiana, a participacao social e o trabalho.",
            )

        novo["texto"] = _remover_nomes_lemov(texto)
        adaptada.append(novo)

    # O parametro garantir_tecnicas_fn permanece por compatibilidade, mas nao e
    # executado no EJA: os nomes das tecnicas nao devem aparecer no plano.
    return consolidar_blocos_eja(adaptada, perfil=perfil)
