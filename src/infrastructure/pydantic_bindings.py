"""pydantic-ai binding for the cognitive layer.

The only file that imports `pydantic_ai`. Provider exceptions are
caught here and translated into domain errors so the rest of the
system never sees pydantic-ai types.
"""

import os

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

from src.domain.cognitive_layer import (
    PROMPTS,
    CognitiveLayer,
    CognitiveRequest,
    CognitiveResponse,
)
from src.domain.errors import CognitiveLayerUnavailable, CognitiveOutputRefused


class PydanticAICognitiveLayer(CognitiveLayer):
    default_model: str = "openai:gpt-4o-mini"
    model_env_var: str = "ASSIST_MODEL"

    def __init__(self, model: str | None = None) -> None:
        self._agent: Agent = Agent(
            model or os.getenv(self.model_env_var, self.default_model),
            output_type=str,
        )

    async def ask(self, request: CognitiveRequest) -> CognitiveResponse:
        prompt: str = self._render(request)

        try:
            result = await self._agent.run(prompt)
        except UsageLimitExceeded as exc:
            raise CognitiveOutputRefused(str(exc)) from exc
        except ModelHTTPError as exc:
            raise CognitiveLayerUnavailable(str(exc)) from exc

        suggestion: str = (result.output or "").strip()
        if not suggestion:
            raise CognitiveOutputRefused("empty response from the model")

        return CognitiveResponse(suggestion=suggestion)

    def _render(self, request: CognitiveRequest) -> str:
        """Glue the domain-owned prompt to the user's input and context."""
        parts: list[str] = [PROMPTS[request.kind], "\n\n", request.input]
        if request.context:
            parts.extend(
                ["\n---\nContext (surrounding article):\n", request.context]
            )
        return "".join(parts)
