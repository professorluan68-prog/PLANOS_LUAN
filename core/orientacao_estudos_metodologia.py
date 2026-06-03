import re
import unicodedata


def _normalizar(texto: str = "") -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower()
    return re.sub(r"\s+", " ", texto).strip()


def _detectar_etapa(tema: str, texto_pdf: str) -> str:
    base = _normalizar(f"{tema} {texto_pdf[:1200]}")
    if "etapa final" in base:
        return "etapa final"
    for numero in ("1", "2", "3", "4"):
        if f"etapa {numero}" in base:
            return f"etapa {numero}"
    return ""


def _limpar_tema(tema: str) -> str:
    base = str(tema or "").strip()
    base = re.sub(r"(?i)\s*-\s*etapa\s+(final|\d+)\s*$", "", base).strip()
    return base


def _titulo_legivel(tema: str) -> str:
    base = _limpar_tema(tema)
    return base or "Orientacao de Estudos"


def _perfil_por_titulo(tema: str) -> dict[str, str]:
    titulo = _normalizar(_limpar_tema(tema))
    perfis = {
        "missao 6 - uma palavra puxa a outra": {
            "objeto": "as palavras que ligam ideias em um texto",
            "foco": "conectivos, conjuncoes e relacoes de sentido entre palavras, frases e paragrafos",
        },
        "missao 7 - a trama do texto": {
            "objeto": "a coesao textual e os recursos usados para evitar repeticoes",
            "foco": "pronomes, sinonimos, retomadas e referentes que mantem a continuidade das ideias",
        },
        "missao 1 - jogos com palavras e imagens": {
            "objeto": "a relacao entre palavras, imagens e regras de jogo",
            "foco": "linguagem verbal e visual, regras e organizacao das informacoes",
        },
        "missao 2 - para chorar de rir": {
            "objeto": "o humor em historias em quadrinhos e outros textos",
            "foco": "efeitos de humor, imagens, falas e quebra de expectativa",
        },
        "missao 3 - da charge a noticia": {
            "objeto": "a comparacao entre charge e noticia",
            "foco": "finalidade, ponto de vista e formas de tratar uma mesma informacao",
        },
        "missao 4 - que tirada!": {
            "objeto": "as tirinhas e os recursos que constroem humor",
            "foco": "linguagem verbal e visual, expressividade e interpretacao das tirinhas",
        },
        "missao 5 - vamos a fundo nos assuntos": {
            "objeto": "a reportagem e a organizacao das informacoes",
            "foco": "titulo, intertitulos, imagens, legendas e aprofundamento do assunto",
        },
        "missao 8 - por dentro dos verbetes": {
            "objeto": "o verbete e sua funcao informativa",
            "foco": "organizacao do verbete, selecao de informacoes e linguagem objetiva",
        },
        "missao 9 - narrativas breves": {
            "objeto": "as narrativas breves e seus elementos",
            "foco": "personagens, conflito, tempo, espaco e sequencia dos fatos",
        },
        "missao 10 - a voz da poesia": {
            "objeto": "os poemas e seus efeitos de sentido",
            "foco": "versos, eu lirico, interlocucao e recursos expressivos",
        },
        "missao 11 - um mergulho no cordel": {
            "objeto": "o cordel e a leitura das entrelinhas",
            "foco": "versos, linguagem figurada, inferencias e pistas textuais",
        },
        "missao 12 - poema para mim e para voce": {
            "objeto": "a leitura e a producao poetica",
            "foco": "estrutura do poema, recursos expressivos e planejamento de escrita",
        },
        "missao 13 - lendas e narrativa": {
            "objeto": "as lendas e a organizacao da narrativa",
            "foco": "personagens, tempo, espaco, conflito e marcas culturais",
        },
        "missao 14 - qual e a moral da historia": {
            "objeto": "as fabulas e a moral da historia",
            "foco": "personagens, conflito, desfecho, moral e relacoes de causa e consequencia",
        },
        "missao 15 - o texto no teatro": {
            "objeto": "o texto teatral e sua organizacao",
            "foco": "falas, rubricas, pontuacao expressiva e construcao da cena",
        },
        "missao 16 - opiniao versus fato": {
            "objeto": "a diferenca entre fato e opiniao",
            "foco": "ponto de vista, argumentos, justificativas e leitura critica",
        },
        "trilha 7 - projetos culturais e coesao textual": {
            "objeto": "os projetos culturais e a coesao textual",
            "foco": "justificativa, objetivos, metodologia, avaliacao e ligacao entre as partes do texto",
        },
        "trilha 8 - cartas de leitor e argumento": {
            "objeto": "as cartas de leitor e a argumentacao",
            "foco": "tese, argumentos, ponto de vista e organizacao da carta",
        },
        "trilha 16 - textos de divulgacao cientifica": {
            "objeto": "os textos de divulgacao cientifica",
            "foco": "linguagem acessivel, tema cientifico, fonte e organizacao das informacoes",
        },
    }
    return perfis.get(titulo, {})


def _perfil_generico(tema: str) -> dict[str, str]:
    perfil = _perfil_por_titulo(tema)
    if perfil:
        return perfil
    return {
        "objeto": _titulo_legivel(tema).lower(),
        "foco": "leitura orientada, interpretacao, organizacao das respostas e autonomia de estudo",
    }


def _referencia_texto(tema: str, texto_pdf: str) -> str:
    base = _normalizar(texto_pdf)
    if "greta thunberg" in base or "fridaysforfuture" in base:
        return "a reportagem sobre Greta Thunberg e o movimento #FridaysForFuture"
    if "vendedor de picole" in base:
        return "a noticia sobre a crianca que ajudou um vendedor de picole a aprender a escrever"
    if "habilidade de um grande amigo" in base:
        return 'o texto de divulgacao cientifica "Habilidade de um grande amigo"'
    if "homem-aranha" in base or "homem-formiga" in base:
        return "o texto de divulgacao cientifica sobre filmes e tratamento de fobia"
    if "mamba" in base:
        return "o texto instrucional com regras do jogo Mamba"
    if "kalapalo" in base:
        return "o texto com regras do jogo indigena apresentado na missao"
    if "hq" in base or "quadrinhos" in base:
        return "o texto em quadrinhos trabalhado na etapa"
    if "charge" in base and "noticia" in base:
        return "os textos de charge e noticia apresentados na etapa"
    if "cordel" in base:
        return "o texto de cordel lido com a turma"
    if "teatro" in base or "rubricas" in base:
        return "o texto teatral apresentado na etapa"
    if "verbete" in base:
        return "o verbete lido com a turma"
    if "fabula" in base:
        return "a fabula trabalhada na etapa"
    if "poema" in base:
        return "o poema apresentado na etapa"
    return f"o material de { _titulo_legivel(tema).lower() }"


def _blocos_especificos_missao_6(etapa: str) -> dict[str, str] | None:
    if etapa == "etapa 1":
        return {
            "para_comecar": "Retomar com a turma a importancia das palavras que ligam ideias em um texto. A partir das perguntas iniciais, conversar sobre como seria um texto sem conectivos e registrar no quadro exemplos citados pelos alunos, como e, mas, porque, para, de e ate.",
            "leitura": "Realizar a leitura orientada da reportagem sobre Greta Thunberg e o movimento #FridaysForFuture, destacando o tema principal, o titulo, a imagem e as informacoes mais importantes. Durante a leitura, orientar os estudantes a contornar palavras e expressoes que ligam frases e paragrafos.",
            "foco": "Explicar que a reportagem e um texto jornalistico que informa sobre um assunto real, podendo apresentar dados, depoimentos e explicacoes. Relacionar essa ideia ao texto lido, mostrando que a reportagem informa sobre os protestos de criancas e jovens contra a falta de acoes para combater as mudancas climaticas.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os alunos voltem ao texto para localizar as respostas. Auxiliar os estudantes com mais dificuldade por meio de perguntas simples, ajudando-os a identificar o objetivo do movimento, quem o criou, onde a reportagem foi publicada e qual e sua finalidade.",
            "encerramento": "Corrigir as respostas de forma dialogada e retomar a ideia central da aula: as palavras de ligacao ajudam o texto a ficar mais claro, organizado e compreensivel. Finalizar com uma pequena lista coletiva de conectivos uteis para leitura e producao de textos.",
        }
    if etapa == "etapa 2":
        return {
            "para_comecar": "Retomar com a turma a reportagem lida na etapa anterior e perguntar quais palavras e expressoes ajudaram a organizar as informacoes. Relembrar tambem o intertitulo apresentado no texto e conversar sobre sua funcao na organizacao da reportagem.",
            "leitura": "Orientar os estudantes a relerem os trechos da reportagem, observando os paragrafos numerados, o titulo, o intertitulo e as expressoes destacadas nas questoes. Durante a leitura, pedir que localizem palavras que indiquem adicao, oposicao, tempo e lugar.",
            "foco": "Explicar que conjuncoes e expressoes adverbiais ajudam a ligar ideias e a indicar relacoes de sentido no texto, como soma de informacoes, contraste, tempo e espaco. Mostrar que, na reportagem, esses recursos tornam a leitura mais clara e ajudam o leitor a compreender melhor os fatos relatados.",
            "pratica": "Acompanhar a resolucao das questoes, incentivando os alunos a justificar as respostas com base no proprio texto. Mediar principalmente as atividades sobre intertitulo, conjuncao aditiva e expressoes de lugar e tempo, ajudando a turma a perceber como cada termo contribui para a construcao de sentido.",
            "encerramento": "Realizar a correcao coletivamente, retomando o que foi aprendido sobre palavras de ligacao e sua funcao na coesao textual. Finalizar com exemplos retirados da reportagem, reforcando que compreender essas relacoes ajuda tanto na leitura quanto na escrita.",
        }
    if etapa == "etapa 3":
        return {
            "para_comecar": "Iniciar com uma conversa breve sobre a importancia da leitura e da escrita na vida das pessoas, relacionando o tema a noticia sobre a crianca que ajudou um vendedor de picole a aprender a escrever o proprio nome. Estimular os estudantes a comentarem o que mais chamou atencao nessa situacao.",
            "leitura": "Realizar a leitura orientada da noticia, destacando o titulo, o subtitulo, o tema central e as informacoes principais. Durante a leitura, orientar os estudantes a localizar palavras que ligam ideias, como e, entao e mas, percebendo como elas ajudam a construir o texto.",
            "foco": "Explicar que as conjuncoes estabelecem relacoes de sentido entre palavras, frases e trechos do texto, podendo indicar adicao, conclusao ou oposicao. Relacionar essa explicacao aos exemplos da noticia, mostrando como esses conectivos organizam o relato e ajudam o leitor a compreender melhor os acontecimentos.",
            "pratica": "Conduzir a resolucao das questoes, pedindo que os alunos retomem os trechos da noticia para identificar o valor semantico das palavras destacadas. Auxiliar os estudantes que apresentarem dificuldade, relendo os trechos e perguntando o que cada palavra esta ligando e qual sentido produz.",
            "encerramento": "Corrigir as atividades com a turma, sistematizando os sentidos das conjuncoes trabalhadas na etapa. Finalizar retomando que as palavras de ligacao sao essenciais para dar clareza, continuidade e logica ao texto.",
        }
    if etapa == "etapa final":
        return {
            "para_comecar": "Retomar com a turma o percurso da missao, lembrando que, ao longo das etapas, foram estudadas palavras e expressoes que ligam ideias e ajudam na coesao textual. Conversar sobre quais conectivos os estudantes mais lembram e em quais situacoes eles aparecem com mais frequencia.",
            "leitura": "Orientar a leitura dos enunciados da etapa final, explicando a proposta do diagrama e da producao escrita. Revisitar, com apoio dos alunos, os sentidos mais comuns das conjuncoes ja estudadas, como explicacao, adicao, contradicao e conclusao.",
            "foco": "Reforcar que as conjuncoes nao apenas ligam partes do texto, mas tambem ajudam o leitor a perceber a relacao de sentido entre as ideias. Mostrar que reconhecer esses usos e importante para compreender melhor os textos e para produzir comentarios mais claros e organizados.",
            "pratica": "Acompanhar a realizacao do diagrama e a identificacao dos sentidos de cada palavra ou expressao encontrada. Em seguida, orientar a escrita do comentario no caderno, incentivando os estudantes a usar conectivos adequados para expressar opiniao e organizar as ideias.",
            "encerramento": "Socializar algumas respostas e comentar os conectivos utilizados pelos alunos em seus textos. Finalizar destacando que compreender e empregar bem essas palavras fortalece tanto a leitura quanto a producao escrita.",
        }
    return None


def _blocos_especificos_missao_7(etapa: str) -> dict[str, str] | None:
    if etapa == "etapa 1":
        return {
            "para_comecar": "Conversar com a turma sobre o que acontece quando um texto repete muitas vezes as mesmas palavras e por que isso pode torna-lo cansativo ou dificil de compreender. Retomar os conhecimentos previos dos estudantes sobre coesao textual e registrar exemplos simples de palavras que ajudam a evitar repeticoes.",
            "leitura": 'Realizar a leitura orientada do texto de divulgacao cientifica "Habilidade de um grande amigo", destacando o tema, a finalidade do genero e as descobertas da pesquisa apresentada. Durante a leitura, orientar os alunos a observar palavras e expressoes usadas para retomar informacoes ja mencionadas no texto.',
            "foco": "Explicar que, em textos de divulgacao cientifica, pronomes, sinonimos e outras retomadas ajudam a manter a continuidade textual, evitando repeticoes desnecessarias. Relacionar essa ideia ao texto lido, mostrando como essas escolhas tornam a leitura mais clara, fluida e organizada.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os alunos localizem no texto as respostas sobre o objetivo da pesquisa, a forma como ela foi realizada e o que foi descoberto. Auxiliar os estudantes com dificuldade a identificar as palavras que retomam informacoes e a compreender por que elas foram usadas.",
            "encerramento": "Corrigir as respostas de maneira dialogada e retomar a ideia central da aula: a coesao textual ajuda a ligar partes do texto e a evitar repeticoes. Finalizar destacando que pronomes e sinonimos sao recursos importantes para dar continuidade e clareza a escrita.",
        }
    if etapa == "etapa 2":
        return {
            "para_comecar": "Retomar com a turma o texto de divulgacao cientifica lido anteriormente e perguntar quais palavras foram usadas para evitar repeticoes. Relembrar tambem a finalidade desse genero textual e o papel da leitura atenta para responder as questoes.",
            "leitura": "Orientar a releitura dos paragrafos do texto, pedindo que os estudantes observem os trechos destacados nas atividades e identifiquem a que ou a quem se referem palavras como isso, eles e outras expressoes de retomada.",
            "foco": "Explicar que pronomes e substituicoes lexicais funcionam como elementos coesivos, retomando informacoes ja apresentadas e mantendo a continuidade das ideias. Mostrar que compreender essas retomadas ajuda a interpretar melhor o texto e a responder com mais seguranca.",
            "pratica": "Acompanhar a resolucao das questoes, orientando os estudantes a voltar ao paragrafo indicado e localizar a ideia retomada em cada caso. Incentivar justificativas apoiadas no proprio texto, especialmente nas atividades que tratam da finalidade do genero, dos referentes e das substituicoes vocabulares.",
            "encerramento": "Corrigir as atividades coletivamente e retomar com a turma que palavras de retomada evitam repeticoes e tornam o texto mais organizado. Finalizar sistematizando alguns exemplos do texto lido para consolidar a aprendizagem.",
        }
    if etapa == "etapa 3":
        return {
            "para_comecar": "Apresentar a nova situacao de leitura da etapa, perguntando se filmes e personagens conhecidos podem ajudar as pessoas a compreender ou enfrentar determinados medos. Estimular os estudantes a comentar suas hipoteses antes da leitura.",
            "leitura": "Realizar a leitura orientada do texto de divulgacao cientifica sobre o uso de cenas de filmes do Homem-Aranha e do Homem-Formiga no tratamento de fobias. Destacar o tema, o objetivo do estudo, os resultados observados e a fala do especialista apresentada no material.",
            "foco": "Explicar que o texto de divulgacao cientifica apresenta informacoes de pesquisas em linguagem acessivel e usa recursos de coesao para manter a clareza das ideias. Relacionar o estudo apresentado ao trabalho com pronomes, sinonimos e retomadas, mostrando como eles ajudam a acompanhar o encadeamento das informacoes.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os estudantes releiam os paragrafos indicados para identificar a que palavras como isso, consigo, seus e seu se referem. Ajudar a turma a perceber como essas retomadas evitam repeticoes e facilitam a compreensao do texto.",
            "encerramento": "Realizar a correcao dialogada e retomar a ideia de que a coesao textual ajuda o leitor a manter o fio das informacoes ao longo do texto. Finalizar destacando que entender referentes e substituicoes e uma estrategia importante de estudo e leitura.",
        }
    if etapa == "etapa final":
        return {
            "para_comecar": "Retomar o percurso da missao, lembrando que a turma estudou como diferentes palavras e expressoes ajudam a dar continuidade ao texto e evitar repeticoes. Conversar rapidamente sobre o que os estudantes ja conseguem observar com mais facilidade ao reler um texto.",
            "leitura": "Ler com a turma o trecho de divulgacao cientifica proposto na etapa final e explicar a tarefa de localizar palavras usadas para se referir as abelhas ao longo do texto. Em seguida, apresentar a proposta de escrita de um pequeno texto de divulgacao cientifica sobre um inseto.",
            "foco": "Reforcar que, para produzir um texto claro e bem organizado, e importante variar as palavras usadas para retomar o mesmo referente, mantendo a continuidade das ideias. Relacionar essa estrategia a leitura e a escrita de textos de divulgacao cientifica.",
            "pratica": "Acompanhar os estudantes na identificacao das palavras que retomam abelha(s) no texto e, depois, orientar a producao escrita no caderno, ajudando a organizar tema, informacoes principais e substituicoes lexicais que evitem repeticoes desnecessarias.",
            "encerramento": "Socializar algumas producoes ou escolhas de vocabulario feitas pela turma e retomar o objetivo da missao: compreender como a coesao textual ajuda a construir textos mais claros, fluidos e bem organizados.",
        }
    return None


def _blocos_especificos_missao_10(etapa: str) -> dict[str, str] | None:
    if etapa == "etapa 1":
        return {
            "para_comecar": "Iniciar com uma conversa breve sobre poemas que os estudantes ja ouviram ou leram e sobre como os sons das palavras podem chamar a atencao do leitor. Retomar tambem as perguntas iniciais da missao, aproximando a leitura do universo dos animais e das experiencias da turma com poemas infantis.",
            "leitura": "Realizar a leitura orientada do poema O gato, primeiro em silencio e depois em voz alta, destacando titulo, tema, musicalidade e palavras que rimam. Durante a leitura, orientar os estudantes a observar quem fala no poema, o publico ao qual o texto parece se dirigir e como os versos ajudam a construir a imagem do gato.",
            "foco": "Explicar que o poema organiza sentidos por meio de versos, estrofes, ritmo e rimas, e que essas escolhas ajudam o leitor a perceber o tom do texto. Relacionar essa ideia ao poema lido, mostrando como a descricao do gato, as rimas e a linguagem simples aproximam o texto de um publico infantil.",
            "pratica": "Acompanhar a resolucao das atividades, pedindo que os estudantes voltem ao poema para localizar o tema, o possivel publico-alvo, o significado de expressões como acrobata nato e a quantidade de versos e estrofes. Auxiliar a turma a marcar as rimas e a justificar as respostas com base em trechos do texto.",
            "encerramento": "Corrigir as atividades de forma dialogada e retomar o que foi aprendido sobre poema, rimas, versos e estrofes. Finalizar destacando que observar essas marcas ajuda a compreender melhor quem fala no texto, com quem dialoga e como o poema produz seus efeitos de sentido.",
        }
    if etapa == "etapa 2":
        return {
            "para_comecar": "Retomar a leitura poetica da etapa anterior e conversar com a turma sobre lembrancas da infancia e conselhos dados por adultos. Relacionar essa conversa ao poema Gente grande, preparando os estudantes para observar quem fala no texto e que pistas revelam essa voz.",
            "leitura": "Realizar a leitura orientada do poema Gente grande, destacando os versos que mostram brincadeiras, avisos e medos da infancia. Durante a leitura, pedir que os estudantes numerem os versos e observem expressoes que ajudem a identificar o eu lirico, as vozes presentes no texto e o possivel publico interessado no poema.",
            "foco": "Explicar que, em um poema, o eu lirico pode revelar sua idade, suas lembrancas e seu ponto de vista por meio das palavras escolhidas. Mostrar que, nesse texto, os verbos, os avisos repetidos e o verso final ajudam a inferir que quem fala revisita experiencias da infancia e dialoga com leitores de diferentes idades.",
            "pratica": "Orientar a resolucao das atividades, pedindo que a turma localize o verso que revela que o eu lirico virou gente grande, interprete quem teria dito os avisos presentes no poema e analise a quem o texto pode interessar. Incentivar a justificativa das respostas com base nos versos lidos.",
            "encerramento": "Realizar a correcao coletivamente e retomar com os estudantes que a leitura de poemas tambem exige inferencia de informacoes sobre quem fala, para quem se fala e em que contexto. Finalizar destacando como a linguagem simples e afetiva amplia a identificacao do leitor com o texto.",
        }
    if etapa == "etapa 3":
        return {
            "para_comecar": "Apresentar a nova leitura perguntando como a maneira de falar de uma pessoa pode aparecer em um poema. Estimular a turma a comentar expressoes regionais ou falas familiares que conhecem, preparando a observacao das marcas de oralidade presentes no texto.",
            "leitura": "Realizar a leitura expressiva do poema Drome, minininha, convidando os estudantes a ouvir o ritmo, as repeticoes e as palavras que se aproximam da fala cotidiana. Durante a leitura, orientar a turma a perceber a quem o eu lirico se dirige, quais pistas revelam esse interlocutor e como aparecem variedades linguisticas e marcas de linguagem informal.",
            "foco": "Explicar que poemas tambem podem valorizar modos de falar de diferentes grupos e regioes, usando vocativos, reducoes de palavras e variedades linguisticas para construir sentido. Relacionar essa ideia ao poema lido, mostrando como esses recursos ajudam a caracterizar a voz que embala a crianca e reforcam o tom afetivo do texto.",
            "pratica": "Conduzir a resolucao das atividades, pedindo que os estudantes identifiquem o verso que mostra a quem o eu lirico se dirige, interpretem o valor de palavras como drome e Orora e reconhecam exemplos de linguagem informal no poema. Auxiliar a turma a justificar as respostas com base em trechos do texto.",
            "encerramento": "Corrigir as atividades dialogando sobre oralidade, variedade linguistica e efeitos de sentido no poema. Finalizar retomando que compreender essas marcas ajuda a ler com mais atencao quem fala, para quem fala e como a linguagem poetica se aproxima da vida cotidiana.",
        }
    if etapa == "etapa final":
        return {
            "para_comecar": "Retomar com a turma o percurso da missao, lembrando que os poemas estudados mostraram diferentes vozes, interlocutores e efeitos de linguagem. Conversar brevemente sobre como os estudantes identificam relacoes afetivas em textos poeticos e que elementos ajudam nessa leitura.",
            "leitura": "Ler com a turma o poema Jardim, destacando que ele se organiza como um dialogo entre mae e filha e que a musicalidade e o tom afetivo ajudam a construir seu sentido. Em seguida, apresentar a proposta de producao poetica inspirada nessa relacao entre crianca e mae.",
            "foco": "Reforcar que o poema pode revelar interlocutores, emocao e intencao por meio de vocativos, imagens poeticas, ritmo e escolha de palavras. Relacionar essa ideia ao texto lido, mostrando como esses recursos ajudam a reconhecer o publico infantil e servem de apoio para a escrita de um novo poema.",
            "pratica": "Acompanhar a resolucao das questoes sobre os interlocutores e o publico-alvo do poema e, depois, orientar a producao escrita, ajudando os estudantes a planejar versos que caracterizem uma crianca e sua mae, com linguagem poetica e tom afetivo. Se necessario, retomar exemplos da missao para apoiar a escrita.",
            "encerramento": "Socializar algumas producoes ou trechos criados pela turma e retomar o objetivo da missao: ler poemas observando eu lirico, interlocucao e recursos expressivos. Finalizar incentivando os estudantes a perceber que a poesia pode transformar experiencias cotidianas em linguagem sensivel e criativa.",
        }
    return None


def _blocos_especificos_missao_11(etapa: str) -> dict[str, str] | None:
    if etapa == "etapa 1":
        return {
            "para_comecar": "Iniciar com uma conversa breve sobre o que os estudantes ja sabem a respeito da literatura de cordel e sobre a ideia de compreender as entrelinhas de um texto. Retomar as perguntas iniciais da missao para preparar a leitura de um cordel conhecido, mas apresentado em versos.",
            "leitura": "Realizar a leitura orientada do cordel A Bela e a Fera em cordel, destacando o enredo, as rimas e a organizacao dos versos em estrofes. Durante a leitura, orientar os estudantes a acompanhar o que acontece com o pai de Bela, como a personagem reage e que pistas do texto ajudam a entender a narrativa.",
            "foco": "Explicar que o cordel e um genero de origem oral que narra historias em versos rimados, exigindo do leitor atencao ao enredo e as pistas textuais. Relacionar essa ideia ao texto lido, mostrando como o ritmo, as rimas e a narrativa ajudam a compreender os acontecimentos e a inferir informacoes.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os estudantes localizem no cordel o momento em que o pai de Bela e abordado pela Fera e o que Bela faz ao descobrir o ocorrido. Incentivar a turma a justificar as respostas com base em trechos do texto e na sequencia dos acontecimentos.",
            "encerramento": "Corrigir as atividades de forma dialogada e retomar com a turma as caracteristicas iniciais do cordel: narrativa em versos, rimas e leitura atenta das pistas do texto. Finalizar destacando que compreender o enredo e o que nao esta dito de forma direta e parte importante da leitura desse genero.",
        }
    if etapa == "etapa 2":
        return {
            "para_comecar": "Retomar com a turma o cordel lido na etapa anterior e perguntar o que mais chamou atencao na atitude de Bela e no desfecho dos acontecimentos. Relembrar tambem como versos, estrofes e rimas ajudam a organizar a narrativa.",
            "leitura": "Orientar a releitura de trechos do cordel, destacando o final da historia, as caracteristicas de Bela, a reacao do pai e a composicao das estrofes. Durante a leitura, pedir que os estudantes observem quantos versos ha em cada estrofe, quais palavras rimam e qual parece ser a finalidade do texto.",
            "foco": "Explicar que o cordel combina narracao e organizacao poetica, exigindo que o leitor observe tanto o enredo quanto a forma. Mostrar que, nesse texto, a coragem e a solidariedade de Bela podem ser inferidas pelas acoes da personagem, ao mesmo tempo em que a estrutura em sextilhas e as rimas marcam o ritmo da leitura.",
            "pratica": "Acompanhar a resolucao das atividades, orientando os estudantes a interpretar o desfecho, analisar o sentimento do pai, contar versos, localizar rimas e identificar a finalidade predominante do cordel. Incentivar a justificativa das respostas com base no texto e na observacao da composicao poetica.",
            "encerramento": "Realizar a correcao coletivamente e sistematizar o que foi aprendido sobre estrutura do cordel e leitura inferencial. Finalizar reforcando que compreender forma e conteudo ao mesmo tempo ajuda a ler com mais profundidade textos em versos.",
        }
    if etapa == "etapa 3":
        return {
            "para_comecar": "Apresentar o novo cordel da etapa perguntando o que a palavra simplicidade pode significar em diferentes modos de vida. Incentivar os estudantes a comentar imagens, comidas, costumes e valores que associam ao Sertao antes da leitura.",
            "leitura": "Realizar a leitura orientada do cordel Prefiro a simplicidade, com entonacao que destaque ritmo, repeticoes e rimas. Durante a leitura, orientar os estudantes a numerar as estrofes, identificar a ideia central de cada uma e observar palavras e expressoes que revelam aspectos culturais do Sertao.",
            "foco": "Explicar que, nesse cordel, o leitor precisa inferir o encantamento do eu lirico pela vida no Sertao a partir de elementos implicitos, como referencias a alimentos, habitos, linguagem e modos de convivencia. Mostrar que essas pistas textuais ajudam a construir o tema e a identificar a regiao evocada pelo texto.",
            "pratica": "Conduzir a resolucao das atividades, pedindo que os estudantes interpretem o tema do cordel, identifiquem a referencia a pratos tradicionais e infiram a regiao a que o eu lirico se liga. Auxiliar a turma a justificar as respostas por meio das palavras, imagens e situacoes presentes nas estrofes.",
            "encerramento": "Corrigir as atividades com a turma, retomando a ideia de que ler cordel tambem envolve perceber referencias culturais e sentidos que nao aparecem de forma totalmente explicita. Finalizar destacando que inferir essas pistas amplia a compreensao do texto e do contexto retratado.",
        }
    if etapa == "etapa final":
        return {
            "para_comecar": "Retomar o percurso da missao, lembrando que a turma leu cordeis, observou rimas, analisou enredos e inferiu informacoes implicitas. Conversar sobre o que caracteriza uma estrofe de cordel e como as rimas ajudam a construir seu ritmo.",
            "leitura": "Ler em voz alta uma estrofe de cordel e revisar com a turma a organizacao em seis versos, com rimas ao final do segundo, quarto e sexto versos. Em seguida, apresentar o quadro de palavras rimadas e a proposta de composicao da propria estrofe.",
            "foco": "Reforcar que escrever cordel exige planejamento da ideia central, atencao ao numero de versos e escolha cuidadosa das rimas. Relacionar essa organizacao ao modelo estudado na missao, mostrando que a escrita poetica se apoia na leitura atenta de exemplos e na experimentacao com a linguagem.",
            "pratica": "Acompanhar os estudantes na selecao das palavras que rimam e na producao de uma estrofe de seis versos, ajudando a organizar tema, ritmo e encaixe das rimas. Se necessario, orientar testes orais das combinacoes antes da escrita e apoiar a ilustracao final do poema.",
            "encerramento": "Socializar algumas estrofes produzidas pela turma e retomar o objetivo da missao: mergulhar no cordel para ler, inferir e tambem criar. Finalizar valorizando o uso das rimas e da criatividade como forma de ampliar a relacao dos estudantes com a poesia popular.",
        }
    return None


def _blocos_especificos_jornada_13(texto_pdf: str) -> dict[str, str] | None:
    base = _normalizar(texto_pdf)

    if any(chave in base for chave in ["meme", "etica dos memes", "girl running", "cemi", "dinofauro"]):
        return {
            "para_comecar": "Iniciar com uma conversa breve sobre os recursos midiaticos que fazem parte do cotidiano da turma, como memes, imagens e campanhas que circulam nas redes. Retomar a abertura da jornada para aproximar o tema da leitura critica de textos que combinam linguagem verbal, visual e humor.",
            "leitura": "Realizar a leitura orientada dos textos e imagens da aula, destacando como memes e outros recursos graficos constroem sentidos, fazem referencia a repertorios conhecidos e podem ser usados para informar, criticar ou conscientizar. Durante a leitura, orientar os estudantes a localizar o objetivo de cada texto e o contexto em que ele circula.",
            "foco": "Explicar que recursos midiaticos, como memes e campanhas visuais, dependem da relacao entre imagem, texto e repertorio do leitor para produzir humor, ironia ou mobilizacao social. Relacionar essa ideia aos materiais lidos, mostrando como a leitura interpretativa ajuda a identificar referencia, finalidade e posicionamento.",
            "pratica": "Acompanhar a resolucao das atividades, pedindo que a turma identifique a que memes os textos fazem referencia, qual e o objetivo de cada producao e como a etica interfere na circulacao desse tipo de conteudo. Incentivar justificativas com base nas pistas visuais e verbais de cada exemplo.",
            "encerramento": "Corrigir as respostas de forma dialogada e retomar que compreender recursos midiaticos exige observar contexto, finalidade e efeitos de sentido. Finalizar destacando que nem todo meme serve apenas para divertir: muitos tambem informam, criticam e conscientizam.",
        }

    if any(chave in base for chave in ["amigos virtuais", "redes sociais", "vinculos", "campanha de conscientizacao", "orgaos de saude", "vacin"]):
        return {
            "para_comecar": "Retomar com a turma o percurso da jornada e conversar brevemente sobre como os recursos midiaticos interferem na vida social, tanto nas relacoes virtuais quanto nas campanhas de interesse coletivo. Incentivar os estudantes a pensar em mensagens que circulam com rapidez e impactam comportamentos.",
            "leitura": "Realizar a leitura orientada da charge sobre relacoes virtuais e do cartaz de conscientizacao, destacando o contraste entre humor e alerta social. Durante a leitura, orientar os estudantes a observar como texto, imagem, cores e composicao visual ajudam a provocar reflexao e a mobilizar o publico.",
            "foco": "Explicar que charges e campanhas publicitarias institucionais usam recursos midiaticos diferentes, mas ambos dependem da articulacao entre linguagem verbal e visual para produzir efeito no leitor. Relacionar essa ideia aos materiais da aula, mostrando como eles ajudam a refletir sobre vinculos sociais, saude e responsabilidade coletiva.",
            "pratica": "Conduzir a resolucao das atividades, pedindo que os estudantes interpretem o humor da charge, identifiquem a critica aos vinculos superficiais nas redes e analisem por que o anuncio institucional pode ser considerado um texto do campo da vida publica com base cientifica. Auxiliar a turma a justificar as respostas com elementos do material.",
            "encerramento": "Realizar a correcao coletiva e finalizar retomando que recursos midiaticos podem divertir, alertar e conscientizar ao mesmo tempo. Destacar que ler esses textos com atencao ajuda a perceber intencoes comunicativas e a agir de forma mais critica diante das mensagens que circulam socialmente.",
        }

    if any(chave in base for chave in ["charge", "por que mais terras", "ranking", "profissoes", "preferencias profissionais"]):
        return {
            "para_comecar": "Retomar com a turma a ideia de que recursos midiaticos organizam e orientam a leitura de informacoes em diferentes generos. Conversar brevemente sobre como charges e rankings podem levar o leitor a comparar dados e tambem perceber pontos de vista.",
            "leitura": "Realizar a leitura orientada da charge e do ranking apresentados na aula, destacando elementos verbais, visuais e graficos que ajudam a construir sentido. Durante a leitura, orientar os estudantes a observar ironia, critica social, comparacoes e contrastes entre os dados apresentados.",
            "foco": "Explicar que a charge expressa posicionamento por meio de humor e ironia, enquanto o ranking organiza informacoes de forma comparativa para facilitar a analise. Relacionar essas caracteristicas aos materiais lidos, mostrando como diferentes recursos midiaticos ajudam o leitor a interpretar opinioes, dados e escolhas sociais.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os estudantes interpretem a critica presente na charge, reconhecam o efeito das falas dos personagens e analisem o que o ranking revela sobre preferencias profissionais. Incentivar a turma a justificar as respostas com base em trechos, imagens e dados observados.",
            "encerramento": "Realizar a correcao coletivamente e sistematizar com a turma que recursos visuais e graficos nao apenas enfeitam os textos, mas tambem orientam a leitura e reforcam posicionamentos. Finalizar retomando a importancia da leitura critica de charges e tabelas no campo da vida publica.",
        }

    if any(chave in base for chave in ["consulta publica", "novo ensino medio", "robos", "inteligencia artificial", "substituir os humanos"]):
        return {
            "para_comecar": "Apresentar a nova situacao de leitura perguntando como campanhas publicas e charges podem levar a populacao a refletir sobre temas coletivos. Estimular a turma a comentar exemplos de campanhas que ja viram e assuntos atuais ligados a tecnologia e sociedade.",
            "leitura": "Realizar a leitura orientada da campanha institucional e da charge propostas na aula, destacando o objetivo da consulta publica, o uso das cores e da tipografia e o contraste entre texto e imagem na construcao do humor. Durante a leitura, orientar os estudantes a observar como os elementos visuais reforcam a mensagem principal.",
            "foco": "Explicar que campanhas institucionais buscam mobilizar o publico em torno de causas coletivas, enquanto charges usam humor e ironia para provocar reflexao critica. Relacionar essa ideia aos textos lidos, mostrando como recursos verbais e visuais ajudam a construir posicionamento e leitura interpretativa.",
            "pratica": "Acompanhar a resolucao das atividades, pedindo que os estudantes identifiquem o objetivo da campanha, analisem o papel das cores e interpretem a critica social presente na charge sobre robos e exclusao. Incentivar a justificativa das respostas com base nas escolhas graficas e no contraste entre imagem e fala.",
            "encerramento": "Corrigir as atividades de maneira dialogada e retomar com a turma que recursos midiaticos podem informar, convocar participacao e tambem questionar problemas sociais. Finalizar destacando que a leitura critica desses materiais ajuda a compreender melhor o debate publico contemporaneo.",
        }

    return None


def _blocos_especificos_jornada_14(texto_pdf: str) -> dict[str, str] | None:
    base = _normalizar(texto_pdf)

    if any(chave in base for chave in ["hunsruckisch", "migna terra", "sarampo", "girias das redes sociais", "fazer a egipcia"]):
        return {
            "para_comecar": "Retomar com a turma a ideia de que a língua muda conforme o tempo, os grupos sociais e os contextos de uso. Conversar brevemente sobre gírias, formas regionais de falar e situações em que as pessoas escolhem registros diferentes para se comunicar.",
            "leitura": "Realizar a leitura orientada dos textos da aula, destacando gírias das redes sociais, exemplos de plurilinguismo e usos informais da língua em charges e poemas. Durante a leitura, orientar os estudantes a observar como cada texto revela uma variedade linguística ou um modo particular de dizer.",
            "foco": "Explicar que a variação linguística pode aparecer no vocabulário, na pronúncia, na escrita e no modo como diferentes grupos se expressam. Relacionar essa ideia aos materiais lidos, mostrando que gírias, línguas de imigração e registros coloquiais fazem parte da diversidade linguística e não devem ser vistos como sinal de erro absoluto ou inferioridade.",
            "pratica": "Conduzir a resolução das atividades, pedindo que os estudantes identifiquem exemplos de linguagem informal, variantes de grupos específicos e situações de plurilinguismo. Incentivar justificativas com base nos textos e apoiar a turma na comparação entre usos formais, informais e regionais da língua.",
            "encerramento": "Corrigir as respostas de forma dialogada e retomar que a língua está viva porque se transforma com seus falantes. Finalizar destacando que reconhecer essa diversidade ajuda a combater preconceitos e a compreender melhor os diferentes modos de expressão presentes na sociedade.",
        }

    if any(chave in base for chave in ["catulo", "caboca", "peleumonia", "nao existe peleumonia", "caboca di caxanga"]):
        return {
            "para_comecar": "Apresentar a nova situação de leitura perguntando como a forma de falar pode revelar origem, grupo social, época e relações de poder. Estimular a turma a comentar se já viu alguém ser julgado pelo modo como fala ou escreve.",
            "leitura": "Realizar a leitura orientada dos textos da aula, destacando a linguagem regional da canção, o uso de variantes populares e a notícia sobre preconceito linguístico no atendimento médico. Durante a leitura, orientar os estudantes a observar como as escolhas linguísticas ajudam a construir identidade e também podem gerar discriminação.",
            "foco": "Explicar que variedades linguísticas regionais, sociais e situacionais fazem parte do funcionamento da língua e revelam histórias, pertencimentos e contextos de uso. Relacionar essa ideia aos textos lidos, mostrando que a avaliação preconceituosa da fala do outro produz exclusão e desrespeito.",
            "pratica": "Acompanhar a resolução das atividades, pedindo que os estudantes identifiquem marcas de oralidade, regionalismo e preconceito linguístico nos textos. Incentivar a turma a justificar as respostas com trechos lidos e a refletir sobre os efeitos sociais de ridicularizar a forma de falar de alguém.",
            "encerramento": "Realizar a correção coletiva e retomar com a turma que falar de modos diferentes não significa falar 'errado' em qualquer situação. Finalizar destacando a importância de reconhecer a diversidade linguística e usar a norma-padrão quando o contexto exigir, sem desvalorizar outras formas de expressão.",
        }

    if any(chave in base for chave in ["tipo de variacao linguistica", "macaxeira", "mandioca", "registro formal", "quarto de despejo", "decolonialidade"]):
        return {
            "para_comecar": "Iniciar com uma conversa sobre como a lingua muda ao longo do tempo e tambem se adapta aos lugares, grupos sociais e situacoes de comunicacao. Retomar com a turma exemplos conhecidos de palavras que variam de uma regiao para outra ou de contextos em que se usa linguagem mais formal ou mais informal.",
            "leitura": "Realizar a leitura orientada dos textos da aula, destacando a comparacao entre relato cientifico e diario, as diferencas de registro e as explicacoes sobre tipos de variacao linguistica. Durante a leitura, orientar os estudantes a observar marcas de formalidade, subjetividade, oralidade e contexto social dos textos.",
            "foco": "Explicar que a lingua apresenta variacoes historicas, geograficas, sociais e situacionais, e que essas diferencas aparecem em generos diversos, como artigo cientifico, diario e textos de circulacao cotidiana. Relacionar essa ideia aos materiais lidos, mostrando que reconhecer essas marcas ajuda a compreender melhor os efeitos de sentido e o contexto de producao.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os estudantes comparem os generos lidos, identifiquem usos de registro formal e informal e localizem exemplos de variacao linguistica. Auxiliar a turma a justificar as respostas com base nas caracteristicas do texto e na situacao comunicativa apresentada.",
            "encerramento": "Corrigir as respostas de forma dialogada e sistematizar com a turma os principais tipos de variacao linguistica observados na aula. Finalizar reforcando que estudar a lingua tambem significa compreender suas transformacoes e respeitar os diferentes modos de expressao presentes na sociedade.",
        }

    return {
        "para_comecar": "Retomar com a turma que a lingua portuguesa nao e fixa nem unica em todos os contextos, mas se transforma conforme o tempo, os lugares, os grupos e as necessidades de comunicacao. Incentivar os estudantes a comentar exemplos de palavras, expressoes ou modos de falar que conhecem em diferentes situacoes.",
        "leitura": "Realizar a leitura orientada dos textos da aula, destacando exemplos de variedades linguisticas, registros formais e informais e situacoes em que a lingua revela identidade, pertencimento ou preconceito. Durante a leitura, orientar os estudantes a observar como os textos tratam a diversidade linguistica.",
        "foco": "Explicar que a variacao linguistica e parte do funcionamento da lingua viva e aparece em diferentes generos, suportes e contextos sociais. Relacionar essa ideia aos materiais lidos, mostrando que compreender essas variacoes ajuda a ler com mais criticidade e respeito as diferentes formas de expressao.",
        "pratica": "Acompanhar a resolucao das atividades, pedindo que os estudantes identifiquem marcas de variacao, analisem situacoes comunicativas e comparem usos formais e informais da lingua. Incentivar justificativas com base nos textos e nas pistas linguisticas encontradas.",
        "encerramento": "Corrigir as respostas de forma dialogada e finalizar retomando que conhecer variedades linguisticas nao significa abandonar a norma-padrao, mas entender quando e por que diferentes usos da lingua aparecem. Destacar que essa compreensao ajuda a combater preconceitos e ampliar a leitura de mundo.",
    }


def montar_frases_orientacao_estudos(tema: str, texto_pdf: str) -> dict[str, str]:
    etapa = _detectar_etapa(tema, texto_pdf)
    tema_norm = _normalizar(_limpar_tema(tema))

    blocos = None
    if "missao 6 - uma palavra puxa a outra" in tema_norm:
        blocos = _blocos_especificos_missao_6(etapa)
    elif "missao 7 - a trama do texto" in tema_norm:
        blocos = _blocos_especificos_missao_7(etapa)
    elif "missao 10 - a voz da poesia" in tema_norm:
        blocos = _blocos_especificos_missao_10(etapa)
    elif "missao 11 - um mergulho no cordel" in tema_norm:
        blocos = _blocos_especificos_missao_11(etapa)
    elif "jornada 13" in tema_norm and "recursos midi" in tema_norm:
        blocos = _blocos_especificos_jornada_13(texto_pdf)
    elif "jornada 14" in tema_norm and "variedades lingu" in tema_norm:
        blocos = _blocos_especificos_jornada_14(texto_pdf)

    if blocos:
        res = dict(blocos)
        res["_e_especifico"] = True
        return res

    perfil = _perfil_generico(tema)
    titulo_legivel = _titulo_legivel(tema)
    referencia = _referencia_texto(tema, texto_pdf)
    objeto = perfil["objeto"]
    foco = perfil["foco"]

    if etapa == "etapa 2":
        res = {
            "para_comecar": f"Retomar com a turma a leitura e os registros da etapa anterior, recuperando o que ja foi observado sobre {objeto} e quais pistas ajudaram na compreensao do material.",
            "leitura": f"Orientar a releitura de trechos, enunciados e exemplos presentes em {referencia}, ajudando os estudantes a localizar informacoes, identificar detalhes importantes e perceber como as questoes retomam o texto.",
            "foco": f"Explicar com a turma os aspectos centrais de {foco}, mostrando como eles aparecem no material e como podem ser usados para interpretar melhor as questoes propostas.",
            "pratica": "Acompanhar a resolucao das atividades de analise, pedindo que os alunos retornem aos trechos lidos para justificar as respostas e explicitem o caminho que seguiram para chegar a cada conclusao.",
            "encerramento": "Corrigir as respostas de forma dialogada e sistematizar no quadro os principais aprendizados da etapa, reforcando as estrategias de leitura e estudo usadas pela turma.",
        }
    elif etapa == "etapa 3":
        res = {
            "para_comecar": f"Introduzir a nova situacao de leitura da etapa e relaciona-la ao que ja foi estudado sobre {objeto}, incentivando os estudantes a antecipar o que podem observar ou comparar no novo material.",
            "leitura": f"Realizar a leitura orientada de {referencia}, destacando o tema central, as informacoes principais e os elementos que ajudam a ampliar ou aplicar o conhecimento construido nas etapas anteriores.",
            "foco": f"Retomar {foco} a partir do novo texto or situacao apresentada, ajudando a turma a perceber continuidades, diferencas e novas possibilidades de interpretacao.",
            "pratica": "Orientar a resolucao das atividades com leitura atenta, comparacao de trechos, justificativa de respostas e retomada de evidencias do material sempre que necessario.",
            "encerramento": "Socializar algumas respostas e fechar a etapa destacando como as estrategias de leitura, registro e revisao ajudam a compreender melhor o material e a responder com mais autonomia.",
        }
    elif etapa == "etapa final":
        res = {
            "para_comecar": f"Retomar com a turma o percurso de {titulo_legivel}, lembrando o que foi estudado nas etapas anteriores e quais estrategias mais ajudaram na leitura, na interpretacao e na organizacao das respostas.",
            "leitura": f"Orientar a leitura dos enunciados e desafios finais presentes em {referencia}, explicando o objetivo da sintese, da producao ou da atividade de fechamento proposta pelo material.",
            "foco": f"Reforcar com a turma os aspectos centrais de {foco}, mostrando como eles aparecem no fechamento da missao ou trilha e como podem ser retomados em outras situacoes de estudo.",
            "pratica": "Acompanhar a realizacao da atividade final, orientando a retomada de anotacoes, a revisao das respostas e a organizacao de uma producao clara, coerente e ligada ao percurso desenvolvido ao longo da aula.",
            "encerramento": "Finalizar com uma socializacao breve e uma sintese coletiva do que foi aprendido, destacando como as estrategias praticadas podem ser aplicadas em outros textos, aulas e momentos de estudo.",
        }
    else:
        res = {
            "para_comecar": f"Retomar com a turma conhecimentos previos sobre {objeto}, aproximando o tema da experiencia dos estudantes e registrando no quadro pistas iniciais que possam orientar o estudo do material.",
            "leitura": f"Realizar a leitura orientada de {referencia}, destacando o tema central, a finalidade do texto e as informacoes mais importantes. Durante a leitura, orientar os estudantes a marcar palavras-chave e trechos que ajudem na compreensao.",
            "foco": f"Explicar {foco}, relacionando o conteudo ao material lido e mostrando como ele pode ser estudado com mais autonomia, por meio de leitura atenta, localizacao de informacoes e justificativa de respostas.",
            "pratica": "Orientar a resolucao das atividades, pedindo que os alunos voltem ao texto para localizar evidencias, interpretar os comandos e organizar respostas completas. Auxiliar os estudantes com mais dificuldade por meio de perguntas simples e retomadas coletivas.",
            "encerramento": "Corrigir as respostas de forma dialogada e retomar a ideia central da aula, destacando quais estrategias de leitura e estudo ajudaram mais a turma a compreender o material e a se organizar para aprender.",
        }
    res["_e_especifico"] = False
    return res
