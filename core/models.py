from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Annotated

from pydantic import BaseModel, Field, field_validator

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


_MARCADOR_LISTA_RE = re.compile(r"^\s*(?:[•▪◦*-]|\d+[.)])\s*")
_SEPARADOR_ITENS_RE = re.compile(r"(?:\r?\n)+|(?=[•▪◦]\s+)|(?=☑\s+)")
_TITULO_ETAPA_RE = re.compile(
    r"(?m)^\s*(?:[•▪◦*-]\s*)?(?P<titulo>[^:\r\n]{2,80})\s*:\s*"
)


def _normalizar_lista_textual(valor: Any) -> list[str]:
    if valor is None:
        return []
    if isinstance(valor, str):
        itens_brutos = _SEPARADOR_ITENS_RE.split(valor)
    elif isinstance(valor, (list, tuple, set)):
        itens_brutos = list(valor)
    else:
        itens_brutos = [valor]

    itens: list[str] = []
    for item in itens_brutos:
        texto = str(item or "").strip()
        if not texto:
            continue
        texto = _MARCADOR_LISTA_RE.sub("", texto).strip()
        if texto:
            itens.append(texto)
    return itens


def _etapas_de_texto(texto_bruto: Any) -> list[dict[str, str]]:
    texto = str(texto_bruto or "").strip()
    if not texto:
        return []

    marcadores = list(_TITULO_ETAPA_RE.finditer(texto))
    if not marcadores:
        return [
            {"titulo": "Ação do Professor", "texto": bloco.strip()}
            for bloco in re.split(r"\r?\n\s*\r?\n", texto)
            if bloco.strip()
        ]

    etapas: list[dict[str, str]] = []
    introducao = texto[: marcadores[0].start()].strip()
    if introducao:
        etapas.append({"titulo": "Ação do Professor", "texto": introducao})

    for indice, marcador in enumerate(marcadores):
        inicio = marcador.end()
        fim = marcadores[indice + 1].start() if indice + 1 < len(marcadores) else len(texto)
        titulo = _MARCADOR_LISTA_RE.sub("", marcador.group("titulo")).strip()
        conteudo = texto[inicio:fim].strip()
        if conteudo:
            etapas.append(
                {
                    "titulo": titulo or "Ação do Professor",
                    "texto": conteudo,
                }
            )
    return etapas


def _normalizar_metodologia(valor: Any) -> list[dict[str, str]]:
    if valor is None:
        return []
    itens = valor if isinstance(valor, (list, tuple)) else [valor]
    etapas: list[dict[str, str]] = []
    for item in itens:
        if isinstance(item, str):
            etapas.extend(_etapas_de_texto(item))
            continue
        if isinstance(item, BaseModel):
            item = _model_dump(item)
        if not isinstance(item, dict):
            etapas.extend(_etapas_de_texto(item))
            continue
        titulo = str(item.get("titulo") or "Ação do Professor").strip()
        texto = str(item.get("texto") or "").strip()
        if texto:
            etapas.append(
                {
                    "titulo": titulo or "Ação do Professor",
                    "texto": texto,
                }
            )
    return etapas


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


TresItens = Annotated[list[str], Field(min_length=3, max_length=3)]


class EtapaMetodologia(ModeloIABase):
    titulo: str = Field(
        description="Titulo da etapa, como Relembre, Foco no conteudo, Na pratica ou Encerramento.",
    )
    texto: str = Field(
        description="Texto descritivo da ação do professor. DEVE TER ENTRE 150 E 200 PALAVRAS no máximo (cerca de 1200 caracteres). JAMAIS escreva textos exaustivos ou longos. Seja objetivo e claro."
    )


class EtapaMetodologiaIA(ModeloIABase):
    titulo: str = Field(
        min_length=2, max_length=80,
        description="Titulo da etapa, como Relembre, Foco no conteudo, Na pratica ou Encerramento.",
    )
    texto: str = Field(
        min_length=40, max_length=600,
        description="Texto descritivo da ação do professor. DEVE TER ENTRE 150 E 200 PALAVRAS no máximo (cerca de 1200 caracteres). JAMAIS escreva textos exaustivos ou longos. Seja objetivo e claro."
    )


class PlanoAulaIA(ModeloIABase):
    tema: str = Field(
        min_length=5, max_length=180,
        description="Conceito central da aula, sem rotulos administrativos como AULA 1 ou bimestre.",
    )
    aprendizagem: str = Field(
        min_length=20, max_length=1500,
        description="Aprendizagem essencial e/ou codigo da BNCC encontrado no slide.",
    )
    metodologia: list[EtapaMetodologiaIA] = Field(
        min_length=1, max_length=10,
        description="Etapas de desenvolvimento da aula.",
    )
    acompanhamento: TresItens = Field(
        description="Lista com exatamente 3 itens curtos de acompanhamento da aprendizagem, focados na aula.",
    )
    acessibilidade: TresItens = Field(
        description="Lista com exatamente 3 itens curtos de acessibilidade/adaptacoes para necessidades especiais, focados na aula.",
    )

    @field_validator("acompanhamento", "acessibilidade")
    @classmethod
    def itens_nao_vazios(cls, itens):
        if any(not item.strip() for item in itens):
            raise ValueError("Os itens não podem estar vazios")
        return [item.strip() for item in itens]



class PlanoCompleto(ModeloPlanoBase):
    disciplina: str = ""
    tema: str = ""
    material: str = ""
    numero_aula: str = ""
    aprendizagem: str = ""
    metodologia: list[EtapaMetodologia] = Field(default_factory=list)
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
    status_referencia_docx: str = ""
    arquivo_referencia_docx: str = ""
    motivo_referencia_docx: str = ""
    texto_central_copiado_literalmente: bool = False
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
    extracao_palavras_chave_ok: bool = True
    valido_palavras_chave: bool | None = None
    cobertura_palavras_chave: float = 100.0
    palavras_chave_encontradas: list[str] = Field(default_factory=list)
    palavras_chave_ausentes: list[str] = Field(default_factory=list)

    @field_validator("metodologia", mode="before")
    @classmethod
    def normalizar_metodologia_no_modelo(cls, valor: Any) -> list[dict[str, str]]:
        """Mantém o contrato list[dict] mesmo na construção direta do modelo."""
        return _normalizar_metodologia(valor)

    @field_validator("acompanhamento", "acessibilidade", mode="before")
    @classmethod
    def normalizar_listas_textuais_no_modelo(cls, valor: Any) -> list[str]:
        """Aceita texto ou listas legadas sem deixar strings soltas no plano."""
        return _normalizar_lista_textual(valor)

    @field_validator("recursos_detectados", mode="before")
    @classmethod
    def normalizar_recursos_no_modelo(cls, valor: Any) -> list[str]:
        if isinstance(valor, dict):
            return [
                str(nome).strip()
                for nome, presente in valor.items()
                if presente and str(nome).strip()
            ]
        return [str(item).strip() for item in (valor or []) if str(item).strip()]

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
            
        dados["metodologia"] = _normalizar_metodologia(dados.get("metodologia"))

        if not dados.get("acompanhamento") and dados.get("acompanhamento_aprendizagem"):
            dados["acompanhamento"] = dados.get("acompanhamento_aprendizagem")
        dados["acompanhamento"] = _normalizar_lista_textual(
            dados.get("acompanhamento")
        )
        dados["acessibilidade"] = _normalizar_lista_textual(
            dados.get("acessibilidade")
        )
            
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

        # Garantir que o campo 'metodologia' no sidecar é uma lista consistente de dicionários
        metodologia_raw = dados.get("metodologia") or []
        metodologia_serializada: list[dict[str, str]] = []
        for item in metodologia_raw:
            if isinstance(item, dict):
                titulo = str(item.get("titulo") or "").strip()
                texto = str(item.get("texto") or "").strip()
            else:
                # Pode ser string ou outro tipo; converte para texto
                titulo = "Ação do Professor"
                texto = str(item or "").strip()
            # manter itens vazios fora do sidecar
            if not titulo and not texto:
                continue
            metodologia_serializada.append({"titulo": titulo, "texto": texto})

        return {
            "disciplina": dados.get("disciplina") or "",
            "tema": dados.get("tema") or "",
            "material": dados.get("material") or caminho_pdf.name,
            "numero_aula": dados.get("numero_aula") or "",
            "aprendizagem": dados.get("aprendizagem") or "",
            "metodologia": metodologia_serializada,
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
            "status_referencia_docx": dados.get("status_referencia_docx") or "",
            "arquivo_referencia_docx": normalizar_caminho(
                dados.get("arquivo_referencia_docx") or ""
            ),
            "motivo_referencia_docx": dados.get("motivo_referencia_docx") or "",
            "texto_central_copiado_literalmente": bool(
                dados.get("texto_central_copiado_literalmente", False)
            ),
            "perfil_metodologico": dados.get("perfil_metodologico") or "",
            "versao_prompt": dados.get("versao_prompt") or "",
            "etapas_detectadas": dados.get("etapas_detectadas") or self.etapas_metodologia(),
            "hash_pdf": hash_pdf,
            "confidence_score": int(dados["confidence_score"]) if dados.get("confidence_score") is not None else 100,
            "avisos_validacao": dados.get("avisos_validacao") or [],
            "versao_gerador": dados.get("versao_gerador") or "",
            "perfil": dados.get("perfil") or "",
            "fingerprint_contexto": dados.get("fingerprint_contexto") or "",
            "recursos_detectados": dados.get("recursos_detectados") or [],
            "texto_fonte": dados.get("texto_fonte") or "",
            "diagnostico_geracao": dados.get("diagnostico_geracao") or {},
            "palavras_chave_esperadas": dados.get("palavras_chave_esperadas") or [],
            "caminho_docx_auxiliar": dados.get("caminho_docx_auxiliar"),
            "extracao_palavras_chave_ok": bool(
                dados.get("extracao_palavras_chave_ok", True)
            ),
            "valido_palavras_chave": bool(dados.get("valido_palavras_chave", True)),
            "cobertura_palavras_chave": float(dados.get("cobertura_palavras_chave", 100.0)),
            "palavras_chave_encontradas": dados.get("palavras_chave_encontradas") or [],
            "palavras_chave_ausentes": dados.get("palavras_chave_ausentes") or [],
        }
