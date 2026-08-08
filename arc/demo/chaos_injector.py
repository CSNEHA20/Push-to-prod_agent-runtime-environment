"""
ARC Chaos Injector
Simulates API failures, corrupted outputs, and network timeouts for testing ARC resilience layer.
"""

import random
import time
import logging
from typing import Optional

logger = logging.getLogger("arc.chaos_injector")


class ChaosInjector:
    """
    Chaos Injector class for simulating runtime failures in Claude AI agents.
    Provides methods to inject API errors, corrupt text outputs, and simulate network timeouts.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def inject_api_failure(self, probability: float = 0.3, force: bool = False) -> None:
        """
        Randomly raises a RuntimeError exception to simulate an Anthropic API 500 failure.
        """
        if not self.enabled and not force:
            return

        if force or random.random() < probability:
            logger.warning("💥 [Chaos Injector] Injecting simulated Anthropic API failure (500 Internal Server Error)")
            raise RuntimeError("Chaos Injector: Simulated Anthropic API failure (500 Internal Server Error)")

    def inject_bad_output(self, text: str, probability: float = 0.3, force: bool = False) -> str:
        """
        Randomly corrupts the output text to trigger low confidence scoring (< 0.2) in FlightRecorder.
        """
        if not self.enabled and not force:
            return text

        if force or random.random() < probability:
            logger.warning("💥 [Chaos Injector] Corrupting LLM output text to trigger low confidence score")
            return "i think probably i'm not sure might be uncertain short output"

        return text

    def inject_timeout(self, seconds: float = 2.0, probability: float = 0.3, force: bool = False) -> None:
        """
        Simulates an API request timeout by sleeping and raising a TimeoutError.
        """
        if not self.enabled and not force:
            return

        if force or random.random() < probability:
            logger.warning(f"💥 [Chaos Injector] Simulating API Timeout ({seconds}s)...")
            time.sleep(seconds)
            raise TimeoutError(f"Chaos Injector: Simulated API Request Timeout after {seconds} seconds")
