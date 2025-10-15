
**Graph visualization**
- The graph image in this README (`images/flow.png`) is generated from `graph.get_graph()`:
  - ASCII (quick): `print(graph.get_graph().draw_ascii())`
  - Mermaid PNG (simple):  
    ```python
    png = graph.get_graph().draw_mermaid_png()
    open("docs/flow.png","wb").write(png)
    ```
  - Graphviz PNG (if you prefer): `graph.get_graph().draw_png("docs/flow.png")`

---

## 🧩 Tech Stack

- **Python 3.12+**
- **LangGraph** for stateful orchestration
- **LLM** via your chosen provider (e.g., OpenAI)  
- **Tavily** (`TAVILY_API_KEY`) for web search
- **Gradio** for UI
- **reportlab** for PDF
- **LangSmith** (optional) for tracing: `LANGSMITH_TRACING=true`
- **Pushover** for notifications

---

## 🔧 Setup
### 1) Install dependencies
```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv add -r requirements.txt
```

### 2) Run app with cli
```bash
uv run app.py
```

### 3) Run app with UI
~~~bash
uv run app_ui.py
~~~

