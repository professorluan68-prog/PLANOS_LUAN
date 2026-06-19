# -*- coding: utf-8 -*-
from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import MotorMetodologico


def test_perfil_arte_detectado_corretamente():
    assert perfil_disciplina("Arte") == "arte"


def test_tipo_aula_arte_detectado_corretamente():
    # 1. dobradura_origami
    texto_dobradura = "Hoje vamos realizar uma atividade de dobradura de papel. Origami tradicional japonês, vincos e dobras precisas."
    assert detectar_tipo_aula(texto_dobradura, "Explorando dobraduras", "Arte") == "dobradura_origami"

    # 2. stop_motion_flipbook
    texto_stop_motion = "Criação de stop-motion e flipbooks quadro a quadro. Gravação de quadros (frames) e ilusão de movimento."
    assert detectar_tipo_aula(texto_stop_motion, "Criando animações", "Arte") == "stop_motion_flipbook"

    # 3. assemblage_mosaico
    texto_assemblage = "Vamos conhecer as assemblages de Vik Muniz. Colagem de objetos cotidianos, resíduos, sucata e montagem tridimensional."
    assert detectar_tipo_aula(texto_assemblage, "Vik Muniz e Assemblage", "Arte") == "assemblage_mosaico"

    # 4. muralismo_grafite
    texto_mural = "Estudo do grafite e do muralismo nas grandes cidades. Intervenção urbana, stickers e lambe-lambe."
    assert detectar_tipo_aula(texto_mural, "Grafite e Arte Urbana", "Arte") == "muralismo_grafite"

    # 5. arte_indigena
    texto_indigena = "Estudo do grafismo indígena e do Manto Tupinambá. Máscaras, modelagem em argila e cerâmica tradicional."
    assert detectar_tipo_aula(texto_indigena, "Tradições Indígenas", "Arte") == "arte_indigena"

    # 6. fotografia_composicao
    texto_foto = "Conceitos de fotografia, enquadramento, luz e sombra. O tridimensional representado no plano bidimensional através da gravura."
    assert detectar_tipo_aula(texto_foto, "Luz, sombra e composição", "Arte") == "fotografia_composicao"

    # 7. exposicao_revisao
    texto_exposicao = "Preparação de uma exposição dos trabalhos e curadoria coletiva da sala de aula."
    assert detectar_tipo_aula(texto_exposicao, "Exposição Colaborativa", "Arte") == "exposicao_revisao"


def test_motor_metodologico_arte_origami():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf='Instruções para dobradura de tsuru. Fazer os vincos no papel quadrado com cuidado.',
        disciplina="Arte",
        turma="6º ANO A",
        tema="Explorando dobraduras",
    )
    titulos = [e["titulo"] for e in etapas]
    assert "Para começar" in titulos
    assert "Foco no conteúdo" in titulos
    assert "Na prática" in titulos
    assert "Encerramento" in titulos

    textos = " ".join(e["texto"] for e in etapas)
    # Deve conter menções a dobras, origami ou papel
    assert "dobradura" in textos.lower() or "origami" in textos.lower()
