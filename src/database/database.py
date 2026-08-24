import os
import sqlite3

from src.config.categorias import CATEGORIAS
class Database:

    def __init__(self, usuario_id):

        # Identificador do usuário do Telegram
        self.usuario_id = usuario_id

        # Pasta com os bancos dos usuários
        self.diretorio = os.path.join(
            "data",
            "usuarios"
        )

        # Cria a pasta caso ela não exista
        os.makedirs(
            self.diretorio,
            exist_ok=True
        )

        # Cada usuário possui seu próprio arquivo .db
        self.db_path = os.path.join(
            self.diretorio,
            f"{usuario_id}.db"
        )

        # Inicializa o banco e as categorias padrões
        self._criar_tabelas()
        self._inserir_categorias()

    def conectar(self):

        # Abre uma conexão com o banco do usuário
        return sqlite3.connect(
            self.db_path
        )

    def _criar_tabelas(self):

        conn = self.conectar()
        cursor = conn.cursor()

        # Tabela que armazena as categorias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        # Tabela que armazena as compras
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

    def _inserir_categorias(self):

        conn = self.conectar()
        cursor = conn.cursor()

        # Insere as categorias padrões na tabela de categorias se não existirem
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

        # Matém "Outros" como última cateogoria
        cursor.execute("""
            SELECT *
            FROM categorias
            ORDER BY
                CASE
                    WHEN nome = 'Outros' THEN 1
                    ELSE 0
                END,
                id
        """)

        categorias = cursor.fetchall()

        conn.close()

        return categorias

    def salvar_compra(
        self,
        produto,
        categoria,
        valor
    ):

        conn = self.conectar()
        cursor = conn.cursor()

        # Busca o ID da categoria antes de salvar a compra
        cursor.execute(
            """
            SELECT id
            FROM categorias
            WHERE nome = ?
            """,
            (categoria,)
        )

        resultado = cursor.fetchone()

        # Impede salvar compra caso a categoria não exista
        if resultado is None:

            conn.close()

            raise ValueError(
                f"Categoria '{categoria}' não encontrada."
            )

        categoria_id = resultado[0]

        # Salva a compra e a vincula a categoria encontrada
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

        # Retorna as comrpas junto com o nome e a categoria
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
            ORDER BY compras.data DESC
        """)

        compras = cursor.fetchall()

        conn.close()

        return compras
    
    def adicionar_categoria(self, nome):

        conn = self.conectar()
        cursor = conn.cursor()

        try:
            # Adiciona uma nova categoria criada pelo usuário
            cursor.execute(
                """
                INSERT INTO categorias (nome)
                VALUES (?)
                """,
                (nome,)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            # Impede a criação de categorias duplicadas
            raise ValueError(
                f"A categoria '{nome}' já existe."
            )

        finally:
            conn.close()
            
    def categoria_existe(self, nome):

        conn = self.conectar()
        cursor = conn.cursor()

        # Verifica se já existe uma categoria com o nome passado no parâmetro da função
        cursor.execute(
            """
            SELECT id
            FROM categorias
            WHERE nome = ?
            """,
            (nome,)
        )

        resultado = cursor.fetchone()

        conn.close()

        return resultado is not None
