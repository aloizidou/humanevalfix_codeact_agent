from langgraph.graph import StateGraph, START, END

def hello_node(state):
    print("LangGraph works!")
    return state

graph = StateGraph(dict)
graph.add_node("hello", hello_node)
graph.add_edge(START, "hello")
graph.add_edge("hello", END)

app = graph.compile()
app.invoke()
