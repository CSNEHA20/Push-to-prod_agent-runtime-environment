"""Tests for Execution Planner & Provider Adapters.

Tests that the execution graph drives runtime execution, and that provider
adapters correctly translate abstract planner decisions into vendor-specific SDK
request parameters (Anthropic, OpenAI, Gemini, Passthrough).
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from arc import ARC
from arc.config import ARCConfig
from arc.integrations.adapter import (
    PassthroughAdapter,
    make_provider_adapter,
)
from arc.integrations.anthropic.params import AnthropicParamAdapter
from arc.integrations.gemini.params import GeminiParamAdapter
from arc.integrations.openai.params import OpenAIParamAdapter
from arc.runtime.graph import ExecutionGraph, ExecutionNode, NodeKind, NodePhase
from arc.types import ExecutionPlan, ReasoningStrategy, ToolStrategy
from tests.conftest import FakeClient

SHORT_MESSAGES = [{"role": "user", "content": "Hi"}]
TOOLS = [{"name": f"t{i}", "description": "d", "input_schema": {"type": "object"}} for i in range(3)]


# ---------------------------------------------------------------------------
# Helper: Build a dummy DISPATCH node with custom config
# ---------------------------------------------------------------------------

def _make_dispatch_node(
    reasoning: str = "direct",
    thinking_budget: int = 0,
    tool_strategy: str = "none",
    context_budget: int = 512,
) -> ExecutionNode:
    return ExecutionNode(
        id="dispatch",
        kind=NodeKind.DISPATCH,
        phase=NodePhase.DISPATCH,
        config={
            "reasoning": reasoning,
            "thinking_budget": thinking_budget,
            "tool_strategy": tool_strategy,
            "context_budget": context_budget,
        },
    )


# ===========================================================================
# 1. Adapter Factory & Registry Tests
# ===========================================================================

class TestAdapterFactory:
    def test_anthropic_adapter_resolution(self) -> None:
        adapter = make_provider_adapter("anthropic")
        assert isinstance(adapter, AnthropicParamAdapter)

    def test_async_anthropic_adapter_resolution(self) -> None:
        adapter = make_provider_adapter("async_anthropic")
        assert isinstance(adapter, AnthropicParamAdapter)

    def test_openai_adapter_resolution(self) -> None:
        adapter = make_provider_adapter("openai")
        assert isinstance(adapter, OpenAIParamAdapter)

    def test_openai_client_adapter_resolution(self) -> None:
        adapter = make_provider_adapter("openai_client")
        assert isinstance(adapter, OpenAIParamAdapter)

    def test_gemini_adapter_resolution(self) -> None:
        adapter = make_provider_adapter("gemini")
        assert isinstance(adapter, GeminiParamAdapter)

    def test_unknown_provider_returns_passthrough(self) -> None:
        adapter = make_provider_adapter("unknown_vendor")
        assert isinstance(adapter, PassthroughAdapter)

    def test_none_provider_returns_passthrough(self) -> None:
        adapter = make_provider_adapter(None)
        assert isinstance(adapter, PassthroughAdapter)


# ===========================================================================
# 2. Anthropic Provider Adapter Unit Tests
# ===========================================================================

class TestAnthropicParamAdapter:
    def setup_method(self) -> None:
        self.adapter = AnthropicParamAdapter()

    def test_injects_extended_thinking(self) -> None:
        node = _make_dispatch_node(reasoning="extended", thinking_budget=8192)
        payload = {"model": "claude-sonnet-4-6", "max_tokens": 16000}
        res = self.adapter.prepare(payload, node)

        assert res["thinking"] == {"type": "enabled", "budget_tokens": 8192}
        assert res["max_tokens"] == 16000
        # Original payload remains un-mutated
        assert "thinking" not in payload

    def test_skips_thinking_if_developer_already_set(self) -> None:
        node = _make_dispatch_node(reasoning="extended", thinking_budget=8192)
        payload = {
            "model": "claude-sonnet-4-6",
            "thinking": {"type": "enabled", "budget_tokens": 4096},
        }
        res = self.adapter.prepare(payload, node)
        # Custom setting preserved
        assert res["thinking"] == {"type": "enabled", "budget_tokens": 4096}

    def test_adjusts_max_tokens_when_below_thinking_budget(self) -> None:
        node = _make_dispatch_node(reasoning="extended", thinking_budget=4000)
        payload = {"model": "claude-sonnet-4-6", "max_tokens": 2000}
        res = self.adapter.prepare(payload, node)

        assert res["max_tokens"] == 4001
        assert res["thinking"]["budget_tokens"] == 4000

    def test_injects_tool_choice_auto(self) -> None:
        node = _make_dispatch_node(tool_strategy="auto")
        payload = {"tools": TOOLS}
        res = self.adapter.prepare(payload, node)
        assert res["tool_choice"] == {"type": "auto"}

    def test_injects_tool_choice_parallel_as_any(self) -> None:
        node = _make_dispatch_node(tool_strategy="parallel")
        payload = {"tools": TOOLS}
        res = self.adapter.prepare(payload, node)
        assert res["tool_choice"] == {"type": "any"}

    def test_skips_tool_choice_if_no_tools(self) -> None:
        node = _make_dispatch_node(tool_strategy="parallel")
        payload = {"tools": []}
        res = self.adapter.prepare(payload, node)
        assert "tool_choice" not in res

    def test_skips_tool_choice_if_already_set(self) -> None:
        node = _make_dispatch_node(tool_strategy="parallel")
        payload = {"tools": TOOLS, "tool_choice": {"type": "auto"}}
        res = self.adapter.prepare(payload, node)
        assert res["tool_choice"] == {"type": "auto"}


# ===========================================================================
# 3. OpenAI Provider Adapter Unit Tests
# ===========================================================================

class TestOpenAIParamAdapter:
    def setup_method(self) -> None:
        self.adapter = OpenAIParamAdapter()

    def test_injects_reasoning_effort_high_for_extended(self) -> None:
        node = _make_dispatch_node(reasoning="extended")
        res = self.adapter.prepare({}, node)
        assert res["reasoning_effort"] == "high"

    def test_injects_reasoning_effort_medium_for_step_by_step(self) -> None:
        node = _make_dispatch_node(reasoning="step_by_step")
        res = self.adapter.prepare({}, node)
        assert res["reasoning_effort"] == "medium"

    def test_injects_reasoning_effort_low_for_direct(self) -> None:
        node = _make_dispatch_node(reasoning="direct")
        res = self.adapter.prepare({}, node)
        assert res["reasoning_effort"] == "low"

    def test_skips_reasoning_effort_if_already_set(self) -> None:
        node = _make_dispatch_node(reasoning="extended")
        res = self.adapter.prepare({"reasoning_effort": "medium"}, node)
        assert res["reasoning_effort"] == "medium"

    def test_injects_tool_choice_required_for_parallel(self) -> None:
        node = _make_dispatch_node(tool_strategy="parallel")
        res = self.adapter.prepare({"tools": TOOLS}, node)
        assert res["tool_choice"] == "required"


# ===========================================================================
# 4. Gemini Provider Adapter Unit Tests
# ===========================================================================

class TestGeminiParamAdapter:
    def setup_method(self) -> None:
        self.adapter = GeminiParamAdapter()

    def test_injects_thinking_config_enabled(self) -> None:
        node = _make_dispatch_node(reasoning="extended", thinking_budget=2048)
        res = self.adapter.prepare({}, node)
        assert res["generation_config"] == {
            "thinking_config": {"mode": "enabled", "budget": 2048}
        }

    def test_injects_thinking_config_auto(self) -> None:
        node = _make_dispatch_node(reasoning="step_by_step")
        res = self.adapter.prepare({}, node)
        assert res["generation_config"] == {"thinking_config": {"mode": "auto"}}

    def test_skips_thinking_config_for_direct(self) -> None:
        node = _make_dispatch_node(reasoning="direct")
        res = self.adapter.prepare({}, node)
        assert "generation_config" not in res

    def test_preserves_existing_generation_config(self) -> None:
        node = _make_dispatch_node(reasoning="step_by_step")
        res = self.adapter.prepare({"generation_config": {"temperature": 0.7}}, node)
        assert res["generation_config"] == {
            "temperature": 0.7,
            "thinking_config": {"mode": "auto"},
        }


# ===========================================================================
# 5. Integration Tests: Execution Graph Drives Provider SDK Calls
# ===========================================================================

class TestExecutionPlannerIntegration:
    def test_end_to_end_anthropic_param_injection(self) -> None:
        client = FakeClient()
        arc = ARC(client, provider="anthropic")

        # Request with tools and hint forces EXTENDED reasoning and PARALLEL tool strategy
        arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            messages=SHORT_MESSAGES,
            tools=TOOLS,
        )

        sent_kwargs = client.messages.calls[-1]
        assert "thinking" in sent_kwargs
        assert sent_kwargs["thinking"]["type"] == "enabled"
        assert sent_kwargs["thinking"]["budget_tokens"] > 0
        assert sent_kwargs["tool_choice"] == {"type": "any"}

    def test_end_to_end_trace_records_enriched_params(self) -> None:
        client = FakeClient()
        arc = ARC(client, provider="anthropic")

        arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            messages=SHORT_MESSAGES,
            tools=TOOLS,
        )

        steps = arc.trace()
        assert len(steps) == 1
        plan_data = steps[0].input_data["plan"]
        assert plan_data["reasoning_strategy"] == "extended"
        assert plan_data["tool_strategy"] == "parallel"
