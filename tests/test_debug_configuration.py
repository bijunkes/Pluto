import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = "${workspaceFolder}/.venv/Scripts/python.exe"


def _json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_debugpy_esta_declarado_nas_dependencias_de_desenvolvimento():
    requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")

    assert any(
        line.strip().lower().startswith("debugpy")
        for line in requirements.splitlines()
    )


def test_launch_usa_interpretador_do_ambiente_virtual():
    launch = _json(".vscode/launch.json")
    configuration = next(
        item
        for item in launch["configurations"]
        if item["name"] == "Pluto: iniciar bot"
    )
    settings = _json(".vscode/settings.json")

    assert configuration["type"] == "debugpy"
    assert configuration["python"] == VENV_PYTHON
    assert configuration["envFile"] == "${workspaceFolder}/.env"
    assert settings["python.defaultInterpreterPath"] == VENV_PYTHON
    assert settings["python.envFile"] == "${workspaceFolder}/.env"


def test_extensoes_de_python_sao_recomendadas():
    recommendations = set(_json(".vscode/extensions.json")["recommendations"])

    assert {"ms-python.python", "ms-python.debugpy"} <= recommendations
