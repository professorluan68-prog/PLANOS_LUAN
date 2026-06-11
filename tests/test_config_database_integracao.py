import config
from core import database


def test_database_usa_o_mesmo_db_path_do_config():
    assert database.DB_PATH == config.DB_PATH
