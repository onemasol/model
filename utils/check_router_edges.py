# utils/check_router_edges.py

from typing import Set
from main import create_graph

def extract_all_nodes() -> Set[str]:
    graph = create_graph()
    return set(graph.nodes)

def check_next_nodes(router_functions: dict):
    graph_nodes = extract_all_nodes()
    for name, func in router_functions.items():
        dummy_state = {"messages": ["테스트 질문"]}
        try:
            result = func(dummy_state.copy())
            next_node = result.get("next_node", None)
            if next_node not in graph_nodes:
                print(f"❌ {name}: next_node='{next_node}' is NOT in LangGraph nodes!")
            else:
                print(f"✅ {name}: next_node='{next_node}' is valid.")
        except Exception as e:
            print(f"⚠️  {name} execution error: {e}")

if __name__ == "__main__":
    from routers.task_router import task_router
    from routers.query_refiner import query_refiner
    from routers.websearch_critic import websearch_critic
    from routers.calendar_needed import calendar_needed

    check_next_nodes({
        "task_router": task_router,
        "query_refiner": query_refiner,
        "websearch_critic": websearch_critic,
        "calendar_needed": calendar_needed
    })
