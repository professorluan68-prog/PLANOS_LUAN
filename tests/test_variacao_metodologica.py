import pytest
import os
import tempfile
import json
from pathlib import Path
from core.variacao_metodologica import (
    selecionar_perfil_metodologico,
    selecionar_proximo_perfil,
    montar_fingerprint_contexto,
    detectar_similaridade_excessiva,
)
from core.lib.metodologia import MotorMetodologico
from core.lote import _aula_por_pdf, processar_varios_pdfs
from core.qualidade_metodologica import naturalizar_texto_metodologico


def test_selecao_perfil_pedagogico_estavel():
    # TESTE 1 — DETERMINISMO
    p1 = selecionar_perfil_metodologico("Beatriz Ribeiro", "1º ano C", "Língua Portuguesa", "3º Bimestre")
    p2 = selecionar_perfil_metodologico("Beatriz Ribeiro", "1º ano C", "Língua Portuguesa", "3º Bimestre")
    assert p1 == p2
    assert p1 in ["LEITURA INVESTIGATIVA", "COMPARAÇÃO E DIÁLOGO", "ANÁLISE MODELADA", "ESCRITA E AUTORIA"]

    # TESTE 2 — PROFESSORES DIFERENTES
    p3 = selecionar_perfil_metodologico("Luis Henrique", "1º ano A", "Língua Portuguesa", "3º Bimestre")
    # Deve dar um perfil diferente ou determinístico
    assert p3 in ["LEITURA INVESTIGATIVA", "COMPARAÇÃO E DIÁLOGO", "ANÁLISE MODELADA", "ESCRITA E AUTORIA"]


def test_selecionar_proximo_perfil():
    p = "LEITURA INVESTIGATIVA"
    p_next = selecionar_proximo_perfil(p)
    assert p_next == "COMPARAÇÃO E DIÁLOGO"
    
    p_last = "ESCRITA E AUTORIA"
    p_first = selecionar_proximo_perfil(p_last)
    assert p_first == "LEITURA INVESTIGATIVA"


def test_montar_fingerprint_contexto():
    f1 = montar_fingerprint_contexto("hash123", "v3", "Beatriz", "1C", "LP", "3B", "simples", "LEITURA INVESTIGATIVA")
    f2 = montar_fingerprint_contexto("hash123", "v3", "Beatriz", "1C", "LP", "3B", "simples", "LEITURA INVESTIGATIVA")
    assert f1 == f2

    f3 = montar_fingerprint_contexto("hash123", "v3", "Luís", "1C", "LP", "3B", "simples", "LEITURA INVESTIGATIVA")
    assert f1 != f3


def test_detectar_similaridade_excessiva():
    m1 = [{"titulo": "Para começar", "texto": "Retomar registros anteriores ajudando a turma a perceber a continuidade do estudo."}]
    m2 = [{"titulo": "Para começar", "texto": "Retomar registros anteriores ajudando a turma a perceber a continuidade do estudo."}]
    assert detectar_similaridade_excessiva(m1, m2) is True

    m3 = [{"titulo": "Para começar", "texto": "Iniciar a aula com uma discussão reflexiva sobre o tema proposto hoje."}]
    assert detectar_similaridade_excessiva(m1, m3) is False


def test_aula_simples_e_dupla_motor_local():
    # TESTE 3 — AULA SIMPLES E AULA DUPLA
    motor = MotorMetodologico()
    
    pdf_text = "Tema da aula: A cantiga e as marcas do trovadorismo. Slide 1: Leitura da cantiga. Slide 2: Pratica."
    
    # Aula simples
    res_simples = motor.gerar(
        texto_pdf=pdf_text,
        disciplina="Língua Portuguesa",
        turma="1º ano C",
        tema="Trovadorismo",
        contexto_geracao={
            "tipo_aula": "simples",
            "perfil_metodologico": "LEITURA INVESTIGATIVA"
        }
    )
    # Deve possuir as 4 etapas básicas
    titulos_simples = [r["titulo"] for r in res_simples]
    assert "Para começar" in titulos_simples
    assert "Na prática" in titulos_simples
    assert "Encerramento" in titulos_simples

    # Aula dupla
    res_dupla = motor.gerar(
        texto_pdf=pdf_text,
        disciplina="Língua Portuguesa",
        turma="1º ano C",
        tema="Trovadorismo",
        contexto_geracao={
            "tipo_aula": "dupla",
            "perfil_metodologico": "LEITURA INVESTIGATIVA"
        }
    )
    titulos_dupla = [r["titulo"] for r in res_dupla]
    assert "Hora da leitura" in titulos_dupla
    assert "Socialização" in titulos_dupla
    assert len(res_dupla) > len(res_simples)


def test_cache_comportamento(monkeypatch):
    import core.lote as lote
    
    mock_contexto = {
        "texto": "Tema da aula: Trovadorismo. Slide 1: Leitura. Slide 2: Pratica.",
        "tema": "Tema Simulado",
        "material_digital": "AULA 1 - Tema Simulado",
        "numero_aula": "1",
        "cdp_contextual": False,
        "disciplina_base": "Língua Portuguesa",
        "perfil": "lingua_portuguesa_em",
        "objetivos_orientacao": [],
        "aprendizagem_orientacao": "",
        "extracao_pdf": {
            "conceito_extraido": "Trovadorismo",
            "atividade_extraida": "Leitura da cantiga",
            "recursos_detectados": ["texto"],
            "etapas_detectadas": ["Leitura"],
            "habilidade": "EM13LP01"
        },
        "tipo": "literatura",
        "metodologia_fixa_pdf": None,
        "modalidade_eja_ativa": False,
        "contexto_metodologico": "regular",
        "escopo_pv": {},
        "aprendizagem_pv": "",
        "fonte_extracao": "pdf",
        "arquivo_fonte_extracao": "aula_teste.pdf"
    }
    
    monkeypatch.setattr(lote, "_preparar_contexto_aula_pdf", lambda **kwargs: mock_contexto)

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_file = Path(tmpdir) / "aula_teste.pdf"
        pdf_file.write_text("Conteudo do PDF de teste", encoding="utf-8")
        
        # Criar sidecar antigo sem fingerprint
        json_file = pdf_file.with_suffix(".json")
        json_data_antigo = {
            "hash_pdf": "hash_antigo",
            "metodologia": [{"titulo": "Etapa", "texto": "Texto antigo do professor A"}],
            "versao_gerador": "v1.0.0"
        }
        json_file.write_text(json.dumps(json_data_antigo), encoding="utf-8")
        
        # TESTE 4 — CACHE ANTIGO (Deve ignorar com segurança e recalcular a metodologia)
        res = _aula_por_pdf(
            caminho_pdf=str(pdf_file),
            disciplina="Língua Portuguesa",
            turma="1º ano C",
            bimestre="3º Bimestre",
            usar_ia=False,
            provedor_ia="sem_ia",
            professor="Beatriz Ribeiro",
            dividir_aula_atual=False
        )
        assert res.get("cache_reutilizado") is not True
        
        # O sidecar agora deve ter sido gravado com o fingerprint correto
        with open(json_file, "r", encoding="utf-8") as f:
            json_salvo = json.load(f)
        assert "fingerprint_contexto" in json_salvo
        fp_antigo = json_salvo["fingerprint_contexto"]
        
        # TESTE 5 — CACHE COMPATÍVEL (Deve retornar do cache sem regenerar se o fingerprint bater)
        res_cached = _aula_por_pdf(
            caminho_pdf=str(pdf_file),
            disciplina="Língua Portuguesa",
            turma="1º ano C",
            bimestre="3º Bimestre",
            usar_ia=False,
            provedor_ia="sem_ia",
            professor="Beatriz Ribeiro",
            dividir_aula_atual=False
        )
        assert res_cached["fingerprint_contexto"] == fp_antigo

        # TESTE 6 — MESMO PDF EM OUTRA TURMA/PROFESSOR: reutiliza o cache.
        res_outro = _aula_por_pdf(
            caminho_pdf=str(pdf_file),
            disciplina="Língua Portuguesa",
            turma="1º ano A",
            bimestre="3º Bimestre",
            usar_ia=False,
            provedor_ia="sem_ia",
            professor="Luis Henrique",
            dividir_aula_atual=False
        )
        assert res_outro["cache_reutilizado"] is True
        assert res_outro["fingerprint_contexto"] == fp_antigo


def test_correcoes_ortograficas_naturalizar():
    # TESTE 6 — CORREÇÕES TEXTUAIS
    t = "Os avancos da proxima aula sao de importancia necessaria em suas proprias palavras."
    t_corr = naturalizar_texto_metodologico(t)
    assert "avanços" in t_corr
    assert "próxima" in t_corr
    assert "necessária" in t_corr
    assert "suas próprias palavras" in t_corr
    
    t2 = "Construir a explicacao de as principais caracteristicas e compartilhem suas impressionantes."
    t2_corr = naturalizar_texto_metodologico(t2)
    assert "explicação das" in t2_corr
    assert "compartilhem suas impressões" in t2_corr


def test_naturalizar_corrige_falhas_do_plano_lp_9ano():
    texto = (
        'Executar a atividade, ouvindo a canção "Pela o material da aula e os registros no caderno" '
        "de Gilberto Gil e acompanhando a letra. Orientar uma conversa rapida de forma individual. "
        "Aplicar Virem e conversem por para que os alunos compartilhem impressoes antes de avancar. "
        "Apresentar o concept central. Conduzir a, em que todos leem juntos três minicontos. "
        "Aplicar o com a leitura em voz alta. Utilizar a técnica Todo mundo escreve para que os alunos responda em duplas questões. "
        "Aplicar o Virem e conversem para que os estudantes compartilharem suas impressões. "
        "As suasFiguras de linguagem serao retomadas na sequencia. "
        "Perguntar o que conhecem sobre canção, utilizando o para promover a troca de ideias. "
        "Realizar leitura orientada com a técnica Hora da leitura. "
        "Iniciar a aula retomar a discussão. Conduzir a realização individual e realizar a atividade. "
        "Realizar uma parada estratégica de verificação (PAUSE E RESPONDA), assegurando a compreensão. "
        "Questionar os alunos sobre novelas, utilizando a técnica Virem e conversem para que compartilhem experiências. "
        "Ao final, aplicar a atividade Todo mundo escreve para que registrem suas interpretações."
    )

    corrigido = naturalizar_texto_metodologico(texto)

    assert '"Pela internet"' in corrigido
    assert "de Gilberto Gil, e acompanhando" in corrigido
    assert "Pela o material" not in corrigido
    assert "registro individual breve" in corrigido
    assert "Promover conversa em duplas para" in corrigido
    assert "conceito central" in corrigido
    assert "Conduzir leitura compartilhada" in corrigido
    assert "Conduzir a leitura em voz alta" in corrigido
    assert "alunos respondam às questões em duplas" in corrigido
    assert "estudantes compartilhem suas impressões" in corrigido
    assert "impressões" in corrigido
    assert "avançar" in corrigido
    assert "suas figuras" in corrigido
    assert "serão" in corrigido
    assert "sequência" in corrigido
    assert "utilizando o para" not in corrigido
    assert "técnica Hora da leitura" not in corrigido
    assert "técnica Virem e conversem" not in corrigido
    assert "promovendo conversa em duplas para que compartilhem experiências" in corrigido
    assert "Solicitar registro individual no caderno para que registrem suas interpretações" in corrigido
    assert "Iniciar a aula retomando" in corrigido
    assert "Orientar a realização individual da atividade" in corrigido
