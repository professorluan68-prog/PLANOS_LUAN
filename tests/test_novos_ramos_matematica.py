import re
import unicodedata
from core.lib.metodologia import _metodologia_matematica
from core.lib.acessibilidade_perfis import _acessibilidade_matematica
from core.lib.acompanhamento_perfis import _acompanhamento_matematica

def norm(text: str) -> str:
    text = str(text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("º", "").replace("ª", "").replace("°", "")
    return re.sub(r"\s+", " ", text)

def test_novos_ramos_metodologia():
    # 1. Numbers / Arithmetic
    met_num = _metodologia_matematica("Exercicios de divisao com numeros decimais", "Fracoes e Decimais", "conceito_novo", "6o ano")
    assert any("frac" in norm(item["texto"]) or "decim" in norm(item["texto"]) for item in met_num)
    
    # 2. Proportionality
    met_prop = _metodologia_matematica("Resolver problemas de regra de tres simples", "Grandezas Diretas", "conceito_novo", "7o ano")
    assert any("proporc" in norm(item["texto"]) or "grandeza" in norm(item["texto"]) for item in met_prop)
    
    # 3. Sequences / Progressions
    met_seq = _metodologia_matematica("Identificar os proximos termos da PA", "Progressao Aritmetica", "conceito_novo", "8o ano")
    assert any("sequencia" in norm(item["texto"]) or "progressao" in norm(item["texto"]) or "padrao" in norm(item["texto"]) for item in met_seq)
    
    # 4. Algorithms / Flowcharts
    met_alg = _metodologia_matematica("Construir um fluxograma de decisao", "Algoritmos", "conceito_novo", "9o ano")
    assert any("algoritmo" in norm(item["texto"]) or "fluxograma" in norm(item["texto"]) for item in met_alg)

def test_novos_ramos_acessibilidade():
    # 1. Numbers
    ace_num = _acessibilidade_matematica("Fracoes", "Soma de fracoes", "Resolver exercicios no caderno")
    assert any("reta numerica" in norm(item) or "fracao" in norm(item) or "grade" in norm(item) for item in ace_num)
    
    # 2. Proportionality
    ace_prop = _acessibilidade_matematica("Regra de tres", "Proporcionalidade", "Organizar grandezas")
    assert any("grandeza" in norm(item) or "proporcionalidade" in norm(item) for item in ace_prop)
    
    # 3. Sequences
    ace_seq = _acessibilidade_matematica("Progressao", "PA e PG", "Termos da sequencia")
    assert any("sequencia" in norm(item) or "tabela de correspondencia" in norm(item) for item in ace_seq)
    
    # 4. Algorithms
    ace_alg = _acessibilidade_matematica("Fluxograma", "Algoritmo", "Passos logicos")
    assert any("fluxograma" in norm(item) or "passos logicos" in norm(item) for item in ace_alg)

def test_novos_ramos_acompanhamento():
    # 1. Numbers
    aco_num = _acompanhamento_matematica("Fracoes", "Soma de fracoes", "Resolver exercicios no caderno")
    assert any("fracao" in norm(item) or "calculo manual" in norm(item) or "representacao" in norm(item) for item in aco_num)
    
    # 2. Proportionality
    aco_prop = _acompanhamento_matematica("Regra de tres", "Proporcionalidade", "Organizar grandezas")
    assert any("grandeza" in norm(item) or "proporcionalidade" in norm(item) or "regra de tres" in norm(item) for item in aco_prop)
    
    # 3. Sequences
    aco_seq = _acompanhamento_matematica("Progressao", "PA e PG", "Termos da sequencia")
    assert any("regularidade" in norm(item) or "termo geral" in norm(item) or "progressao" in norm(item) for item in aco_seq)
    
    # 4. Algorithms
    aco_alg = _acompanhamento_matematica("Fluxograma", "Algoritmo", "Passos logicos")
    assert any("fluxograma" in norm(item) or "passos estruturados" in norm(item) or "teste de mesa" in norm(item) for item in aco_alg)
