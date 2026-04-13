"""
LLM Client for PADI.AI API.
Provides LiteLLM-based routing with COPPA-compliant local model for student-facing features.

Critical COPPA Compliance:
- Student tutoring ALWAYS uses local Ollama (never sends data to cloud)
- Question generation and admin features can use cloud LLMs
- This routing is non-negotiable for COPPA compliance
"""

import litellm
from litellm import completion, acompletion
from typing import Any, Optional
from enum import Enum
import logging

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMPurpose(Enum):
    """LLM usage purpose for COPPA-compliant routing."""

    STUDENT_TUTORING = "student_tutoring"  # Always local
    ASSESSMENT = "assessment"  # Local
    QUESTION_GENERATION = "question_generation"  # Can use cloud
    ADMIN = "admin"  # Can use cloud
    ANALYTICS = "analytics"  # Local preferred


class LLMClient:
    """
    LiteLLM client with COPPA-compliant model routing.
    """

    def __init__(self):
        self.settings = settings
        self._initialize_litellm()

    def _initialize_litellm(self) -> None:
        """Initialize LiteLLM with settings."""
        litellm.set_verbose = False
        litellm.suppress_debug_info = True

        # Configure timeouts
        litellm.request_timeout = self.settings.LLM_TIMEOUT_SECONDS

        # Configure retries
        litellm.num_retries = 3

    def _get_model_for_purpose(self, purpose: LLMPurpose) -> str:
        """
        Get the appropriate model for a given purpose (COPPA compliance).

        Args:
            purpose: The purpose of the LLM call

        Returns:
            str: Model identifier (e.g., "ollama/qwen2.5:72b")
        """
        routing_map = {
            LLMPurpose.STUDENT_TUTORING: self.settings.LLM_ROUTING__TUTOR,
            LLMPurpose.ASSESSMENT: self.settings.LLM_ROUTING__ASSESSMENT,
            LLMPurpose.QUESTION_GENERATION: self.settings.LLM_ROUTING__QUESTION_GEN,
            LLMPurpose.ADMIN: self.settings.LLM_ROUTING__ADMIN,
            LLMPurpose.ANALYTICS: self.settings.LLM_ROUTING__TUTOR,  # Prefer local
        }

        model = routing_map.get(purpose, self.settings.OLLAMA_DEFAULT_MODEL)

        logger.debug(f"Routing {purpose.value} to model: {model}")
        return model

    def complete(
        self,
        messages: list[dict[str, Any]],
        purpose: LLMPurpose = LLMPurpose.STUDENT_TUTORING,
        **kwargs: Any,
    ) -> Any:
        """
        Complete an LLM call with COPPA-compliant routing.

        Args:
            messages: List of message dictionaries
            purpose: Purpose of the LLM call (determines routing)
            **kwargs: Additional arguments passed to litellm.completion

        Returns:
            Any: Litellm completion response

        Raises:
            Exception: If the LLM call fails
        """
        model = self._get_model_for_purpose(purpose)

        try:
            response = completion(
                model=model,
                messages=messages,
                **kwargs,
            )
            return response
        except Exception as e:
            logger.error(f"LLM completion failed for {purpose.value}: {e}")
            raise

    async def acomplete(
        self,
        messages: list[dict[str, Any]],
        purpose: LLMPurpose = LLMPurpose.STUDENT_TUTORING,
        **kwargs: Any,
    ) -> Any:
        """
        Async complete an LLM call with COPPA-compliant routing.

        Args:
            messages: List of message dictionaries
            purpose: Purpose of the LLM call (determines routing)
            **kwargs: Additional arguments passed to litellm.acompletion

        Returns:
            Any: Litellm completion response

        Raises:
            Exception: If the LLM call fails
        """
        model = self._get_model_for_purpose(purpose)

        try:
            response = await acompletion(
                model=model,
                messages=messages,
                **kwargs,
            )
            return response
        except Exception as e:
            logger.error(f"LLM acompletion failed for {purpose.value}: {e}")
            raise

    def get_health(self) -> dict[str, Any]:
        """
        Check LLM health and connectivity.

        Returns:
            dict: Health status including model and connectivity
        """
        health = {
            "status": "healthy",
            "tutor_model": self.settings.LLM_ROUTING__TUTOR,
            "assessment_model": self.settings.LLM_ROUTING__ASSESSMENT,
            "question_gen_model": self.settings.LLM_ROUTING__QUESTION_GEN,
            "admin_model": self.settings.LLM_ROUTING__ADMIN,
            "ollama_base_url": self.settings.OLLAMA_BASE_URL,
        }

        # Check Ollama connectivity
        try:
            response = litellm.completion(
                model="ollama/qwen2.5:72b",
                messages=[{"role": "user", "content": "ping"}],
                timeout=5,
            )
            health["ollama_status"] = "connected"
        except Exception as e:
            health["ollama_status"] = "disconnected"
            health["ollama_error"] = str(e)

        return health


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get singleton LLM client instance.

    Returns:
        LLMClient: Global LLM client instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
