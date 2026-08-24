from src.database.database import Database


def main():

    usuario_id = 123456789

    db = Database(usuario_id)

    print("Banco:", db.db_path)

    print("\nCategorias:")
    print(db.listar_categorias())

    db.salvar_compra(
        produto="Camisa",
        categoria="Roupas",
        valor=129.90
    )

    print("\nCompras:")
    print(db.listar_compras())


if __name__ == "__main__":
    main()