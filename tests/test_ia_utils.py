from unittest.mock import Mock

import pytest

from src.services.compra_service import CompraService
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import extrair_valor_monetario_br, validar_resultado_compra


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Comprei um celular por 3.000", 3000.0),
        ("Paguei R$ 3.000,50 no celular", 3000.5),
        ("Café por 3,50", 3.5),
        ("Notebook por 3000", 3000.0),
    ],
)
def test_extrai_valor_monetario_no_formato_brasileiro(texto, esperado):
    assert extrair_valor_monetario_br(texto) == esperado


def test_valor_do_texto_prevalece_sobre_interpretacao_da_ia():
    service = CompraService.__new__(CompraService)
    service.ia = Mock()
    service.ia.analisar_mensagem.return_value = {
        "produto": "Celular",
        "categoria": "Outros",
        "valor": 3.0,
    }

    resultado = service.processar_compra("Comprei um celular por 3.000")

    assert resultado["valor"] == 3000.0


def test_valida_compra_com_produto_e_valor_positivo():
    resultado = validar_resultado_compra(
        {"produto": "Mercado", "categoria": "Outros", "valor": "42.50"},
        ["Outros"],
    )

    assert resultado == {
        "produto": "Mercado",
        "categoria": "Outros",
        "valor": 42.5,
        "data_compra": None,
        "hora_compra": None,
    }


@pytest.mark.parametrize("valor", [0, -1, "0"])
def test_rejeita_compra_sem_valor_positivo(valor):
    with pytest.raises(AnaliseIAError, match="maior que zero"):
        validar_resultado_compra(
            {"produto": "Mercado", "categoria": "Outros", "valor": valor},
            ["Outros"],
        )


@pytest.mark.parametrize("produto", ["", "Não informado", "Nao informado"])
def test_rejeita_compra_sem_produto(produto):
    with pytest.raises(AnaliseIAError, match="identificar o produto"):
        validar_resultado_compra(
            {"produto": produto, "categoria": "Outros", "valor": 10},
            ["Outros"],
        )
