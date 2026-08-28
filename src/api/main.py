import os
import tempfile

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
    Cookie,
    Response
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.database.database import Database
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import validar_resultado_compra
from src.services.csv_import_service import (
    importar_csv,
    ImportacaoCSVError
)
from src.services.auth_service import (
    validar_token_login,
    validar_sessao,
    gerar_sessao,
    TokenInvalidoError,
    VALIDADE_SESSAO
)
from src.api.schemas import (
    CompraCreate,
    CompraOut,
    CategoriaCreate,
    CategoriaOut,
    ImportacaoCSVResultado,
    LoginToken,
    SessaoOut
)

from dotenv import load_dotenv

load_dotenv()

# Nome do cookie que guarda a sessão do dashboard no navegador
NOME_COOKIE_SESSAO = "pluto_session"

# URL onde o dashboard web roda. Usada tanto pro CORS quanto,
# indiretamente, pelo bot (via auth_service) pra montar o link.
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://girdle-unstaffed-frequency.ngrok-free.dev")

# Em desenvolvimento local sem HTTPS, o cookie "Secure" não é
# gravado pelo navegador. Definir AMBIENTE=dev no .env pra desligar
# essa exigência localmente; em produção deixar como está (exige
# HTTPS, que é o correto).
COOKIE_SECURE = os.environ.get("AMBIENTE", "producao") != "dev"

app = FastAPI(
    title="Pluto API",
    description=(
        "Backend compartilhado entre o bot do Telegram e o dashboard web do Pluto."
    )
)

# Libera acesso do frontend do dashboard (rodando em outra origem).
# allow_origins precisa ser uma lista explícita (não "*") porque
# allow_credentials=True é o que permite o cookie de sessão viajar
# junto nas requisições do dashboard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[DASHBOARD_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def usuario_logado(
    pluto_session: str | None = Cookie(default=None)
):
    """
    Dependência que extrai e valida o usuário autenticado a partir
    do cookie de sessão. Toda rota que expõe dados de um usuário
    depende disso, direta ou indiretamente. Sem cookie válido,
    ninguém acessa `/usuarios/{id}/...`.
    """

    if pluto_session is None:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login pelo bot."
        )

    try:
        return validar_sessao(pluto_session)

    except TokenInvalidoError as e:
        raise HTTPException(status_code=401, detail=str(e))

def exigir_dono(
    usuario_id: int,
    usuario_autenticado: int = Depends(usuario_logado)
):
    """
    Garante que o usuário autenticado só acesse os próprios dados,
    mesmo que troque o usuario_id diretamente na URL. O FastAPI
    resolve o parâmetro `usuario_id` a partir do mesmo path
    parameter da rota que usa essa dependência.
    """

    if usuario_autenticado != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem acesso aos dados desse usuário."
        )

    return usuario_autenticado

def _compra_para_dict(compra):
    """
    Converte a tupla retornada por Database.listar_compras()
    (id, produto, categoria, valor, data) em um dicionário,
    já que a API responde em JSON.
    """

    return {
        "id": compra[0],
        "produto": compra[1],
        "categoria": compra[2],
        "valor": compra[3],
        "data": compra[4]
    }

def _categoria_para_dict(categoria):
    return {
        "id": categoria[0],
        "nome": categoria[1]
    }

@app.get(
    "/usuarios/{usuario_id}/compras",
    response_model=list[CompraOut]
)

def listar_compras(
    usuario_id: int,
    _: int = Depends(exigir_dono)
):

    database = Database(usuario_id)
    compras = database.listar_compras()
    return [_compra_para_dict(c) for c in compras]

@app.post(
    "/usuarios/{usuario_id}/compras",
    response_model=CompraOut,
    status_code=201
)

def criar_compra(
    usuario_id: int,
    compra: CompraCreate,
    _: int = Depends(exigir_dono)
):
    """
    Registra uma compra digitada manualmente pelo usuário no
    dashboard web (sem passar pela IA).
    """

    database = Database(usuario_id)

    try:
        resultado = validar_resultado_compra(
            compra.model_dump(),
            database.listar_nomes_categorias()
        )

        compra_id = database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            valor=resultado["valor"]
        )

    except AnaliseIAError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Busca a compra recém-criada pelo id retornado (não pela
    # posição na lista, já que timestamps podem empatar)
    compra_criada = database.buscar_compra(compra_id)

    return _compra_para_dict(compra_criada)

@app.get(
    "/usuarios/{usuario_id}/categorias",
    response_model=list[CategoriaOut]
)
def listar_categorias(
    usuario_id: int,
    _: int = Depends(exigir_dono)
):

    database = Database(usuario_id)
    categorias = database.listar_categorias()
    return [_categoria_para_dict(c) for c in categorias]


@app.post(
    "/usuarios/{usuario_id}/categorias",
    response_model=CategoriaOut,
    status_code=201
)

def criar_categoria(
    usuario_id: int,
    categoria: CategoriaCreate,
    _: int = Depends(exigir_dono)
):

    database = Database(usuario_id)

    try:
        database.adicionar_categoria(categoria.nome)

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    categorias = database.listar_categorias()

    criada = next(
        c for c in categorias if c[1] == categoria.nome
    )

    return _categoria_para_dict(criada)


@app.post(
    "/usuarios/{usuario_id}/compras/importar-csv",
    response_model=ImportacaoCSVResultado
)

async def importar_compras_csv(
    usuario_id: int,
    arquivo: UploadFile = File(...),
    _: int = Depends(exigir_dono)
):
    """
    Recebe um CSV enviado pelo dashboard web e importa as
    compras nele contidas para o banco do usuário.
    """

    if not arquivo.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado precisa ser um .csv."
        )

    database = Database(usuario_id)

    # Salva o upload em um arquivo temporário, já que o pandas
    # lê a partir de um caminho em disco
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv"
    ) as arquivo_temporario:

        conteudo = await arquivo.read()
        arquivo_temporario.write(conteudo)
        caminho_temporario = arquivo_temporario.name

    try:
        resultado = importar_csv(database, caminho_temporario)

    except ImportacaoCSVError as e:
        raise HTTPException(status_code=422, detail=str(e))

    finally:
        os.unlink(caminho_temporario)

    return resultado

@app.get("/usuarios/{usuario_id}/saude")
def verificar_usuario(
    usuario_id: int,
    _: int = Depends(exigir_dono)
):
    """
    Endpoint simples para o dashboard confirmar que o backend
    está de pé e que o banco do usuário foi inicializado.
    """

    Database(usuario_id)

    return {"status": "ok", "usuario_id": usuario_id}

@app.post("/auth/sessao", response_model=SessaoOut)
def login(dados: LoginToken, response: Response):
    """
    Troca o token do link (enviado pelo bot via /dashboard)
    por uma sessão. Se o token for válido e ainda não tiver
    expirado, grava o cookie de sessão httpOnly no navegador.
    """

    try:
        usuario_id = validar_token_login(dados.token)

    except TokenInvalidoError as e:
        raise HTTPException(status_code=401, detail=str(e))

    sessao = gerar_sessao(usuario_id)

    response.set_cookie(
        key=NOME_COOKIE_SESSAO,
        value=sessao,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=VALIDADE_SESSAO,
        path="/"
    )

    # Garante que o banco desse usuário já existe antes do
    # dashboard fazer a primeira consulta
    Database(usuario_id)

    return {"usuario_id": usuario_id}

@app.get("/auth/me", response_model=SessaoOut)
def usuario_atual(usuario_id: int = Depends(usuario_logado)):
    """
    Devolve o usuário da sessão atual (a partir do cookie). O
    dashboard chama isso ao carregar a página pra descobrir quem
    está logado, já que o usuario_id não aparece na URL.
    """

    return {"usuario_id": usuario_id}

@app.post("/auth/logout")
def logout(response: Response):

    response.delete_cookie(NOME_COOKIE_SESSAO, path="/")

    return {"status": "ok"}

# Serve os arquivos estáticos do dashboard (login.html, index.html,
# etc). Precisa ficar depois de todas as rotas acima: como está
# montado na raiz "/", ele só entra em ação pras requisições que
# nenhuma rota da API respondeu.
if os.path.isdir("dashboard"):

    app.mount(
        "/",
        StaticFiles(directory="dashboard", html=True),
        name="dashboard"
    )
