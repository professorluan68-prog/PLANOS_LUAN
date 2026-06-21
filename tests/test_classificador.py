from core.lib.classificador import (
    _classificar_por_pontos,
    _tipo_aula_lingua_portuguesa_ef,
    _tipo_aula_lingua_portuguesa_em,
)

def test_classificar_por_pontos_titulo():
    categorias = [
        ("gramatica", ["gramática", "sintaxe"]),
        ("literatura", ["romance", "poesia"]),
    ]
    # Palavra chave no título: peso 3 (ativa categoria se minimo_pontos=3)
    res = _classificar_por_pontos(
        titulo="Aula de Sintaxe",
        texto="Texto comum de aula",
        categorias=categorias,
        default="outro",
        minimo_pontos=3
    )
    assert res == "gramatica"

def test_classificar_por_pontos_secao_delimitada():
    categorias = [
        ("gramatica", ["gramática", "sintaxe"]),
        ("literatura", ["romance", "poesia"]),
    ]
    # Seção delimitada: peso 4
    res = _classificar_por_pontos(
        titulo="Aula Geral",
        texto="poesia - ler o livro de versos",
        categorias=categorias,
        default="outro",
        minimo_pontos=4
    )
    assert res == "literatura"

def test_classificar_por_pontos_corpo_isolado_nao_atinge_minimo():
    categorias = [
        ("gramatica", ["gramática", "sintaxe"]),
        ("literatura", ["romance", "poesia"]),
    ]
    # Corpo isolado: peso 1 (não atinge mínimo de 2)
    res = _classificar_por_pontos(
        titulo="Aula Geral",
        texto="Hoje vamos falar de um romance legal.",
        categorias=categorias,
        default="outro",
        minimo_pontos=2
    )
    assert res == "outro"

def test_tipo_aula_lingua_portuguesa_ef_leitura():
    # Deve cair no default 'leitura_literaria' se não bater nenhuma keyword
    res = _tipo_aula_lingua_portuguesa_ef("Aula de Leitura", "Texto comum de leitura")
    assert res == "leitura_literaria"

def test_tipo_aula_lingua_portuguesa_em_genero():
    # Deve cair no default 'genero_textual' se não bater nenhuma keyword
    res = _tipo_aula_lingua_portuguesa_em("Aula Geral", "Texto de português")
    assert res == "genero_textual"
