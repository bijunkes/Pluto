from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================
# COMPRAS
# ============================================================

class CompraCreate(BaseModel):
    """
    Dados necessários para registrar uma compra manualmente
    pelo dashboard.
    """

    produto: str = Field(..., min_length=1)
    categoria: str = Field(..., min_length=1)
    valor: float = Field(..., ge=0)
    contaId: int = Field(..., gt=0)


class CompraOut(BaseModel):

    id: int
    produto: str
    categoria: str
    valor: float
    data: datetime


# ============================================================
# CATEGORIAS
# ============================================================

class CategoriaCreate(BaseModel):

    nome: str = Field(..., min_length=1)


class CategoriaOut(BaseModel):

    id: int
    nome: str


# ============================================================
# CONTAS
# ============================================================

class ContaCreate(BaseModel):
    """
    Dados necessários para criar uma conta.
    """

    nome: str = Field(..., min_length=1)
    tipo: str = Field(..., min_length=1)
    saldoInicial: float = Field(default=0, ge=0)


class ContaOut(BaseModel):

    id: int
    nome: str
    tipo: str
    saldo: float
    ativa: bool


# ============================================================
# IMPORTAÇÃO CSV
# ============================================================

class ImportacaoCSVErro(BaseModel):

    linha: int
    motivo: str


class ImportacaoCSVResultado(BaseModel):

    total_linhas: int
    inseridas: int
    erros: list[ImportacaoCSVErro]


# ============================================================
# AUTENTICAÇÃO
# ============================================================

class LoginToken(BaseModel):
    """
    Corpo enviado pelo dashboard ao trocar o token do link mágico
    recebido pelo bot por uma sessão autenticada.
    """

    token: str = Field(..., min_length=1)


class SessaoOut(BaseModel):
    """
    Identifica o usuário do Telegram autenticado.
    """

    usuario_id: int