"""
ARC Demo Agent — Investment Research Agent
Showcases all three ARC engines:
1. Engine 1: Flight Recorder (Step recording, timeline & token tracking)
2. Engine 2: Context Firewall (Conflict detection between $7.3B vs $8.1B funding figures)
3. Engine 3: Recovery Engine (Auto-rollback and recovery from API / low-confidence failure)
"""

import os
import sys
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any, List

import anthropic

# Module import compatibility handling
try:
    from core.arc_runtime import ARCRuntime
except ImportError:
    try:
        from arc.backend.core.arc_runtime import ARCRuntime
    except ImportError:
        from backend.core.arc_runtime import ARCRuntime

try:
    from chaos_injector import ChaosInjector
except ImportError:
    try:
        from arc.demo.chaos_injector import ChaosInjector
    except ImportError:
        from demo.chaos_injector import ChaosInjector

logger = logging.getLogger("arc.demo_agent")


class MockAnthropicResponseBlock:
    def __init__(self, text: str):
        self.text = text


class MockAnthropicUsage:
    def __init__(self, input_tokens: int = 150, output_tokens: int = 350):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockAnthropicResponse:
    def __init__(self, text: str):
        self.content = [MockAnthropicResponseBlock(text)]
        self.usage = MockAnthropicUsage()


class MockAnthropicClient:
    """
    Fallback mock client for offline testing or when ANTHROPIC_API_KEY is not configured.
    Provides realistic Claude model responses for Anthropic Investment Research.
    """

    class Messages:
        def __init__(self, parent):
            self.parent = parent

        def create(self, **kwargs) -> MockAnthropicResponse:
            messages = kwargs.get("messages", [])
            last_msg = ""
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    last_msg = str(msg.get("content", ""))
                    break

            if "Section 1" in last_msg or "Company Overview" in last_msg:
                text = (
                    "### Anthropic Investment Brief — Section 1: Corporate Overview & Product Lineup\n\n"
                    "**Corporate Overview:**\n"
                    "Founded in 2021 by Dario Amodei and Daniela Amodei (former OpenAI research leaders), Anthropic is an AI safety "
                    "and research company headquartered in San Francisco. The company is dedicated to building reliable, steerable, "
                    "and interpretable AI models using Constitutional AI principles.\n\n"
                    "**Key Products & Foundation Models:**\n"
                    "1. **Claude Sonnet 4.6:** Flagship frontier intelligence model optimized for complex code synthesis, structured data extraction, and multi-step agentic workflows.\n"
                    "2. **Claude 3.5 Opus:** Deep reasoning engine designed for scientific research and high-complexity analytics.\n"
                    "3. **Claude 3.5 Haiku:** Ultra-fast, low-latency foundation model for real-time edge processing and high-throughput workloads.\n"
                    "4. **Artifacts & Computer Use API:** Interactive canvas workspace and native GUI automation interfaces."
                )
            elif "Section 2" in last_msg or "Financial Overview" in last_msg:
                text = (
                    "### Anthropic Investment Brief — Section 2: Financial Analysis & Market Positioning\n\n"
                    "**Capital Structure & Verified Funding:**\n"
                    "Anthropic has secured $7.3 Billion in cumulative total funding, anchored by major strategic commitments from "
                    "Amazon ($4.0B investment with AWS default cloud partnership) and Google ($2.0B strategic investment). "
                    "*(Note: ARC Context Firewall successfully detected and filtered conflicting media reports claiming $8.1B total funding).* \n\n"
                    "**Competitive Landscape:**\n"
                    "Anthropic commands a strong market share alongside OpenAI (GPT-4o/o3) and Google DeepMind (Gemini 2.0). "
                    "Key differentiators include industry-leading safety standards, Constitutional AI alignment, and enterprise privacy guarantees."
                )
            else:
                text = (
                    "# ANTHROPIC ENTERPRISE INVESTMENT BRIEF\n\n"
                    "## Executive Summary\n"
                    "Anthropic represents a premier investment opportunity in frontier generative AI technology. "
                    "With $7.3 Billion in strategic capital from Amazon and Google, Anthropic combines state-of-the-art foundation "
                    "models (Claude Sonnet 4.6, Opus, Haiku) with industry-leading Constitutional AI safety standards.\n\n"
                    "## Key Financial & Strategic Highlights\n"
                    "- **Verified Raised Funding:** $7.3 Billion (Audited Pitchbook Verified)\n"
                    "- **Primary Strategic Partners:** Amazon (AWS Bedrock), Google Cloud\n"
                    "- **Core Product Portfolio:** Claude Sonnet 4.6, Opus 3.5, Haiku 3.5, Computer Use API\n"
                    "- **Competitive Position:** Top-tier enterprise AI partner with high developer adoption\n\n"
                    "**Investment Verdict:** Strongly Favorable / Overweight"
                )

            return MockAnthropicResponse(text)

    def __init__(self):
        self.messages = self.Messages(self)


def get_anthropic_client() -> Any:
    """Returns Anthropic API client if ANTHROPIC_API_KEY is configured, else fallback mock client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "mock-key":
        try:
            return anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client with API key: {e}. Falling back to MockAnthropicClient.")
            return MockAnthropicClient()
    logger.info("No ANTHROPIC_API_KEY found in environment. Using MockAnthropicClient for ARC demo.")
    return MockAnthropicClient()


# -------------------------------------------------------------------
# Simulated Search Tools
# -------------------------------------------------------------------

def search_anthropic_overview(query: str) -> Dict[str, Any]:
    """Step 1: Search for Anthropic overview (simulated realistic data)."""
    return {
        "company": "Anthropic PBC",
        "founded": 2021,
        "founders": ["Dario Amodei", "Daniela Amodei"],
        "headquarters": "San Francisco, CA",
        "mission": "Build reliable, steerable, and interpretable AI systems using Constitutional AI.",
        "category": "Frontier AI Safety & Foundation Models",
    }


def search_funding_information(query: str) -> List[Dict[str, Any]]:
    """
    Step 2: Search for funding information.
    Returns two conflicting sources to trigger Context Firewall conflict detection:
    - Source A: $7.3B total raised (Audited pitchbook)
    - Source B: $8.1B total raised (Unverified tech blog rumor)
    """
    return [
        {
            "name": "audited_pitchbook_2025.pdf",
            "content": (
                "Anthropic's total verified funding raised to date stands at $7.3 Billion, including "
                "Amazon's $4.0B commitment and Google's $2.0B strategic investment round."
            ),
        },
        {
            "name": "tech_rumors_daily_blog.html",
            "content": (
                "Anthropic has raised a total of $8.1 Billion in cumulative funding to date following an "
                "unannounced Series D extension debt facility in Q3."
            ),
        },
    ]


def search_products_list(query: str) -> Dict[str, Any]:
    """Step 3: Search for key Anthropic Claude products."""
    return {
        "flagship_models": [
            {"name": "Claude Sonnet 4.6", "type": "Frontier Reasoning & Coding"},
            {"name": "Claude 3.5 Opus", "type": "Deep Complex Analysis"},
            {"name": "Claude 3.5 Haiku", "type": "High Speed & Low Latency"},
        ],
        "developer_tools": ["Artifacts Interactive Canvas", "Computer Use GUI API", "Prompt Caching"],
    }


def search_competitors(query: str) -> Dict[str, Any]:
    """Step 4: Search for frontier AI competitors."""
    return {
        "primary_competitors": [
            {"name": "OpenAI", "models": ["GPT-4o", "o1", "o3-mini"], "market": "Consumer & Enterprise"},
            {"name": "Google DeepMind", "models": ["Gemini 1.5 Pro", "Gemini 2.0 Flash"], "market": "Cloud & Ecosystem"},
            {"name": "Meta AI", "models": ["Llama 3.3 70B"], "market": "Open Source Weights"},
        ]
    }


# -------------------------------------------------------------------
# Main Async Agent Runner
# -------------------------------------------------------------------

async def run_demo_agent(
    task: str = "Research Anthropic, find their latest funding, key products, and write an investment brief",
    scenario: str = "research_company",
    inject_chaos: bool = False,
    session_id: Optional[Union[uuid.UUID, str]] = None,
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Executes the Investment Research Demo Agent wrapped in ARCRuntime.

    Steps:
    1. Search for Anthropic overview (simulated tool call)
    2. Search for funding information (2 conflicting sources: $7.3B vs $8.1B -> Context Firewall conflict)
    3. Search for products list (simulated tool call)
    4. Search for competitors (simulated tool call)
    5. Write investment brief section 1 (Claude API call with context firewall filtering)
    6. Write investment brief section 2 (Claude API call with optional chaos injection & auto-recovery)
    7. Compile final investment brief (Claude API call & session complete)
    """
    client = get_anthropic_client()
    chaos = ChaosInjector(enabled=inject_chaos)

    arc = ARCRuntime(
        anthropic_client=client,
        agent_name="Investment Research Agent",
        task=task,
        db_session=db_session,
        session_id=session_id,
    )

    logger.info(f"🚀 Starting ARC Demo Agent. Session ID: {arc.session_id} | Chaos: {inject_chaos}")

    results: Dict[str, Any] = {}

    # Step 1: Search Anthropic Overview
    overview_data = await arc.run_tool(
        tool_name="search_anthropic_overview",
        tool_input={"query": "Anthropic company overview founders mission"},
        tool_fn=search_anthropic_overview,
    )
    results["overview"] = overview_data

    # Step 2: Search Funding Information (returns conflicting sources $7.3B vs $8.1B)
    funding_sources = await arc.run_tool(
        tool_name="search_funding_information",
        tool_input={"query": "Anthropic total funding capital raised Amazon Google"},
        tool_fn=search_funding_information,
    )
    results["funding_sources"] = funding_sources

    # Step 3: Search Key Products
    products_data = await arc.run_tool(
        tool_name="search_products_list",
        tool_input={"query": "Anthropic Claude models Sonnet Opus Haiku APIs"},
        tool_fn=search_products_list,
    )
    results["products"] = products_data

    # Step 4: Search Competitors
    competitors_data = await arc.run_tool(
        tool_name="search_competitors",
        tool_input={"query": "OpenAI Google DeepMind Meta AI competitors"},
        tool_fn=search_competitors,
    )
    results["competitors"] = competitors_data

    # Step 5: Write Investment Brief Section 1 (Claude call with Context Firewall active)
    messages_sec1 = [
        {
            "role": "user",
            "content": (
                f"Task: {task}\n\n"
                "Please write Section 1 of the Anthropic Investment Brief: Company Overview, Core Mission, "
                "Product Portfolio (Claude Sonnet 4.6, Opus, Haiku), and Market Position based on the retrieved context."
            ),
        }
    ]

    # Pass the conflicting funding sources so Context Firewall evaluates & flags the numerical conflict!
    sec1_text = await arc.call_claude(
        messages=messages_sec1,
        context_sources=funding_sources,
    )
    results["section_1"] = sec1_text

    # Step 6: Write Investment Brief Section 2 (Claude call with optional Chaos Injection & Recovery)
    messages_sec2 = [
        {
            "role": "user",
            "content": (
                "Please write Section 2 of the Anthropic Investment Brief: Financial Overview, Verified Funding Analysis "
                "($7.3B vs $8.1B discrepancy resolution), Risks, and Competitive Landscape."
            ),
        }
    ]

    sec2_text = ""
    if inject_chaos:
        try:
            # Simulate an API failure or corrupted output on first attempt
            chaos.inject_api_failure(probability=1.0, force=True)
            sec2_text = await arc.call_claude(messages=messages_sec2)
        except Exception as e:
            logger.warning(f"⚠️ Injected failure captured at Step 6: {e}. Initiating Recovery Engine rollback & retry.")
            # Trigger Recovery Engine rollback to latest valid checkpoint
            recovery_res = await arc.recovery_engine.recover(
                session_id=arc.session_id,
                failed_at_step=arc.step_counter,
                failure_type="api_error",
                error_message=f"Simulated API Failure: {e}",
            )
            # Re-execute step 6 after recovery
            logger.info("🔄 Step 6 successfully recovered from checkpoint. Re-executing Claude API call.")
            sec2_text = await arc.call_claude(messages=messages_sec2, _is_retry=True)
    else:
        sec2_text = await arc.call_claude(messages=messages_sec2)

    results["section_2"] = sec2_text

    # Step 7: Compile Final Brief
    messages_final = [
        {
            "role": "user",
            "content": (
                f"Please compile the complete executive Anthropic Investment Brief by combining Section 1 and Section 2:\n\n"
                f"Section 1:\n{sec1_text}\n\n"
                f"Section 2:\n{sec2_text}"
            ),
        }
    ]

    final_brief = await arc.call_claude(messages=messages_final)
    results["final_brief"] = final_brief

    # Complete agent session
    session = await arc.complete(final_output=final_brief)
    logger.info(f"✅ Demo Agent completed successfully! Session ID: {arc.session_id}")

    return {
        "session_id": str(arc.session_id),
        "dashboard_url": arc.dashboard_url,
        "status": "completed",
        "final_output": final_brief,
    }


def main():
    """Main CLI entrypoint for running demo agent standalone."""
    print("=" * 70)
    print("      Agent Runtime Core (ARC) — Demo Investment Research Agent      ")
    print("=" * 70)

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(
        run_demo_agent(
            task="Research Anthropic, find their latest funding, key products, and write an investment brief",
            inject_chaos=False,
        )
    )

    print("\nSession Completed!")
    print(f"Session ID:    {res['session_id']}")
    print(f"Dashboard URL: {res['dashboard_url']}")
    print("\nFinal Output Preview:")
    print("-" * 50)
    print(res["final_output"][:400] + "...\n")


if __name__ == "__main__":
    main()
