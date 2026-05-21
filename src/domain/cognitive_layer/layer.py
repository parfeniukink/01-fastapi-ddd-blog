"""Cognitive-layer contract — owned by the domain."""

import abc

from .entities import CognitiveRequest, CognitiveResponse


class CognitiveLayer(abc.ABC):
    @abc.abstractmethod
    async def ask(self, request: CognitiveRequest) -> CognitiveResponse: ...
