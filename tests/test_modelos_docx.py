from core.modelos_docx import caminho_template_central, template_id_por_contexto


def test_template_por_contexto_prioriza_cdp():
    assert template_id_por_contexto("CDP - Ciclo I", "MATEMATICA") == "cdp"
    assert template_id_por_contexto("Matematica", "CDP-EJA") == "cdp"


def test_template_por_contexto_usa_egle_como_padrao():
    assert template_id_por_contexto("Biologia", "Biologia") == "egle"


def test_caminho_template_central_normaliza_desconhecido():
    assert caminho_template_central("qualquer").name == "MODELOEGLE.docx"
