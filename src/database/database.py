import os

import psycopg
from decimal import Decimal
from datetime import datetime
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

    def atualizar_conta(self, conta_id, nome=None, tipo=None):
        """
        Atualiza nome e/ou tipo de uma conta do usuário.
        """

        campos = []
        parametros = []

        if nome is not None:
            nome = nome.strip()
            if not nome:
                raise ValueError("O nome da conta não pode ser vazio.")
            campos.append("nome = %s")
            parametros.append(nome)

        if tipo is not None:
            tipo = tipo.strip().upper()
            if not tipo:
                raise ValueError("O tipo da conta não pode ser vazio.")
            campos.append("tipo = %s")
            parametros.append(tipo)

        if not campos:
            return

        parametros.extend([conta_id, self.usuario_id])

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                if nome is not None:
                    cursor.execute(
                        """
                        SELECT id
                        FROM contas
                        WHERE LOWER(nome) = LOWER(%s)
                        AND telegram_id = %s
                        AND id != %s
                        LIMIT 1
                        """,
                        (nome, self.usuario_id, conta_id),
                    )

                    if cursor.fetchone() is not None:
                        raise ValueError(f"A conta '{nome}' já existe.")

                cursor.execute(
                    f"""
                    UPDATE contas
                    SET {', '.join(campos)}
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    parametros,
                )

                if cursor.rowcount == 0:
                    raise ValueError("Conta não encontrada ou inativa.")

    def desativar_conta(self, conta_id):
        """
        Desativa (exclusão lógica) uma conta do usuário.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE contas
                    SET ativa = FALSE
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    (conta_id, self.usuario_id),
                )

                if cursor.rowcount == 0:
                    raise ValueError("Conta não encontrada ou já inativa.")

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

    def adicionar_saldo_conta(self, conta_id, valor):
        """Adiciona dinheiro manualmente ao saldo de uma conta."""
        valor = Decimal(str(valor))
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")

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

    def retirar_saldo_conta(self, conta_id, valor):
        """Retira dinheiro manualmente do saldo de uma conta."""
        valor = Decimal(str(valor))
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")

        with self.conectar() as conn:
            with conn.cursor() as cursor:
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

    def transferir_saldo(self, conta_origem_id, conta_destino_id, valor):
        """Transfere dinheiro entre duas contas ativas do mesmo usuário."""
        valor = Decimal(str(valor))
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        if conta_origem_id == conta_destino_id:
            raise ValueError("A conta de origem e a conta de destino devem ser diferentes.")

        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, saldo, ativa
                    FROM contas
                    WHERE id IN (%s, %s)
                    AND telegram_id = %s
                    ORDER BY id
                    FOR UPDATE
                    """,
                    (conta_origem_id, conta_destino_id, self.usuario_id),
                )
                contas = {row[0]: row for row in cursor.fetchall()}

                origem = contas.get(conta_origem_id)
                destino = contas.get(conta_destino_id)

                if origem is None or destino is None:
                    raise ValueError("Uma das contas não foi encontrada.")
                if not origem[2] or not destino[2]:
                    raise ValueError("As duas contas precisam estar ativas.")

                cursor.execute(
                    """
                    UPDATE contas
                    SET saldo = saldo - %s
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    (valor, conta_origem_id, self.usuario_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Não foi possível debitar a conta de origem.")

                cursor.execute(
                    """
                    UPDATE contas
                    SET saldo = saldo + %s
                    WHERE id = %s
                    AND telegram_id = %s
                    AND ativa = TRUE
                    """,
                    (valor, conta_destino_id, self.usuario_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Não foi possível creditar a conta de destino.")

    # =========================================================
    # COMPRAS
    # =========================================================

    def salvar_compra(self, produto, categoria, conta_id, valor, data_compra=None):
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
                        valor,
                        data
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        COALESCE(%s, CURRENT_TIMESTAMP)
                    )
                    RETURNING id
                    """,
                    (self.usuario_id, produto, categoria_id, conta_id, valor, data_compra),
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

    def buscar_compra_detalhada(self, compra_id):
        """Retorna os dados da compra incluindo os IDs de categoria e conta."""
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        compras.id,
                        compras.produto,
                        compras.categoria_id,
                        categorias.nome,
                        compras.conta_id,
                        contas.nome,
                        compras.valor,
                        compras.data
                    FROM compras
                    JOIN categorias ON compras.categoria_id = categorias.id
                    JOIN contas ON compras.conta_id = contas.id
                    WHERE compras.id = %s
                    AND compras.telegram_id = %s
                    """,
                    (compra_id, self.usuario_id),
                )
                return cursor.fetchone()

    def atualizar_compra(
        self,
        compra_id,
        produto=None,
        categoria_id=None,
        conta_id=None,
        valor=None,
        data_compra=None,
    ):
        """Atualiza uma compra e ajusta os saldos das contas atomicamente."""
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT categoria_id, conta_id, valor
                    FROM compras
                    WHERE id = %s AND telegram_id = %s
                    FOR UPDATE
                    """,
                    (compra_id, self.usuario_id),
                )
                atual = cursor.fetchone()
                if atual is None:
                    raise ValueError("Compra não encontrada.")

                antiga_categoria, antiga_conta, antigo_valor = atual
                nova_categoria = antiga_categoria if categoria_id is None else categoria_id
                nova_conta = antiga_conta if conta_id is None else conta_id
                novo_valor = antigo_valor if valor is None else valor

                cursor.execute(
                    """
                    SELECT id, tipo, telegram_id
                    FROM categorias
                    WHERE id = %s
                    AND (tipo = 'PADRAO' OR (tipo = 'PERSONALIZADA' AND telegram_id = %s))
                    """,
                    (nova_categoria, self.usuario_id),
                )
                if cursor.fetchone() is None:
                    raise ValueError("Categoria não encontrada.")

                cursor.execute(
                    """
                    SELECT id, ativa
                    FROM contas
                    WHERE id = %s AND telegram_id = %s
                    """,
                    (nova_conta, self.usuario_id),
                )
                conta_nova = cursor.fetchone()
                if conta_nova is None:
                    raise ValueError("Conta não encontrada.")
                if not conta_nova[1]:
                    raise ValueError("A conta está inativa.")

                if novo_valor < 0:
                    raise ValueError("O valor da compra não pode ser negativo.")

                if antiga_conta == nova_conta:
                    diferenca = antigo_valor - novo_valor
                    if diferenca:
                        cursor.execute(
                            """
                            UPDATE contas
                            SET saldo = saldo + %s
                            WHERE id = %s AND telegram_id = %s
                            """,
                            (diferenca, antiga_conta, self.usuario_id),
                        )
                else:
                    cursor.execute(
                        """
                        UPDATE contas
                        SET saldo = saldo + %s
                        WHERE id = %s AND telegram_id = %s
                        """,
                        (antigo_valor, antiga_conta, self.usuario_id),
                    )
                    if cursor.rowcount == 0:
                        raise ValueError("Conta anterior não encontrada.")
                    cursor.execute(
                        """
                        UPDATE contas
                        SET saldo = saldo - %s
                        WHERE id = %s AND telegram_id = %s AND ativa = TRUE
                        """,
                        (novo_valor, nova_conta, self.usuario_id),
                    )
                    if cursor.rowcount == 0:
                        raise ValueError("Nova conta não encontrada ou inativa.")

                campos = ["categoria_id = %s", "conta_id = %s", "valor = %s"]
                parametros = [nova_categoria, nova_conta, novo_valor]
                if produto is not None:
                    produto = produto.strip()
                    if not produto:
                        raise ValueError("O produto não pode ser vazio.")
                    campos.append("produto = %s")
                    parametros.append(produto)
                if data_compra is not None:
                    campos.append("data = %s")
                    parametros.append(data_compra)

                parametros.extend([compra_id, self.usuario_id])
                cursor.execute(
                    f"UPDATE compras SET {', '.join(campos)} WHERE id = %s AND telegram_id = %s",
                    parametros,
                )
                if cursor.rowcount == 0:
                    raise ValueError("Compra não encontrada.")

    def buscar_categoria_por_id(self, categoria_id):
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, nome, tipo, telegram_id
                    FROM categorias
                    WHERE id = %s
                    AND (tipo = 'PADRAO' OR (tipo = 'PERSONALIZADA' AND telegram_id = %s))
                    """,
                    (categoria_id, self.usuario_id),
                )
                return cursor.fetchone()

    def atualizar_categoria(self, categoria_id, nome):
        nome = nome.strip()
        if not nome:
            raise ValueError("O nome da categoria não pode ser vazio.")
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT tipo, telegram_id FROM categorias WHERE id = %s",
                    (categoria_id,),
                )
                categoria = cursor.fetchone()
                if categoria is None:
                    raise ValueError("Categoria não encontrada.")
                if categoria[0] != "PERSONALIZADA" or categoria[1] != self.usuario_id:
                    raise ValueError("Categorias padrão não podem ser alteradas.")
                cursor.execute(
                    """
                    SELECT id FROM categorias
                    WHERE LOWER(nome) = LOWER(%s)
                    AND (tipo = 'PADRAO' OR (tipo = 'PERSONALIZADA' AND telegram_id = %s))
                    AND id != %s
                    LIMIT 1
                    """,
                    (nome, self.usuario_id, categoria_id),
                )
                if cursor.fetchone() is not None:
                    raise ValueError(f"A categoria '{nome}' já existe.")
                cursor.execute(
                    "UPDATE categorias SET nome = %s WHERE id = %s AND telegram_id = %s AND tipo = 'PERSONALIZADA'",
                    (nome, categoria_id, self.usuario_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Categoria não encontrada.")

    def excluir_categoria(self, categoria_id):
        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT tipo, telegram_id, nome FROM categorias WHERE id = %s",
                    (categoria_id,),
                )
                categoria = cursor.fetchone()
                if categoria is None:
                    raise ValueError("Categoria não encontrada.")
                if categoria[0] != "PERSONALIZADA" or categoria[1] != self.usuario_id:
                    raise ValueError("Categorias padrão não podem ser excluídas.")
                cursor.execute("SELECT COUNT(*) FROM compras WHERE categoria_id = %s", (categoria_id,))
                if cursor.fetchone()[0] > 0:
                    raise ValueError("Esta categoria está sendo usada por compras. Altere a categoria dessas compras antes de excluí-la.")
                cursor.execute(
                    "DELETE FROM categorias WHERE id = %s AND telegram_id = %s AND tipo = 'PERSONALIZADA'",
                    (categoria_id, self.usuario_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Categoria não encontrada.")

    # =========================================================
    # INSIGHTS
    # =========================================================

    def criar_configuracao_insights(self):
        """
        Cria a configuração padrão de insights para o usuário.

        Por padrão:
        - insights ativados
        - frequência semanal
        - horário às 09:00
        - nenhum envio realizado ainda
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO configuracoes_insights (
                        telegram_id
                    )
                    VALUES (%s)
                    ON CONFLICT (telegram_id) DO NOTHING
                    RETURNING id
                    """,
                    (self.usuario_id,),
                )

                resultado = cursor.fetchone()

                return resultado[0] if resultado else None

    def buscar_configuracao_insights(self):
        """
        Retorna a configuração de insights do usuário.

        Se ainda não existir, cria a configuração padrão.
        """

        self.criar_configuracao_insights()

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        telegram_id,
                        ativo,
                        frequencia,
                        horario,
                        ultimo_envio
                    FROM configuracoes_insights
                    WHERE telegram_id = %s
                    """,
                    (self.usuario_id,),
                )

                resultado = cursor.fetchone()

                if resultado is None:
                    return None

                return {
                    "id": resultado[0],
                    "telegram_id": resultado[1],
                    "ativo": resultado[2],
                    "frequencia": resultado[3],
                    "horario": resultado[4],
                    "ultimo_envio": resultado[5],
                }

    def atualizar_frequencia_insights(self, frequencia):
        """
        Atualiza a frequência dos insights.

        Valores permitidos:
        DIARIO
        SEMANAL
        NENHUM
        """

        frequencia = frequencia.strip().upper()

        frequencias_validas = {
            "DIARIO",
            "SEMANAL",
            "NENHUM",
        }

        if frequencia not in frequencias_validas:
            raise ValueError(
                "Frequência inválida. "
                "Use DIARIO, SEMANAL ou NENHUM."
            )

        self.criar_configuracao_insights()

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE configuracoes_insights
                    SET
                        frequencia = %s,
                        ativo = %s
                    WHERE telegram_id = %s
                    """,
                    (
                        frequencia,
                        frequencia != "NENHUM",
                        self.usuario_id,
                    ),
                )

    def atualizar_horario_insights(self, horario):
        """Atualiza o horário preferido para receber insights no formato HH:MM."""
        horario = str(horario).strip()
        try:
            horario = datetime.strptime(horario, "%H:%M").time()
        except ValueError as exc:
            raise ValueError("Horário inválido. Use o formato HH:MM, por exemplo 09:30.") from exc

        self.criar_configuracao_insights()

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE configuracoes_insights
                    SET horario = %s
                    WHERE telegram_id = %s
                    """,
                    (
                        horario,
                        self.usuario_id,
                    ),
                )

    def definir_insights_ativos(self, ativo):
        """
        Ativa ou desativa o recebimento de insights.
        """

        self.criar_configuracao_insights()

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE configuracoes_insights
                    SET ativo = %s
                    WHERE telegram_id = %s
                    """,
                    (
                        ativo,
                        self.usuario_id,
                    ),
                )

    def registrar_envio_insight(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        agora = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).replace(tzinfo=None)

        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE configuracoes_insights
                    SET ultimo_envio = %s
                    WHERE telegram_id = %s
                    """,
                    (agora, self.usuario_id)
                )

    def total_gastos_periodo(self, data_inicio, data_fim):
        """
        Retorna o total de gastos do usuário em um período.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(valor), 0)
                    FROM compras
                    WHERE telegram_id = %s
                    AND data >= %s
                    AND data < %s
                    """,
                    (
                        self.usuario_id,
                        data_inicio,
                        data_fim,
                    ),
                )

                resultado = cursor.fetchone()

                return float(resultado[0])

    def gastos_por_categoria(self, data_inicio, data_fim):
        """
        Retorna os gastos agrupados por categoria
        dentro de um período.
        """

        with self.conectar() as conn:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        categorias.nome,
                        COALESCE(SUM(compras.valor), 0),
                        COUNT(compras.id)
                    FROM compras

                    JOIN categorias
                        ON compras.categoria_id = categorias.id

                    WHERE compras.telegram_id = %s
                    AND compras.data >= %s
                    AND compras.data < %s

                    GROUP BY
                        categorias.id,
                        categorias.nome

                    ORDER BY
                        SUM(compras.valor) DESC
                    """,
                    (
                        self.usuario_id,
                        data_inicio,
                        data_fim,
                    ),
                )

                resultados = cursor.fetchall()

                return [
                    {
                        "categoria": resultado[0],
                        "total": float(resultado[1]),
                        "quantidade": resultado[2],
                    }
                    for resultado in resultados
                ]

    def listar_configuracoes_insights_ativas(self):
        """
        Retorna as configurações de insights dos usuários ativos.
        """

        with self.conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        telegram_id,
                        ativo,
                        frequencia,
                        horario,
                        ultimo_envio
                    FROM configuracoes_insights
                    WHERE ativo = TRUE
                    AND frequencia != 'NENHUM'
                    """
                )

                resultados = cursor.fetchall()

                return [
                    {
                        "telegram_id": resultado[0],
                        "ativo": resultado[1],
                        "frequencia": resultado[2],
                        "horario": resultado[3],
                        "ultimo_envio": resultado[4],
                    }
                    for resultado in resultados
                ]

    def definir_ultimo_envio_insight_teste(self, telegram_id, data_hora):
        with psycopg.connect(
            os.getenv("DATABASE_URL"),
            prepare_threshold=None
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE configuracoes_insights
                    SET ultimo_envio = %s
                    WHERE telegram_id = %s
                    """,
                    (data_hora, telegram_id)
                )

            conn.commit()