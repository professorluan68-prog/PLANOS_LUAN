from core.validador_plano import validar_aula_final
from core.qualidade_metodologica import consolidar_quatro_etapas


def test_consolidar_etapas_sempre_gera_quatro():
    metodologia_curta = [
        {"titulo": "Abertura", "texto": "Iniciar a aula conversando sobre frações."}
    ]
    revisada = consolidar_quatro_etapas(metodologia_curta, tema="frações")
    
    assert len(revisada) == 4
    titulos = [item["titulo"] for item in revisada]
    assert titulos == ["Para começar", "Foco no conteúdo", "Na prática", "Encerramento"]


def test_validador_rejeita_tema_generico():
    aula = {
        "disciplina": "Matemática",
        "tema": "tema da aula",
        "aprendizagem": "Resolver problemas envolvendo frações.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "O professor apresenta frações no caderno para a turma."},
            {"titulo": "Foco no conteúdo", "texto": "O mediador exibe os conceitos de frações e os alunos registram no caderno."},
            {"titulo": "Na prática", "texto": "Os estudantes resolvem exercícios no caderno sobre frações."},
            {"titulo": "Encerramento", "texto": "O professor orienta a turma a socializar e responder as dúvidas."}
        ],
        "acompanhamento": ["☑ Acompanhar"],
        "acessibilidade": ["☑ Apoiar"]
    }
    
    avisos = validar_aula_final(aula)
    assert any("Tema muito genérico" in aviso for aviso in avisos)


def test_validador_rejeita_metodologia_sem_relacao_ao_conteudo():
    aula = {
        "disciplina": "Matemática",
        "tema": "Frações Equivalentes",
        "aprendizagem": "Identificar e representar frações equivalentes.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "O professor apresenta uma pergunta para os estudantes em duplas."},
            {"titulo": "Foco no conteúdo", "texto": "O docente exibe o texto explicativo geral e orienta a leitura dos alunos."},
            {"titulo": "Na prática", "texto": "Os estudantes resolvem uma atividade geral no caderno em duplas."},
            {"titulo": "Encerramento", "texto": "O mediador orienta a turma a registrar a resposta final no caderno."}
        ],
        "acompanhamento": ["☑ Acompanhar"],
        "acessibilidade": ["☑ Apoiar"]
    }
    
    avisos = validar_aula_final(aula)
    assert any("não menciona termos específicos do conteúdo" in aviso for aviso in avisos)


def test_validador_rejeita_metodologia_sem_acao_professor_ou_aluno():
    aula = {
        "disciplina": "Matemática",
        "tema": "História dos Números",
        "aprendizagem": "Compreender a história dos números e sistemas de numeração.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "Iniciar a aula com discussão sobre números."},
            {"titulo": "Foco no conteúdo", "texto": "Leitura compartilhada sobre os sistemas de numeração."},
            {"titulo": "Na prática", "texto": "Realizar exercícios sobre os numerais."},
            {"titulo": "Encerramento", "texto": "Socialização das conclusões sobre sistemas."}
        ],
        "acompanhamento": ["☑ Acompanhar"],
        "acessibilidade": ["☑ Apoiar"]
    }
    
    avisos = validar_aula_final(aula)
    assert any("não descreve claramente a ação do professor" in aviso for aviso in avisos) or \
           any("não descreve claramente a ação dos alunos" in aviso for aviso in avisos)


def test_validador_sinaliza_acessibilidade_generica():
    aula = {
        "disciplina": "Matemática",
        "tema": "Geometria Espacial",
        "aprendizagem": "Calcular o volume de prismas e cilindros.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "O professor propõe pergunta aos estudantes sobre volumes e prismas."},
            {"titulo": "Foco no conteúdo", "texto": "O mediador explica volume e prismas, e a turma anota no caderno."},
            {"titulo": "Na prática", "texto": "Os estudantes resolvem exercícios de volume e prismas no caderno."},
            {"titulo": "Encerramento", "texto": "O professor retoma volume e prismas e finaliza com a turma em roda."}
        ],
        "acompanhamento": ["☑ Verificar"],
        "acessibilidade": ["☑ apoio generico"]
    }
    
    avisos = validar_aula_final(aula)
    assert any("Acessibilidade contém orientações ou placeholders genéricos" in aviso for aviso in avisos) or \
           any("Acessibilidade genérica sem ligação" in aviso for aviso in avisos)


def test_normalizar_itens_acompanhamento_acessibilidade_exatamente_tres_itens():
    from core.lote import _normalizar_itens_contextuais
    
    # Menos de 3 itens
    acomp_curto = ["Acompanhar os registros."]
    acess_curto = ["Oferecer apoio."]
    
    a, b = _normalizar_itens_contextuais(acomp_curto, acess_curto, tema="Equações", perfil="matematica")
    
    assert len(a) == 3
    assert len(b) == 3
    assert all(item.startswith("☑ ") for item in a)
    assert all(item.startswith("☑ ") for item in b)
    
    # Mais de 3 itens
    acomp_longo = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
    acess_longo = ["Item A", "Item B", "Item C", "Item D"]
    
    a_long, b_long = _normalizar_itens_contextuais(acomp_longo, acess_longo, tema="Equações", perfil="matematica")
    
    assert len(a_long) == 3
    assert len(b_long) == 3
    assert all(item.startswith("☑ ") for item in a_long)
    assert all(item.startswith("☑ ") for item in b_long)


def test_ordenar_pdfs_por_numero_com_underscore():
    from core.helpers import ordenar_pdfs_por_numero, numero_aula_pdf
    
    arquivos = [
        "Adição e subtração de frações – Parte 1_12.pdf",
        "A literatura medieval_01.pdf",
        "Revisão Comparação de frações_04.pdf",
    ]
    
    # Testar extração do número individual
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1_12.pdf") == 12
    assert numero_aula_pdf("A literatura medieval_01.pdf") == 1
    assert numero_aula_pdf("Revisão Comparação de frações_04.pdf") == 4
    
    # Testar variações de separadores e espaçamento
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1 _ 12.pdf") == 12
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1 - 12.pdf") == 12
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1-12.pdf") == 12
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1 12.pdf") == 12
    
    # Testar sufixos de cópia
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1_12 (1).pdf") == 12
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1_12 - copia.pdf") == 12
    assert numero_aula_pdf("Adição e subtração de frações – Parte 1_12 - Cópia.pdf") == 12
    
    # Testar série/ano no início + número no final
    assert numero_aula_pdf("1a _ Série Revisão - Razão entre grandezas de espécies diferentes_20.pdf") == 20
    
    # Testar ordenação
    ordenados = ordenar_pdfs_por_numero(arquivos)
    assert ordenados == [
        "A literatura medieval_01.pdf",
        "Revisão Comparação de frações_04.pdf",
        "Adição e subtração de frações – Parte 1_12.pdf",
    ]



