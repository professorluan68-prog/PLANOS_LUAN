from core.disciplinas import (
    COMPONENTES_CURRICULARES_CDP_CICLO_I,
    DISCIPLINA_CDP_CICLO_I,
    componentes_curriculares_por_disciplina,
    eh_cdp_fundamental,
    nomes_disciplinas,
    obter_config,
)
from ui.cadastro import _opcoes_componente_curricular


def test_cdp_ciclo_i_esta_disponivel_no_catalogo_de_cadastro():
    assert DISCIPLINA_CDP_CICLO_I in nomes_disciplinas()
    assert eh_cdp_fundamental(DISCIPLINA_CDP_CICLO_I)
    assert obter_config(DISCIPLINA_CDP_CICLO_I).exige_pdf is False


def test_componentes_cdp_ciclo_i_aparecem_no_cadastro():
    esperado = [
        "ANOS INICIAIS 4º e 5º ANO- EJA TURMA D",
        "ANOS INICIAIS 1º, 2º e 3º ANO- EJA TURMA C",
    ]

    assert COMPONENTES_CURRICULARES_CDP_CICLO_I == esperado
    assert componentes_curriculares_por_disciplina(DISCIPLINA_CDP_CICLO_I) == esperado
    assert all(
        componente
        in _opcoes_componente_curricular(DISCIPLINA_CDP_CICLO_I)
        for componente in esperado
    )
