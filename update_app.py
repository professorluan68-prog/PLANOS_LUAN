import pathlib
path = pathlib.Path(r'd:\PLANOS_LUAN\planos_luan_app.py')
content = path.read_text('utf-8')

content = content.replace(
'''def _gerar_docx_final(
    modelo_bytes: bytes,
    aulas,
    professor: str,
    disciplina: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    observacao: str,
    aulas_previstas_manual: str,
):''', '''def _gerar_docx_final(
    modelo_bytes: bytes,
    aulas,
    escola: str,
    professor: str,
    disciplina: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    semana: str,
    observacao: str,
    aulas_previstas_manual: str,
):''')

content = content.replace(
'''    docx_bytes = preencher_documento(
        BytesIO(modelo_bytes),
        aulas,
        professor,
        disciplina,
        turma_atual,
        mes,
        bimestre,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )''', '''    docx_bytes = preencher_documento(
        BytesIO(modelo_bytes),
        aulas,
        escola=escola,
        professor=professor,
        disciplina=disciplina,
        turma=turma_atual,
        mes=mes,
        bimestre=bimestre,
        semana=semana,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )''')


content = content.replace(
'''def _gerar_docx_cdp_final(
    modelo_bytes: bytes,
    professor: str,
    disciplina: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    observacao: str,
    aulas_previstas_manual: str,
    cdp_aula_inicial: int,
    turma_cdp: str = "",
):''', '''def _gerar_docx_cdp_final(
    modelo_bytes: bytes,
    escola: str,
    professor: str,
    disciplina: str,
    turma_atual: str,
    mes: str,
    bimestre: str,
    semana: str,
    observacao: str,
    aulas_previstas_manual: str,
    cdp_aula_inicial: int,
    turma_cdp: str = "",
):''')

content = content.replace(
'''    docx_bytes = preencher_documento_cdp(
        BytesIO(modelo_bytes),
        professor,
        turma_atual,
        mes,
        bimestre,
        int(cdp_aula_inicial or 1),
        fundamental=eh_cdp_fundamental(disciplina),
        multisseriada=eh_cdp_multisseriada(disciplina),
        serie_cdp=turma_cdp if eh_cdp_multisseriada(disciplina) else "",
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )''', '''    docx_bytes = preencher_documento_cdp(
        BytesIO(modelo_bytes),
        escola=escola,
        professor=professor,
        turma=turma_atual,
        mes=mes,
        bimestre=bimestre,
        aula_inicial=int(cdp_aula_inicial or 1),
        fundamental=eh_cdp_fundamental(disciplina),
        multisseriada=eh_cdp_multisseriada(disciplina),
        serie_cdp=turma_cdp if eh_cdp_multisseriada(disciplina) else "",
        semana=semana,
        observacao=observacao,
        aulas_previstas_manual=aulas_previstas_manual,
    )''')


content = content.replace(
'''observacao = st.text_area(
    "Observação",
    placeholder="Opcional: acrescente orientações específicas para o campo de observações do plano.",
    height=90,
    key="observacao",
)''', '''col_escola, col_semana = st.columns(2)
with col_escola:
    escola = st.text_input(
        "Escola",
        value="",
        placeholder="Ex.: Prof.ª EGLE LUPORINI COSTA",
        key="escola",
    )
with col_semana:
    semana = st.text_input(
        "Semana",
        value="",
        placeholder="Ex.: 04/05 a 08/05",
        key="semana",
    )

observacao = st.text_area(
    "Observação",
    placeholder="Opcional: acrescente orientações específicas para o campo de observações do plano.",
    height=90,
    key="observacao",
)''')

content = content.replace(
'''                    planos_gerados.append(
                        _gerar_docx_cdp_final(
                            modelo_bytes=modelo_bytes,
                            professor=professor,
                            disciplina=disciplina,
                            turma_atual=turma_atual,
                            mes=mes,
                            bimestre=bimestre,
                            observacao=observacao,
                            aulas_previstas_manual=aulas_previstas_manual,
                            cdp_aula_inicial=cdp_aula_inicial,
                            turma_cdp=turma_cdp,
                        )
                    )''', '''                    planos_gerados.append(
                        _gerar_docx_cdp_final(
                            modelo_bytes=modelo_bytes,
                            escola=escola,
                            professor=professor,
                            disciplina=disciplina,
                            turma_atual=turma_atual,
                            mes=mes,
                            bimestre=bimestre,
                            semana=semana,
                            observacao=observacao,
                            aulas_previstas_manual=aulas_previstas_manual,
                            cdp_aula_inicial=cdp_aula_inicial,
                            turma_cdp=turma_cdp,
                        )
                    )''')


content = content.replace(
'''            planos_gerados.append(
                _gerar_docx_final(
                    modelo_bytes=modelo_bytes,
                    aulas=turma_rev["aulas"],
                    professor=professor,
                    disciplina=disciplina,
                    turma_atual=turma_rev["turma"],
                    mes=mes,
                    bimestre=bimestre,
                    observacao=observacao,
                    aulas_previstas_manual=aulas_previstas_manual,
                )
            )''', '''            planos_gerados.append(
                _gerar_docx_final(
                    modelo_bytes=modelo_bytes,
                    aulas=turma_rev["aulas"],
                    escola=escola,
                    professor=professor,
                    disciplina=disciplina,
                    turma_atual=turma_rev["turma"],
                    mes=mes,
                    bimestre=bimestre,
                    semana=semana,
                    observacao=observacao,
                    aulas_previstas_manual=aulas_previstas_manual,
                )
            )''')

path.write_text(content, 'utf-8')
print('Replacement complete.')
