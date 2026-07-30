from core.estrutura_metodologia import validar_etapas_obrigatorias
from core.refino_referencia_docx import validar_refino_ia_do_docx


def _etapa(titulo):
    return {"titulo": titulo, "texto": f"Texto da etapa {titulo}."}


def test_etapas_obrigatorias_aceitam_ordem_livre_e_repeticoes():
    metodologia = [
        _etapa("Na prática - Atividade 1"),
        _etapa("Foco no conteúdo"),
        _etapa("Relembre"),
        _etapa("Foco no conteúdo - Continuação"),
        _etapa("Encerramento"),
    ]

    assert validar_etapas_obrigatorias(metodologia) == (True, "")


def test_etapas_obrigatorias_exigem_as_quatro_etapas_minimas():
    valido, motivo = validar_etapas_obrigatorias([
        _etapa("Para começar"),
        _etapa("Foco no conteúdo"),
        _etapa("Encerramento"),
    ])

    assert valido is False
    assert "Na prática" in motivo


def test_refino_ia_aceita_ordem_e_quantidade_diferentes_do_docx():
    referencia = {"metodologia": [_etapa("Etapa livre")]}
    plano_ia = {
        "metodologia": [
            _etapa("Encerramento"),
            _etapa("Na prática"),
            _etapa("Foco no conteúdo"),
            _etapa("Para começar"),
            _etapa("Na prática - revisão"),
        ]
    }

    assert validar_refino_ia_do_docx(referencia, plano_ia) == (True, "")


def test_refino_ia_rejeita_retomada_generica_que_substitui_abertura_do_docx():
    referencia = {
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Assistir ao video e discutir diferentes percepcoes sobre a escola."},
            _etapa("Foco no conteudo"),
            _etapa("Na pratica"),
            _etapa("Encerramento"),
        ]
    }
    plano_ia = {
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Retomar o percurso das aulas anteriores antes de iniciar o tema."},
            _etapa("Foco no conteudo"),
            _etapa("Na pratica"),
            _etapa("Encerramento"),
        ]
    }

    valido, motivo = validar_refino_ia_do_docx(referencia, plano_ia)

    assert valido is False
    assert "retomada generica" in motivo


def test_refino_ia_aceita_retomada_quando_ela_ja_esta_no_docx():
    referencia = {
        "metodologia": [
            {"titulo": "Relembre", "texto": "Retomar a leitura do texto iniciada no encontro anterior."},
            _etapa("Foco no conteudo"),
            _etapa("Na pratica"),
            _etapa("Encerramento"),
        ]
    }
    plano_ia = {
        "metodologia": [
            {"titulo": "Para comecar", "texto": "Retomar a leitura do texto e organizar os registros no caderno."},
            _etapa("Foco no conteudo"),
            _etapa("Na pratica"),
            _etapa("Encerramento"),
        ]
    }

    assert validar_refino_ia_do_docx(referencia, plano_ia) == (True, "")
