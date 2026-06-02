# -*- coding: utf-8 -*-
from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import MotorMetodologico, _etapas_por_perfil
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada


def test_perfil_ingles_detectado_corretamente():
    assert perfil_disciplina("Língua Inglesa") == "ingles"
    assert perfil_disciplina("English") == "ingles"


def test_tipo_aula_ingles_detectado_corretamente():
    # 1. Leitura EM
    texto_leitura = "Evolution in communication. Article from CEU, comic strip, vestibular, enem, reading strategies."
    assert detectar_tipo_aula(texto_leitura, "Evolution in communication", "Língua Inglesa") == "leitura_em"

    # 2. Gramática
    texto_gramatica = "Foco no conteúdo. Grammar, simple past, irregular verbs, regular verbs."
    assert detectar_tipo_aula(texto_gramatica, "Had fun", "Língua Inglesa") == "gramatica"

    # 3. Listening
    texto_listening = "Listen to the audio and conversation. Script para o estudante surdo."
    assert detectar_tipo_aula(texto_listening, "Listening practice", "Língua Inglesa") == "listening"

    # 4. Vocabulário
    texto_vocab = "Learn these words and practice pronunciation. Word bank, listen and repeat."
    assert detectar_tipo_aula(texto_vocab, "Vocabulary time", "Língua Inglesa") == "vocabulario"

    # 5. Produção Oral
    texto_speaking = "In pairs, talk to your classmate. Speak in English, dialogue."
    assert detectar_tipo_aula(texto_speaking, "Let's speak", "Língua Inglesa") == "producao_oral"

    # 6. Leitura Literária
    texto_literario = "Literary reading, novel, character, setting, Dracula, Stoker."
    assert detectar_tipo_aula(texto_literario, "Dracula novel", "Língua Inglesa") == "leitura_literaria"

    # 7. Música
    texto_musica = "Song lyrics, listen to the song, Count on Me by Bruno Mars, youtube."
    assert detectar_tipo_aula(texto_musica, "Count on Me", "Língua Inglesa") == "musica"

    # 8. Revisão
    texto_revisao = "Let's review. Review of simple past."
    assert detectar_tipo_aula(texto_revisao, "Review class", "Língua Inglesa") == "revisao"


def test_etapas_por_perfil_ingles():
    etapas_leitura = _etapas_por_perfil("ingles", "leitura_em")
    chaves_leitura = [e[1] for e in etapas_leitura]
    assert "para_comecar_virem_e_conversem" in chaves_leitura
    assert "questoes_vestibular" in chaves_leitura

    etapas_gramatica = _etapas_por_perfil("ingles", "gramatica")
    chaves_gramatica = [e[1] for e in etapas_gramatica]
    assert "listening_ou_vocabulario" in chaves_gramatica
    assert "producao_oral_duplas" in chaves_gramatica


def test_motor_metodologico_ingles_leitura_em():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf="Evolution in communication. Article from CEU, comic strip, vestibular, enem, reading strategies.",
        disciplina="Língua Inglesa",
        turma="2º ANO A",
        tema="Evolution in communication",
    )
    # Deve conter etapas típicas de leitura
    titulos = [e["titulo"] for e in etapas]
    assert "Para começar" in titulos
    assert "Hora da leitura" in titulos
    assert "Na prática" in titulos

    textos = " ".join(e["texto"] for e in etapas)
    assert "conversa" in textos
    assert "cognatas" in textos


def test_acompanhamento_ingles_leitura_em():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Evolution in communication",
        desenvolvimento="Evolution in communication. Article from CEU, comic strip, vestibular, enem, reading strategies.",
        disciplina="Língua Inglesa"
    )
    assert len(acompanhamento) == 3
    assert any("☑" in item for item in acompanhamento)
    assert any("estratégias de leitura" in item for item in acompanhamento)


def test_acessibilidade_ingles_listening():
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Listening activity",
        desenvolvimento="Listen to the audio and conversation. Script para o estudante surdo.",
        disciplina="Língua Inglesa"
    )
    assert len(acessibilidade) == 3
    assert any("script" in item.lower() for item in acessibilidade)
    assert any("surdos" in item.lower() for item in acessibilidade)
