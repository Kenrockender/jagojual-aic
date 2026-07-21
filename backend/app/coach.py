"""Mode Pelatih — menilai seluruh percakapan di akhir sesi (inti inovasi).

Di MODE=local (M3) inilah tugas yang dijalankan LLM fine-tuned.
"""

from . import mock
from .config import settings
from .schemas import ChatMessage, EvaluateResponse, Scenario


def evaluate(scenario: Scenario, history: list[ChatMessage]) -> EvaluateResponse:
    if settings.mode == "mock":
        return mock.mock_evaluate(scenario, history)
    from . import llm

    return llm.evaluate_conversation(scenario, history)
