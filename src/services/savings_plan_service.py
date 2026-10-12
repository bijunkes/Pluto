from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class SavingsPlanService:
    """Cria um plano mensal simples usando a referência 50-30-20."""

    CENTAVOS = Decimal("0.01")

    @staticmethod
    def interpretar_valor(texto: str) -> Decimal:
        valor = texto.strip().lower().replace("r$", "").replace("reais", "")
        valor = valor.replace(" ", "")
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif "." in valor:
            valor_sem_sinal = valor.lstrip("+-")
            grupos = valor_sem_sinal.split(".")
            if (
                1 <= len(grupos[0]) <= 3
                and grupos[0].isdigit()
                and len(grupos) > 1
                and all(len(grupo) == 3 and grupo.isdigit() for grupo in grupos[1:])
            ):
                valor = valor.replace(".", "")
        try:
            resultado = Decimal(valor)
        except InvalidOperation as erro:
            raise ValueError("Valor de salário inválido.") from erro
        if resultado <= 0:
            raise ValueError("O salário deve ser maior que zero.")
        return resultado.quantize(SavingsPlanService.CENTAVOS, rounding=ROUND_HALF_UP)

    @staticmethod
    def calcular(salario) -> dict:
        salario = Decimal(str(salario)).quantize(
            SavingsPlanService.CENTAVOS, rounding=ROUND_HALF_UP
        )
        if salario <= 0:
            raise ValueError("O salário deve ser maior que zero.")
        necessidades = (salario * Decimal("0.50")).quantize(
            SavingsPlanService.CENTAVOS, rounding=ROUND_HALF_UP
        )
        desejos = (salario * Decimal("0.30")).quantize(
            SavingsPlanService.CENTAVOS, rounding=ROUND_HALF_UP
        )
        return {
            "salario": salario,
            "necessidades": necessidades,
            "desejos": desejos,
            "guardar": salario - necessidades - desejos,
        }
