"""Mode Pelanggan — menghasilkan balasan pelanggan AI untuk satu giliran."""

from . import mock
from .config import settings
from .schemas import ChatMessage, Scenario


def customer_reply(scenario: Scenario, history: list[ChatMessage], message: str) -> str:
    if settings.mode == "mock":
        return mock.mock_customer_reply(scenario, history, message)
    from . import llm

    return llm.generate_customer_reply(scenario, history, message)
