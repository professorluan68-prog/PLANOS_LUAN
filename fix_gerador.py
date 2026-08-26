import os
import re

filepath = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\core\lib\gerador_colunas_pedagogicas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Vamos limpar os blocos injetados e refazer mais robusto
content = re.sub(r'# INJECAO DE MELHORIAS: MATEMATICA, HISTORIA, GEOGRAFIA E CIENCIAS.*?return "Para começar:[^\n]*"\n', '', content, flags=re.DOTALL)
content = re.sub(r'# INJECAO DE MELHORIAS: FOCO NO CONTEUDO.*?return "Foco no conteúdo:[^\n]*"\n', '', content, flags=re.DOTALL)
content = re.sub(r'# INJECAO DE MELHORIAS: PRATICA.*?return "Na prática:[^\n]*"\n', '', content, flags=re.DOTALL)
content = re.sub(r'# INJECAO DE MELHORIAS: PAUSE E RESPONDA.*?return "Realizar checagem de entendimento[^\n]*"\n', '', content, flags=re.DOTALL)
content = re.sub(r'# INJECAO DE MELHORIAS: ENCERRAMENTO.*?return "Sistematizar os conceitos científicos[^\n]*"\n', '', content, flags=re.DOTALL)

# Refazendo
bloco_inicial = '''
    # INJECAO REFEITA
    if p.perfil in ["resolucao_problemas", "modelagem", "grafico", "khan"] or p.tem_calculo:
        return "Para começar: Explorar conhecimentos prévios conectando o conceito matemático com experiências cotidianas através de perguntas reflexivas ou desafios simples."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Para começar: Apresentar o tema central conectando-o com o contexto histórico/geográfico atual, ativando conhecimentos prévios e incentivando hipóteses."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"] or (p.perfil == "conceito_novo" and not p.tem_calculo):
        return "Para começar: Introduzir a temática com uma situação-problema ou imagem do material, mobilizando a curiosidade investigativa dos estudantes."
'''

bloco_foco = '''
    # INJECAO REFEITA FOCO
    if p.perfil in ["resolucao_problemas", "modelagem", "grafico", "khan"] or p.tem_calculo:
        return "Foco no conteúdo: Apresentar os conceitos centrais utilizando a técnica 'Um passo de cada vez', fragmentando a explicação e demonstrando resoluções com exemplos práticos."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Foco no conteúdo: Conduzir a leitura guiada do material destacando fatos, causas e consequências com a técnica 'Um passo de cada vez' para facilitar a construção do pensamento crítico."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"] or (p.perfil == "conceito_novo" and not p.tem_calculo):
        return "Foco no conteúdo: Explicar os fenômenos e conceitos, fragmentando a informação em partes menores ('Um passo de cada vez') e relacionando à prática abordada."
'''

bloco_pratica = '''
    # INJECAO REFEITA PRATICA
    if p.perfil in ["resolucao_problemas", "modelagem", "grafico", "khan"] or p.tem_calculo:
        return "Na prática: Orientar a resolução dos exercícios do material. Promover discussão em duplas utilizando a técnica 'Virem e conversem' para comparar métodos de cálculo."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Na prática: Propor análise de fontes ou estudo de caso. Utilizar a técnica 'Virem e conversem' para que os estudantes confrontem diferentes pontos de vista antes do registro no caderno."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"] or (p.perfil == "conceito_novo" and not p.tem_calculo):
        return "Na prática: Orientar a atividade investigativa ou resolução de questões. Aplicar a técnica 'Todo mundo escreve' para garantir o registro individual e a sistematização da descoberta."
'''

bloco_pause = '''
    # INJECAO REFEITA PAUSE
    if p.perfil in ["resolucao_problemas", "modelagem", "grafico", "khan"] or p.tem_calculo:
        return "Realizar correção coletiva e mediada, promovendo debate sobre diferentes estratégias de resolução e verificando onde houve maiores dificuldades."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Pausar para correção e socialização das interpretações, garantindo que os conceitos históricos e geográficos foram assimilados corretamente."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"] or (p.perfil == "conceito_novo" and not p.tem_calculo):
        return "Realizar checagem de entendimento, garantindo que as hipóteses científicas ou gerais levantadas pelos estudantes sejam discutidas e fundamentadas coletivamente."
'''

bloco_encerramento = '''
    # INJECAO REFEITA ENCERRAMENTO
    if p.perfil in ["resolucao_problemas", "modelagem", "grafico", "khan"] or p.tem_calculo:
        return "Sintetizar as aprendizagens da aula e promover reflexão final pedindo que os estudantes expliquem a lógica do cálculo 'Com suas palavras'."
    if p.perfil in ["leitura", "debate_critico", "fonte_historica", "analise_geografica"]:
        return "Encerrar a aula com síntese dos pontos principais, incentivando os estudantes a explicarem as conclusões do dia 'Com suas palavras'."
    if p.perfil in ["estudo_caso", "leitura_analise", "impacto_socioambiental", "investigativa", "analise_dados"] or (p.perfil == "conceito_novo" and not p.tem_calculo):
        return "Sistematizar os conceitos abordados na aula, finalizando com a técnica 'Com suas palavras' para reelaboração autônoma do conhecimento."
'''

content = re.sub(r'(def frase_inicial\(p: PistasPedagogicas\) -> str:\n    opcoes = \[\])', r'\1' + bloco_inicial, content)
content = re.sub(r'(def frase_foco\(p: PistasPedagogicas\) -> str:\n    frase = "")', r'\1' + bloco_foco, content)
content = re.sub(r'(def frase_pratica\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_pratica, content)
content = re.sub(r'(def frase_pause\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_pause, content)
content = re.sub(r'(def frase_encerramento\(p: PistasPedagogicas\) -> str:)', r'\1' + bloco_encerramento, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Gerador Refatorado com Sucesso!")
