from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - compatibilidade com Pydantic v1
    ConfigDict = None


def _model_dump(objeto: BaseModel) -> dict[str, Any]:
    if hasattr(objeto, "model_dump"):
        return objeto.model_dump()
    return objeto.dict()


def _model_validate(modelo: type[BaseModel], dados: Any) -> BaseModel:
    if isinstance(dados, modelo):
        return dados
    if isinstance(dados, BaseModel):
        dados = _model_dump(dados)
    dados = dados or {}
    if hasattr(modelo, "model_validate"):
        return modelo.model_validate(dados)
    return modelo.parse_obj(dados)


def _normalizar_valor(valor: Any) -> Any:
    if isinstance(valor, BaseModel):
        return {
            chave: _normalizar_valor(item)
            for chave, item in _model_dump(valor).items()
        }
    if isinstance(valor, list):
        return [_normalizar_valor(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: _normalizar_valor(item) for chave, item in valor.items()}
    return valor


class ModeloPlanoBase(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover - compatibilidade com Pydantic v1
        class Config:
            extra = "allow"

    @classmethod
    def from_any(cls, dados: Any):
        return _model_validate(cls, dados)

    def to_dict(self) -> dict[str, Any]:
        return _normalizar_valor(_model_dump(self))


class ModeloIABase(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:  # pragma: no cover - compatibilidade com Pydantic v1
        class Config:
            extra = "forbid"

    @classmethod
    def from_any(cls, dados: Any):
        return _model_validate(cls, dados)

    def to_dict(self) -> dict[str, Any]:
        return _normalizar_valor(_model_dump(self))


class EtapaMetodologia(ModeloIABase):
    titulo: str = Field(
        description="Titulo da etapa, como Relembre, Foco no conteudo, Na pratica ou Encerramento.",
    )
    texto: str = Field(
        description="Texto descritivo da ação do professor. DEVE TER ENTRE 150 E 200 PALAVRAS no máximo (cerca de 1200 caracteres). JAMAIS escreva textos exaustivos ou longos. Seja objetivo e conciso.",
    )


class PlanoAulaIA(ModeloIABase):
    tema: str = Field(
        description="Conceito central da aula, sem rotulos administrativos como AULA 1 ou bimestre.",
    )
    aprendizagem: str = Field(
        description="Aprendizagem essencial e/ou codigo da BNCC encontrado no slide.",
    )
    metodologia: list[EtapaMetodologia] = Field(
        description="Etapas de desenvolvimento da aula.",
    )
    acompanhamento: list[str] = Field(
        description="Lista com exatamente 3 itens curtos de acompanhamento da aprendizagem, focados na aula.",
    )
    acessibilidade: list[str] = Field(
        description="Lista com exatamente 3 itens curtos de acessibilidade/adaptacoes para necessidades especiais, focados na aula.",
    )


class PlanoCompleto(ModeloPlanoBase):
    disciplina: str = ""
    tema: str = ""
    material: str = ""
    numero_aula: str = ""
    aprendizagem: str = ""
    metodologia: list[EtapaMetodologia | str] = Field(default_factory=list)
    acompanhamento: list[str] = Field(default_factory=list)
    acessibilidade: list[str] = Field(default_factory=list)
    conteudo: str = ""
    data: Any = None
    horario: str = ""
    ia_usada: bool = False
    ia_provedor: str = ""
    ia_erro: str = ""
    fonte_extracao: str = "pdf"
    arquivo_fonte_extracao: str = ""
    hash_fonte_extracao: str = ""
    fonte_principal: str = ""
    arquivo_fonte: str = ""
    cache_reutilizado: bool = False
    origem_metodologia: str = ""
    fonte_referencia_metodologia: str = ""
    perfil_metodologico: str = ""
    versao_prompt: str = ""
    etapas_detectadas: list[str] = Field(default_factory=list)
    hash_pdf: str = ""
    confidence_score: int = 100
    avisos_validacao: list[str] = Field(default_factory=list)
    versao_gerador: str = ""
    perfil: str = ""
    fingerprint_contexto: str = ""
    recursos_detectados: list[str] = Field(default_factory=list)
    texto_fonte: str = ""
    diagnostico_geracao: dict[str, Any] = Field(default_factory=dict)
    palavras_chave_esperadas: list[str] = Field(default_factory=list)
    caminho_docx_auxiliar: str | None = None
    valido_palavras_chave: bool = True
    cobertura_palavras_chave: float = 100.0
    palavras_chave_encontradas: list[str] = Field(default_factory=list)
    palavras_chave_ausentes: list[str] = Field(default_factory=list)

    @classmethod
    def from_any(cls, dados: Any):
        if isinstance(dados, cls):
            return dados
        if isinstance(dados, BaseModel):
            dados = _model_dump(dados)
        dados = dict(dados or {})
        recursos = dados.get("recursos_detectados")
        if isinstance(recursos, dict):
            dados["recursos_detectados"] = [
                str(nome).strip()
                for nome, presente in recursos.items()
                if presente and str(nome).strip()
            ]
        elif recursos is None:
            dados["recursos_detectados"] = []
            
        metodologia_bruta = dados.get("metodologia")
        if isinstance(metodologia_bruta, list):
            metodologia_limpa = []
            for item in metodologia_bruta:
                if isinstance(item, str):
                    texto = item.strip()
                    if texto:
                        metodologia_limpa.append(texto)
                elif hasattr(item, "model_dump"):
                    metodologia_limpa.append(item.model_dump())
                elif hasattr(item, "dict"):
                    metodologia_limpa.append(item.dict())
                elif isinstance(item, dict):
                    metodologia_limpa.append(item)
            dados["metodologia"] = metodologia_limpa
            
        return _model_validate(cls, dados)

    def etapas_metodologia(self) -> list[str]:
        etapas = []
        for item in self.metodologia:
            if isinstance(item, EtapaMetodologia):
                titulo = str(item.titulo or "").strip()
            elif isinstance(item, dict):
                titulo = str(item.get("titulo") or "").strip()
            else:
                titulo = ""
            if titulo:
                etapas.append(titulo)
        return etapas

    def to_sidecar_dict(
        self,
        caminho_pdf: str | Path,
        hash_pdf: str,
        normalizar_caminho: Callable[[Any], str],
    ) -> dict[str, Any]:
        dados = self.to_dict()
        caminho_pdf = Path(caminho_pdf)
        return {
            "disciplina": dados.get("disciplina") or "",
            "tema": dados.get("tema") or "",
            "material": dados.get("material") or caminho_pdf.name,
            "numero_aula": dados.get("numero_aula") or "",
            "aprendizagem": dados.get("aprendizagem") or "",
            "metodologia": dados.get("metodologia") or [],
            "acompanhamento": dados.get("acompanhamento") or [],
            "acessibilidade": dados.get("acessibilidade") or [],
            "ia_usada": bool(dados.get("ia_usada", False)),
            "ia_provedor": dados.get("ia_provedor") or "",
            "ia_erro": dados.get("ia_erro") or "",
            "fonte_extracao": dados.get("fonte_extracao") or "pdf",
            "arquivo_fonte_extracao": normalizar_caminho(
                dados.get("arquivo_fonte_extracao") or caminho_pdf
            ),
            "hash_fonte_extracao": dados.get("hash_fonte_extracao") or hash_pdf,
            "fonte_principal": dados.get("fonte_principal")
            or dados.get("fonte_extracao")
            or "pdf",
            "arquivo_fonte": normalizar_caminho(
                dados.get("arquivo_fonte")
                or dados.get("arquivo_fonte_extracao")
                or caminho_pdf
            ),
            "cache_reutilizado": bool(dados.get("cache_reutilizado", False)),
            "origem_metodologia": dados.get("origem_metodologia") or "",
            "fonte_referencia_metodologia": normalizar_caminho(
                dados.get("fonte_referencia_metodologia") or ""
            ),
            "perfil_metodologico": dados.get("perfil_metodologico") or "",
            "versao_prompt": dados.get("versao_prompt") or "",
            "etapas_detectadas": dados.get("etapas_detectadas") or self.etapas_metodologia(),
            "hash_pdf": hash_pdf,
            "confidence_score": int(dados.get("confidence_score", 100) or 100),
            "avisos_validacao": dados.get("avisos_validacao") or [],
            "versao_gerador": dados.get("versao_gerador") or "",
            "perfil": dados.get("perfil") or "",
            "fingerprint_contexto": dados.get("fingerprint_contexto") or "",
            "recursos_detectados": dados.get("recursos_detectados") or [],
            "texto_fonte": dados.get("texto_fonte") or "",
            "diagnostico_geracao": dados.get("diagnostico_geracao") or {},
            "palavras_chave_esperadas": dados.get("palavras_chave_esperadas") or [],
            "caminho_docx_auxiliar": dados.get("caminho_docx_auxiliar"),
            "valido_palavras_chave": bool(dados.get("valido_palavras_chave", True)),
            "cobertura_palavras_chave": float(dados.get("cobertura_palavras_chave", 100.0)),
            "palavras_chave_encontradas": dados.get("palavras_chave_encontradas") or [],
            "palavras_chave_ausentes": dados.get("palavras_chave_ausentes") or [],
        }
