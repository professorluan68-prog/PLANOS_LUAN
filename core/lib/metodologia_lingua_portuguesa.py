from core.lib.classificador import normalizar_texto 
def _metodologia_lingua_portuguesa( 
    texto_base: str, 
    tema: str, 
    tipo: str, 
    perfil_metodologico: str = None, 
    tipo_aula: str = 'simples' 
) -> dict[str, str] | None: 
    inicio = f'Explorar conhecimentos previos sobre {tema} conectando o conteudo com experiencias e situacoes cotidianas dos estudantes atraves de perguntas reflexivas ou leitura de imagens.' 
    foco = f'Apresentar os conceitos centrais de {tema} utilizando a tecnica Um passo de cada vez, fragmentando as informacoes e demonstrando os conceitos com exemplos praticos extraidos do material.' 
    pratica = f'Orientar a resolucao das atividades sobre {tema}. Promover discussao estruturada em duplas com a tecnica Virem e conversem para analise de elementos textuais, e orientar o registro no caderno.' 
    hora_leitura = f'Conduzir leitura guiada e compartilhada do texto modelo sobre {tema}, observando marcas linguisticas, estrutura e intencionalidades.' 
    pause = f'Realizar correcao coletiva e mediada das questoes sobre {tema}, promovendo debate para verificacao imediata da aprendizagem e troca de justificativas.' 
    encerramento = f'Sintetizar as aprendizagens da aula sobre {tema} e promover reflexao final pedindo que os estudantes expliquem os conceitos Com suas palavras.' 
    if tipo == 'literatura': 
        inicio = f'Apresentar imagens, contexto historico ou perguntas sobre {tema} para aquecimento e ativacao de conhecimentos previos.' 
        foco = f'Apresentar a estetica, autores e marcas literarias de {tema}, utilizando a tecnica Um passo de cada vez para relacionar o texto ao contexto social.' 
    elif tipo == 'genero_textual': 
        foco = f'Apresentar a definicao, suporte, publico-alvo e marcas linguisticas do genero {tema} com a tecnica Um passo de cada vez.' 
        pratica = f'Propor exercicios de interpretacao do genero {tema}. Utilizar a tecnica Virem e conversem para comparar percepcoes antes do registro estruturado.' 
    elif tipo == 'producao_textual': 
        pratica = f'Orientar as etapas de planejamento estrutural e escrita do rascunho de {tema}. Utilizar a tecnica Todo mundo escreve para garantir o registro autoral e focado.' 
    elif tipo == 'gramatica_integrada': 
        foco = f'Explicar a norma-padrao ou regra gramatical de {tema} utilizando Um passo de cada vez, conectando a regra aos efeitos de sentido no texto lido.' 
    elif tipo == 'variacao_linguistica': 
        foco = f'Sistematizar o conceito de variacao em {tema} desconstruindo preconceitos. Demonstrar, um passo de cada vez, como a adequacao linguistica depende do contexto de uso.' 
    etapas_base = { 
        'para_comecar': inicio, 
        'relembre': inicio.replace('Explorar', 'Relembrar'), 
        'hora_leitura': hora_leitura, 
        'foco': foco, 
        'pratica': pratica, 
        'todo_mundo_escreve': f'Conduzir atividade de escrita focada e autoral sobre {tema} utilizando a tecnica Todo mundo escreve.', 
        'pause': pause, 
        'socializacao': pause.replace('Realizar', 'Promover socializacao e'), 
        'encerramento': encerramento, 
        'de_olho_modelo': f'Apresentar exemplo estruturado e modelo de referencia sobre {tema} para orientar a producao dos estudantes.', 
        'revisao_colega': f'Promover troca de textos entre pares para revisao colaborativa de {tema}, buscando aprimoramento da escrita.', 
        'planejamento_oral': f'Orientar a organizacao do roteiro, topicos de fala e recursos expressivos (entonacao, clareza) para a apresentacao sobre {tema}.', 
        'planejamento_debate': f'Organizar roteiro simples de argumentos e contra-argumentos sobre {tema} para estruturar o posicionamento dos estudantes.' 
    } 
    return etapas_base 
