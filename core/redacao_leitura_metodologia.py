import re
import unicodedata


_TITULOS_PADRAO = [
    "Disparo inicial / contextualizacao",
    "Leitura ou exploracao inicial",
    "Analise guiada",
    "Sistematizacao",
    "Producao textual",
    "Revisao e fechamento",
]


def _normalizar(texto: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower()
    return re.sub(r"\s+", " ", texto).strip()


def _contem(base: str, termos: list[str]) -> bool:
    return any(_normalizar(termo) in base for termo in termos)


def _tema_legivel(tema: str) -> str:
    texto = re.sub(r"^\s*aula\s*\d+\s*[-:–—]?\s*", "", str(tema or ""), flags=re.I).strip(" -:–—")
    return texto or "o material em estudo"


def _obra_literaria(tema: str, texto_base: str = "") -> str:
    fonte = " ".join([str(tema or ""), str(texto_base or "")[:900]])
    match = re.search(r"[\"â€œâ€']([^\"â€œâ€']{3,120})[\"â€œâ€']", fonte)
    if match:
        return match.group(1).strip()
    texto = _tema_legivel(tema)
    texto = re.sub(r"^trilha\s*", "", texto, flags=re.I).strip(" -:–—")
    return texto or "a obra literaria em estudo"


def _eh_producao_final(base: str) -> bool:
    termos = [
        "versao final",
        "revisao orientada",
        "redacao paulista",
        "submissao",
        "reescrita",
        "rascunho",
    ]
    if "pratica de linguagem leitura" in base and not _contem(base, ["producao de textos", "rascunho", "versao final"]):
        return False
    return _contem(base, termos)


def _eh_ensino_medio(base: str, turma: str = "") -> bool:
    turma_norm = _normalizar(turma)
    return _contem(base, ["em13", "ensino medio", "1a serie", "2a serie", "3a serie", "1o ano", "2o ano", "3o ano", "serie em"]) or _contem(
        turma_norm, ["1a serie", "2a serie", "3a serie", "1o ano", "2o ano", "3o ano", "ensino medio", "em"]
    )


def _detectar_tipo_aula(texto_base: str, tema: str, turma: str = "") -> str:
    base = _normalizar(f"{tema} {turma} {texto_base}")
    if _eh_producao_final(base):
        return "producao_final"
    if _contem(base, ["devolutiva", "quadro de analise autoral", "o que esta bom", "o que precisa melhorar"]):
        return "devolutiva"
    if _contem(base, ["fluencia leitora", "leitura oral", "leitura em coro", "leitura-modelo", "ef69lp53"]):
        return "fluencia_leitora"
    if _contem(base, ["leitura e citacoes", "citacoes", "citar nao e copiar", "claim", "evidence", "reasoning"]):
        return "leitura_citacoes_em"
    if _eh_ensino_medio(base, turma) and _contem(
        base,
        [
            "argumentacao",
            "conclusao",
            "proposta de intervencao",
            "topico frasal",
            "repertorio sociocultural",
            "tese",
            "paragrafo",
            "artigo de opiniao",
            "projeto de texto e tese",
        ],
    ):
        return "argumentacao_em"
    if _contem(base, ["planejamento", "projeto de texto", "roteiro", "antes da escrita", "planejar", "organizar"]):
        return "planejamento_producao"
    return "leitura_literaria"


def _detectar_genero(texto_base: str, tema: str) -> str:
    base = _normalizar(f"{tema} {texto_base}")
    if "conto realista" in base:
        return "conto realista"
    if "artigo de opiniao" in base:
        return "artigo de opiniao"
    if "resenha" in base:
        return "resenha"
    if "cronica" in base:
        return "cronica"
    if "fabula" in base:
        return "fabula"
    if "poema" in base or "poesia" in base:
        return "poema"
    if "conto" in base:
        return "conto"
    if "dissertativo-argumentativo" in base or "proposta de intervencao" in base:
        return "redacao dissertativo-argumentativa"
    if _eh_producao_final(base):
        return "producao textual"
    return "texto literario"


def _detectar_estrategias(texto_base: str, tema: str) -> set[str]:
    base = _normalizar(f"{tema} {texto_base}")
    estrategias = set()
    if _contem(base, ["cer", "claim", "evidence", "reasoning", "afirmacao", "trecho", "mini-argumento"]):
        estrategias.add("cer")
    if _contem(base, ["predict and verify", "confirmou", "adiou", "contradisse", "previsao"]):
        estrategias.add("predict_verify")
    if _contem(base, ["paradas estrategicas", "recapitular", "inferir", "visualizar"]):
        estrategias.add("paradas_estrategicas")
    if _contem(base, ["quadro de analise autoral", "o que esta bom", "o que vou fazer"]):
        estrategias.add("quadro_autoral")
    if _contem(base, ["mapeamento coletivo", "organize no quadro", "quadro"]):
        estrategias.add("mapeamento_coletivo")
    if _contem(base, ["predicao guiada", "hipoteses", "antecipar", "prever"]):
        estrategias.add("predicao_guiada")
    if _contem(base, ["emprestimos criativos", "enriquecer", "recursos observados"]):
        estrategias.add("emprestimos_criativos")
    return estrategias


def _objetivo_pedagogico(tipo: str, genero: str, obra: str, tema: str, ensino_medio: bool) -> str:
    if tipo == "devolutiva":
        return (
            "desenvolver a autonomia autoral, transformando a devolutiva em criterio de revisao, "
            "planejamento de melhorias e tomada de decisao sobre o proprio texto"
        )
    if tipo == "producao_final":
        return (
            "consolidar o processo de escrita por meio da revisao do rascunho, da passagem para a versao final "
            "e da adequacao do texto ao genero e ao leitor previsto"
        )
    if tipo == "planejamento_producao":
        return (
            f"organizar um projeto de texto coerente para o genero {genero}, definindo intencao, estrutura, "
            "leitor previsto e criterios de qualidade antes da escrita"
        )
    if tipo in {"argumentacao_em", "leitura_citacoes_em"}:
        return (
            "articular tese, argumentos, repertorio sociocultural e coesao textual para construir uma escrita "
            "dissertativa mais consistente e intencional"
        )
    if tipo == "fluencia_leitora":
        return (
            "desenvolver leitura oral com ritmo, entonacao e compreensao, fortalecendo a autonomia leitora "
            "e a participacao da turma em praticas sociais de leitura"
        )
    foco = obra if obra and obra != "a obra literaria em estudo" else _tema_legivel(tema)
    if ensino_medio:
        return (
            f"aprofundar a leitura de {foco}, relacionando escolhas de linguagem, contexto e sentidos do texto "
            "ao repertorio que alimenta a argumentacao e a escrita"
        )
    return (
        f"aprofundar a leitura de {foco}, relacionando personagens, acontecimentos, linguagem e efeitos de sentido "
        "ao repertorio necessario para futuras producoes textuais criativas"
    )


def _roteiro_genero(genero: str) -> str:
    roteiros = {
        "conto realista": "protagonista, cenario, objeto ou fato disparador, conflito, ponto de virada, decisao, consequencia e desfecho verossimil",
        "conto": "personagens, cenario, conflito, desenvolvimento e desfecho",
        "cronica": "episodio cotidiano, narrador, ponto de vista, conflito breve, marcas de linguagem e reflexao final",
        "resenha": "apresentacao da obra, breve sintese, analise com opiniao fundamentada e recomendacao final",
        "artigo de opiniao": "tese, argumentos, repertorio, articulacao logica e conclusao coerente",
        "redacao dissertativo-argumentativa": "tese, argumentos, repertorio sociocultural e proposta de intervencao",
        "fabula": "personagens, conflito, desfecho e moral da historia",
        "poema": "voz poetica, imagens, escolhas de linguagem e efeitos de sentido",
    }
    return roteiros.get(genero, "ideia central, leitor previsto, organizacao das partes e recursos de linguagem")


def _frase_estrategias_leitura(estrategias: set[str]) -> str:
    partes = []
    if "predicao_guiada" in estrategias or "predict_verify" in estrategias:
        partes.append(
            "Provocar hipoteses antes da leitura e retomar, ao longo do percurso, se o texto confirmou, adiou ou contradisse as previsoes levantadas."
        )
    if "paradas_estrategicas" in estrategias:
        partes.append(
            "Realizar duas ou tres paradas estrategicas para recapitular fatos, levantar inferencias e imaginar cenas ou desdobramentos."
        )
    return " ".join(partes).strip()


def _metodologia_leitura_literaria(texto_base: str, tema: str, turma: str) -> list[dict]:
    obra = _obra_literaria(tema, texto_base)
    genero = _detectar_genero(texto_base, tema)
    estrategias = _detectar_estrategias(texto_base, tema)
    objetivo = _objetivo_pedagogico("leitura_literaria", genero, obra, tema, _eh_ensino_medio(_normalizar(texto_base), turma))
    frase_estrategias = _frase_estrategias_leitura(estrategias)
    mapeamento = (
        "Organizar no quadro um mapeamento coletivo de personagens, espacos, narrador, conflitos e acontecimentos, retomando como cada elemento participa da construcao de sentido."
        if "mapeamento_coletivo" in estrategias or True
        else ""
    )
    analise = (
        "Organizar a estrategia CER, relacionando afirmacoes sobre o texto, trechos que servem de evidencia e explicacoes do que esses trechos revelam."
        if "cer" in estrategias
        else "Conduzir perguntas abertas sobre personagens, acontecimentos, escolhas de linguagem e conflitos, incentivando comentarios justificadas com base no texto."
    )
    producao = (
        "Propor um registro de leitura, comentario, diario ou planejamento breve, explicando o que escrever, para quem escrever e com qual intencao, para conectar a leitura a futuras producoes textuais criativas."
    )
    if "emprestimos_criativos" in estrategias:
        producao += " Retomar recursos observados na obra e propor que os estudantes identifiquem emprestimos criativos que possam enriquecer a propria escrita."
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": (
                f"Retomar com a turma o percurso de leitura de {obra}, mobilizando memorias leitoras, impressoes pessoais e relacoes com o cotidiano antes de apresentar o novo foco da aula. "
                f"Explicitar o objetivo pedagogico da aula: {objetivo}."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": (
                f"Conduzir a leitura compartilhada ou exploracao inicial de trechos de {obra}, orientando a observacao do genero {genero}, das personagens, dos acontecimentos e da forma como o texto envolve o leitor. "
                f"{frase_estrategias}".strip()
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": analise,
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": mapeamento,
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": producao,
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                "Encerrar com sintese reflexiva e breve socializacao das leituras, retomando como a observacao de personagens, linguagem e conflitos fortalece tanto a interpretacao quanto a escrita das proximas aulas."
            ),
        },
    ]


def _metodologia_planejamento(texto_base: str, tema: str, turma: str) -> list[dict]:
    genero = _detectar_genero(texto_base, tema)
    objetivo = _objetivo_pedagogico("planejamento_producao", genero, "", tema, _eh_ensino_medio(_normalizar(texto_base), turma))
    roteiro = _roteiro_genero(genero)
    tema_legivel = _tema_legivel(tema)
    disparo = (
        "Apresentar uma situacao-problema ligada ao tema e organizar com a turma as tensoes, decisoes e consequencias que podem alimentar a escrita."
        if genero == "conto realista"
        else f"Contextualizar a proposta de {tema_legivel}, retomando o percurso do bimestre e conectando o genero ao que os estudantes ja leram e discutiram."
    )
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": f"{disparo} Explicitar o objetivo pedagogico da aula: {objetivo}.",
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": (
                f"Explorar com a turma as caracteristicas do genero {genero}, destacando sua finalidade, condicoes de producao, leitor previsto e exemplos do repertorio de leitura que podem orientar a escrita."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": (
                f"Conduzir uma analise guiada sobre o que nao pode faltar no genero, discutindo com perguntas abertas como cada escolha de linguagem, estrutura e ponto de vista contribui para o efeito de sentido do texto."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": (
                f"Organizar no quadro um roteiro orientador com {roteiro}, deixando visiveis os criterios obrigatorios que servirao de referencia para o planejamento no caderno."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": (
                f"Orientar os estudantes a registrarem no caderno o projeto de texto, definindo {roteiro}, para que a escrita comece com mais intencao, coerencia e clareza."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                f"Encerrar reforcando que um bom planejamento qualifica a escrita do genero {genero}, ajuda a antecipar problemas de organizacao e fortalece a autonomia para a producao textual que vira na sequencia."
            ),
        },
    ]


def _metodologia_devolutiva(texto_base: str, tema: str, turma: str) -> list[dict]:
    genero = _detectar_genero(texto_base, tema)
    objetivo = _objetivo_pedagogico("devolutiva", genero, "", tema, _eh_ensino_medio(_normalizar(texto_base), turma))
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": (
                f"Retomar com a turma o caminho percorrido na escrita, do planejamento ao rascunho e a versao entregue, reforcando que a devolutiva nao e julgamento final, mas orientacao de melhoria. Explicitar o objetivo pedagogico da aula: {objetivo}."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": (
                "Orientar a leitura dos comentarios, criterios e marcas de revisao, ajudando os estudantes a identificar como a plataforma ou o professor observaram construcao do texto, clareza das ideias, organizacao e adequacao ao genero."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": (
                "Conduzir perguntas-guia sobre pontos fortes, escolhas que funcionaram, aspectos que precisam melhorar e quais revisoes podem tornar o texto mais consciente, coerente e adequado ao leitor."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": (
                "Orientar o preenchimento do quadro de analise autoral com tres campos: o que esta bom, o que precisa melhorar e o que vou fazer para melhorar, circulando pela sala para mediar reflexoes sobre as escolhas de escrita."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": (
                "Solicitar um plano de acao breve ou uma reescrita focalizada do trecho mais fragil, para que cada estudante transforme a devolutiva em decisao concreta de revisao."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                "Encerrar destacando que compreender a devolutiva ajuda a enxergar o proprio texto com mais criterio e autonomia, pedindo um registro final sobre a decisao autoral que cada estudante levara para a proxima producao."
            ),
        },
    ]


def _metodologia_producao_final(texto_base: str, tema: str, turma: str) -> list[dict]:
    genero = _detectar_genero(texto_base, tema)
    objetivo = _objetivo_pedagogico("producao_final", genero, "", tema, _eh_ensino_medio(_normalizar(texto_base), turma))
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": (
                f"Apresentar o foco da aula como momento de consolidacao da escrita, retomando o percurso realizado e explicando que a turma vai passar do rascunho para a versao final. Explicitar o objetivo pedagogico da aula: {objetivo}."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": (
                "Orientar a releitura guiada do proprio texto e, quando necessario, de modelos do genero, pedindo que os estudantes observem tema, organizacao das ideias, coesao, clareza das informacoes e dialogo com o leitor."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": (
                "Conduzir uma revisao orientada com perguntas sobre o que o texto comunica, como as partes se articulam, onde faltam explicacoes ou exemplos e quais ajustes podem melhorar o efeito pretendido no leitor."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": (
                "Organizar no quadro um checklist de revisao com criterios obrigatorios: atendimento ao tema, estrutura do genero, paragrafos organizados, pontuacao, conectivos, ortografia e efeito pretendido no leitor."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": (
                "Solicitar a escrita da versao final do texto, incorporando as melhorias identificadas no rascunho e preparando o envio em contexto real de circulacao, como mural da escola, pasta da turma ou plataforma Redacao Paulista."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                "Finalizar com revisao em dupla ou individual apoiada pelo checklist, incentivando ajustes antes da entrega e retomando por que revisar, reescrever e socializar fazem parte do processo de escrita."
            ),
        },
    ]


def _metodologia_fluencia(texto_base: str, tema: str, turma: str) -> list[dict]:
    objetivo = _objetivo_pedagogico("fluencia_leitora", "", "", tema, _eh_ensino_medio(_normalizar(texto_base), turma))
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": (
                f"Retomar com a turma o contexto da leitura e explicar que a aula sera uma pratica de fluencia leitora, nao um teste punitivo. Explicitar o objetivo pedagogico da aula: {objetivo}."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": (
                "Propor uma predicao guiada a partir do titulo ou do trecho inicial e, em seguida, realizar leitura-modelo para mostrar como ritmo, pausas e entonacao ajudam a construir sentidos."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": (
                "Conduzir observacao guiada sobre pontuacao, falas das personagens, pausas e marcas de oralidade, ajudando a turma a perceber como esses elementos orientam a leitura em voz alta."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": (
                "Registrar com a turma criterios de uma boa leitura oral e combinar procedimentos de apoio, como acompanhar com o dedo, reler trechos curtos e respirar nos pontos de pausa."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": (
                "Organizar leitura compartilhada, em coro ou alternada, oferecendo apoio durante a oralizacao e incentivando uma leitura clara, segura e respeitosa entre os colegas."
            ),
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                "Encerrar retomando que ouvir o colega, ajustar a entonacao e ganhar confianca na leitura oral fazem parte da formacao leitora e ampliam a compreensao textual."
            ),
        },
    ]


def _metodologia_argumentacao_em(texto_base: str, tema: str, turma: str, leitura_citacoes: bool = False) -> list[dict]:
    objetivo = _objetivo_pedagogico(
        "leitura_citacoes_em" if leitura_citacoes else "argumentacao_em",
        "redacao dissertativo-argumentativa",
        "",
        tema,
        True,
    )
    leitura = (
        "Recuperar com a turma os textos de apoio e orientar a leitura de trechos selecionados, destacando como citacoes e repertorios nao servem para copiar, mas para dialogar com o texto e transformar leitura em argumento."
        if leitura_citacoes
        else "Recuperar com a turma a tese ja definida, os argumentos selecionados e o repertorio sociocultural disponivel, retomando como esse percurso prepara a escrita dos paragrafos e da conclusao."
    )
    analise = (
        "Explicar como selecionar citacoes produtivas, apresentar a afirmacao principal, inserir o trecho de apoio e desenvolver a explicacao do que a evidencia revela sobre o tema."
        if leitura_citacoes
        else "Explicar a estrutura do paragrafo de desenvolvimento: topico frasal, explicacao, repertorio sociocultural e analise, relacionando cada parte a uma argumentacao mais consistente."
    )
    sistematizacao = (
        "Organizar no quadro um roteiro com tese, afirmacao central, citacao escolhida, comentario analitico e articulacao entre os argumentos."
        if leitura_citacoes
        else "Organizar no quadro um roteiro de escrita com tese, argumentos, repertorio sociocultural, conectivos e criterios da proposta de intervencao."
    )
    producao = (
        "Orientar a escrita de paragrafo(s) de desenvolvimento com integracao de citacoes e explicacoes autorais, acompanhando a coerencia entre repertorio, tese e analise."
        if leitura_citacoes
        else "Orientar a producao dos paragrafos e da conclusao, retomando os criterios da proposta de intervencao completa: agente, acao, meio e finalidade."
    )
    return [
        {
            "titulo": _TITULOS_PADRAO[0],
            "texto": f"Retomar com a turma o percurso de argumentacao ja construido, situando a aula dentro do processo de escrita. Explicitar o objetivo pedagogico da aula: {objetivo}.",
        },
        {
            "titulo": _TITULOS_PADRAO[1],
            "texto": leitura,
        },
        {
            "titulo": _TITULOS_PADRAO[2],
            "texto": analise,
        },
        {
            "titulo": _TITULOS_PADRAO[3],
            "texto": sistematizacao,
        },
        {
            "titulo": _TITULOS_PADRAO[4],
            "texto": producao,
        },
        {
            "titulo": _TITULOS_PADRAO[5],
            "texto": (
                "Encerrar com revisao da coesao, da progressao argumentativa e da adequacao ao tema, destacando como a articulacao entre tese, repertorio e escrita autoral fortalece a producao final."
            ),
        },
    ]


def gerar_metodologia_redacao_leitura(texto_base: str, tema: str, turma: str = "") -> list[dict]:
    tipo = _detectar_tipo_aula(texto_base, tema, turma)
    if tipo == "producao_final":
        return _metodologia_producao_final(texto_base, tema, turma)
    if tipo == "devolutiva":
        return _metodologia_devolutiva(texto_base, tema, turma)
    if tipo == "fluencia_leitora":
        return _metodologia_fluencia(texto_base, tema, turma)
    if tipo == "planejamento_producao":
        return _metodologia_planejamento(texto_base, tema, turma)
    if tipo == "leitura_citacoes_em":
        return _metodologia_argumentacao_em(texto_base, tema, turma, leitura_citacoes=True)
    if tipo == "argumentacao_em":
        return _metodologia_argumentacao_em(texto_base, tema, turma, leitura_citacoes=False)
    return _metodologia_leitura_literaria(texto_base, tema, turma)
