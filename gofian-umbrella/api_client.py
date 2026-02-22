"""
GOFIAN Umbrella BUILDER v2.2.0
Module: api_client
Description: OpenAI API wrapper with retry logic, timeout handling, token counting,
             error normalization. Injectable design for multi-provider support.
Author: Philippe Maréchal / GOFIAN AI
Last modified: 2026-02-23
"""

import logging
import os
import time

from openai import OpenAI, RateLimitError, APITimeoutError, APIError

from config import MODEL, MAX_TOKENS, TEMPERATURE, API_TIMEOUT

logger = logging.getLogger(__name__)


class AIClient:
    """
    Wrapper around OpenAI API with:
    - Configurable model, tokens, temperature
    - Retry logic with exponential backoff for rate limits
    - Separate handling for different error types
    - Timeout protection
    - Startup validation
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=API_TIMEOUT,
        )
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE

        logger.info(f"AIClient initialized: model={self.model}, timeout={API_TIMEOUT}s")

    def validate_key(self) -> bool:
        """Verify API key works at startup. Returns True if valid."""
        try:
            self.client.models.list()
            logger.info("API key validation: OK")
            return True
        except Exception as e:
            logger.error(f"API key validation FAILED: {type(e).__name__}")
            return False

    def chat(self, messages: list, max_retries: int = 2) -> dict:
        """
        Send messages to OpenAI and return parsed response.

        Args:
            messages: List of message dicts [{"role": "...", "content": "..."}]
            max_retries: Number of retry attempts for rate limit errors

        Returns:
            {"content": str, "usage": dict} on success
            {"error": str, "error_type": str} on failure
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_completion_tokens=self.max_tokens,
                )

                content = response.choices[0].message.content or ""

                if not content.strip():
                    logger.warning("Empty response from API")
                    return {
                        "error": "The AI returned an empty response. Please try again.",
                        "error_type": "empty_response",
                    }

                usage = {}
                if response.usage:
                    usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }

                return {"content": content, "usage": usage}

            except RateLimitError as e:
                if attempt < max_retries:
                    wait = 2 ** (attempt + 1)  # 2s, 4s
                    logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                    time.sleep(wait)
                    continue
                logger.error("Rate limit exceeded after all retries")
                return {
                    "error": "Our AI is very busy right now. Please try again in a moment.",
                    "error_type": "rate_limit",
                }

            except APITimeoutError:
                logger.error(f"API timeout after {API_TIMEOUT}s")
                return {
                    "error": "The AI took too long to respond. Please try again.",
                    "error_type": "timeout",
                }

            except APIError as e:
                logger.error(f"OpenAI API error: {e.status_code} - {type(e).__name__}")
                return {
                    "error": "Service temporarily unavailable. Please try again.",
                    "error_type": "api_error",
                }

            except Exception as e:
                # Catch-all: NEVER leak internal details to the user
                logger.error(f"Unexpected error: {type(e).__name__} - {str(e)}")
                return {
                    "error": "Something went wrong. Please try again.",
                    "error_type": "unknown",
                }

        # Should not reach here, but safety net
        return {
            "error": "Service temporarily unavailable.",
            "error_type": "exhausted_retries",
        }
