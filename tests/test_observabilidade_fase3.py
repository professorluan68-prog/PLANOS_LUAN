import logging

from core.lib.higienizador_pedagogico import (
    _REGRAS_RECURSOS_COMPILADAS,
    higienizar_string,
)
from core.lib.metodologia import MotorMetodologico
from core.models import PlanoCompleto


def test_plano_completo_normaliza_na_construcao_direta():
    plano = PlanoCompleto(
        metodologia="Para começar: Retomar a atividade anterior.",
        acompanhamento="• Observar os registros.\n• Verificar a compreensão.",
        acessibilidade=["☑ Oferecer apoio visual."],
        recursos_detectados={"tabela": True, "grafico": False},
    )

    assert plano.metodologia[0].titulo == "Para começar"
    assert plano.acompanhamento == ["Observar os registros.", "Verificar a compreensão."]
    assert plano.acessibilidade == ["☑ Oferecer apoio visual."]
    assert plano.recursos_detectados == ["tabela"]


def test_regras_de_recursos_sao_compiladas_uma_vez():
    assert _REGRAS_RECURSOS_COMPILADAS
    assert all(
        hasattr(padrao, "sub")
        for regras in _REGRAS_RECURSOS_COMPILADAS.values()
        for padrao, _ in regras
    )
    assert "registro do material" in higienizar_string(
        "Preencher tabela.",
        "geral",
        {"tabela": False},
    )


def test_motor_emite_eventos_estruturados(caplog):
    caplog.set_level(logging.INFO, logger="core.lib.metodologia")

    resultado = MotorMetodologico().gerar(
        "A aula apresenta fontes históricas e propõe análise do material.",
        "História",
        "8º ano",
        "Fontes históricas",
    )

    assert resultado
    eventos = [
        registro.evento
        for registro in caplog.records
        if hasattr(registro, "evento")
    ]
    assert "motor_metodologico_classificado" in eventos
    assert "motor_metodologico_finalizado" in eventos
