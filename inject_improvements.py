import os
import re

filepath = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\core\lib\gerador_colunas_pedagogicas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# BLOCO INICIAL
bloco_inicial = '''
    # INJECAO DE MELHORIAS: MATEMATICA, HISTORIA, GEOGRAFIA E CIENCIAS
    if p.perfil in ["conceito_novo", "resolucao_problemas", "modelagem", "grafico"] and "matematica" in p.titulo.lower():
        return "Para começar: Explorar conhecimentos prévios conectando o conceito matemático com experiências cotidianas através de perguntas reflexivas ou desafios simples."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Para começar: Apresentar o tema central conectando-o com o contexto histórico/geográfico atual, ativando conhecimentos prévios e incentivando hipóteses."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"]:
        return "Para começar: Introduzir a temática científica com uma situação-problema ou imagem do material, mobilizando a curiosidade investigativa dos estudantes."
'''

# BLOCO FOCO
bloco_foco = '''
    # INJECAO DE MELHORIAS: FOCO NO CONTEUDO
    if p.perfil in ["conceito_novo", "resolucao_problemas", "modelagem", "grafico"] and "matematica" in p.titulo.lower():
        return "Foco no conteúdo: Apresentar os conceitos centrais utilizando a técnica 'Um passo de cada vez', fragmentando a explicação e demonstrando resoluções com exemplos práticos."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Foco no conteúdo: Conduzir a leitura guiada do material destacando fatos, causas e consequências com a técnica 'Um passo de cada vez' para facilitar a construção do pensamento crítico."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"]:
        return "Foco no conteúdo: Explicar os fenômenos e processos científicos, fragmentando a informação em partes menores ('Um passo de cada vez') e relacionando ao experimento ou caso estudado."
'''

# BLOCO PRATICA
bloco_pratica = '''
    # INJECAO DE MELHORIAS: PRATICA
    if p.perfil in ["conceito_novo", "resolucao_problemas", "modelagem", "grafico"] and "matematica" in p.titulo.lower():
        return "Na prática: Orientar a resolução dos exercícios do material. Promover discussão em duplas utilizando a técnica 'Virem e conversem' para comparar métodos de cálculo."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Na prática: Propor análise de fontes ou estudo de caso. Utilizar a técnica 'Virem e conversem' para que os estudantes confrontem diferentes pontos de vista antes do registro no caderno."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"]:
        return "Na prática: Orientar a atividade investigativa ou resolução de questões. Aplicar a técnica 'Todo mundo escreve' para garantir o registro individual e a sistematização da descoberta."
'''

# BLOCO PAUSE
bloco_pause = '''
    # INJECAO DE MELHORIAS: PAUSE E RESPONDA
    if p.perfil in ["conceito_novo", "resolucao_problemas", "modelagem", "grafico"] and "matematica" in p.titulo.lower():
        return "Realizar correção coletiva e mediada, promovendo debate sobre diferentes estratégias de resolução e verificando onde houve maiores dificuldades."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Pausar para correção e socialização das interpretações, garantindo que os conceitos históricos e geográficos foram assimilados corretamente."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"]:
        return "Realizar checagem de entendimento, garantindo que as hipóteses científicas levantadas pelos estudantes sejam discutidas e fundamentadas coletivamente."
'''

# BLOCO ENCERRAMENTO
bloco_encerramento = '''
    # INJECAO DE MELHORIAS: ENCERRAMENTO
    if p.perfil in ["conceito_novo", "resolucao_problemas", "modelagem", "grafico"] and "matematica" in p.titulo.lower():
        return "Sintetizar as aprendizagens da aula e promover reflexão final pedindo que os estudantes expliquem a lógica do cálculo 'Com suas palavras'."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Encerrar a aula com síntese dos pontos principais, incentivando os estudantes a explicarem as conclusões do dia 'Com suas palavras'."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"]:
        return "Sistematizar os conceitos científicos abordados na aula, finalizando com a técnica 'Com suas palavras' para reelaboração autônoma do conhecimento."
'''

content = re.sub(r'(def frase_inicial\(p: PistasPedagogicas\) -> str:\n    opcoes = \[\])', r'\1' + bloco_inicial, content)
content = re.sub(r'(def frase_foco\(p: PistasPedagogicas\) -> str:\n    frase = "")', r'\1' + bloco_foco, content)
content = re.sub(r'(def frase_pratica\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_pratica, content)
content = re.sub(r'(def frase_pause\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_pause, content)
content = re.sub(r'(def frase_encerramento\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_encerramento, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Gerador Atualizado com Sucesso!")
