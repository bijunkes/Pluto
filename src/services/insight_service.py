from datetime import datetime, timedelta

class InsightService:

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

        agora = datetime.now()

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

        agora = datetime.now()

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

        agora = datetime.now()

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
        """
        Verifica se está na hora de gerar um insight automático.
        """

        configuracao = self.obter_configuracao()

        if configuracao is None:
            return False

        if not configuracao["ativo"]:
            return False

        frequencia = configuracao["frequencia"]

        if frequencia == "NENHUM":
            return False

        if agora is None:
            agora = datetime.now()

        horario_configurado = configuracao["horario"]

        ultimo_envio = configuracao["ultimo_envio"]

        # Primeiro envio:
        # só pode acontecer depois do horário configurado.
        if ultimo_envio is None:
            return agora.time() >= horario_configurado

        # =========================
        # INSIGHT DIÁRIO
        # =========================
        if frequencia == "DIARIO":
            mesma_data = ultimo_envio.date() == agora.date()

            if mesma_data:
                return False

            return agora.time() >= horario_configurado

        # =========================
        # INSIGHT SEMANAL
        # =========================
        if frequencia == "SEMANAL":
            # Segunda-feira = 0
            inicio_semana = agora - timedelta(
                days=agora.weekday()
            )

            inicio_semana = inicio_semana.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            ultimo_envio_na_semana = (
                ultimo_envio >= inicio_semana
            )

            if ultimo_envio_na_semana:
                return False

            # O insight semanal só é enviado na segunda-feira.
            if agora.weekday() != 0:
                return False

            return agora.time() >= horario_configurado

        return False