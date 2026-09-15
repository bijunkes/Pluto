import os

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
    Cookie,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.database.database import Database
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import validar_resultado_compra
from src.services.csv_import_service import (
    importar_csv,
    ImportacaoCSVError,
)
from src.services.financial_summary_service import FinancialSummaryService
from src.services.auth_service import (
    validar_token_login,
    validar_sessao,
    gerar_sessao,
    TokenInvalidoError,
    VALIDADE_SESSAO,
)
from src.api.schemas import (
    CompraCreate,
    CompraOut,
    CategoriaCreate,
    CategoriaOut,
    ContaCreate,
    ContaOut,
    ImportacaoCSVResultado,
    LoginToken,
    SessaoOut,
)

load_dotenv()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

NOME_COOKIE_SESSAO = "pluto_session"

DASHBOARD_URL = os.environ.get(
    "DASHBOARD_URL",
    "https://girdle-unstaffed-frequency.ngrok-free.dev",
)

COOKIE_SECURE = (
    os.environ.get("AMBIENTE", "producao") != "dev"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Pluto API",
    description="API do assistente financeiro Pluto",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[DASHBOARD_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def usuario_logado(
    pluto_session: str | None = Cookie(default=None),
):
    """
    Retorna o ID do usuário autenticado através
    do cookie de sessão.
    """

    if pluto_session is None:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login pelo bot.",
        )

    try:
        return validar_sessao(pluto_session)

    except TokenInvalidoError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )


def exigir_dono(
    usuario_id: int,
    usuario_autenticado: int = Depends(usuario_logado),
):
    """
    Garante que o usuário autenticado só consiga
    acessar os próprios dados.
    """

    if usuario_autenticado != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem acesso aos dados desse usuário.",
        )

    return usuario_autenticado


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _compra_para_dict(compra):
    """
    Converte o retorno do banco para o formato
    esperado pelo CompraOut.

    O banco retorna:

    (
        id,
        produto,
        categoria,
        conta,
        valor,
        data
    )
    """

    return {
        "id": compra[0],
        "produto": compra[1],
        "categoria": compra[2],
        "valor": float(compra[4]),
        "data": compra[5],
    }


def _categoria_para_dict(categoria):
    """
    Converte o retorno do banco para CategoriaOut.
    """

    return {
        "id": categoria[0],
        "nome": categoria[1],
    }


def _conta_para_dict(conta):
    """
    Converte o retorno do banco para ContaOut.

    O banco retorna:

    (
        id,
        nome,
        tipo,
        saldo,
        criada_em,
        ativa
    )
    """

    return {
        "id": conta[0],
        "nome": conta[1],
        "tipo": conta[2],
        "saldo": float(conta[3]),
        "ativa": conta[5],
    }


# ============================================================
# AUTENTICAÇÃO
# ============================================================

@app.post(
    "/auth/sessao",
    response_model=SessaoOut,
)
def login(
    dados: LoginToken,
    response: Response,
):
    """
    Recebe o token enviado pelo bot e cria uma sessão.
    """

    try:
        usuario_id = validar_token_login(dados.token)

    except TokenInvalidoError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    sessao = gerar_sessao(usuario_id)

    response.set_cookie(
        key=NOME_COOKIE_SESSAO,
        value=sessao,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=VALIDADE_SESSAO,
        path="/",
    )

    return {
        "usuario_id": usuario_id
    }


@app.get(
    "/auth/me",
    response_model=SessaoOut,
)
def usuario_atual(
    usuario_id: int = Depends(usuario_logado),
):
    """
    Retorna o usuário atualmente autenticado.
    """

    return {
        "usuario_id": usuario_id
    }


@app.post("/auth/logout")
def logout(response: Response):
    """
    Remove a sessão do usuário.
    """

    response.delete_cookie(
        key=NOME_COOKIE_SESSAO,
        path="/",
    )

    return {
        "status": "ok"
    }


# ============================================================
# CONTAS
# ============================================================

@app.get(
    "/usuarios/{usuario_id}/contas",
    response_model=list[ContaOut],
)
def listar_contas(
    usuario_id: int,
    _: int = Depends(exigir_dono),
):
    """
    Lista as contas ativas do usuário.
    """

    database = Database(usuario_id)

    contas = database.listar_contas()

    return [
        _conta_para_dict(conta)
        for conta in contas
    ]


@app.post(
    "/usuarios/{usuario_id}/contas",
    response_model=ContaOut,
    status_code=201,
)
def criar_conta(
    usuario_id: int,
    conta: ContaCreate,
    _: int = Depends(exigir_dono),
):
    """
    Cria uma nova conta para o usuário.
    """

    database = Database(usuario_id)

    try:

        conta_id = database.adicionar_conta(
            nome=conta.nome,
            tipo=conta.tipo,
            saldo=conta.saldoInicial,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    conta_criada = database.buscar_conta(
        conta_id
    )

    if conta_criada is None:
        raise HTTPException(
            status_code=404,
            detail="Conta criada, mas não encontrada.",
        )

    return _conta_para_dict(conta_criada)


# ============================================================
# COMPRAS
# ============================================================

@app.get(
    "/usuarios/{usuario_id}/compras",
    response_model=list[CompraOut],
)
def listar_compras(
    usuario_id: int,
    _: int = Depends(exigir_dono),
):
    """
    Lista as compras do usuário.
    """

    database = Database(usuario_id)

    compras = database.listar_compras()

    return [
        _compra_para_dict(compra)
        for compra in compras
    ]


@app.post(
    "/usuarios/{usuario_id}/compras",
    response_model=CompraOut,
    status_code=201,
)
def criar_compra(
    usuario_id: int,
    compra: CompraCreate,
    _: int = Depends(exigir_dono),
):
    """
    Cria uma compra manualmente pelo dashboard.

    A compra obrigatoriamente pertence a uma conta.
    """

    database = Database(usuario_id)

    try:

        # Enviamos somente os dados esperados
        # pelo validador da compra.
        dados_compra = {
            "produto": compra.produto,
            "categoria": compra.categoria,
            "valor": compra.valor,
        }

        resultado = validar_resultado_compra(
            dados_compra,
            database.listar_nomes_categorias(),
        )

        compra_id = database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            conta_id=compra.contaId,
            valor=resultado["valor"],
        )

    except AnaliseIAError as e:

        raise HTTPException(
            status_code=422,
            detail=str(e),
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    compra_criada = database.buscar_compra(
        compra_id
    )

    if compra_criada is None:
        raise HTTPException(
            status_code=404,
            detail="Compra criada, mas não encontrada.",
        )

    return _compra_para_dict(compra_criada)


# ============================================================
# CATEGORIAS
# ============================================================

@app.get(
    "/usuarios/{usuario_id}/categorias",
    response_model=list[CategoriaOut],
)
def listar_categorias(
    usuario_id: int,
    _: int = Depends(exigir_dono),
):
    """
    Lista as categorias do usuário.
    """

    database = Database(usuario_id)

    categorias = database.listar_categorias()

    return [
        _categoria_para_dict(categoria)
        for categoria in categorias
    ]


@app.post(
    "/usuarios/{usuario_id}/categorias",
    response_model=CategoriaOut,
    status_code=201,
)
def criar_categoria(
    usuario_id: int,
    categoria: CategoriaCreate,
    _: int = Depends(exigir_dono),
):
    """
    Cria uma nova categoria.
    """

    database = Database(usuario_id)

    try:

        database.adicionar_categoria(
            categoria.nome
        )

    except ValueError as e:

        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    categorias = database.listar_categorias()

    criada = next(
        (
            c
            for c in categorias
            if c[1] == categoria.nome
        ),
        None,
    )

    if criada is None:
        raise HTTPException(
            status_code=404,
            detail="Categoria criada, mas não encontrada.",
        )

    return _categoria_para_dict(criada)


# ============================================================
# RESUMO FINANCEIRO
# ============================================================

@app.get("/usuarios/{usuario_id}/resumo-financeiro")
def obter_resumo_financeiro(
    usuario_id: int,
    _: int = Depends(exigir_dono),
):
    """Retorna os indicadores financeiros do mês atual."""

    return FinancialSummaryService(Database(usuario_id)).calcular_resumo_mensal()


# ============================================================
# IMPORTAÇÃO CSV
# ============================================================

@app.post(
    "/usuarios/{usuario_id}/compras/importar-csv",
    response_model=ImportacaoCSVResultado,
)
def importar_compras_csv(
    usuario_id: int,
    arquivo: UploadFile = File(...),
    _: int = Depends(exigir_dono),
):
    """
    Importa compras através de um arquivo CSV.
    """

    database = Database(usuario_id)

    caminho_temporario = None

    try:

        import tempfile

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".csv",
        ) as arquivo_temporario:

            arquivo_temporario.write(
                arquivo.file.read()
            )

            caminho_temporario = (
                arquivo_temporario.name
            )

        resultado = importar_csv(
            caminho_temporario,
            database,
        )

        return resultado

    except ImportacaoCSVError as e:

        raise HTTPException(
            status_code=422,
            detail=str(e),
        )

    finally:

        if caminho_temporario:

            try:
                os.remove(caminho_temporario)

            except OSError:
                pass


# ============================================================
# SAÚDE DA API
# ============================================================

@app.get("/usuarios/{usuario_id}/saude")
def verificar_saude(
    usuario_id: int,
    _: int = Depends(exigir_dono),
):
    """
    Verifica se a API e o banco estão acessíveis.
    """

    try:

        database = Database(usuario_id)

        # Apenas cria a conexão para verificar
        # se o banco está acessível.
        with database.conectar():
            pass

        return {
            "status": "ok"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao acessar o banco: {str(e)}",
        )


# ============================================================
# DASHBOARD
# ============================================================

if os.path.isdir("dashboard"):

    app.mount(
        "/",
        StaticFiles(
            directory="dashboard",
            html=True,
        ),
        name="dashboard",
    )
