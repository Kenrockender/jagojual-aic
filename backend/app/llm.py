"""Integrasi LLM lokal (Qwen2.5-7B-Instruct + adapter LoRA).

Placeholder untuk MODE=local — DIISI pada M3. Saat scaffold (M0), MODE=local
belum diimplementasikan; gunakan MODE=mock.
"""

from .schemas import ChatMessage, EvaluateResponse, Scenario


def _not_ready() -> None:
    raise NotImplementedError(
        "MODE=local belum diimplementasikan (dikerjakan di M3). "
        "Set JAGOJUAL_MODE=mock untuk menjalankan scaffold."
    )


def generate_customer_reply(scenario: Scenario, history: list[ChatMessage], message: str) -> str:
    _not_ready()
    raise AssertionError  # unreachable


def evaluate_conversation(scenario: Scenario, history: list[ChatMessage]) -> EvaluateResponse:
    _not_ready()
    raise AssertionError  # unreachable
