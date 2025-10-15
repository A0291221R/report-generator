from langchain_core.messages import HumanMessage

from report_generator.crew import CreateCrew
from report_generator.crew_agents import State

from langsmith import Client, tracing_context

app = CreateCrew()

# # Print workflow
# png_bytes = app.get_graph().draw_mermaid_png()           # returns PNG bytes
# with open("sentinel_flow.png", "wb") as f:
#     f.write(png_bytes)

if __name__ == "__main__":
    init_state: State = {
        "topic": "Edge-AI pedestrain tracking",
        "messages": [
            HumanMessage(content=(
                "Research the latest developments and cite sources. "
                "Then draft a concise report and export it as a PDF titled "
                "'Edge-AI Pedestrian Tracking — Brief'."
            ))
        ],
        # "facts": ['YOLOv11 + DeepSORT + OSNET', 'Target >= 6FPS on edge GPU']
    }

    # with tracing_context(client=Client(), tracing_enabled=True):
    result = app.invoke(init_state)
    print(result["messages"][-1].content)