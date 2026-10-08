import docx

doc_path = r"C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS\HISTÓRIACDP\EF\3_BIMESTRE\8_9_ANO_MULTISSERIADO\METODOLOGIA_HISTORIACDP_8_9_ANO_3_B.docx"
doc = docx.Document(doc_path)

replacements = {
    # Aula 7
    "Apresentar o contexto dos anos 1960 marcado por grandes transformações culturais e políticas: a contracultura e o pacifismo contra as guerras, a luta pelos direitos civis e contra a segregação racial nos Estados Unidos liderada por Martin Luther King Jr., e as manifestações culturais e musicais no Brasil (Tropicália e festivais da canção) como formas de contestação e afirmação da liberdade. Utilizar trechos impressos do discurso \"Eu tenho um sonho\" para leitura compartilhada.": "Apresentar o contexto dos anos 1960 (contracultura e pacifismo) e a luta contra a segregação racial nos EUA liderada por Martin Luther King Jr. Abordar as manifestações culturais no Brasil (Tropicália) como forma de contestação e liberdade. Utilizar trechos do discurso 'Eu tenho um sonho' para leitura compartilhada.",
    "Atividade 1. Com leitura mediada de pequenos trechos impressos do discurso de Martin Luther King Jr., os estudantes identificam as principais ideias de igualdade, fraternidade e não violência. Em seguida, respondem no caderno ou folha avulsa a duas questões objetivas sobre a importância do combate ao preconceito racial e a defesa dos direitos fundamentais. A correção é feita coletivamente na lousa.": "Atividade 1: Com leitura mediada de trechos do discurso de Martin Luther King Jr., os estudantes identificam ideias de igualdade e não violência. Depois, respondem a duas questões sobre a importância do combate ao preconceito e defesa dos direitos fundamentais. A correção é coletiva na lousa.",
    
    # Aula 8
    "Abrir a aula desenhando na lousa o símbolo de uma vassoura e propondo as perguntas: \"O que significa prometer 'varrer a corrupção' em uma eleição?\" e \"Proibições morais resolvem os problemas reais do trabalhador, como salário baixo e preço alto dos alimentos?\". Estimular reflexões sobre discursos políticos e as reais necessidades da população.": "Abrir a aula desenhando uma vassoura na lousa e perguntando: 'O que significa prometer varrer a corrupção na eleição?' e 'Proibições morais resolvem os problemas reais do trabalhador, como salário baixo?'. Estimular reflexões sobre discursos políticos e as reais necessidades da população.",
    "Explicar o governo de Jânio Quadros (1961), suas medidas polêmicas, a crise política e sua renúncia inesperada. Abordar a crise de sucessão e a posse de João Goulart (Jango), passando pela fase do parlamentarismo até o plebiscito que devolveu plenos poderes ao presidente. Explorar as Reformas de Base de Jango: Reforma Agrária (acesso à terra), Educacional (combate ao analfabetismo) e Tributária (justiça nos impostos), e a forte reação de oposição dos setores conservadores e empresariais.": "Explicar o governo Jânio Quadros (1961), a crise e sua renúncia. Abordar a posse de João Goulart, o parlamentarismo e o plebiscito. Explorar as Reformas de Base de Jango: Agrária (acesso à terra), Educacional (combate ao analfabetismo) e Tributária (justiça nos impostos), além da forte oposição dos setores conservadores.",
    "Atividade 1. Em folha impressa ou no caderno, os estudantes realizam uma atividade de correspondência ligando cada Reforma de Base ao seu objetivo (Agrária  distribuição de terras improdutivas; Educacional  alfabetização e escolas públicas; Tributária  cobrança justa de impostos). Em seguida, respondem a uma questão sobre por que os grandes proprietários de terras e empresários se opuseram a essas reformas. Correção comentada na lousa.": "Atividade 1: Os estudantes realizam atividade de correspondência ligando cada Reforma de Base (Agrária, Educacional, Tributária) ao seu objetivo. Em seguida, respondem no caderno por que grandes proprietários de terras e empresários se opuseram a essas reformas. Correção comentada na lousa.",
    
    # Aula 9
    "Explicar o golpe civil-militar de 1964: a deposição inconstitucional de João Goulart pelas Forças Armadas com o apoio de setores empresariais, parte da imprensa e políticos conservadores, sob o pretexto de combate ao comunismo. Apresentar o conceito de Atos Institucionais, destacando o AI-1 (1964): cassação de mandatos políticos, suspensão de direitos políticos de opositores, fechamento de organizações sociais e estabelecimento de eleições indiretas para presidente.": "Explicar o golpe civil-militar de 1964: deposição de João Goulart com apoio de setores empresariais e conservadores, sob pretexto de combater o comunismo. Apresentar os Atos Institucionais, destacando o AI-1 (1964): cassação de mandatos políticos, suspensão de direitos de opositores, fechamento de organizações e eleições indiretas.",
    "Atividade 1. Leitura mediada de dois trechos curtos de jornais de 1964 impressos em folha avulsa. Em seguida, os estudantes respondem a duas questões objetivas: (1) O que foi o AI-1 e como ele afetou o direito do povo de votar? (2) Por que esse acontecimento é classificado pela história como um golpe civil-militar? Correção coletiva na lousa.": "Atividade 1: Leitura mediada de trechos curtos de jornais de 1964. Em seguida, os estudantes respondem a duas questões objetivas: (1) O que foi o AI-1 e como afetou o direito de votar? (2) Por que este acontecimento é classificado como golpe civil-militar? Correção coletiva na lousa.",
    
    # Aula 10
    "Analisar o período conhecido como \"Milagre Econômico\" (1968-1973): forte crescimento industrial e grandes obras públicas, acompanhado de arrocho salarial (salários sem reajuste real), endividamento externo e aumento da desigualdade social. Explicar o uso da propaganda ufanista (\"Brasil, ame-o ou deixe-o\" e o uso político do tricampeonato de futebol de 1970) para encobrir a miséria e a repressão. Apresentar a resistência cultural através da música popular e dos festivais da canção.": "Analisar o 'Milagre Econômico' (1968-1973): forte crescimento e grandes obras, com arrocho salarial, endividamento e desigualdade social. Explicar a propaganda ufanista ('Brasil, ame-o ou deixe-o') e o uso político do futebol para encobrir a miséria. Apresentar a resistência cultural pela música e festivais da canção.",
    "Atividade 1. Leitura coletiva da letra impressa da música \"Disparada\" (Geraldo Vandré e Jair Rodrigues). Os estudantes analisam os versos sobre a recusa em ser tratado como boiada e respondem: (1) O que significa a afirmação poética de não se deixar guiar como gado? (2) O crescimento econômico da época melhorou a vida de toda a população ou concentrou a renda? Correção na lousa.": "Atividade 1: Leitura coletiva da música 'Disparada'. Os estudantes analisam versos sobre recusar ser tratado como boiada e respondem: (1) O que significa não se deixar guiar como gado? (2) O crescimento econômico melhorou a vida de todos ou concentrou renda? Correção na lousa.",
    
    # Aula 11
    "Apresentar o aparato repressivo do regime militar: a criação de órgãos de espionagem e controle (SNI, DOPS, DOI-CODI), as perseguições políticas, prisões arbitrárias e interrogatórios contra opositores. Explicar o Ato Institucional nº 5 (AI-5, 1968): fechamento do Congresso Nacional, censura prévia total a jornais, livros e músicas, e suspensão do direito de Habeas Corpus (possibilidade de prisão de qualquer cidadão sem acusação formal).": "Apresentar o aparato repressivo militar (SNI, DOPS, DOI-CODI), perseguições e prisões arbitrárias. Explicar o AI-5 (1968): fechamento do Congresso Nacional, censura prévia total a jornais, livros e músicas, e suspensão do Habeas Corpus (prisão sem acusação formal).",
    "Atividade 1. Leitura compartilhada de trechos da letra da música \"Cálice\" (Chico Buarque e Gilberto Gil), explicando o trocadilho poético entre a palavra \"cálice\" e a ordem de silenciamento \"cale-se\". Em seguida, os estudantes respondem a duas questões sobre o papel da censura e o impacto da suspensão do Habeas Corpus na segurança jurídica dos cidadãos. Correção comentada.": "Atividade 1: Leitura compartilhada da música 'Cálice' (Chico Buarque e Gilberto Gil), explicando o trocadilho poético com 'cale-se'. Os estudantes respondem a duas questões sobre censura e o impacto da suspensão do Habeas Corpus na segurança dos cidadãos. Correção comentada.",
    
    # Aula 12
    "Apresentar as diversas frentes de resistência da sociedade civil contra a ditadura: as manifestações estudantis e populares (como a Passeata dos Cem Mil em 1968 após a morte do estudante Edson Luís), as organizações de luta armada que enfrentaram o regime, e o papel decisivo do movimento operário com as grandes greves do ABC Paulista (1978-1980), que paralisaram as fábricas exigindo reposição salarial e liberdade sindical.": "Apresentar as frentes de resistência à ditadura: manifestações estudantis e populares (Passeata dos Cem Mil em 1968), as organizações de luta armada e o papel do movimento operário com as greves do ABC Paulista (1978-1980), que paralisaram fábricas exigindo reposição salarial."
}

def normalize(text):
    return " ".join(text.split())

replacements_norm = {normalize(k): v for k, v in replacements.items()}

count = 0
for p in doc.paragraphs:
    if "Para começar:" in p.text or "Foco no conteúdo:" in p.text or "Na prática:" in p.text or "Encerramento:" in p.text:
        parts = p.text.split(":", 1)
        if len(parts) == 2:
            prefix, content = parts[0], parts[1].strip()
            norm_content = normalize(content)
            for orig_key, new_val in replacements_norm.items():
                if orig_key == norm_content or orig_key in norm_content:
                    p.text = ""
                    run = p.add_run(prefix + ": ")
                    run.bold = True
                    p.add_run(new_val)
                    count += 1
                    break

print(f"Modificados {count} parágrafos.")
doc.save(doc_path)
