from pydantic import BaseModel, Field


class CompraCreate(BaseModel):
    """
    Dados necessários para registrar uma compra manualmente
    (usado pelo dashboard web, sem passar pela IA).
    """

    produto: str = Field(..., min_length=1)
    categoria: str = Field(..., min_length=1)
    valor: float = Field(..., ge=0)


class CompraOut(BaseModel):

    id: int
    produto: str
    categoria: str
    valor: float
    data: str


class CategoriaCreate(BaseModel):

    nome: str = Field(..., min_length=1)


class CategoriaOut(BaseModel):

    id: int
    nome: str


class ImportacaoCSVErro(BaseModel):

    linha: int
    motivo: str


class ImportacaoCSVResultado(BaseModel):

    total_linhas: int
    inseridas: int
    erros: list[ImportacaoCSVErro]


class LoginToken(BaseModel):
    """
    Corpo enviado pelo dashboard ao trocar o token do link mágico
    (recebido do bot) por uma sessão autenticada.
    """

    token: str = Field(..., min_length=1)


class SessaoOut(BaseModel):
    """
    Retornado depois de um login (ou consulta de sessão) bem
    sucedido, identificando o usuário do Telegram autenticado.
    """

    usuario_id: int
