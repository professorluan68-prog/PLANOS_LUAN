import importlib

import config
from core import database


def test_database_usa_o_mesmo_db_path_do_config():
    assert database.DB_PATH == config.DB_PATH


def test_pdfs_usam_raiz_oficial_fora_do_repositorio():
    raiz_esperada = config.BASE_DIR.parent / "PLANOS_LUAN_DADOS"

    assert config.PLANOS_LUAN_DADOS_DIR == raiz_esperada
    assert config.PDF_AULAS_DIR == raiz_esperada / "PDF_AULAS"
    assert config.PDF_AULAS_DIR.parent != config.BASE_DIR


def test_pdfs_ignoram_override_legado_do_ambiente(monkeypatch):
    monkeypatch.setenv(
        "PDF_AULAS_DIR",
        r"C:\Users\Luan Dias\OneDrive\Documents\PDF_AULAS",
    )

    config_recarregado = importlib.reload(config)

    assert config_recarregado.PDF_AULAS_DIR == (
        config_recarregado.BASE_DIR.parent / "PLANOS_LUAN_DADOS" / "PDF_AULAS"
    )
