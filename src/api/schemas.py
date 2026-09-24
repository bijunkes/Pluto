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
    conta: str
    valor: float
    data: datetime


class CompraUpdate(BaseModel):
    """
    Dados para editar uma compra existente.
    Todos os campos são opcionais.
    """

    produto: str | None = Field(default=None, min_length=1)
    categoria: str | None = Field(default=None, min_length=1)
    contaId: int | None = Field(default=None, gt=0)
    valor: float | None = Field(default=None, ge=0)


# ============================================================
# CATEGORIAS
# ============================================================

class CategoriaCreate(BaseModel):

    nome: str = Field(..., min_length=1)


class CategoriaOut(BaseModel):

    id: int
    nome: str


class CategoriaUpdate(BaseModel):

    nome: str = Field(..., min_length=1)


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


class ContaUpdate(BaseModel):
    """
    Dados para atualizar uma conta existente.
    Ambos os campos são opcionais.
    """

    nome: str | None = Field(default=None, min_length=1)
    tipo: str | None = Field(default=None, min_length=1)


class MovimentacaoSaldo(BaseModel):
    """
    Depósito ou retirada manual de saldo de uma conta.
    """

    valor: float = Field(..., gt=0)


class TransferenciaSaldo(BaseModel):

    contaDestinoId: int = Field(..., gt=0)
    valor: float = Field(..., gt=0)


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


# ============================================================
# INSIGHTS
# ============================================================

class InsightOut(BaseModel):

    id: str
    type: str
    title: str
    description: str