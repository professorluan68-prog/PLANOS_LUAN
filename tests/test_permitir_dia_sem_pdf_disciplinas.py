from datetime import date
import pytest
from planos_luan_app import (
    _permite_um_dia_sem_pdf,
    _frequencia_dia_sem_pdf,
    _eh_data_sem_pdf,
)


def test_permite_um_dia_sem_pdf_artes_e_gerais():
    # Artes e disciplinas regulares devem permitir a opção
    assert _permite_um_dia_sem_pdf("Arte") is True
    assert _permite_um_dia_sem_pdf("Arte e Mídias Digitais") is True
    assert _permite_um_dia_sem_pdf("Língua Portuguesa") is True
    assert _permite_um_dia_sem_pdf("Matemática") is True
    assert _permite_um_dia_sem_pdf("Ciências") is True
    assert _permite_um_dia_sem_pdf("Biologia") is True
    assert _permite_um_dia_sem_pdf("Geografia") is True
    assert _permite_um_dia_sem_pdf("História") is True
    assert _permite_um_dia_sem_pdf("Física") is True
    assert _permite_um_dia_sem_pdf("Química") is True
    assert _permite_um_dia_sem_pdf("Filosofia") is True
    assert _permite_um_dia_sem_pdf("Sociologia") is True
    assert _permite_um_dia_sem_pdf("Língua Inglesa") is True
    assert _permite_um_dia_sem_pdf("Liderança e Oratória") is True
    assert _permite_um_dia_sem_pdf("Educação Financeira") is True
    assert _permite_um_dia_sem_pdf("Educação Física") is True
    assert _permite_um_dia_sem_pdf("Orientação de Estudos") is True
    assert _permite_um_dia_sem_pdf("Tecnologia e Inovação") is True
    assert _permite_um_dia_sem_pdf("Robótica") is True
    assert _permite_um_dia_sem_pdf("Outra") is True


def test_bloqueia_projeto_de_vida():
    # Projeto de Vida deve ser bloqueado
    assert _permite_um_dia_sem_pdf("Projeto de Vida") is False
    assert _permite_um_dia_sem_pdf("Projeto de vida") is False
    assert _permite_um_dia_sem_pdf("projeto de vida") is False


def test_bloqueia_aprofundamento_biologia_e_geografia():
    # Aprofundamento em Biologia e Aprofundamento em Geografia devem ser bloqueados
    assert _permite_um_dia_sem_pdf("Aprofundamento em Biologia") is False
    assert _permite_um_dia_sem_pdf("Aprofundamento Biologia") is False
    assert _permite_um_dia_sem_pdf("Aprofundamento em Geografia") is False
    assert _permite_um_dia_sem_pdf("Aprofundamento Geografia") is False


def test_bloqueia_cdp():
    # Disciplinas em modo CDP ou com CDP no nome devem ser bloqueadas
    assert _permite_um_dia_sem_pdf("Arte", modo_cdp=True) is False
    assert _permite_um_dia_sem_pdf("Ciências-CDP") is False
    assert _permite_um_dia_sem_pdf("Geografia_EM-CDP") is False
    assert _permite_um_dia_sem_pdf("CDP- Multisseriada") is False
    assert _permite_um_dia_sem_pdf("CDP - Ciclo I") is False


def test_bloqueia_eja():
    # Disciplinas em modo EJA ou com EJA no nome devem ser bloqueadas
    assert _permite_um_dia_sem_pdf("Arte", modo_eja=True) is False
    assert _permite_um_dia_sem_pdf("Biologia", modo_eja=True) is False
    assert _permite_um_dia_sem_pdf("Química-EJA") is False
    assert _permite_um_dia_sem_pdf("Biologia EJA") is False


def test_frequencia_dia_sem_pdf():
    # Semanal para Português, Matemática, Ciências
    assert _frequencia_dia_sem_pdf("Língua Portuguesa") == "semanal"
    assert _frequencia_dia_sem_pdf("Matemática") == "semanal"
    assert _frequencia_dia_sem_pdf("Ciências") == "semanal"
    assert _frequencia_dia_sem_pdf("Redação e Leitura") == "semanal"

    # Quinzenal para Arte e demais
    assert _frequencia_dia_sem_pdf("Arte") == "quinzenal"
    assert _frequencia_dia_sem_pdf("Biologia") == "quinzenal"
    assert _frequencia_dia_sem_pdf("Geografia") == "quinzenal"
    assert _frequencia_dia_sem_pdf("História") == "quinzenal"
    assert _frequencia_dia_sem_pdf("Física") == "quinzenal"
    assert _frequencia_dia_sem_pdf("Química") == "quinzenal"


def test_eh_data_sem_pdf_semanal_vs_quinzenal():
    segundas = [
        date(2026, 9, 7),   # Seg 1 (índice 0)
        date(2026, 9, 14),  # Seg 2 (índice 1)
        date(2026, 9, 21),  # Seg 3 (índice 2)
        date(2026, 9, 28),  # Seg 4 (índice 3)
    ]
    segunda_weekday = 0  # Segunda-feira = 0

    # Teste semanal (Português, Matemática, etc.): todas as segundas ficam sem PDF
    for d in segundas:
        assert _eh_data_sem_pdf(d, segunda_weekday, datas_agenda=segundas, frequencia="semanal") is True

    # Teste quinzenal (Arte, Biologia, etc.): apenas segundas alternadas (a cada 15 dias: 1ª e 3ª) ficam sem PDF
    assert _eh_data_sem_pdf(segundas[0], segunda_weekday, datas_agenda=segundas, frequencia="quinzenal") is True
    assert _eh_data_sem_pdf(segundas[1], segunda_weekday, datas_agenda=segundas, frequencia="quinzenal") is False
    assert _eh_data_sem_pdf(segundas[2], segunda_weekday, datas_agenda=segundas, frequencia="quinzenal") is True
    assert _eh_data_sem_pdf(segundas[3], segunda_weekday, datas_agenda=segundas, frequencia="quinzenal") is False
