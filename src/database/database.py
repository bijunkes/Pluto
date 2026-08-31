import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


class Database:

    def __init__(self, usuario_id):

        # ID do usuário no Telegram
        self.usuario_id = usuario_id

    def conectar(self):
        """
        Cria uma conexão com o banco PostgreSQL.
        """

        return psycopg.connect(
            os.getenv("DATABASE_URL"),
            prepare_threshold=None
        )

    def listar_categorias(self):
        """
        Retorna as categorias padrão e as categorias
        personalizadas do usuário atual.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        nome,
                        tipo,
                        criado_em
                    FROM categorias
                    WHERE tipo = 'PADRAO'
                       OR (
                            tipo = 'PERSONALIZADA'
                            AND telegram_id = %s
                       )
                    ORDER BY
                        CASE
                            WHEN nome = 'Outros' THEN 1
                            ELSE 0
                        END,
                        CASE
                            WHEN tipo = 'PADRAO' THEN 0
                            ELSE 1
                        END,
                        id
                    """,
                    (
                        self.usuario_id,
                    )
                )

                return cursor.fetchall()

    def listar_nomes_categorias(self):
        """
        Retorna apenas os nomes das categorias
        disponíveis para o usuário.
        """

        return [
            categoria[1]
            for categoria in self.listar_categorias()
        ]

    def buscar_categoria(self, nome):
        """
        Busca uma categoria disponível para o usuário.

        Pode ser uma categoria padrão ou uma categoria
        personalizada pertencente ao usuário.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        nome,
                        tipo,
                        telegram_id
                    FROM categorias
                    WHERE LOWER(nome) = LOWER(%s)
                    AND (
                        tipo = 'PADRAO'
                        OR (
                            tipo = 'PERSONALIZADA'
                            AND telegram_id = %s
                        )
                    )
                    ORDER BY
                        CASE
                            WHEN tipo = 'PERSONALIZADA' THEN 0
                            ELSE 1
                        END
                    LIMIT 1
                    """,
                    (
                        nome,
                        self.usuario_id
                    )
                )

                return cursor.fetchone()

    def salvar_compra(
        self,
        produto,
        categoria,
        valor
    ):
        """
        Salva uma compra associada a uma categoria
        padrão ou personalizada do usuário.
        """

        categoria_encontrada = self.buscar_categoria(
            categoria
        )

        if categoria_encontrada is None:
            raise ValueError(
                f"Categoria '{categoria}' não encontrada."
            )

        categoria_id = categoria_encontrada[0]

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO compras (
                        telegram_id,
                        produto,
                        categoria_id,
                        valor
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        self.usuario_id,
                        produto,
                        categoria_id,
                        valor
                    )
                )

                compra_id = cursor.fetchone()[0]

                return compra_id

    def buscar_compra(self, compra_id):
        """
        Busca uma única compra pertencente ao usuário.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        compras.id,
                        compras.produto,
                        categorias.nome,
                        compras.valor,
                        compras.data
                    FROM compras
                    JOIN categorias
                        ON compras.categoria_id = categorias.id
                    WHERE compras.id = %s
                    AND compras.telegram_id = %s
                    """,
                    (
                        compra_id,
                        self.usuario_id
                    )
                )

                return cursor.fetchone()

    def listar_compras(
        self,
        data_inicio=None,
        data_fim=None
    ):
        """
        Lista as compras do usuário.

        Opcionalmente pode receber uma data inicial
        e uma data final para filtrar os resultados.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                query = """
                    SELECT
                        compras.id,
                        compras.produto,
                        categorias.nome,
                        compras.valor,
                        compras.data
                    FROM compras
                    JOIN categorias
                        ON compras.categoria_id = categorias.id
                    WHERE compras.telegram_id = %s
                """

                parametros = [
                    self.usuario_id
                ]

                if data_inicio and data_fim:

                    query += """
                        AND compras.data >= %s
                        AND compras.data < %s
                    """

                    parametros.extend([
                        data_inicio,
                        data_fim
                    ])

                query += """
                    ORDER BY compras.data DESC
                """

                cursor.execute(
                    query,
                    parametros
                )

                return cursor.fetchall()

    def adicionar_categoria(self, nome):
        """
        Cria uma categoria personalizada para o usuário.

        Categorias padrão não são criadas aqui.
        """

        nome = nome.strip()

        if not nome:
            raise ValueError(
                "O nome da categoria não pode ser vazio."
            )

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                # Verifica se já existe uma categoria
                # com esse nome disponível para o usuário.
                cursor.execute(
                    """
                    SELECT id
                    FROM categorias
                    WHERE LOWER(nome) = LOWER(%s)
                    AND (
                        tipo = 'PADRAO'
                        OR (
                            tipo = 'PERSONALIZADA'
                            AND telegram_id = %s
                        )
                    )
                    LIMIT 1
                    """,
                    (
                        nome,
                        self.usuario_id
                    )
                )

                resultado = cursor.fetchone()

                if resultado is not None:

                    raise ValueError(
                        f"A categoria '{nome}' já existe."
                    )

                # Cria categoria personalizada
                cursor.execute(
                    """
                    INSERT INTO categorias (
                        telegram_id,
                        nome,
                        tipo
                    )
                    VALUES (
                        %s,
                        %s,
                        'PERSONALIZADA'
                    )
                    RETURNING id
                    """,
                    (
                        self.usuario_id,
                        nome
                    )
                )

                categoria_id = cursor.fetchone()[0]

                return categoria_id

    def categoria_existe(self, nome):
        """
        Verifica se uma categoria existe para o usuário.

        Considera tanto categorias padrão quanto
        categorias personalizadas do usuário.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT id
                    FROM categorias
                    WHERE LOWER(nome) = LOWER(%s)
                    AND (
                        tipo = 'PADRAO'
                        OR (
                            tipo = 'PERSONALIZADA'
                            AND telegram_id = %s
                        )
                    )
                    LIMIT 1
                    """,
                    (
                        nome,
                        self.usuario_id
                    )
                )

                resultado = cursor.fetchone()

                return resultado is not None

    def excluir_compra(self, compra_id):
        """
        Exclui uma compra pertencente ao usuário.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM compras
                    WHERE id = %s
                    AND telegram_id = %s
                    """,
                    (
                        compra_id,
                        self.usuario_id
                    )
                )