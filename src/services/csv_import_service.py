import re

import pandas as pd

from src.services.exceptions import AnaliseIAError


# Nomes de coluna aceitos no CSV, por campo. O usuário pode exportar
# a planilha com nomes um pouco diferentes (ex: "Preço" em vez de
# "Valor"), então tentamos casar por sinônimo em vez de exigir um
# cabeçalho exato.
SINONIMOS_COLUNAS = {
    "produto": ["produto", "item", "descricao", "descrição", "nome"],
    "categoria": ["categoria", "tipo", "category"],
    "valor": ["valor", "preco", "preço", "price", "total"],
}


class ImportacaoCSVError(Exception):
    """
    Erro lançado quando o próprio arquivo CSV não pode ser lido
    ou não tem as colunas mínimas necessárias (produto e valor).

    Diferente de erros linha a linha (que são reportados no
    resumo da importação), este erro interrompe a importação
    inteira antes mesmo de começar.
    """
    pass


def _normalizar_nome_coluna(nome):

    return (
        str(nome)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def _encontrar_coluna(colunas_normalizadas, sinonimos):

    for sinonimo in sinonimos:

        sinonimo_normalizado = _normalizar_nome_coluna(sinonimo)

        if sinonimo_normalizado in colunas_normalizadas:

            return colunas_normalizadas[sinonimo_normalizado]

    return None


def _parsear_valor(valor_bruto):
    """
    Converte valores como "R$ 129,90", "129.90" ou "1.234,56"
    em um float. Lança ValueError se não conseguir interpretar.
    """

    if valor_bruto is None or (
        isinstance(valor_bruto, float) and pd.isna(valor_bruto)
    ):

        raise ValueError("valor ausente")

    if isinstance(valor_bruto, (int, float)):

        return float(valor_bruto)

    texto = str(valor_bruto).strip()

    # Remove tudo que não for dígito, vírgula, ponto ou sinal de menos
    texto = re.sub(r"[^\d,.\-]", "", texto)

    if not texto:

        raise ValueError("valor vazio após limpeza")

    # Formato brasileiro "1.234,56" -> remove os pontos de milhar
    # e troca a vírgula decimal por ponto
    if "," in texto and "." in texto:

        texto = texto.replace(".", "").replace(",", ".")

    elif "," in texto:

        texto = texto.replace(",", ".")

    return float(texto)


def importar_csv(database, caminho_arquivo):
    """
    Lê um CSV de compras e insere as linhas válidas no banco
    do usuário. Diferente da análise por IA, aqui a categoria
    informada pelo usuário é respeitada como está: se ela ainda
    não existir, é criada automaticamente em vez de cair em
    "Outros".

    Retorna um resumo com o total de linhas processadas, quantas
    foram inseridas com sucesso e os erros encontrados linha a
    linha (a importação não para no meio por causa de uma linha
    ruim).
    """

    try:

        df = pd.read_csv(caminho_arquivo)

    except Exception as e:

        raise ImportacaoCSVError(
            "Não foi possível ler o arquivo como CSV."
        ) from e

    if df.empty:

        raise ImportacaoCSVError(
            "O arquivo CSV não contém nenhuma linha."
        )

    colunas_normalizadas = {
        _normalizar_nome_coluna(coluna): coluna
        for coluna in df.columns
    }

    coluna_produto = _encontrar_coluna(
        colunas_normalizadas,
        SINONIMOS_COLUNAS["produto"]
    )

    coluna_categoria = _encontrar_coluna(
        colunas_normalizadas,
        SINONIMOS_COLUNAS["categoria"]
    )

    coluna_valor = _encontrar_coluna(
        colunas_normalizadas,
        SINONIMOS_COLUNAS["valor"]
    )

    if coluna_produto is None or coluna_valor is None:

        raise ImportacaoCSVError(
            "O CSV precisa ter ao menos uma coluna de produto "
            "e uma coluna de valor. Colunas encontradas: "
            f"{list(df.columns)}"
        )

    categorias_existentes = set(
        database.listar_nomes_categorias()
    )

    total_linhas = len(df)
    inseridas = 0
    erros = []

    for indice, linha in df.iterrows():

        numero_linha = indice + 2  # +2: cabeçalho + índice 0-based

        try:

            produto = str(linha[coluna_produto]).strip()

            if not produto or produto.lower() == "nan":

                raise ValueError("produto vazio")

            valor = _parsear_valor(linha[coluna_valor])

            if valor < 0:

                raise ValueError("valor negativo")

            if coluna_categoria is not None:

                categoria = str(linha[coluna_categoria]).strip()

                if not categoria or categoria.lower() == "nan":

                    categoria = "Outros"

            else:

                categoria = "Outros"

            # Categoria nova do CSV é criada automaticamente,
            # em vez de ser descartada como "Outros"
            if categoria not in categorias_existentes:

                database.adicionar_categoria(categoria)

                categorias_existentes.add(categoria)

            database.salvar_compra(
                produto=produto,
                categoria=categoria,
                valor=valor
            )

            inseridas += 1

        except Exception as e:

            erros.append({
                "linha": numero_linha,
                "motivo": str(e)
            })

    return {
        "total_linhas": total_linhas,
        "inseridas": inseridas,
        "erros": erros
    }
