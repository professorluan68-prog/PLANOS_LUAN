from core.lib.classificador import normalizar_texto
from core.lib.metodologia import MotorMetodologico


def _texto_etapas(etapas):
    return normalizar_texto(" ".join(etapa["texto"] for etapa in etapas))


def test_tecnologia_inovacao_dispositivos_entrada_saida_gera_metodologia_concreta():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf=(
            "Tecnologia e Inovação\n"
            "Entrada e saída no computador\n"
            "Dispositivos de entrada e suas funções: mouse, teclado, microfone e câmera.\n"
            "Dispositivos de saída e suas funções: monitor, impressora, projetor e caixa de som.\n"
        ),
        disciplina="Tecnologia e Inovação",
        turma="7º ANO A",
        tema="Entrada e saída no computador",
    )

    texto = _texto_etapas(etapas)
    assert "dispositivos de entrada e de saida" in texto
    assert "teclado" in texto
    assert "monitor" in texto


def test_tecnologia_inovacao_programacao_inicial_usa_startlab():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf=(
            "Tecnologia e Inovação\n"
            "Criando com teclado\n"
            "Uso da bandeira verde e de blocos de eventos.\n"
            "Personalização de mensagens com blocos da categoria aparência.\n"
            "Aplicar comandos do teclado e do mouse para elaborar mensagens interativas no ambiente de programação.\n"
        ),
        disciplina="Tecnologia e Inovação",
        turma="7º ANO A",
        tema="Criando com teclado",
    )

    texto = _texto_etapas(etapas)
    assert "startlab" in texto
    assert "bandeira verde" in texto
    assert "bloco diga" in texto


def test_tecnologia_inovacao_comunicacao_digital_usa_perguntas_claras():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf=(
            "Tecnologia e Inovação\n"
            "Tirando dúvidas corretamente\n"
            "Como fazer perguntas claras e objetivas.\n"
            "Estratégias de criação de boas perguntas.\n"
            "Análise de perguntas inadequadas.\n"
        ),
        disciplina="Tecnologia e Inovação",
        turma="7º ANO A",
        tema="Tirando dúvidas corretamente",
    )

    texto = _texto_etapas(etapas)
    assert "perguntas claras" in texto
    assert "ambientes digitais" in texto
    assert "mensagens" in texto or "informacoes" in texto
