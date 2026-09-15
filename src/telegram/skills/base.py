from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Pattern

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes


def normalizar(texto: str) -> str:
    """Remove acentos e diferencas de caixa para comparar intencoes."""
    import unicodedata

    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(char for char in texto if not unicodedata.combining(char))


@dataclass(frozen=True)
class SkillInfo:
    nome: str
    descricao: str
    exemplos: tuple[str, ...]


class Skill(ABC):
    info: SkillInfo
    prioridade = 0
    padroes: tuple[Pattern[str], ...] = ()

    def pontuacao(self, texto: str) -> int:
        texto_normalizado = normalizar(texto)
        return sum(1 for padrao in self.padroes if padrao.search(texto_normalizado))

    @abstractmethod
    async def executar(self, bot, update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
        raise NotImplementedError


def padrao(expressao: str) -> Pattern[str]:
    return re.compile(expressao, re.IGNORECASE)
