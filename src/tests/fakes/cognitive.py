"""Fake cognitive layer for tests."""

from src.domain.cognitive_layer import (
    CognitiveLayer,
    CognitiveRequest,
    CognitiveResponse,
)


class FakeCognitiveLayer(CognitiveLayer):
    def __init__(self, suggestion: str = "[fake suggestion]") -> None:
        self._suggestion = suggestion
        self.calls: list[CognitiveRequest] = []

    async def ask(self, request: CognitiveRequest) -> CognitiveResponse:
        self.calls.append(request)
        return CognitiveResponse(suggestion=self._suggestion)
