import asyncio
import json
import os
import random
import time
import networkx as nx
from PIL import Image, ImageDraw, ImageFont

from src.graph.generator import KnowledgeGraphGenerator
from src.graph.config import WorldConfig
from src.generation.llm_client import UnifiedAIClient
from src.generation.visual_renderer import VisualRenderer
import src.settings as settings

async def generate_chapter(llm, context, chapter_num, focus_node_name, theme):
    prompt = f"""
    You are a bestselling fantasy author writing a dark fantasy series.
    Write CHAPTER {chapter_num} of the novel. The chapter must focus heavily on the character/entity: {focus_node_name}.
    
    GROUND TRUTH LORE (You must strictly adhere to these relationships):
    {context}
    
    Write a long, immersive, atmospheric chapter (at least 1000 words). Include dialogue, internal monologue, and visceral descriptions. DO NOT output anything except the chapter text (start with '## Chapter X: ...').
    """
    return await llm.generate_lore(prompt, system_prompt="You are a master fantasy author. Write epic prose.")

async def generate_wiki_page(llm, context, node_name):
    prompt = f"""
    You are writing a Fandom Wiki page for the entity '{node_name}'.
    
    GROUND TRUTH LORE (Strictly adhere to this):
    {context}
    
    Format as a comprehensive Wiki page in Markdown.
    Include:
    1. An Infobox (using a markdown table) with key stats.
    2. A 'History' section.
    3. A 'Known Affiliations' section.
    4. A 'Trivia' section.
    Write at least 600 words.
    """
    return await llm.generate_lore(prompt, system_prompt="You are a meticulous wiki archivist for a fantasy franchise.")

async def generate_codex_entry(llm, context, node_name):
    prompt = f"""
    You are writing an official Lore Codex / RPG Data page for '{node_name}'.
    
    GROUND TRUTH LORE:
    {context}
    
    Format as a dry, atmospheric lore book entry. Include tactical data, historical significance, and a rumor/secret.
    """
    return await llm.generate_lore(prompt, system_prompt="You are a lore-master writing a tabletop RPG codex.")

async def main():
    print("Generating Master Franchise Ecosystem...", flush=True)
    out_dir = "output/franchise_masterpiece"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Generate Graph
    config = WorldConfig.default_grim_fantasy()
    generator = KnowledgeGraphGenerator(config)
    G = generator.generate(num_nodes=25)
    
    # Save graph
    nx.write_gml(G, os.path.join(out_dir, "world_graph.gml"))
    
    llm = UnifiedAIClient()
    await llm.initialize()
    
    # Identify Core Cast (the hubs of our franchise)
    core_nodes = [n for n, d in G.nodes(data=True) if d.get("is_core_cast")]
    if not core_nodes:
        core_nodes = list(G.nodes)[:5]
        
    print(f"Identified {len(core_nodes)} Core Cast members for the Novel arcs.")
    
    # 2. Generate VOLUME 1: THE NOVEL
    print("\nWriting Volume 1: The Ashen Chronicles (Novel)...")
    novel_content = "# THE ASHEN CHRONICLES\n\n*A Tale of Vaeloria*\n\n---\n\n"
    
    for i, node_id in enumerate(core_nodes):
        print(f"  -> Writing Chapter {i+1}...")
        # Get 2-hop context for deeper storytelling
        context_edges = list(nx.edge_bfs(G, node_id, orientation='ignore'))[:10]
        real_edges = [(u, v, G.get_edge_data(u, v) or G.get_edge_data(v, u)) for u, v, _ in context_edges]
        context_str = "\n".join([f"{G.nodes[u]['name']} -> {d.get('type', 'CONNECTS')} -> {G.nodes[v]['name']}" for u, v, d in real_edges if d])
        
        chapter_text = await generate_chapter(llm, context_str, i+1, G.nodes[node_id]['name'], config.setting_name)
        novel_content += chapter_text + "\n\n---\n\n"
        
    with open(os.path.join(out_dir, "Volume_1_The_Ashen_Chronicles.md"), "w") as f:
        f.write(novel_content)
        
    # 3. Generate VOLUME 2: THE WIKI ARCHIVE
    print("\nWriting Volume 2: The Fandom Wiki...")
    wiki_dir = os.path.join(out_dir, "Vaeloria_Wiki")
    os.makedirs(wiki_dir, exist_ok=True)
    
    for node_id in list(G.nodes)[:10]: # Write 10 detailed wiki pages
        node_name = G.nodes[node_id]['name']
        print(f"  -> Writing Wiki Page for {node_name}...")
        context_edges = list(nx.edge_bfs(G, node_id, orientation='ignore'))[:8]
        real_edges = [(u, v, G.get_edge_data(u, v) or G.get_edge_data(v, u)) for u, v, _ in context_edges]
        context_str = "\n".join([f"{G.nodes[u]['name']} -> {d.get('type', 'CONNECTS')} -> {G.nodes[v]['name']}" for u, v, d in real_edges if d])
        
        wiki_text = await generate_wiki_page(llm, context_str, node_name)
        
        # Generate an image for the wiki
        node_type = G.nodes[node_id].get("type", "")
        if node_type in ["Person", "Inquisitor"]:
            img_prompt = f"Dark fantasy digital painting portrait of {node_name}, grimdark masterpiece."
        elif node_type in ["Stronghold", "Facility"]:
            img_prompt = f"Epic dark fantasy landscape map of {node_name}, atmospheric lighting."
        else:
            img_prompt = f"Dark fantasy heraldry or artifact illustration of {node_name}."
            
        print(f"     -> Generating Wiki Image...")
        try:
            img_b64 = await llm.image_client.images.generate(
                model=settings.image_generation_deployment,
                prompt=img_prompt, n=1, size="1024x1024", response_format="b64_json"
            )
            import base64
            img_data = base64.b64decode(img_b64.data[0].b64_json)
            img_path = os.path.join(wiki_dir, f"{node_name.replace(' ', '_')}.png")
            with open(img_path, "wb") as f:
                f.write(img_data)
            
            wiki_text = f"![{node_name}]({node_name.replace(' ', '_')}.png)\n\n" + wiki_text
        except Exception as e:
            print(f"     -> Image failed: {e}")
            
        with open(os.path.join(wiki_dir, f"{node_name.replace(' ', '_')}.md"), "w") as f:
            f.write(wiki_text)
            
    print("\nFranchise Generation Complete! Output saved to output/franchise_masterpiece/")

if __name__ == "__main__":
    asyncio.run(main())
