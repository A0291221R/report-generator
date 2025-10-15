from __future__ import annotations
from typing import Annotated, TypedDict, NotRequired, List, Dict, Any
from pathlib import Path
import yaml, os
from pydantic import BaseModel, Field
from jinja2 import Template

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, AnyMessage, ToolMessage
from langgraph.graph import MessagesState


def _sanitize_for_openai(msgs: list[AnyMessage]) -> list[AnyMessage]:
    """
    Ensure every ToolMessage is preceded by an AIMessage with a tool_call
    (as required by OpenAI's chat.completions). If not, drop that ToolMessage.
    """
    cleaned = []
    last_ai_tool_ids = set()

    for m in msgs:
        if isinstance(m, AIMessage):
            # capture tool_call ids for the next ToolMessage(s)
            last_ai_tool_ids = set()
            for tc in getattr(m, "tool_calls", []) or []:
                # tc like {"id": "...", "type": "tool_call", "name": "...", "args": {...}}
                tc_id = tc.get("id")
                if tc_id:
                    last_ai_tool_ids.add(tc_id)
            cleaned.append(m)
        elif isinstance(m, ToolMessage):
            # keep only if it matches a tool_call id from the immediately preceding AIMessage
            if getattr(m, "tool_call_id", None) in last_ai_tool_ids:
                cleaned.append(m)
            # else: drop this orphan tool result
        else:
            cleaned.append(m)

    # Also handle the edge case where the very first non-system message is a ToolMessage
    # (the loop above already drops it because last_ai_tool_ids is empty)
    return cleaned

# ---------- Graph State (new reducer style) ----------
class State(MessagesState):
    topic: str
    facts: NotRequired[List[str]]  # optional: extra context

# ---------- YAML spec ----------
class AgentSpec(BaseModel):
    role: str = Field(default="")
    goal: str = Field(default="")
    backstory: str = Field(default="")
    style: str = Field(default="")
    template: str | None = None

    def render(self, **kwargs) -> str:
        if self.template:
            return Template(self.template).render(**kwargs)
        default = (
            "You are an autonomous agent.\n"
            "=== ROLE ===\n{{ role }}\n\n"
            "=== GOAL ===\n{{ goal }}\n\n"
            "=== BACKSTORY ===\n{{ backstory }}\n\n"
            "{% if style %}=== STYLE ===\n{{ style }}\n{% endif %}"
        )
        return Template(default).render(
            role=self.role, goal=self.goal, backstory=self.backstory, style=self.style, **kwargs
        )

def load_spec(path: str | Path) -> AgentSpec:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AgentSpec.model_validate(data)

# ---------- Callable node ----------
class CrewAgent:
    """
    Callable LangGraph node that renders a system prompt from YAML
    and can call bound tools via tool calls.
    """
    def __init__(
        self,
        name: str,
        yaml_path: str | Path,
        root_dir: str | Path = os.path.dirname(__file__),
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        tools: list | None = None,
    ):
        self.name = name
        self.spec = load_spec(os.path.join(root_dir, "prompts", yaml_path))
        base = ChatOpenAI(model=model, temperature=temperature)
        self.llm = base.bind_tools(tools) if tools else base
        self.tools = tools or []

    def build_messages(self, state: State):
        sys_text = self.spec.render(**{k: v for k, v in state.items() if k != "messages"})
        return [SystemMessage(content=sys_text), *state["messages"]]

    def __call__(self, state: State) -> Dict[str, Any]:
        msgs = self.build_messages(state)
        msgs = _sanitize_for_openai(msgs)
        resp = self.llm.invoke(msgs)  # AIMessage (may include tool_calls)
        ai = AIMessage(content=resp.content, name=self.name, tool_calls=getattr(resp, "tool_calls", None))
        return {"messages": [ai]}
