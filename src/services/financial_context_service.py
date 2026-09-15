from collections import defaultdict

from src.database.database import Database


class FinancialContextService:
    """Produz um retrato financeiro limitado e serializavel para a conversa."""

    MAX_PURCHASES = 50

    def obter(self, usuario_id: int) -> dict:
        database = Database(usuario_id)
        contas = database.listar_contas()
        compras = database.listar_compras()[:self.MAX_PURCHASES]

        por_categoria = defaultdict(float)
        total = 0.0
        itens = []
        for compra in compras:
            valor = float(compra[4])
            total += valor
            por_categoria[str(compra[2])] += valor
            itens.append(
                {
                    "produto": str(compra[1]),
                    "categoria": str(compra[2]),
                    "conta": str(compra[3]),
                    "valor": valor,
                    "data": compra[5].isoformat() if hasattr(compra[5], "isoformat") else str(compra[5]),
                }
            )

        return {
            "escopo": f"ultimas {len(compras)} compras, limite {self.MAX_PURCHASES}",
            "total_no_escopo": round(total, 2),
            "totais_por_categoria": {
                nome: round(valor, 2)
                for nome, valor in sorted(por_categoria.items(), key=lambda x: -x[1])
            },
            "contas": [
                {"nome": str(c[1]), "tipo": str(c[2]), "saldo": float(c[3])}
                for c in contas
            ],
            "compras": itens,
        }
