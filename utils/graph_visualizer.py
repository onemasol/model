from langgraph.graph import StateGraph, END
from typing import Dict, Any
import graphviz

def visualize_graph(graph: StateGraph, output_path: str = "graph_visualization") -> None:
    """
    Visualize the StateGraph using graphviz.
    
    Args:
        graph: The StateGraph to visualize
        output_path: Path to save the visualization (without extension)
    """
    # Create a new directed graph
    dot = graphviz.Digraph(comment='OMS Agent Graph')
    dot.attr(rankdir='LR')  # Left to right direction
    
    # Add nodes
    for node in graph.nodes:
        if node == END:
            dot.node(str(node), "END", shape="doublecircle")
        else:
            dot.node(str(node), str(node), shape="box")
    
    # Add edges
    for edge in graph.edges:
        dot.edge(str(edge[0]), str(edge[1]))
    
    # Save the visualization
    dot.render(output_path, view=True, format='png') 