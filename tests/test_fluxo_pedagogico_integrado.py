from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.classificador import perfil_disciplina
from core.lib.extrator_pdf import ExtratorPDF
from core.lote import _montar_etapas_metodologia
from core.qualidade_metodologica import limitar_texto_natural, normalizar_texto
from core.validador_plano import validar_aula_final


def test_classificador_nao_contamina_por_termos_genericos():
    assert perfil_disciplina("Projeto integrador") == "geral"
    assert perfil_disciplina("Leitura complementar") == "geral"
    assert perfil_disciplina("Orientacoes gerais") == "geral"
    assert perfil_disciplina("Projeto de Vida") == "projeto_de_vida"


def test_classificador_reconhece_orientacao_estudos_mesmo_com_texto_torto():
    assert perfil_disciplina("Orientação de Estudos") == "orientacao_estudos"
    assert perfil_disciplina("Orienta??o de Estudos") == "orientacao_estudos"
    assert perfil_disciplina("ORIENTA??O DE ESTUDOS") == "orientacao_estudos"


def test_extrator_prioriza_secao_na_pratica_para_atividade():
    texto = (
        "Para comecar\n"
        "Retomar a ideia de grandezas proporcionais.\n"
        "Foco no conteudo\n"
        "Explicar como a tabela organiza os valores.\n"
        "Na pratica\n"
        "Resolver uma tabela de valores, identificar o padrao e escrever a expressao algébrica.\n"
        "Encerramento\n"
        "Retomar o que foi aprendido.\n"
    )

    extracao = ExtratorPDF().extrair(texto, "Relacao entre grandezas")

    assert "tabela de valores" in normalizar_texto(extracao["atividade_extraida"])
    assert "retomar a ideia" not in normalizar_texto(extracao["atividade_extraida"])


def test_limitar_texto_natural_nao_termina_com_conectivo_solto():
    texto = (
        "Verificar se o estudante organiza os dados, registra as etapas do calculo "
        "e justifica oralmente o raciocinio com"
    )

    resultado = limitar_texto_natural(texto, limite=95)
    palavras = normalizar_texto(resultado).split()

    assert resultado.endswith(".")
    assert palavras[-1] not in {"a", "as", "o", "os", "de", "da", "das", "do", "dos", "para", "com", "e", "em", "por"}


def test_validador_final_detecta_contaminacao_e_falta_de_revisao():
    avisos = validar_aula_final(
        {
            "disciplina": "Matematica",
            "tema": "Producao textual: relato",
            "aprendizagem": "Resolver problemas e registrar respostas.",
            "metodologia": [
                {
                    "titulo": "Foco no conteudo",
                    "texto": "Analisar personagens, enredo e efeitos do texto literario antes dos calculos.",
                }
            ],
            "acompanhamento": ["Observar a leitura do texto."],
            "acessibilidade": ["Oferecer leitura mediada."],
        }
    )

    texto = normalizar_texto(" ".join(avisos))
    assert "leitura liter" in texto
    assert "producao textual sem etapa clara" in texto


def test_acessibilidade_prioriza_recurso_do_pdf_em_producao_textual():
    itens = gerar_acessibilidade_aprimorada(
        tema="Pratica de linguagem: Producao de textos",
        aprendizagem="Planejar, revisar e reescrever um texto de opiniao.",
        desenvolvimento="Metodologia contaminada com tabela e grafico, mas o PDF pede escrita e revisao.",
        disciplina="Redacao e Leitura",
        perfil="leitura_redacao",
        recursos_detectados=["producao_textual"],
    )

    texto = normalizar_texto(" ".join(itens))
    assert "revis" in texto or "checklist" in texto or "rascunho" in texto
    assert "tabela" not in texto
    assert "grafico" not in texto


def test_saida_metodologica_nao_retorna_mojibake_em_projeto_de_vida():
    etapas = _montar_etapas_metodologia(
        texto="Na pratica\nRegistro individual e conversa em dupla sobre autoconhecimento.",
        disciplina="Projeto de Vida",
        turma="6 ano B",
        tema="Quem sou quando estou comigo?",
    )

    texto = " ".join(etapa["texto"] for etapa in etapas)
    for padrao in ("Ã", "Â", "�", "??"):
        assert padrao not in texto
