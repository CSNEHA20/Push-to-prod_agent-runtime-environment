"""ARC integration — AutoGen agent wrapper.

Intercepts ``agent.initiate_chat(...)``, ``agent.receive(...)``, and
``agent.generate_reply(...)`` so AutoGen conversational turns are
recorded in the Flight Recorder without modifying agent definitions.

Duck-type detection:
    ``hasattr(agent, "initiate_chat") and hasattr(agent, "system_message")``.
"""

from __future__ import annotations

from typing import Any, List, Optional

from ..._runtime import ARCRuntime


class AutoGenWrapper:
    """ARC-instrumented proxy for an AutoGen ``ConversableAgent``.

    ``initiate_chat``, ``receive``, and ``generate_reply`` are intercepted.
    All other attributes delegate to the original agent unchanged.
    """

    def __init__(self, agent: Any, runtime: ARCRuntime, name: str = "autogen") -> None:
        self._agent = agent
        self._runtime = runtime
        self._name = name

    def initiate_chat(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.initiate_chat(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.initiate_chat(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.initiate_chat",
        )

    def receive(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.receive(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.receive(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.receive",
        )

    def generate_reply(
        self,
        messages: Optional[List[Any]] = None,
        sender: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Intercept ``agent.generate_reply(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.generate_reply(messages=messages, sender=sender, **kwargs),
            args=(messages, sender),
            kwargs=kwargs,
            name=f"{self._name}.generate_reply",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def __repr__(self) -> str:
        return (
            f"AutoGenWrapper(name={self._name!r}, "
            f"session_id={self._runtime.session_id!r})"
        )


__all__ = ["AutoGenWrapper"]
