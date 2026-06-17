from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import _etapas_por_perfil, MotorMetodologico

def test_historia_perfil():
    assert perfil_disciplina("História") == "historia"
    assert perfil_disciplina("Historia") == "historia"

def test_historia_detectar_tipo_aula():
    # 1. Fonte Histórica
    assert detectar_tipo_aula(
        "Orientar a leitura de uma carta escrita por um camponês medieval analisando o contexto de produção e autoria.",
        "A vida na Idade Média",
        "História"
    ) == "fonte_historica"
    
    # 2. Debate Crítico
    assert detectar_tipo_aula(
        "Dividir a sala para debater as diferentes narrativas sobre os impactos da Revolução Industrial.",
        "Guerra do Paraguai: conflito de narrativas",
        "História"
    ) == "debate_critico"

    # 3. Análise Geográfica
    assert detectar_tipo_aula(
        "Foco no conteúdo analisando as rotas comerciais no mar Mediterrâneo antigo e sua expansão territorial.",
        "Rotas comerciais na África",
        "História"
    ) == "analise_geografica"

    # 4. Produção Projeto
    assert detectar_tipo_aula(
        "Elaborar em grupos um mapa mental sobre as corporações de ofício.",
        "A economia na Baixa Idade Média",
        "História"
    ) == "producao_projeto"

def test_historia_etapas_config():
    etapas = _etapas_por_perfil("historia", "fonte_historica")
    chaves = [chave for _, chave in etapas]
    assert chaves == ["para_comecar", "foco", "pause", "pratica", "encerramento"]

def test_historia_geracao_metodologia():
    generator = MotorMetodologico()
    texto_pdf = (
        "Texto da aula que orienta a análise de uma fonte histórica (carta de lei da Lei Áurea). "
        "Pedir que os estudantes leiam e respondam o que a lei determinou."
    )
    resultado = generator.gerar(
        texto_pdf=texto_pdf,
        disciplina="História",
        turma="8º ANO",
        tema="A Lei Áurea",
        indice_aula=0,
        total_aulas=1
    )
    
    assert len(resultado) == 5
    # Check if "linha do tempo" is present in the first stage (para_comecar)
    assert "linha do tempo" in resultado[0]["texto"].lower()
    # Check if source analysis questions are in the methodology (pratica)
    assert "quem produziu" in resultado[3]["texto"].lower()
    assert "ponto de vista" in resultado[3]["texto"].lower()
    # Check if past-present connection is in the closing stage (encerramento)
    assert "permanências" in resultado[4]["texto"].lower() or "atualidade" in resultado[4]["texto"].lower()
