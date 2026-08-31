import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


database_url = os.getenv("DATABASE_URL")

print("Testando conexão...")


try:

    with psycopg.connect(database_url) as conn:

        with conn.cursor() as cursor:

            cursor.execute("SELECT version();")

            resultado = cursor.fetchone()

            print("Conexão realizada com sucesso!")
            print(resultado[0])


except Exception as e:

    print("Erro ao conectar ao banco de dados:")
    print(e)
    