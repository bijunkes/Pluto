import os

from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer
)


# Validade do link mágico enviado pelo bot (em segundos).
# Curto de propósito: é só o tempo pra o usuário clicar no botão.
VALIDADE_LINK_LOGIN = 5 * 60  # 5 minutos

# Validade da sessão do dashboard depois que o login é concluído.
VALIDADE_SESSAO = 30 * 24 * 60 * 60  # 30 dias


class TokenInvalidoError(Exception):
    """
    Levantado quando um token de login ou de sessão é inválido,
    foi adulterado ou já expirou.
    """


def _chave_secreta():
    """
    Chave usada para assinar os tokens. É compartilhada entre o
    bot (que gera o link mágico) e a API (que valida o link e
    emite a sessão) — por isso PRECISA ser a mesma nos dois
    processos, configurada via variável de ambiente.
    """

    chave = os.environ.get("AUTH_SECRET_KEY")

    if not chave:

        raise RuntimeError(
            "AUTH_SECRET_KEY não configurada. Defina uma chave "
            "secreta longa e aleatória no .env. Você pode gerar "
            "uma com: python -c \"import secrets; "
            "print(secrets.token_hex(32))\""
        )

    return chave


def _serializer(salt):
    """
    Cada tipo de token usa um "salt" diferente. Assim, mesmo
    assinados com a mesma chave secreta, um link de login não
    pode ser reaproveitado como token de sessão (nem vice-versa).
    """

    return URLSafeTimedSerializer(
        _chave_secreta(),
        salt=salt
    )


def gerar_link_login(usuario_id, dashboard_url=None):
    """
    Gera a URL completa do link mágico enviado pelo bot. O token
    embutido carrega o usuario_id do Telegram assinado, e expira
    em VALIDADE_LINK_LOGIN segundos.
    """

    token = _serializer("login").dumps(usuario_id)

    base_url = dashboard_url or os.environ.get(
        "DASHBOARD_URL",
        "https://girdle-unstaffed-frequency.ngrok-free.dev"
    )

    return f"{base_url.rstrip('/')}/login.html?token={token}"


def validar_token_login(token):
    """
    Valida o token do link mágico e devolve o usuario_id nele
    contido. Levanta TokenInvalidoError se o token for inválido
    ou já ter expirado.
    """

    try:

        return _serializer("login").loads(
            token,
            max_age=VALIDADE_LINK_LOGIN
        )

    except SignatureExpired:

        raise TokenInvalidoError(
            "Link expirado. Peça um novo link ao bot com /dashboard."
        )

    except BadSignature:

        raise TokenInvalidoError(
            "Link de login inválido."
        )


def gerar_sessao(usuario_id):
    """
    Gera o token de sessão de longa duração, emitido pela API
    depois que o link mágico é validado com sucesso. É esse token
    que fica guardado no cookie do navegador do usuário.
    """

    return _serializer("sessao").dumps(usuario_id)


def validar_sessao(token):
    """
    Valida o token de sessão (vindo do cookie) e devolve o
    usuario_id. Levanta TokenInvalidoError se for inválido ou
    tiver expirado.
    """

    try:

        return _serializer("sessao").loads(
            token,
            max_age=VALIDADE_SESSAO
        )

    except SignatureExpired:

        raise TokenInvalidoError("Sessão expirada.")

    except BadSignature:

        raise TokenInvalidoError("Sessão inválida.")
