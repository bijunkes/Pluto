import json
import re

from src.services.exceptions import AnaliseIAError


def extrair_json(texto):
    """
    Extrai um objeto JSON de um texto retornado por um modelo de IA.

    Alguns modelos (especialmente rodando localmente via Ollama)
    não retornam um JSON puro: podem envolver a resposta em blocos
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

    # Remove blocos de código markdown (```json ... ``` ou ``` ... ```)
    texto_sem_blocos = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE | re.MULTILINE
    ).strip()

    try:

        return json.loads(texto_sem_blocos)

    except json.JSONDecodeError:

        pass

    # Última tentativa: procura o primeiro objeto "{ ... }" no texto,
    # caso a IA tenha adicionado alguma explicação junto da resposta
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
    Garante que o dicionário retornado pela IA tem os campos
    'produto', 'categoria' e 'valor' com os tipos corretos.

    Se a categoria identificada não estiver entre as categorias
    conhecidas, cai em "Outros" em vez de quebrar o fluxo.
    """

    if not isinstance(resultado, dict):

        raise AnaliseIAError("A resposta da IA não é um objeto JSON.")

    campos_obrigatorios = ("produto", "categoria", "valor")

    for campo in campos_obrigatorios:

        if campo not in resultado:

            raise AnaliseIAError(f"A resposta da IA não contém o campo '{campo}'.")

    try:

        resultado["valor"] = float(resultado["valor"])

    except (TypeError, ValueError) as e:

        raise AnaliseIAError("O valor retornado pela IA não é um número válido.") from e

    if not isinstance(resultado["produto"], str) or not resultado["produto"].strip():

        resultado["produto"] = "Não informado"

    if resultado["categoria"] not in categorias:

        resultado["categoria"] = "Outros"

    return resultado
