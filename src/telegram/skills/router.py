from __future__ import annotations

from collections.abc import Iterable

from .base import Skill
from .builtin import SKILLS_PADRAO


class SkillRouter:
    """Registro extensivel que seleciona a melhor skill para cada mensagem."""

    def __init__(self, skills: Iterable[Skill] | None = None):
        origem = skills if skills is not None else (classe() for classe in SKILLS_PADRAO)
        self._skills = list(origem)

    @property
    def skills(self) -> tuple[Skill, ...]:
        return tuple(self._skills)

    def registrar(self, skill: Skill) -> None:
        if any(item.info.nome == skill.info.nome for item in self._skills):
            raise ValueError(f"Skill ja registrada: {skill.info.nome}")
        self._skills.append(skill)

    def selecionar(self, texto: str) -> Skill | None:
        candidatas = []
        for skill in self._skills:
            pontos = skill.pontuacao(texto)
            if pontos:
                candidatas.append((pontos, skill.prioridade, skill))
        return max(candidatas, key=lambda item: (item[0], item[1]))[2] if candidatas else None

    async def executar(self, texto: str, bot, update, context) -> bool:
        skill = self.selecionar(texto)
        if skill is None:
            return False
        await skill.executar(bot, update, context)
        return True
