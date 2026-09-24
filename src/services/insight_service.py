from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class InsightService:

    FUSO = ZoneInfo("America/Sao_Paulo")

    @classmethod
    def agora(cls):
        # O banco armazena datas sem timezone; mantemos o horário brasileiro
        # como datetime ingênuo para as comparações existentes.
        return datetime.now(cls.FUSO).replace(tzinfo=None)

    def __init__(self, database):
        self.database = database

    def coletar_dados_periodo(self, data_inicio, data_fim):
        total = self.database.total_gastos_periodo(
            data_inicio,
            data_fim,
        )

        categorias = self.database.gastos_por_categoria(
            data_inicio,
            data_fim,
        )

        return {
            "total": total,
            "categorias": categorias,
        }

    def comparar_periodos(
        self,
        periodo_atual_inicio,
        periodo_atual_fim,
        periodo_anterior_inicio,
        periodo_anterior_fim,
    ):
        dados_atual = self.coletar_dados_periodo(
            periodo_atual_inicio,
            periodo_atual_fim,
        )

        dados_anterior = self.coletar_dados_periodo(
            periodo_anterior_inicio,
            periodo_anterior_fim,
        )

        total_atual = dados_atual["total"]
        total_anterior = dados_anterior["total"]

        if total_anterior > 0:
            variacao_total = (
                (total_atual - total_anterior)
                / total_anterior
            ) * 100
        elif total_atual > 0:
            variacao_total = None
        else:
            variacao_total = 0

        return {
            "atual": dados_atual,
            "anterior": dados_anterior,
            "variacao_total": variacao_total,
        }

    def comparar_categorias(self, dados_atual, dados_anterior):
        categorias_atual = {
            item["categoria"]: item["total"]
            for item in dados_atual["categorias"]
        }

        categorias_anterior = {
            item["categoria"]: item["total"]
            for item in dados_anterior["categorias"]
        }

        categorias = (
            set(categorias_atual)
            | set(categorias_anterior)
        )

        resultado = []

        for categoria in categorias:

            valor_atual = categorias_atual.get(
                categoria,
                0,
            )

            valor_anterior = categorias_anterior.get(
                categoria,
                0,
            )

            if valor_anterior > 0:

                variacao = (
                    (valor_atual - valor_anterior)
                    / valor_anterior
                ) * 100

            elif valor_atual > 0:

                variacao = None

            else:

                variacao = 0

            resultado.append(
                {
                    "categoria": categoria,
                    "atual": valor_atual,
                    "anterior": valor_anterior,
                    "variacao": variacao,
                }
            )

        return sorted(
            resultado,
            key=lambda item: item["atual"],
            reverse=True,
        )

    def gerar_analise_diaria(self):
        """
        Gera uma análise estruturada dos gastos das últimas 24 horas,
        comparando com as 24 horas anteriores.
        """

        agora = self.agora()

        inicio_atual = agora - timedelta(days=1)
        fim_atual = agora

        inicio_anterior = agora - timedelta(days=2)
        fim_anterior = agora - timedelta(days=1)

        comparacao = self.comparar_periodos(
            inicio_atual,
            fim_atual,
            inicio_anterior,
            fim_anterior,
        )

        variacoes_categorias = self.comparar_categorias(
            comparacao["atual"],
            comparacao["anterior"],
        )

        return {
            "periodo": "diario",
            "atual": comparacao["atual"],
            "anterior": comparacao["anterior"],
            "variacao_total": comparacao["variacao_total"],
            "variacoes_categorias": variacoes_categorias,
        }

    def gerar_analise_semanal(self):
        """
        Gera uma análise estruturada dos gastos da semana atual
        comparando com a semana anterior.
        """

        agora = self.agora()

        inicio_atual = agora - timedelta(days=7)
        fim_atual = agora

        inicio_anterior = agora - timedelta(days=14)
        fim_anterior = agora - timedelta(days=7)

        comparacao = self.comparar_periodos(
            inicio_atual,
            fim_atual,
            inicio_anterior,
            fim_anterior,
        )

        variacoes_categorias = self.comparar_categorias(
            comparacao["atual"],
            comparacao["anterior"],
        )

        return {
            "periodo": "semanal",
            "atual": comparacao["atual"],
            "anterior": comparacao["anterior"],
            "variacao_total": comparacao["variacao_total"],
            "variacoes_categorias": variacoes_categorias,
        }

    def gerar_analise_mensal(self):
        """
        Gera uma análise dos gastos do mês atual,
        comparando com o mês anterior.
        """

        agora = self.agora()

        inicio_atual = agora.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        # Primeiro dia do próximo mês
        if agora.month == 12:
            inicio_proximo = inicio_atual.replace(
                year=agora.year + 1,
                month=1,
            )
        else:
            inicio_proximo = inicio_atual.replace(
                month=agora.month + 1,
            )

        # Primeiro dia do mês anterior
        if agora.month == 1:
            inicio_anterior = inicio_atual.replace(
                year=agora.year - 1,
                month=12,
            )
        else:
            inicio_anterior = inicio_atual.replace(
                month=agora.month - 1,
            )

        comparacao = self.comparar_periodos(
            inicio_atual,
            inicio_proximo,
            inicio_anterior,
            inicio_atual,
        )

        variacoes_categorias = self.comparar_categorias(
            comparacao["atual"],
            comparacao["anterior"],
        )

        return {
            "periodo": "mensal",
            "atual": comparacao["atual"],
            "anterior": comparacao["anterior"],
            "variacao_total": comparacao["variacao_total"],
            "variacoes_categorias": variacoes_categorias,
        }

    def identificar_padroes(self, analise):
        """
        Identifica padrões relevantes nos gastos
        a partir de uma análise já calculada.
        """

        padroes = []

        variacao_total = analise["variacao_total"]

        # Aumento ou redução do gasto total
        if variacao_total is not None:

            if variacao_total > 0:
                padroes.append(
                    {
                        "tipo": "aumento_total",
                        "variacao": variacao_total,
                        "valor_atual": analise["atual"]["total"],
                        "valor_anterior": analise["anterior"]["total"],
                    }
                )

            elif variacao_total < 0:
                padroes.append(
                    {
                        "tipo": "reducao_total",
                        "variacao": variacao_total,
                        "valor_atual": analise["atual"]["total"],
                        "valor_anterior": analise["anterior"]["total"],
                    }
                )

        # Análise das categorias
        for categoria in analise["variacoes_categorias"]:

            variacao = categoria["variacao"]

            # Categoria nova
            if variacao is None and categoria["atual"] > 0:
                padroes.append(
                    {
                        "tipo": "nova_categoria",
                        "categoria": categoria["categoria"],
                        "valor_atual": categoria["atual"],
                    }
                )

            # Aumento de categoria
            elif variacao is not None and variacao > 0:
                padroes.append(
                    {
                        "tipo": "aumento_categoria",
                        "categoria": categoria["categoria"],
                        "variacao": variacao,
                        "valor_atual": categoria["atual"],
                        "valor_anterior": categoria["anterior"],
                    }
                )

            # Redução de categoria
            elif variacao is not None and variacao < 0:
                padroes.append(
                    {
                        "tipo": "reducao_categoria",
                        "categoria": categoria["categoria"],
                        "variacao": variacao,
                        "valor_atual": categoria["atual"],
                        "valor_anterior": categoria["anterior"],
                    }
                )

        return padroes

    def preparar_dados_para_ia(self, analise):
        """
        Prepara os dados da análise para serem enviados ao IAService.

        A IA recebe apenas informações relevantes e já calculadas
        pelo sistema, sem acesso direto ao banco de dados.
        """

        padroes = self.identificar_padroes(analise)

        return {
            "periodo": analise["periodo"],
            "total_atual": analise["atual"]["total"],
            "total_anterior": analise["anterior"]["total"],
            "variacao_total": analise["variacao_total"],
            "padroes": padroes,
        }

    def configurar_frequencia(self, frequencia):
        """
        Configura a frequência dos insights automáticos.
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

        self.database.atualizar_frequencia_insights(
            frequencia
        )

    def configurar_horario(self, horario):
        """Configura o horário diário/semanal dos insights."""
        self.database.atualizar_horario_insights(horario)

    def obter_configuracao(self):
        """
        Retorna a configuração atual dos insights.
        """

        return self.database.buscar_configuracao_insights()

    def gerar_dados_insight(self, periodo):
        """
        Gera os dados necessários para um insight.
        """

        if periodo == "diario":
            analise = self.gerar_analise_diaria()

        elif periodo == "semanal":
            analise = self.gerar_analise_semanal()

        elif periodo == "mensal":
            analise = self.gerar_analise_mensal()

        else:
            raise ValueError(
                "Período inválido. "
                "Use diario, semanal ou mensal."
            )

        return self.preparar_dados_para_ia(analise)

    def deve_gerar_insight(self, agora=None):
        configuracao = self.obter_configuracao()

        if configuracao is None:
            return False

        if not configuracao["ativo"]:
            return False

        frequencia = configuracao["frequencia"]

        if frequencia == "NENHUM":
            return False

        if agora is None:
            agora = self._agora_local()

        horario_configurado = configuracao["horario"]
        ultimo_envio = configuracao["ultimo_envio"]

        # Garante que horario_configurado seja time
        if hasattr(horario_configurado, "hour"):
            horario_configurado = horario_configurado.replace(
                second=0,
                microsecond=0
            )

        # ---------------------------------------------------------
        # PRIMEIRO ENVIO
        # ---------------------------------------------------------
        if ultimo_envio is None:
            return agora.time() >= horario_configurado

        # ---------------------------------------------------------
        # DIÁRIO
        # ---------------------------------------------------------
        if frequencia == "DIARIO":
            horario_envio_hoje = agora.replace(
                hour=horario_configurado.hour,
                minute=horario_configurado.minute,
                second=0,
                microsecond=0
            )

            # Ainda não chegou o horário configurado
            if agora < horario_envio_hoje:
                return False

            # Já enviou hoje no horário ou depois dele
            if (
                ultimo_envio.date() == agora.date()
                and ultimo_envio >= horario_envio_hoje
            ):
                return False

            return True

        # ---------------------------------------------------------
        # SEMANAL
        # ---------------------------------------------------------
        if frequencia == "SEMANAL":

            dias_desde_envio = (agora.date() - ultimo_envio.date()).days

            if dias_desde_envio < 7:
                return False

            return agora.time() >= horario_configurado

        return False

    # =========================================================
    # INSIGHTS DO DASHBOARD (texto pronto, sem chamar a IA)
    # =========================================================

    @staticmethod
    def _formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _insights_de_padroes(self, padroes, prefixo_id, secao):
        """
        Converte padrões estruturados (vindos de identificar_padroes)
        em textos amigáveis, já classificados por seção do dashboard
        (habito, comparativo, alerta ou recomendacao).
        """

        resultado = []

        for indice, padrao in enumerate(padroes):

            tipo = padrao["tipo"]

            if tipo == "aumento_total":
                resultado.append({
                    "id": f"{prefixo_id}-{indice}",
                    "type": "comparativo",
                    "title": "Seus gastos subiram",
                    "description": (
                        f"Percebi que você gastou {abs(padrao['variacao']):.0f}% a mais "
                        f"nesse {secao} do que no período anterior "
                        f"({self._formatar_moeda(padrao['valor_atual'])} contra "
                        f"{self._formatar_moeda(padrao['valor_anterior'])})."
                    ),
                })

            elif tipo == "reducao_total":
                resultado.append({
                    "id": f"{prefixo_id}-{indice}",
                    "type": "habito",
                    "title": "Seus gastos caíram",
                    "description": (
                        f"Boa! Você gastou {abs(padrao['variacao']):.0f}% a menos "
                        f"nesse {secao} do que no período anterior "
                        f"({self._formatar_moeda(padrao['valor_atual'])} contra "
                        f"{self._formatar_moeda(padrao['valor_anterior'])})."
                    ),
                })

            elif tipo == "nova_categoria":
                resultado.append({
                    "id": f"{prefixo_id}-{indice}",
                    "type": "habito",
                    "title": f"Nova categoria: {padrao['categoria']}",
                    "description": (
                        f"Percebi um novo tipo de gasto — "
                        f"{self._formatar_moeda(padrao['valor_atual'])} em "
                        f"{padrao['categoria']} nesse {secao}."
                    ),
                })

            elif tipo == "aumento_categoria":
                variacao = padrao["variacao"]
                grave = variacao >= 30
                resultado.append({
                    "id": f"{prefixo_id}-{indice}",
                    "type": "alerta" if grave else "habito",
                    "title": f"{padrao['categoria']} em alta",
                    "description": (
                        ("Talvez valha observar: " if grave else "Percebi que ")
                        + f"seus gastos com {padrao['categoria']} subiram {variacao:.0f}% "
                        f"nesse {secao}, indo de "
                        f"{self._formatar_moeda(padrao['valor_anterior'])} para "
                        f"{self._formatar_moeda(padrao['valor_atual'])}."
                        + (" Se esse padrão continuar, pode valer a pena revisar essa categoria." if grave else "")
                    ),
                })

            elif tipo == "reducao_categoria":
                resultado.append({
                    "id": f"{prefixo_id}-{indice}",
                    "type": "habito",
                    "title": f"{padrao['categoria']} em queda",
                    "description": (
                        f"Você reduziu {abs(padrao['variacao']):.0f}% os gastos com "
                        f"{padrao['categoria']} nesse {secao}, indo de "
                        f"{self._formatar_moeda(padrao['valor_anterior'])} para "
                        f"{self._formatar_moeda(padrao['valor_atual'])}."
                    ),
                })

        return resultado

    def montar_insights_dashboard(self):
        """
        Monta a lista de insights exibida na página de Insights do
        dashboard, combinando a análise semanal e a mensal.

        Não depende de chamadas à IA: os textos são gerados a partir
        dos padrões já calculados a partir dos dados reais do usuário,
        o que mantém a página rápida e sem custo de API.
        """

        insights = []

        try:
            analise_semanal = self.gerar_analise_semanal()
            padroes_semanal = self.identificar_padroes(analise_semanal)
            insights.extend(
                self._insights_de_padroes(padroes_semanal, "semanal", "últimos 7 dias")
            )
        except Exception:
            pass

        try:
            analise_mensal = self.gerar_analise_mensal()
            padroes_mensal = self.identificar_padroes(analise_mensal)
            insights.extend(
                self._insights_de_padroes(padroes_mensal, "mensal", "mês")
            )

            categorias_atual = analise_mensal["atual"]["categorias"]
            total_atual = analise_mensal["atual"]["total"]

            if categorias_atual and total_atual > 0:

                maior = max(categorias_atual, key=lambda item: item["total"])
                percentual = (maior["total"] / total_atual) * 100

                if percentual >= 35:
                    insights.append({
                        "id": "recomendacao-concentracao",
                        "type": "recomendacao",
                        "title": "Gastos concentrados",
                        "description": (
                            f"Quase {percentual:.0f}% do que você gastou este mês foi em "
                            f"{maior['categoria']}. Talvez valha observar se esse é o "
                            "equilíbrio que você gostaria de ter entre as categorias."
                        ),
                    })
        except Exception:
            pass

        return insights