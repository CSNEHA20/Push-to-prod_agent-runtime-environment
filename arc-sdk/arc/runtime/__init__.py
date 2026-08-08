"""ARC runtime — modular core execution engines.

Each subpackage owns one concern and exposes a structural interface only:

- :mod:`arc.runtime.scheduler` — execution scheduling & loop management
- :mod:`arc.runtime.recovery`  — self-healing rollback & state checkpointing
- :mod:`arc.runtime.verifier`  — compliance & policy verification
- :mod:`arc.runtime.firewall`  — context security & conflict filtering
- :mod:`arc.runtime.recorder`  — execution step tracing (Flight Recorder)
- :mod:`arc.runtime.plugins`   — plugin registry
- :mod:`arc.runtime.middleware`— interceptor middleware pipeline
- :mod:`arc.runtime.events`    — event broker & pub/sub dispatcher
- :mod:`arc.runtime.replay`    — replay-timeline assembler

The interfaces decouple the :class:`arc.ARC` facade from concrete engine
implementations, per PROJECT.md §5 ("Strict Decoupling"). Each subpackage also
ships a concrete default (``default.py``) that the ARC runtime composes.
"""

from __future__ import annotations

from .events import EventBus
from .firewall import Firewall
from .middleware import MiddlewarePipeline
from .planner import Planner
from .plugins import PluginRegistry
from .recorder import Recorder
from .recovery import RecoveryEngine
from .replay import ReplayStore
from .scheduler import Scheduler
from .verifier import Verifier

__all__ = [
    "Scheduler",
    "RecoveryEngine",
    "Verifier",
    "Firewall",
    "Recorder",
    "Planner",
    "PluginRegistry",
    "MiddlewarePipeline",
    "EventBus",
    "ReplayStore",
]
