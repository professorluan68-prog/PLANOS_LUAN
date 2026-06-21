import json
from pathlib import Path
import pytest
from core.revisao_final import calcular_sha256, revisar_aula_gerada, gravar_sidecar_json
from core.lote import _aula_por_pdf

def test_calcular_sha256(tmp_path):
    temp_file = tmp_path / "teste.txt"
    temp_file.write_text("conteudo de teste", encoding="utf-8")
    
    hash_val = calcular_sha256(temp_file)
    assert len(hash_val) == 64
    assert hash_val == "66690828e56a5f43d36843c11accbd0687b296d9839af584aae86b234aecf013"

def test_revisar_aula_gerada_auditoria():
    # 1. Aula perfeita (deve pontuar 100)
    aula_perfeita = {
        "tema": "Grandezas Proporcionais",
        "aprendizagem": "Resolver problemas envolvendo grandezas diretamente proporcionais.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "O professor apresenta o tema de grandezas proporcionais aos estudantes em uma roda de conversa inicial."},
            {"titulo": "Foco no conteúdo", "texto": "O professor explica as propriedades das grandezas proporcionais e os alunos anotam os conceitos principais em seus cadernos."},
            {"titulo": "Na prática", "texto": "O professor propõe que os estudantes se organizem em duplas para resolver problemas práticos de grandezas proporcionais em folha de registro."},
            {"titulo": "Encerramento", "texto": "O professor orienta que os alunos façam um debate rápido compartilhando as resoluções sobre grandezas proporcionais e registrem a síntese final no caderno."}
        ],
        "acompanhamento": [
            "☑ Observar a participação dos estudantes na resolução dos problemas.",
            "☑ Verificar os registros das estratégias usadas nas duplas.",
            "☑ Conferir as respostas socializadas ao final da aula.",
        ],
        "acessibilidade": [
            "☑ Disponibilizar representações visuais de grandezas proporcionais.",
            "☑ Oferecer leitura guiada dos enunciados com palavras-chave destacadas.",
            "☑ Permitir resposta oral mediada antes do registro escrito.",
        ]
    }
    resultado = revisar_aula_gerada(aula_perfeita, "matematica")
    assert resultado["confidence_score"] == 100
    assert len(resultado["avisos_validacao"]) == 0

    # 2. Aula com poucas etapas e falta de itens mínimos
    aula_ruim = {
        "tema": "",
        "aprendizagem": "",
        "metodologia": [
            {"titulo": "Início", "texto": "Introdução curta."}
        ],
        "acompanhamento": ["Apenas observação"],
        "acessibilidade": ["Informação do material simples."]
    }
    resultado_ruim = revisar_aula_gerada(aula_ruim, "matematica")
    assert resultado_ruim["confidence_score"] < 50
    alertas = resultado_ruim["avisos_validacao"]
    assert "Tema não identificado." in alertas
    assert "Campo de aprendizagem vazio." in alertas
    assert "Metodologia com poucas etapas." in alertas
    assert "Acompanhamento da aprendizagem deve ter exatamente 3 itens; foram encontrados 1." in alertas
    assert "Acompanhamento da aprendizagem deve ter todos os itens iniciando com ☑." in alertas
    assert "Acessibilidade deve ter exatamente 3 itens; foram encontrados 1." in alertas
    assert "Acessibilidade deve ter todos os itens iniciando com ☑." in alertas
    assert "Placeholder residual em acessibilidade: 'informação do material simples'." in alertas

def test_lote_cache_validation_by_hash(tmp_path):
    # Criar PDF de mentira
    pdf_file = tmp_path / "AULA 1.pdf"
    pdf_file.write_text("PDF Original Content", encoding="utf-8")
    hash_orig = calcular_sha256(pdf_file)

    # Criar cache JSON de mentira válido
    json_data = {
        "disciplina": "História",
        "tema": "Revolução Francesa",
        "material": "AULA 1.pdf",
        "numero_aula": "1",
        "aprendizagem": "Identificar os principais fatores da Revolução Francesa.",
        "metodologia": [
            {"titulo": "Para começar", "texto": "Problematização da sociedade estamental francesa."},
            {"titulo": "Foco no conteúdo", "texto": "Explanação dos três estados e a Queda da Bastilha."},
            {"titulo": "Na prática", "texto": "Trabalho em grupo sobre a Declaração de Direitos."}
        ],
        "acompanhamento": ["Observação", "Análise de questões", "Sondagem final"],
        "acessibilidade": ["Texto ampliado", "Uso de glossário", "Apoio individualizado"],
        "fonte_principal": "pdf",
        "arquivo_fonte": "AULA 1.pdf",
        "cache_reutilizado": False,
        "origem_metodologia": "motor_local",
        "perfil_metodologico": "analise_modelada",
        "versao_prompt": "educacao_financeira_1.0",
        "etapas_detectadas": ["Para começar", "Foco no conteúdo", "Na prática"],
        "hash_pdf": hash_orig,
        "confidence_score": 100,
        "avisos_validacao": []
    }

    # Gravar o sidecar
    caminho_json = gravar_sidecar_json(pdf_file, json_data, hash_orig)
    assert caminho_json.exists()
    dados_salvos = json.loads(caminho_json.read_text(encoding="utf-8"))
    assert dados_salvos["fonte_principal"] == "pdf"
    assert dados_salvos["cache_reutilizado"] is False
    assert dados_salvos["origem_metodologia"] == "motor_local"
    assert dados_salvos["perfil_metodologico"] == "analise_modelada"
    assert dados_salvos["versao_prompt"] == "educacao_financeira_1.0"
    assert dados_salvos["etapas_detectadas"] == ["Para começar", "Foco no conteúdo", "Na prática"]

    # Chamar _aula_por_pdf e verificar se carrega o cache
    aula_carregada = _aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="História",
        turma="8º ano",
        bimestre="2º Bimestre",
        usar_ia=False,
        provedor_ia=""
    )
    assert aula_carregada["tema"] == "Revolução Francesa"
    assert aula_carregada["hash_pdf"] == hash_orig

    # Agora modificamos o PDF original (alterando o hash)
    pdf_file.write_text("PDF Modified Content - Stale Cache!", encoding="utf-8")
    hash_novo = calcular_sha256(pdf_file)
    assert hash_novo != hash_orig

    # Chamar _aula_por_pdf novamente - deve ignorar o cache e regenerar (usando o motor local fallback)
    aula_regenerada = _aula_por_pdf(
        caminho_pdf=str(pdf_file),
        disciplina="História",
        turma="8º ano",
        bimestre="2º Bimestre",
        usar_ia=False,
        provedor_ia=""
    )
    # Como o PDF de mentira não tem texto real de História estruturado, a geração local
    # retornará um plano com o tema inferido do PDF ou tema genérico, mas definitivamente
    # NÃO o tema "Revolução Francesa" do cache invalidado.
    assert aula_regenerada["tema"] != "Revolução Francesa"
