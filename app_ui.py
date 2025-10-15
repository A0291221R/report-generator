# app_ui.py
import os
import json
import traceback
import gradio as gr

from langchain_core.messages import HumanMessage
from report_generator.crew import CreateCrew
from report_generator.crew_agents import State

app = CreateCrew()

DEFAULT_PROMPT = (
    "Research the latest developments and cite sources. "
    "Then draft a concise report and export it as a PDF titled "
    "'Edge-AI Pedestrian Tracking — Brief'."
)

def run_pipeline(topic: str, custom_prompt: str, facts_text: str):
    topic = (topic or "").strip()
    if not topic:
        return "❗ Please provide a topic.", ""

    prompt = (custom_prompt or DEFAULT_PROMPT).strip()

    # Parse facts: split by newline or comma
    facts = []
    if facts_text and facts_text.strip():
        raw = [seg for line in facts_text.splitlines() for seg in line.split(",")]
        facts = [f.strip() for f in raw if f.strip()]

    init_state: State = {
        "topic": topic,
        "messages": [HumanMessage(content=prompt)],
    }
    if facts:
        init_state["facts"] = facts

    try:
        result = app.invoke(init_state)
        msgs = result.get("messages", [])
        final_text = msgs[-1].content if msgs else "(No messages returned.)"

        # Optional: simple JSON trace
        messages_dump = [
            {"type": type(m).__name__, "content": getattr(m, "content", None)}
            for m in msgs
        ]
        return final_text, json.dumps(messages_dump, ensure_ascii=False, indent=2)

    except Exception as e:
        tb = traceback.format_exc()
        return f"❌ Error while running pipeline:\n\n{e}", tb

with gr.Blocks(title="Report Generator — Crew UI") as demo:
    gr.Markdown("# 🧑‍🔬 Report Generator (Crew)")

    topic = gr.Textbox(
        label="Topic",
        placeholder="e.g., Edge-AI pedestrian tracking",
        value="Edge-AI pedestrian tracking"
    )

    custom_prompt = gr.Textbox(
        label="Custom Prompt (optional)",
        placeholder="Leave blank to use the default prompt.",
        value=DEFAULT_PROMPT,
        lines=3
    )

    facts_text = gr.Textbox(
        label="Extra Facts (optional, comma/newline separated)",
        placeholder="e.g., YOLOv11 + DeepSORT + OSNet, Target ≥ 6 FPS on edge GPU",
        lines=3
    )

    run_btn = gr.Button("▶️ Run")

    final_report = gr.Markdown(label="Final Report")   # <- Renders report!
    full_trace = gr.Code(label="Message Trace (JSON)", language="json")

    run_btn.click(
        fn=run_pipeline,
        inputs=[topic, custom_prompt, facts_text],
        outputs=[final_report, full_trace]
    )

if __name__ == "__main__":
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name=os.getenv("GRADIO_SERVER_NAME", "localhost"), server_port=port)
