from core import database
from core.professores_planos import mesclar_professores
from ui.cadastro import _disciplinas_por_professor, _eh_professor_dados_piloto


def _preparar_banco(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "planos_teste.db")
    database.init_db()


def test_disciplinas_do_filtro_respeitam_o_professor_selecionado():
    cadastros = [
        {"professor": "ANA", "disciplina": "Matemática"},
        {"professor": "ANA", "disciplina": "História"},
        {"professor": "BIA", "disciplina": "Ciências"},
        {"professor": "ANA", "disciplina": "Matemática"},
    ]

    assert _disciplinas_por_professor(cadastros, "ANA") == ["História", "Matemática"]
    assert _disciplinas_por_professor(cadastros, "BIA") == ["Ciências"]
    assert _disciplinas_por_professor(cadastros) == ["Ciências", "História", "Matemática"]


def test_edita_duplica_e_exclui_vinculo_sem_apagar_historico(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_professor_turma(
        "Ana",
        "Matematica",
        "6 ANO A",
        "Segunda",
        "07h - 1 aula",
        "1",
        "modelo.docx",
        "Matematica",
        "egle",
    )
    vinculo = database.listar_vinculos_professores()[0]

    atualizado = database.atualizar_vinculo_professor(
        vinculo["id"],
        "Ana Maria",
        "Matematica",
        "6 ANO B",
        "Terca",
        "08h - 2 aula",
        "2",
        "modelo_6b.docx",
        "Matematica",
        "padre",
    )
    assert atualizado["professor"] == "ANA MARIA"
    assert atualizado["turma"] == "6 ANO B"
    assert atualizado["horario"] == "08h - 2 aula"
    assert atualizado["template_id"] == "padre"

    novo_id = database.duplicar_vinculo_professor(
        atualizado["id"],
        turma="7 ANO A",
        arquivo_modelo="modelo_7a.docx",
        template_id="egle",
    )
    duplicado = database.obter_vinculo_professor(novo_id)
    assert duplicado["professor"] == "ANA MARIA"
    assert duplicado["turma"] == "7 ANO A"
    assert duplicado["arquivo_modelo"] == "modelo_7a.docx"
    assert duplicado["template_id"] == "egle"

    database.salvar_historico_plano("ANA MARIA", "Matematica", "6 ANO B", "plano.docx", b"docx")
    assert database.excluir_vinculo_professor(atualizado["id"]) is True

    restantes = database.listar_vinculos_professores()
    assert [item["turma"] for item in restantes] == ["7 ANO A"]
    assert len(database.listar_historico_planos()) == 1


def test_excluir_ultimo_vinculo_remove_professor_sem_remover_historico(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_professor_turma("Bia", "Historia", "8 ANO A", "", "", "1")
    vinculo = database.listar_vinculos_professores()[0]
    database.salvar_historico_plano("BIA", "Historia", "8 ANO A", "historia.docx", b"docx")

    assert database.excluir_vinculo_professor(vinculo["id"]) is True
    assert database.obter_professores_db() == {}
    assert len(database.listar_historico_planos()) == 1


def test_dados_administrativos_do_professor_salvam_e_atualizam(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_dados_administrativos_professor(
        "Luan Dias",
        cpf="000.000.000-00",
        email="luan@example.com",
        valor_mensal="R$ 1.500,00",
        telefone="(11) 99999-0000",
        observacoes="Piloto",
    )

    dados = database.obter_dados_administrativos_professor("LUAN DIAS")
    assert dados["professor"] == "LUAN DIAS"
    assert dados["cpf"] == "000.000.000-00"
    assert dados["email"] == "luan@example.com"
    assert dados["valor_mensal"] == "R$ 1.500,00"
    assert dados["telefone"] == "(11) 99999-0000"
    assert dados["observacoes"] == "Piloto"

    database.salvar_dados_administrativos_professor(
        "LUAN DIAS",
        email="novo@example.com",
        observacoes="Atualizado",
    )
    atualizado = database.obter_dados_administrativos_professor("Luan Dias")
    assert atualizado["cpf"] == ""
    assert atualizado["email"] == "novo@example.com"
    assert atualizado["observacoes"] == "Atualizado"


def test_dados_administrativos_preservam_professor_ao_excluir_ultimo_vinculo(monkeypatch, tmp_path):
    _preparar_banco(monkeypatch, tmp_path)

    database.salvar_professor_turma("Luan Dias", "Fisica", "3 ANO A", "", "", "1")
    database.salvar_dados_administrativos_professor("Luan Dias", email="luan@example.com")
    vinculo = database.listar_vinculos_professores()[0]

    assert database.excluir_vinculo_professor(vinculo["id"]) is True

    professores = database.obter_professores_db()
    assert "LUAN DIAS" in professores
    assert professores["LUAN DIAS"]["disciplinas"] == []
    assert database.obter_dados_administrativos_professor("Luan Dias")["email"] == "luan@example.com"


def test_piloto_dados_professor_fica_restrito_ao_luan():
    assert _eh_professor_dados_piloto("Luan Dias") is True
    assert _eh_professor_dados_piloto("Luan Das") is True
    assert _eh_professor_dados_piloto("Bruna") is False


def test_mesclagem_preserva_banco_e_importa_dados_da_pasta():
    banco = {
        "ANA": {
            "disciplinas": [
                {
                    "disciplina": "Matematica",
                    "turma": "6 ANO A",
                    "horario": "horario do banco",
                    "arquivo": "",
                    "datas_horarios": [],
                    "componente_curricular": "",
                }
            ]
        }
    }
    pasta = {
        "ANA": {
            "disciplinas": [
                {
                    "disciplina": "Matematica",
                    "turma": "6 ANO A",
                    "horario": "horario da pasta",
                    "arquivo": "modelo.docx",
                    "datas_horarios": [{"data": "2026-05-01"}],
                    "componente_curricular": "MATEMATICA",
                }
            ]
        },
        "BIA": {
            "disciplinas": [
                {
                    "disciplina": "Historia",
                    "turma": "8 ANO A",
                    "horario": "quarta",
                    "arquivo": "historia.docx",
                }
            ]
        },
    }

    mesclado = mesclar_professores(banco, pasta)

    ana = mesclado["ANA"]["disciplinas"][0]
    assert ana["horario"] == "horario do banco"
    assert ana["arquivo"] == "modelo.docx"
    assert ana["datas_horarios"] == [{"data": "2026-05-01"}]
    assert ana["componente_curricular"] == "MATEMATICA"
    assert mesclado["BIA"]["disciplinas"][0]["arquivo"] == "historia.docx"


def test_mesclagem_unifica_disciplina_por_grafia_sem_duplicar():
    banco = {
        "VÂNIA": {
            "disciplinas": [
                {
                    "disciplina": "Arte",
                    "turma": "6º ANO B",
                    "horario": "horario do banco",
                    "arquivo": "",
                    "datas_horarios": [],
                    "componente_curricular": "Arte",
                }
            ]
        }
    }
    pasta = {
        "VÂNIA": {
            "disciplinas": [
                {
                    "disciplina": "ARTE",
                    "turma": "6º ANO B",
                    "horario": "",
                    "arquivo": "plano_arte.docx",
                    "datas_horarios": [],
                    "componente_curricular": "ARTE",
                }
            ]
        }
    }

    mesclado = mesclar_professores(banco, pasta)

    disciplinas = mesclado["VÂNIA"]["disciplinas"]
    assert len(disciplinas) == 1
    assert disciplinas[0]["disciplina"] == "Arte"
    assert disciplinas[0]["arquivo"] == "plano_arte.docx"
