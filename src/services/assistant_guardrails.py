import re
import time
from collections import defaultdict, deque


class GuardrailViolation(ValueError):
    pass


class AssistantGuardrails:
    MAX_MESSAGE_LENGTH = 2000
    MAX_HISTORY_ITEMS = 12
    REQUESTS_PER_MINUTE = 15

    _injection_patterns = (
        re.compile(r"ignore (todas|as|suas|the|previous).*(instrucoes|instructions)", re.I),
        re.compile(r"(revele|mostre|exiba|print).*(system prompt|prompt do sistema)", re.I),
        re.compile(r"(api[_ -]?key|senha|token).*(revele|mostre|exiba)", re.I),
        re.compile(r"finja que (nao ha|voce nao tem).*(regras|restricoes)", re.I),
    )
    _secret_pattern = re.compile(
        r"(?i)(api[_ -]?key|authorization|senha|password|token)\s*[:=]\s*\S+"
    )
    _unsafe_claims = (
        re.compile(r"\b(retorno|lucro|rentabilidade) garantid[oa]\b", re.I),
        re.compile(r"\bsem risco\b", re.I),
        re.compile(r"\bcompre agora\b", re.I),
    )

    def __init__(self):
        self._requests = defaultdict(deque)

    def validar_entrada(self, usuario_id: int, mensagem: str) -> str:
        mensagem = (mensagem or "").strip()
        if not mensagem:
            raise GuardrailViolation("Envie uma mensagem para eu poder ajudar.")
        if len(mensagem) > self.MAX_MESSAGE_LENGTH:
            raise GuardrailViolation(
                f"A mensagem deve ter no maximo {self.MAX_MESSAGE_LENGTH} caracteres."
            )
        if self._secret_pattern.search(mensagem):
            raise GuardrailViolation(
                "Por seguranca, nao envie senhas, tokens ou chaves de API na conversa."
            )
        if any(pattern.search(mensagem) for pattern in self._injection_patterns):
            raise GuardrailViolation(
                "Nao posso alterar minhas regras internas nem revelar instrucoes do sistema."
            )

        agora = time.monotonic()
        fila = self._requests[usuario_id]
        while fila and agora - fila[0] >= 60:
            fila.popleft()
        if len(fila) >= self.REQUESTS_PER_MINUTE:
            raise GuardrailViolation(
                "Muitas mensagens em pouco tempo. Aguarde um minuto e tente novamente."
            )
        fila.append(agora)
        return mensagem

    def limitar_historico(self, historico) -> list[dict]:
        seguro = []
        for item in list(historico or [])[-self.MAX_HISTORY_ITEMS:]:
            role = item.get("role")
            content = str(item.get("content", ""))[:self.MAX_MESSAGE_LENGTH]
            if role in {"user", "assistant"} and not self._secret_pattern.search(content):
                seguro.append({"role": role, "content": content})
        return seguro

    def validar_saida(self, resposta: str, assunto_investimento: bool) -> str:
        resposta = self._secret_pattern.sub("[dado sensivel removido]", resposta or "")
        if any(pattern.search(resposta) for pattern in self._unsafe_claims):
            return (
                "Nao posso prometer retornos nem indicar uma operacao como livre de risco. "
                "Posso explicar os riscos, custos e cenarios para apoiar sua decisao."
            )
        if assunto_investimento:
            aviso = (
                "\n\nConteudo educativo, nao uma recomendacao individual de investimento. "
                "Considere seu perfil, objetivos, custos e riscos."
            )
            if "nao uma recomendacao" not in resposta.casefold():
                resposta += aviso
        return resposta[:4000]
