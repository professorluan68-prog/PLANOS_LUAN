import sys
from pathlib import Path

path = Path("core/lote.py")
content = path.read_text(encoding="utf-8")

start_str = "def _aula_por_pdf("
end_str = "def processar_varios_pdfs("

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx == -1 or end_idx == -1:
    print("Error: string not found")
    sys.exit(1)

new_func = """def _aula_por_pdf(
    caminho_pdf: str,
    disciplina: str,
    turma: str,
    bimestre: str,
    usar_ia: bool,
    provedor_ia: str,
    modelo_ia: str = "",
    indice_aula: int = 0,
    total_aulas: int = 1,
    modalidade_eja: bool = False,
) -> dict:
    hash_atual = ""
    if caminho_pdf:
        try:
            from core.revisao_final import calcular_sha256
            hash_atual = calcular_sha256(caminho_pdf)
        except Exception:
            pass

    # Verificar cache JSON pré-gerado
    if caminho_pdf:
        try:
            import json
            from pathlib import Path
            caminho_json = Path(caminho_pdf).with_suffix(".json")
            if caminho_json.exists():
                with open(caminho_json, "r", encoding="utf-8") as f:
                    dados_json = json.load(f)
                if isinstance(dados_json, dict) and "metodologia" in dados_json:
                    hash_salvo = dados_json.get("hash_pdf")
                    if hash_salvo and hash_atual and hash_salvo != hash_atual:
                        # Ignorar cache inválido por alteração do arquivo PDF
                        pass
                    else:
                        aula_gerada = {
                            "disciplina": dados_json.get("disciplina") or disciplina,
                            "tema": dados_json.get("tema") or "",
                            "material": dados_json.get("material") or Path(caminho_pdf).name,
                            "numero_aula": dados_json.get("numero_aula") or "",
                            "aprendizagem": dados_json.get("aprendizagem") or "",
                            "metodologia": dados_json["metodologia"],
                            "acompanhamento": dados_json.get("acompanhamento") or [],
                            "acessibilidade": dados_json.get("acessibilidade") or [],
                            "ia_usada": dados_json.get("ia_usada", False),
                            "ia_provedor": dados_json.get("ia_provedor", ""),
                            "ia_erro": dados_json.get("ia_erro", ""),
                            # Campos extras da auditoria
                            "hash_pdf": hash_salvo or hash_atual,
                            "confidence_score": dados_json.get("confidence_score", 100),
                            "avisos_validacao": dados_json.get("avisos_validacao") or [],
                        }
                        if "avisos_validacao" not in dados_json:
                            aula_gerada["avisos_validacao"] = validar_aula_final(aula_gerada)
                        return aula_gerada
        except Exception:
            pass

    contexto = _preparar_contexto_aula_pdf(
        caminho_pdf=caminho_pdf,
        disciplina=disciplina,
        turma=turma,
        bimestre=bimestre,
        indice_aula=indice_aula,
        modalidade_eja=modalidade_eja,
    )
    texto = contexto["texto"]
    tema = contexto["tema"]
    material_digital = contexto["material_digital"]
    numero_aula = contexto["numero_aula"]
    cdp_contextual = contexto["cdp_contextual"]
    disciplina_base = contexto["disciplina_base"]
    perfil = contexto["perfil"]
    objetivos_orientacao = contexto["objetivos_orientacao"]
    aprendizagem_orientacao = contexto["aprendizagem_orientacao"]
    extracao_pdf = contexto["extracao_pdf"]
    tipo = contexto["tipo"]
    metodologia_fixa_pdf = contexto["metodologia_fixa_pdf"]
    modalidade_eja_ativa = contexto["modalidade_eja_ativa"]
    contexto_metodologico = contexto["contexto_metodologico"]
    escopo_pv = contexto["escopo_pv"]
    aprendizagem_pv = contexto["aprendizagem_pv"]

    resultado_final = None

    if cdp_contextual:
        resultado_final = _montar_resultado_cdp_contextual(
            texto=texto,
            tema=tema,
            disciplina_base=disciplina_base,
            numero_aula=numero_aula,
            indice_aula=indice_aula,
            perfil=perfil,
            tipo=tipo,
            extracao_pdf=extracao_pdf,
        )
    else:
        ia_erro = ""

        if usar_ia:
            try:
                from core.ia import processar_plano_ia

                plano_ia = processar_plano_ia(texto, disciplina, turma, provedor_ia, modelo_ia, modalidade_eja=modalidade_eja_ativa)
                tema_ia = tema if escopo_pv.get("titulo") else plano_ia.get("tema") or tema
                resultado_final = _montar_resultado_aula_ia(
                    texto=texto,
                    tema=tema_ia,
                    material_digital=material_digital,
                    numero_aula=numero_aula,
                    disciplina_base=disciplina_base,
                    turma=turma,
                    provedor_ia=provedor_ia,
                    perfil=perfil,
                    contexto_metodologico=contexto_metodologico,
                    indice_aula=indice_aula,
                    total_aulas=total_aulas,
                    modalidade_eja_ativa=modalidade_eja_ativa,
                    plano_ia=plano_ia,
                    metodologia_fixa_pdf=metodologia_fixa_pdf,
                    aprendizagem_pv=aprendizagem_pv,
                    objetivos_orientacao=objetivos_orientacao,
                    aprendizagem_orientacao=aprendizagem_orientacao,
                )
            except Exception as e:
                ia_erro = f"Falha na IA ({provedor_ia}): {str(e)[:150]}. Usando motor heurístico local."

        if resultado_final is None:
            resultado_final = _montar_resultado_aula_local(
                texto=texto,
                tema=tema,
                material_digital=material_digital,
                numero_aula=numero_aula,
                disciplina_base=disciplina_base,
                turma=turma,
                provedor_ia=provedor_ia,
                perfil=perfil,
                contexto_metodologico=contexto_metodologico,
                indice_aula=indice_aula,
                total_aulas=total_aulas,
                modalidade_eja_ativa=modalidade_eja_ativa,
                metodologia_fixa_pdf=metodologia_fixa_pdf,
                aprendizagem_pv=aprendizagem_pv,
                objetivos_orientacao=objetivos_orientacao,
                aprendizagem_orientacao=aprendizagem_orientacao,
                usar_ia=usar_ia,
                ia_erro=ia_erro,
            )

    try:
        from core.revisao_final import revisar_aula_gerada, gravar_sidecar_json
        resultado_final = revisar_aula_gerada(resultado_final, perfil)
        if caminho_pdf and hash_atual:
            gravar_sidecar_json(caminho_pdf, resultado_final, hash_atual)
    except Exception:
        pass

    return resultado_final


"""

new_content = content[:start_idx] + new_func + content[end_idx:]
path.write_text(new_content, encoding="utf-8")
print("Replacement successful!")
