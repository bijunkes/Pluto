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

        return psycopg.connect(os.getenv("DATABASE_URL"), prepare_threshold=None)

    # =========================================================
    # CATEGORIAS
    # =========================================================

    def listar_categorias(self):
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nome, tipo, criado_em
                    FROM categorias
                    WHERE tipo = 'PADRAO'
                    OR (
                            tipo = 'PERSONALIZADA'
                            AND telegram_id = %s
                    )
                    ORDER BY
                        CASE WHEN nome = 'Outros' THEN 1 ELSE 0 END,
                        CASE WHEN tipo = 'PADRAO' THEN 0 ELSE 1 END,
                        id
                    """,
                    (self.usuario_id,),
                )

                return cursor.fetchall()

    def listar_nomes_categorias(self):
        """
        Retorna apenas os nomes das categorias
        disponíveis para o usuário.
        """

        return [categoria[1] for categoria in self.listar_categorias()]

    def buscar_categoria(self, nome):
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nome, tipo, telegram_id
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
                    (nome, self.usuario_id),
                )

                return cursor.fetchone()

    def adicionar_categoria(self, nome):
        nome = nome.strip()

        if not nome:
            raise ValueError("O nome da categoria não pode ser vazio.")

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
                    (nome, self.usuario_id),
                )

                resultado = cursor.fetchone()

                if resultado is not None:
                    raise ValueError(f"A categoria '{nome}' já existe.")

                cursor.execute(
                    """
                    INSERT INTO categorias (
                        telegram_id,
                        nome,
                        tipo
                    )
                    VALUES (%s, %s, 'PERSONALIZADA')
                    RETURNING id
                    """,
                    (self.usuario_id, nome),
                )

                return cursor.fetchone()[0]

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
                    (nome, self.usuario_id),
                )

                resultado = cursor.fetchone()

                return resultado is not None

    # =========================================================
    # CONTAS
    # =========================================================

    def listar_contas(self, apenas_ativas=True):
        """
        Lista as contas do usuário.

        Por padrão, retorna apenas contas ativas.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                query = """
                    SELECT
                        id,
                        nome,
                        tipo,
                        saldo,
                        criada_em,
                        ativa
                    FROM contas
                    WHERE telegram_id = %s
                """

                parametros = [self.usuario_id]

                if apenas_ativas:

                    query += """
                        AND ativa = TRUE
                    """

                query += """
                    ORDER BY nome
                """

                cursor.execute(query, parametros)

                return cursor.fetchall()

    def listar_nomes_contas(self):
        """
        Retorna apenas os nomes das contas ativas.
        """

        return [conta[1] for conta in self.listar_contas()]

    def buscar_conta(self, conta_id):
        """
        Busca uma conta pelo ID.

        A conta precisa pertencer ao usuário atual.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        nome,
                        tipo,
                        saldo,
                        criada_em,
                        ativa
                    FROM contas
                    WHERE id = %s
                    AND telegram_id = %s
                    """,
                    (conta_id, self.usuario_id),
                )

                return cursor.fetchone()

    def buscar_conta_por_nome(self, nome):
        """
        Busca uma conta ativa pelo nome.
        """

        nome = nome.strip()

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        nome,
                        tipo,
                        saldo,
                        criada_em,
                        ativa
                    FROM contas
                    WHERE LOWER(nome) = LOWER(%s)
                    AND telegram_id = %s
                    AND ativa = TRUE
                    LIMIT 1
                    """,
                    (nome, self.usuario_id),
                )

                return cursor.fetchone()

    def adicionar_conta(self, nome, tipo, saldo=0):
        """
        Cria uma nova conta para o usuário.
        """

        nome = nome.strip()
        tipo = tipo.strip().upper()

        if not nome:

            raise ValueError("O nome da conta não pode ser vazio.")

        if not tipo:

            raise ValueError("O tipo da conta não pode ser vazio.")

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                # Verifica se já existe uma conta
                # com esse nome para o usuário.
                cursor.execute(
                    """
                    SELECT id
                    FROM contas
                    WHERE LOWER(nome) = LOWER(%s)
                    AND telegram_id = %s
                    LIMIT 1
                    """,
                    (nome, self.usuario_id),
                )

                resultado = cursor.fetchone()

                if resultado is not None:

                    raise ValueError(f"A conta '{nome}' já existe.")

                cursor.execute(
                    """
                    INSERT INTO contas (
                        telegram_id,
                        nome,
                        tipo,
                        saldo
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (self.usuario_id, nome, tipo, saldo),
                )

                return cursor.fetchone()[0]

    def conta_existe(self, nome):
        """
        Verifica se uma conta ativa existe
        para o usuário.
        """

        return self.buscar_conta_por_nome(nome) is not None

    def atualizar_saldo_conta(self, conta_id, valor, cursor=None):
        """
        Atualiza o saldo da conta.

        O valor pode ser positivo ou negativo.

        Exemplo:

        +100 -> adiciona R$ 100
        -50  -> remove R$ 50
        """

        if cursor is not None:

            cursor.execute(
                """
                UPDATE contas
                SET saldo = saldo + %s
                WHERE id = %s
                AND telegram_id = %s
                AND ativa = TRUE
                """,
                (valor, conta_id, self.usuario_id),
            )

            if cursor.rowcount == 0:

                raise ValueError("Conta não encontrada ou inativa.")

            return

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE contas
                    SET saldo = saldo + %s
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    (valor, conta_id, self.usuario_id),
                )

                if cursor.rowcount == 0:

                    raise ValueError("Conta não encontrada ou inativa.")

    # =========================================================
    # COMPRAS
    # =========================================================

    def salvar_compra(self, produto, categoria, conta_id, valor):
        """
        Salva uma compra associada a uma categoria e a uma
        conta pertencentes ao usuário.

        A compra e a alteração do saldo acontecem
        dentro da mesma transação.
        """

        categoria_encontrada = self.buscar_categoria(categoria)

        if categoria_encontrada is None:
            raise ValueError(f"Categoria '{categoria}' não encontrada.")

        conta_encontrada = self.buscar_conta(conta_id)

        if conta_encontrada is None:
            raise ValueError("Conta não encontrada.")

        if not conta_encontrada[5]:
            raise ValueError("A conta está inativa.")

        categoria_id = categoria_encontrada[0]

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                # Registra a compra
                cursor.execute(
                    """
                    INSERT INTO compras (
                        telegram_id,
                        produto,
                        categoria_id,
                        conta_id,
                        valor
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (self.usuario_id, produto, categoria_id, conta_id, valor),
                )

                compra_id = cursor.fetchone()[0]

                # Remove o valor do saldo
                cursor.execute(
                    """
                    UPDATE contas
                    SET saldo = saldo - %s
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    (valor, conta_id, self.usuario_id),
                )

                if cursor.rowcount == 0:
                    raise ValueError("Conta não encontrada ou inativa.")

                return compra_id

    def buscar_compra(self, compra_id):
        """
        Busca uma única compra pertencente ao usuário.

        Retorna:
        id, produto, categoria, conta, valor, data
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        compras.id,
                        compras.produto,
                        categorias.nome,
                        contas.nome,
                        compras.valor,
                        compras.data
                    FROM compras

                    JOIN categorias
                        ON compras.categoria_id = categorias.id

                    JOIN contas
                        ON compras.conta_id = contas.id

                    WHERE compras.id = %s
                    AND compras.telegram_id = %s
                    """,
                    (compra_id, self.usuario_id),
                )

                return cursor.fetchone()

    def listar_compras(self, data_inicio=None, data_fim=None):
        """
        Lista as compras do usuário.

        Opcionalmente pode receber uma data inicial
        e uma data final para filtrar os resultados.

        Retorna:
        id, produto, categoria, conta, valor, data
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                query = """
                    SELECT
                        compras.id,
                        compras.produto,
                        categorias.nome,
                        contas.nome,
                        compras.valor,
                        compras.data
                    FROM compras

                    JOIN categorias
                        ON compras.categoria_id = categorias.id

                    JOIN contas
                        ON compras.conta_id = contas.id

                    WHERE compras.telegram_id = %s
                """

                parametros = [self.usuario_id]

                if data_inicio and data_fim:

                    query += """
                        AND compras.data >= %s
                        AND compras.data < %s
                    """

                    parametros.extend([data_inicio, data_fim])

                query += """
                    ORDER BY compras.data DESC
                """

                cursor.execute(query, parametros)

                return cursor.fetchall()

    def excluir_compra(self, compra_id):
        """
        Exclui uma compra pertencente ao usuário.

        Antes de excluir, recupera o valor e a conta
        para devolver o dinheiro ao saldo da conta.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                # Busca os dados da compra
                cursor.execute(
                    """
                    SELECT
                        conta_id,
                        valor
                    FROM compras
                    WHERE id = %s
                    AND telegram_id = %s
                    """,
                    (compra_id, self.usuario_id),
                )

                compra = cursor.fetchone()

                if compra is None:

                    raise ValueError("Compra não encontrada.")

                conta_id = compra[0]
                valor = compra[1]

                # Exclui a compra
                cursor.execute(
                    """
                    DELETE FROM compras
                    WHERE id = %s
                    AND telegram_id = %s
                    """,
                    (compra_id, self.usuario_id),
                )

                # Devolve o valor para a conta
                cursor.execute(
                    """
                    UPDATE contas
                    SET saldo = saldo + %s
                    WHERE id = %s
                    AND telegram_id = %s
                    """,
                    (valor, conta_id, self.usuario_id),
                )
