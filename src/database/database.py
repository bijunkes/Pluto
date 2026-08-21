import sqlite3

from src.config.categorias import CATEGORIAS


class Database:

    def __init__(self, db_name="pluto.db"):
        self.db_name = db_name

        self.criar_tabelas()
        self.inserir_categorias()

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def criar_tabelas(self):

        conn = self.conectar()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT NOT NULL,
                categoria_id INTEGER NOT NULL,
                valor REAL NOT NULL,
                data TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id)
                    REFERENCES categorias(id)
            )
        """)

        conn.commit()
        conn.close()

    def inserir_categorias(self):

        conn = self.conectar()
        cursor = conn.cursor()

        for categoria in CATEGORIAS:

            cursor.execute(
                """
                INSERT OR IGNORE INTO categorias (nome)
                VALUES (?)
                """,
                (categoria,)
            )

        conn.commit()
        conn.close()

    def listar_categorias(self):

        conn = self.conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM categorias"
        )

        categorias = cursor.fetchall()

        conn.close()

        return categorias

    def salvar_compra(self, produto, categoria, valor):

        conn = self.conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM categorias
            WHERE nome = ?
            """,
            (categoria,)
        )

        resultado = cursor.fetchone()

        if resultado is None:

            conn.close()

            raise ValueError(
                f"Categoria '{categoria}' não encontrada."
            )

        categoria_id = resultado[0]

        cursor.execute(
            """
            INSERT INTO compras (
                produto,
                categoria_id,
                valor
            )
            VALUES (?, ?, ?)
            """,
            (
                produto,
                categoria_id,
                valor
            )
        )

        conn.commit()
        conn.close()

    def listar_compras(self):

        conn = self.conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                compras.id,
                compras.produto,
                categorias.nome,
                compras.valor,
                compras.data
            FROM compras
            JOIN categorias
                ON compras.categoria_id = categorias.id
        """)

        compras = cursor.fetchall()

        conn.close()

        return compras
