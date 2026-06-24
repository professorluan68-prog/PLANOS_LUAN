from core.lib.classificador import normalizar_texto, contem_termos
import re

def _metodologia_biologia(texto_base: str, tema: str, tipo: str, conceito: str = "", atividade_extraida: str = "", habilidade: str = "") -> dict[str, str] | None:
    """Gerador especializado de frases para Biologia."""
    base = normalizar_texto(" ".join([tema, texto_base, atividade_extraida, habilidade]))
    conceito_seguro = conceito if normalizar_texto(conceito) not in {"biologia", "geral", ""} else tema
    atividade = atividade_extraida or "as atividades propostas no material"

    # Extração inteligente de vídeo
    video_titulo = "informativo sobre o tema"
    video_canal = "de divulgação científica"
    video_minutos = "com duração sugerida no material"
    
    # Buscar padrões no texto_base para encontrar títulos de vídeos e canais
    aspas = re.findall(r'["\'“‘]([^"\'”’\n]{3,100})["\'”’]', texto_base)
    # Order alternation from longest to shortest to prevent eager partial matching (e.g. matching 'assista' first)
    video_match = re.search(r'(?:assista ao vídeo|assista ao video|vídeo|video)\s+["\'“‘]?([^"\'”’\n]{3,100})["\'”’]?', texto_base, re.IGNORECASE)
    
    if aspas:
        video_titulo = f'"{aspas[0].strip()}"'
    elif video_match:
        video_titulo = f'"{video_match.group(1).strip()}"'

    canal_match = re.search(r'(?:canal|veiculado pelo canal|do canal|youtube)\s+[:\-]?\s*([A-ZÀ-ÿa-z0-9\s]{3,30})', texto_base, re.IGNORECASE)
    if canal_match:
        video_canal = canal_match.group(1).strip()
    else:
        if "butantan" in base:
            video_canal = "Instituto Butantan"
        elif "fiocruz" in base:
            video_canal = "Fiocruz"
        elif "nerdologia" in base:
            video_canal = "Nerdologia"
        elif "atila" in base or "iamarino" in base:
            video_canal = "Átila Iamarino"

    minutos_match = re.search(r'(?:minuto|minutos|duracao|duração|tempo|de|ate|até)\s+(\d+(?:\'\d+)?(?:\s*(?:a|à|ao|min|s|seg|-\d+))*)', texto_base, re.IGNORECASE)
    if minutos_match:
        video_minutos = minutos_match.group(1).strip()
        if not ("minuto" in video_minutos or "tempo" in video_minutos or "duracao" in video_minutos):
            video_minutos = f"do início ao minuto {video_minutos}"
    else:
        video_minutos = "com duração sugerida no material"

    # Extração de perguntas do texto
    perguntas = [p.strip() for p in re.findall(r'([^?\n.]{10,120}\?)', texto_base)]
    perguntas = [re.sub(r'^[^\w\s]+', '', p).strip() for p in perguntas]
    perguntas = [p for p in perguntas if not re.match(r'^[a-eA-E0-9]\)', p)]

    pergunta_slide = perguntas[0] if len(perguntas) > 0 else f"Como o conhecimento sobre {tema} se aplica no dia a dia?"
    pergunta_sintese_1 = perguntas[-2] if len(perguntas) > 1 else f"Quais são os conceitos principais de {tema} estudados na aula?"
    pergunta_sintese_2 = perguntas[-1] if len(perguntas) > 0 else f"Como as implicações bioéticas e sociais se relacionam com {tema}?"
    if len(perguntas) == 1:
        pergunta_sintese_1 = perguntas[0]
        pergunta_sintese_2 = f"Qual é a importância biológica e social de {tema}?"

    # Extração de palavras-chave
    palavras_chave_match = re.search(r'(?:palavras-chave|palavras chave|termos-chave)[:\-]?\s*([^\n\.]+)', texto_base, re.IGNORECASE)
    if palavras_chave_match:
        palavras_chave_str = palavras_chave_match.group(1).strip()
    else:
        palavras_sugeridas = [w.strip() for w in re.split(r'[,;\s]+', conceito_seguro) if len(w.strip()) > 3]
        if len(palavras_sugeridas) < 2:
            palavras_sugeridas.append(tema)
        palavras_chave_str = ", ".join(palavras_sugeridas[:4])

    # Detecção de ferramenta genética
    ferramenta_genetica = "quadro de Punnett"
    if "heredograma" in base:
        ferramenta_genetica = "heredograma"

    contexto = "uma imagem, noticia, dado ou situacao concreta apresentada no material"
    if any(k in base for k in ["reportagem", "noticia", "amazonia", "inpe", "ods", "matriz energetica", "saude publica", "desmatamento"]):
        contexto = "um dado real, noticia ou problema socioambiental apresentado no material"
    elif any(k in base for k in ["grafico", "infografico", "esquema", "de olho no modelo"]):
        contexto = "o modelo visual cientifico apresentado no material"

    # 1. etico_biotecnologico
    if tipo == "etico_biotecnologico":
        return {
            "para_comecar": (
                f"Iniciar a aula com a exibição do vídeo {video_titulo}, do canal {video_canal} ({video_minutos}), "
                f"propondo a questão: '{pergunta_slide}'. Solicitar que os estudantes registrem suas percepções iniciais e "
                f"abrir para breve discussão coletiva, coletando os conhecimentos prévios da turma sobre o tema."
            ),
            "foco_1": (
                f"Apresentar, de forma dialogada, as informações científicas básicas e o desenvolvimento histórico associados a "
                f"{conceito_seguro}, explicando o mecanismo biológico de forma progressiva e contextualizada."
            ),
            "foco_2": (
                f"Discutir as implicações éticas, legais ou sociais envolvidas, abordando aspectos de bioética, autonomia e consentimento "
                f"associados a {conceito_seguro}, conectando com a atuação de comitês de ética e a dignidade humana."
            ),
            "pause": (
                f"Propor questão de verificação formativa sobre os conceitos éticos ou biológicos discutidos. "
                f"Aguardar as respostas antes de revelar o gabarito e explicar o raciocínio correto."
            ),
            "pratica": (
                f"Organizar os estudantes em duplas para análise do estudo de caso ou texto sobre {tema}. Orientar a leitura e "
                f"a resolução da atividade: {atividade}. Corrigir coletivamente destacando as palavras-chave: {palavras_chave_str}."
            ),
            "encerramento": (
                f"Encerrar com as perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Solicitar que diferentes estudantes respondam, sistematizando as respostas com as palavras-chave centrais: {palavras_chave_str}."
            ),
        }

    # 2. molecular_genetico
    if tipo == "molecular_genetico":
        return {
            "relembre": (
                f"Retomar com os estudantes os conceitos básicos necessários estudados na aula anterior sobre {tema}, "
                f"utilizando esquema ou tabela comparativa como apoio visual para verificar dúvidas antes de avançar."
            ),
            "foco_1": (
                f"Explicar {conceito_seguro} na escala celular e molecular, descrevendo as etapas do processo biológico. "
                f"Utilizar animação ou imagem detalhada do material para ilustrar as estruturas envolvidas."
            ),
            "foco_2": (
                f"Conectar o processo molecular estudado ao seu funcionamento prático no organismo e às suas manifestações fenotípicas, "
                f"explicando a relação de causa e consequência biológica de forma progressiva."
            ),
            "pause": (
                f"Propor questão de múltipla escolha para verificação formativa sobre a estrutura molecular ou cruzamento genético discutido. "
                f"Aguardar as respostas antes de revelar o gabarito e explicar o raciocínio correto."
            ),
            "pratica": (
                f"Orientar a resolução del problema genético ou atividade molecular em duplas, auxiliando na construção do {ferramenta_genetica}. "
                f"Atividade central: {atividade}. Estimular que os estudantes apresentem suas soluções na lousa."
            ),
            "encerramento": (
                f"Finalizar respondendo às perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Sistematizar os resultados na lousa, confirmando os genótipos, fenótipos e proporções esperadas."
            ),
        }

    # 3. debate_critico
    if tipo == "debate_critico":
        return {
            "para_comecar": (
                f"Iniciar a aula com uma imagem provocadora ou trecho de notícia do material sobre {tema}, propondo a questão disparadora: "
                f"'{pergunta_slide}'. Estimular a expressão livre de opiniões e hipóteses iniciais dos estudantes antes do conceito formal."
            ),
            "foco_1": (
                f"Explicar {conceito_seguro} a partir de uma contextualização histórica e social detalhada, demonstrando como teorias pseudocientíficas "
                f"(como eugenia, determinismo biológico ou darwinismo social) foram construídas e desmistificadas pela ciência moderna."
            ),
            "foco_2": (
                f"Aprofundar a base científica sobre a variabilidade genética humana, demonstrando a inexistência de raças biológicas sob a perspectiva "
                f"da genética moderna. Sistematizar os conceitos de ancestralidade e diversidade genética."
            ),
            "pause": (
                f"Propor um Pause e responda com tempo breve para que os estudantes se posicionem individualmente com argumentos científicos antes da correção dialogada."
            ),
            "pratica": (
                f"Organizar grupos para debater as evidências científicas contra preconceitos históricos ou analisar criticamente o texto proposto. "
                f"Orientar a elaboração de um plano de ação ou síntese coletiva sobre a diversidade genética. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Finalizar coletando as sínteses dos grupos e respondendo às perguntas de reflexão: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Sistematizar com as palavras-chave de direitos e ciência: {palavras_chave_str}."
            ),
        }

    # 4. aplicacao_biotecnologica
    if tipo == "aplicacao_biotecnologica":
        return {
            "para_comecar": (
                f"Iniciar a aula com a apresentação de um caso clínico real ou notícia recente sobre {tema}, propondo a questão disparadora: '{pergunta_slide}'. "
                f"Permitir que os estudantes compartilhem suas opiniões e vivências cotidianas com a tecnologia em foco."
            ),
            "foco_1": (
                f"Explicar o conceito de {conceito_seguro} e descrever as etapas do processo biotecnológico envolvido (como produção de vacinas, soros, clonagem ou terapia gênica). "
                f"Exibir o vídeo informativo {video_titulo} do canal {video_canal} ({video_minutos}) para ilustrar a produção real."
            ),
            "foco_2": (
                f"Destacar o papel de instituições públicas de pesquisa do Brasil (como Instituto Butantan, Fiocruz e universidades públicas) na soberania científica e "
                f"saúde coletiva. Discutir aspectos de propriedade intelectual (patentes) e equidade de acesso (SUS)."
            ),
            "pause": (
                f"Propor questão de verificação formativa sobre as etapas de produção ou mecanismos de ação biológicos discutidos. Corrigir revelando o gabarito e detalhando a resposta."
            ),
            "pratica": (
                f"Orientar os estudantes a analisarem em duplas o estudo de caso ou atividade clínica aplicada no material. Propor o preenchimento dos esquemas ou lacunas "
                f"para fixar o vocabulário científico e a lógica do processo. Realizar correção coletiva destacando as palavras-chave: {palavras_chave_str}."
            ),
            "encerramento": (
                f"Encerrar respondendo às perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}'. "
                f"Destacar como o conhecimento biotecnológico se traduz em bem-estar social e imunidade coletiva."
            ),
        }

    # 5. revisao_aprofundamento
    if tipo == "revisao_aprofundamento":
        return {
            "relembre": (
                f"Retomar os conceitos fundamentais de aulas anteriores sobre {tema} por meio de uma tabela comparativa ou imagem de síntese na lousa. "
                f"Conduzir uma breve arguição diagnóstica para verificar o que foi consolidado."
            ),
            "foco_1": (
                f"Aprofundar os aspectos mais complexos de {conceito_seguro}, utilizando novos exemplos ou contextos que integrem os conhecimentos moleculares e celulares revisados."
            ),
            "pause": (
                f"Realizar um Pause e responda com questões de vestibular ou do material para checagem rápida de consolidação dos tópicos. Discutir a resolução coletivamente."
            ),
            "pratica": (
                f"Propor a resolução em duplas de uma situação-problema mais complexa que integre múltiplos conceitos revisados ou questões de exames (ENEM/vestibulares). "
                f"Conduzir a correção passo a passo na lousa, validando os raciocínios dos estudantes. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Finalizar com perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}', esclarecendo dúvidas remanescentes antes do encerramento."
            ),
        }

    # Fallbacks para compatibilidade com tipos antigos
    if tipo == "aula_desafio":
        return {
            "desafio": (
                f"Apresentar o caso real relacionado a {tema}, destacando os dados mais impactantes e convidando a turma a levantar hipoteses iniciais sem corrigi-las neste momento."
            ),
            "entendendo_problema": (
                f"Conduzir a analise das evidencias em etapas, revelando gradualmente as informacoes do caso e explicando {conceito_seguro} com apoio do raciocinio cientifico, sempre um passo de cada vez."
            ),
            "solucao_acao": (
                f"Organizar duplas ou grupos para elaborar hipoteses, comparar explicacoes e propor respostas fundamentadas para o caso, usando como base {atividade}."
            ),
            "hora_verdade": (
                "Retomar as hipoteses construidas pelos grupos, apresentar as respostas esperadas e discutir por que algumas explicacoes se aproximam mais das evidencias do que outras."
            ),
            "encerramento": (
                f"Encerrar com Com suas palavras, pedindo que os estudantes expliquem o que o caso ajudou a compreender sobre {tema} e quais medidas ou conclusoes cientificas podem ser defendidas."
            ),
        }

    if tipo == "aula_pratica":
        return {
            "relembre": (
                f"Retomar com a turma os conceitos necessarios para observar o fenomeno relacionado a {tema}, recuperando equacoes, etapas ou ideias-chave antes da pratica."
            ),
            "pratica": (
                f"Apresentar os materiais e orientar a montagem da atividade experimental em etapas curtas, pedindo que os estudantes observem, registrem e relacionem o que ocorre com {conceito_seguro}. Atividade central: {atividade}."
            ),
            "discussao_resultados": (
                "Conduzir a discussao dos resultados com Todo mundo escreve, comparando observacoes, confirmando ou revendo hipoteses e explicitando as evidencias mais importantes."
            ),
            "encerramento": (
                f"Finalizar solicitando que os estudantes expliquem, com suas palavras, o que foi observado e como a pratica ajudou a compreender {tema}."
            ),
        }

    if tipo == "revisao_consolidacao":
        return {
            "relembre": (
                f"Retomar termos e conceitos ja estudados sobre {tema}, pedindo que a turma explique com suas palavras o que lembra antes da correcao formal."
            ),
            "foco": (
                f"Conduzir a revisao por meio de quiz, comparacoes e retomada dos conceitos centrais de {conceito_seguro}, esclarecendo diferencas, relacoes e exemplos."
            ),
            "pratica": (
                f"Orientar leitura, classificacao ou resolucao das questoes de consolidacao, solicitando que os estudantes voltem ao material para localizar evidencias e justificar respostas. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar com perguntas comparativas e Com suas palavras, consolidando o que foi retomado sobre {tema} e identificando duvidas que ainda precisam de reforco."
            ),
        }

    if tipo == "impacto_socioambiental":
        return {
            "para_comecar": (
                f"Iniciar a aula apresentando {contexto} sobre {tema}, propondo uma pergunta disparadora que ajude a turma a relacionar fenomenos biologicos, sociedade e ambiente."
            ),
            "foco": (
                f"Explicar {conceito_seguro} de forma progressiva, relacionando o conteudo a impactos ambientais, saude publica, sustentabilidade ou responsabilidade coletiva, sempre um passo de cada vez."
            ),
            "de_olho_modelo": (
                "Apresentar o grafico, infografico, mapa ou esquema do material e orientar a leitura, pedindo que os estudantes identifiquem dados-chave, comparacoes e implicacoes do modelo visual."
            ),
            "pratica": (
                f"Propor atividade de analise de caso, texto ou dados, solicitando registro individual com base em evidencias e conexoes entre ciência, ambiente e vida cotidiana. Atividade central: {atividade}."
            ),
            "encerramento": (
                f"Encerrar retomando a conexao entre {tema} e suas implicacoes sociais, ambientais ou de saude, com perguntas de sintese em Com suas palavras."
            ),
        }

    # Fallback Geral (Conceito Novo)
    return {
        "para_comecar": (
            f"Iniciar a aula com {contexto} relacionado a {tema}, propondo a questão disparadora: '{pergunta_slide}'. "
            f"Convidar os estudantes a levantar hipóteses e ativar conhecimentos prévios."
        ),
        "foco": (
            f"Explicar {conceito_seguro} em etapas sequenciais, destacando processos, relações de causa e consequência "
            f"e exemplos biológicos reais de forma dialógica e progressiva."
        ),
        "pause": (
            "Propor um Pause e responda antes da atividade prática, com tempo breve para resposta individual e correção dialogada "
            "baseada no conceito central."
        ),
        "pratica": (
            f"Orientar a aplicação do conceito em leitura, classificação, interpretação de modelo ou atividade investigativa em duplas. "
            f"Atividade central: {atividade}."
        ),
        "encerramento": (
            f"Finalizar com as perguntas de síntese: '{pergunta_sintese_1}' e '{pergunta_sintese_2}', "
            f"sistematizando o aprendizado com as palavras-chave: {palavras_chave_str}."
        ),
    }

