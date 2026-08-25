import os
import sys
import json
import networkx as nx
import matplotlib.pyplot as plt

def generate_visualization():
    # Load the graph
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    graph_path = os.path.join(base_dir, "output", "samples", "ground_truth_graph.json")
    
    with open(graph_path, "r") as f:
        data = json.load(f)
        
    G = nx.node_link_graph(data)
    
    # Arcane Industrial Color Palette
    color_map = {
        "Guild": "#D4AF37",          # Gold / Brass
        "Aether-Reactor": "#00FFFF", # Aether Cyan
        "Overseer": "#8A2BE2",       # Royal Purple
        "Dispatch Hub": "#FF8C00",   # Amber / Copper
        "Foundry": "#FF4500",        # Forge Red
        "Automaton": "#A9A9A9"       # Iron Gray
    }
    
    node_colors = []
    labels = {}
    
    for node, attrs in G.nodes(data=True):
        ntype = attrs.get("type", "Unknown")
        node_colors.append(color_map.get(ntype, "#FFFFFF"))
        
        # Abbreviate names for cleaner visualization
        name = attrs.get("name", node)
        abbr = name.split('-')[0][:3].upper() + "-" + name.split('-')[-1][:3]
        labels[node] = abbr

    # Set up the plot (Diagnostic Readout style)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    
    # Layout
    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#555555', arrows=True, arrowsize=15, alpha=0.7)
    
    # Draw edge labels
    edge_labels = {(u, v): d['relation'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='#888888', font_size=8, font_family='monospace')
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=1200, edgecolors='#333333', linewidths=2)
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=9, font_weight='bold', font_color='black')
    
    # Title & Legend
    plt.title("ARCANE INDUSTRIAL NETWORK DIAGNOSTIC READOUT", color="#D4AF37", fontfamily='monospace', fontsize=16, pad=20)
    
    # Custom legend
    import matplotlib.patches as mpatches
    legend_handles = [mpatches.Patch(color=color, label=ntype) for ntype, color in color_map.items()]
    plt.legend(handles=legend_handles, loc='upper left', facecolor='#1a1a1a', edgecolor='#555555', labelcolor='white')
    
    plt.tight_layout()
    
    # Save the plot
    out_path = os.path.join(base_dir, "output", "samples", "graph_viz.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#1a1a1a')
    print(f"Visualization saved to {out_path}")

if __name__ == "__main__":
    generate_visualization()
