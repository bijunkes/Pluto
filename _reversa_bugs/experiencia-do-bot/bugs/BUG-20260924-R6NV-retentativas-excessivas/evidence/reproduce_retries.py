from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from src.services.gemini_service import GeminiService
from src.services.ia_service import IAService


gemini = GeminiService.__new__(GeminiService)
generate_content = Mock(side_effect=Exception("503 UNAVAILABLE"))
gemini.client = SimpleNamespace(
    models=SimpleNamespace(generate_content=generate_content)
)
gemini.categorias = ["Outros"]

groq = Mock()
groq.analisar_mensagem.return_value = {
    "produto": "Pão",
    "categoria": "Outros",
    "valor": 10.0,
}

service = IAService.__new__(IAService)
service.gemini = gemini
service.groq = groq

with (
    patch("src.services.gemini_service.time.sleep"),
    patch("src.services.ia_service.time.sleep"),
):
    resultado = service.analisar_mensagem("Comprei pão por R$ 10")

print(f"gemini_calls={generate_content.call_count}")
print(f"groq_calls={groq.analisar_mensagem.call_count}")
print(f"resultado={resultado['produto']}")

raise SystemExit(1 if generate_content.call_count > 3 else 0)
