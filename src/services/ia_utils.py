import json
import re
from datetime import datetime

from src.services.exceptions import AnaliseIAError


def extrair_json(texto):
    """
    Extrai um objeto JSON de um texto retornado por um modelo de IA.

    Alguns modelos podem envolver a resposta em blocos
    ```json ... ``` ou adicionar frases antes/depois do objeto.
    Esta função tenta lidar com esses casos antes de desistir.
    """

    if not texto or not texto.strip():
        raise AnaliseIAError("A IA retornou uma resposta vazia.")

    texto = texto.strip()

    # Tenta o caminho direto: o texto já é um JSON válido
    try:
        return json.loads(texto)

    except json.JSONDecodeError:
        pass

    # Remove blocos de código markdown
    texto_sem_blocos = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    ).strip()

    try:
        return json.loads(texto_sem_blocos)

    except json.JSONDecodeError:
        pass

    # Última tentativa: procura o primeiro objeto JSON
    match = re.search(r"\{.*\}", texto, flags=re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))

        except json.JSONDecodeError as e:
            raise AnaliseIAError(
                "Não foi possível interpretar o JSON retornado pela IA."
            ) from e

    raise AnaliseIAError("A resposta da IA não contém um JSON reconhecível.")


def validar_resultado_compra(resultado, categorias):
    """
    Valida o resultado retornado pela IA.

    Campos obrigatórios:
    - produto
    - categoria
    - valor

    Campos opcionais:
    - data_compra
    - hora_compra

    Data e hora só são preenchidas quando identificadas
    na mensagem do usuário. Caso contrário, permanecem como None
    para que o CompraService possa utilizar a data/hora atual.
    """

    if not isinstance(resultado, dict):
        raise AnaliseIAError("A resposta da IA não é um objeto JSON.")

    campos_obrigatorios = (
        "produto",
        "categoria",
        "valor",
    )

    for campo in campos_obrigatorios:
        if campo not in resultado:
            raise AnaliseIAError(
                f"A resposta da IA não contém o campo '{campo}'."
            )

    # ---------------------------------------------------------
    # VALOR
    # ---------------------------------------------------------

    try:
        resultado["valor"] = float(resultado["valor"])

    except (TypeError, ValueError) as e:
        raise AnaliseIAError(
            "O valor retornado pela IA não é um número válido."
        ) from e

    # ---------------------------------------------------------
    # PRODUTO
    # ---------------------------------------------------------

    if (
        not isinstance(resultado["produto"], str)
        or not resultado["produto"].strip()
    ):
        resultado["produto"] = "Não informado"

    # ---------------------------------------------------------
    # CATEGORIA
    # ---------------------------------------------------------

    if resultado["categoria"] not in categorias:
        resultado["categoria"] = "Outros"

    # ---------------------------------------------------------
    # DATA DA COMPRA
    # ---------------------------------------------------------

    data_compra = resultado.get("data_compra")

    if data_compra in ("", "null", "None"):
        data_compra = None

    if data_compra is not None:

        if not isinstance(data_compra, str):
            raise AnaliseIAError(
                "A data da compra retornada pela IA não é válida."
            )

        try:
            datetime.strptime(data_compra, "%Y-%m-%d")

        except ValueError as e:
            raise AnaliseIAError(
                "A data da compra retornada pela IA não está "
                "no formato YYYY-MM-DD."
            ) from e

    resultado["data_compra"] = data_compra

    # ---------------------------------------------------------
    # HORA DA COMPRA
    # ---------------------------------------------------------

    hora_compra = resultado.get("hora_compra")

    if hora_compra in ("", "null", "None"):
        hora_compra = None

    if hora_compra is not None:

        if not isinstance(hora_compra, str):
            raise AnaliseIAError(
                "A hora da compra retornada pela IA não é válida."
            )

        try:
            datetime.strptime(hora_compra, "%H:%M")

        except ValueError as e:
            raise AnaliseIAError(
                "A hora da compra retornada pela IA não está "
                "no formato HH:MM."
            ) from e

    resultado["hora_compra"] = hora_compra

    return resultado