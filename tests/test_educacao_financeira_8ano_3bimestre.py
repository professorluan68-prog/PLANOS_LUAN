from pathlib import Path

from docx import Document

from core.educacao_financeira_validacao import validar_requisitos_educacao_financeira
from core.helpers import resolver_pasta_pdfs
from core.referencias_educacao_financeira import localizar_docx_referencia


def _criar_referencia(caminho: Path, titulo: str = "Orçamento doméstico") -> None:
    doc = Document()
    doc.add_paragraph(f"AULA 1 - {titulo}")
    doc.add_paragraph("Metodologia")
    doc.add_paragraph("Para começar: Retomar receitas e despesas do orçamento doméstico.")
    doc.add_paragraph("Foco no conteúdo: Orientar a leitura da planilha de gastos.")
    doc.add_paragraph("Na prática: Organizar prioridades e reserva financeira.")
    doc.add_paragraph("Encerramento: Socializar critérios de economia doméstica.")
    doc.add_paragraph("Acompanhamento da aprendizagem")
    doc.add_paragraph("☑ Observar se os estudantes identificam receitas e despesas.")
    doc.add_paragraph("☑ Verificar os registros feitos na planilha de gastos.")
    doc.add_paragraph("☑ Conferir as justificativas para a reserva financeira.")
    doc.add_paragraph("Acessibilidade")
    doc.add_paragraph("☑ Disponibilizar tabela de apoio para receitas e despesas.")
    doc.add_paragraph("☑ Oferecer roteiro com perguntas orientadoras em frases curtas.")
    doc.add_paragraph("☑ Permitir resposta oral antes do registro guiado.")
    doc.save(caminho)


def test_8_ano_corrigido_tem_prioridade_exata(tmp_path):
    esperado = tmp_path / "Metodologias_Educacao_Financeira_8_Ano_CORRIGIDO.docx"
    concorrente = tmp_path / "Metodologias_Educacao_Financeira_8_Ano_ATUALIZADO.docx"
    pdf = tmp_path / "AULA 1.pdf"
    _criar_referencia(esperado)
    _criar_referencia(concorrente, titulo="Título concorrente")
    pdf.write_bytes(b"%PDF-1.4\n")

    assert localizar_docx_referencia(pdf) == esperado


def test_validacao_financeira_aceita_tres_itens_concretos():
    aula = {
        "disciplina": "Educação Financeira",
        "acompanhamento": [
            "☑ Observar se os estudantes identificam receitas e despesas.",
            "☑ Verificar os registros na planilha de gastos.",
            "☑ Conferir as justificativas para a reserva financeira.",
        ],
        "acessibilidade": [
            "☑ Disponibilizar tabela de apoio para receitas e despesas.",
            "☑ Oferecer roteiro com perguntas orientadoras.",
            "☑ Permitir resposta oral antes do registro guiado.",
        ],
    }

    assert validar_requisitos_educacao_financeira(aula) == []


def test_validacao_financeira_rejeita_item_sem_check_verbo_ou_apoio():
    aula = {
        "disciplina": "Educação Financeira",
        "acompanhamento": [
            "Acompanhar a turma.",
            "☑ Ideias dos estudantes.",
        ],
        "acessibilidade": [
            "☑ Apoiar a turma.",
            "☑ Material adaptado.",
        ],
    }

    problemas = validar_requisitos_educacao_financeira(aula)

    assert any("exatamente 3" in problema for problema in problemas)
    assert any("iniciar com ☑" in problema for problema in problemas)


def test_resolvedor_automatico_monta_pasta_8_ano_3_bimestre(tmp_path):
    caminho = resolver_pasta_pdfs(
        str(tmp_path / "PDF novos"),
        "Educação Financeira",
        "8º ANO",
        "3º BIMESTRE",
    )

    assert caminho == tmp_path / "PDF novos" / "EDUCACAO_FINANCEIRA" / "AF" / "3_BIMESTRE" / "8_ANO"
