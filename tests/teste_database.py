import sys
import os

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from src.database.database import Database


USUARIO_A = 111111
USUARIO_B = 222222


# =========================================
# USUÁRIO A
# =========================================

db_a = Database(USUARIO_A)

db_a.garantir_categorias()

db_a.salvar_compra(
    produto="Tênis Nike",
    categoria="Calçados",
    valor=299.90
)


# =========================================
# USUÁRIO B
# =========================================

db_b = Database(USUARIO_B)

db_b.garantir_categorias()

db_b.salvar_compra(
    produto="Pizza",
    categoria="Alimentação",
    valor=59.90
)


# =========================================
# VERIFICAR ISOLAMENTO
# =========================================

print("\n=== COMPRAS DO USUÁRIO A ===")

for compra in db_a.listar_compras():
    print(compra)


print("\n=== COMPRAS DO USUÁRIO B ===")

for compra in db_b.listar_compras():
    print(compra)