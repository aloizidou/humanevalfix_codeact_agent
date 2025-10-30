from langgraph.graph import StateGraph, START, END

def node1(state): 
    print("hi"); 
    return state

g = StateGraph(dict)
g.add_node("test", node1)
g.add_edge(START, "test")
g.add_edge("test", END)
app = g.compile()
app.invoke({})
