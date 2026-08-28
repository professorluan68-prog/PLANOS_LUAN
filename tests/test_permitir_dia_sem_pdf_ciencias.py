import re
from pathlib import Path
from core.lib.classificador import perfil_disciplina


def test_perfil_disciplina_ciencias_mapeia_corretamente():
    # Garante que Ciências e Matemática mapeiam para os perfis corretos
    assert perfil_disciplina("Ciências") == "ciencias_ef"
    assert perfil_disciplina("Matemática") == "matematica"
    assert perfil_disciplina("Língua Portuguesa") in {"lingua_portuguesa_ef", "lingua_portuguesa_em"}


def test_planos_luan_app_contem_ciencias_no_dia_sem_pdf():
    app_path = Path(__file__).resolve().parents[1] / "planos_luan_app.py"
    texto = app_path.read_text(encoding="utf-8")

    # 1. Verifica se ciencias_ef está no conjunto _PERFIS_PORTUGUES_PERMITEM_SEM_PDF
    assert "ciencias_ef" in texto

    # 2. Verifica se a definição de _PERFIS_PORTUGUES_PERMITEM_SEM_PDF contém ciencias_ef
    # Vamos achar o bloco da constante _PERFIS_PORTUGUES_PERMITEM_SEM_PDF
    match_const = re.search(r"_PERFIS_PORTUGUES_PERMITEM_SEM_PDF\s*=\s*\{([^}]+)\}", texto)
    assert match_const is not None, "Constante _PERFIS_PORTUGUES_PERMITEM_SEM_PDF nao encontrada no app"
    conteudo_const = match_const.group(1)
    assert "ciencias_ef" in conteudo_const

    # 3. Verifica se o help do checkbox foi atualizado para mencionar Ciências
    assert "Português, Matemática ou Ciências em branco no plano" in texto


def test_permite_um_dia_sem_pdf_portugues_fallback_ciencias():
    app_path = Path(__file__).resolve().parents[1] / "planos_luan_app.py"
    texto = app_path.read_text(encoding="utf-8")

    # Verifica se o fallback da exceção na função _permite_um_dia_sem_pdf_portugues
    # possui as palavras-chave para ciências (cienc, cien) e matemática (matem)
    assert '"cienc" in disciplina_norm' in texto or "'cienc' in disciplina_norm" in texto
    assert '"cien" in disciplina_norm' in texto or "'cien' in disciplina_norm" in texto
    assert '"matem" in disciplina_norm' in texto or "'matem' in disciplina_norm" in texto
