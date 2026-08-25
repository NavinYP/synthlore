import os
import sys
import json
import random
import asyncio
import base64
import docx
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.config import WorldConfig
from src.graph.generator import KnowledgeGraphGenerator
from src.generation.llm_client import UnifiedAIClient
from src.generation.document_compiler import DocumentCompiler
from src.generation.visual_renderer import VisualRenderer
from src.settings import settings

async def generate_corpus(num_docs=10):
    print("="*60)
    print("🏭 SYNTHLORE PIPELINE: GENERATING FRESH SAMPLE CORPUS")
    print("="*60)
    
    pipeline_start = time.time()
    
    # Setup Directories (Timestamped)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_dir = os.path.join(base_dir, "output", f"sample_corpus_{timestamp}")
    os.makedirs(corpus_dir, exist_ok=True)
    
    print(f"\n[Phase 1] Initializing WorldConfig and generating graph...")
    t0 = time.time()
    config = WorldConfig.default_arcane_industrial()
    generator = KnowledgeGraphGenerator(config)
    G = generator.generate(num_nodes=30)
    graph_time = time.time() - t0
    
    # Use dynamic distribution rules
    dist = config.corpus_distribution
    num_with_image = int(num_docs * dist.image_injection_ratio)
    
    formats = []
    for ext, ratio in dist.format_ratios.items():
        formats.extend([ext] * int(num_docs * ratio))
    # Fill any rounding remainders with the first format
    while len(formats) < num_docs:
        formats.append(list(dist.format_ratios.keys())[0])
    random.shuffle(formats)
    
    graph_path = os.path.join(corpus_dir, "ground_truth_graph.json")
    import networkx as nx
    with open(graph_path, "w") as f:
        json.dump(nx.node_link_data(G), f, indent=2)
    print(f"   ✅ Saved Ground Truth Graph ({graph_time:.2f}s)")
    
    # 2. Initialization
    llm_client = UnifiedAIClient()
    await llm_client.initialize()
    compiler = DocumentCompiler(llm_client, config)
    renderer = VisualRenderer()
    
    target_nodes = list(G.nodes)[:num_docs]
    
    # Decide which non-txt nodes get an image to hit exact count
    valid_image_indices = [i for i, ext in enumerate(formats) if ext != ".txt"]
    image_indices = set(random.sample(valid_image_indices, min(num_with_image, len(valid_image_indices))))
    
    print(f"\n[Phase 2 & 3] Compiling and Rendering {num_docs} Documents...")
    
    metrics = {"llm_text": [], "llm_image": [], "render": []}
    
    for i, node_id in enumerate(target_nodes):
        node_name = G.nodes[node_id]['name']
        doc_type = random.choice(list(renderer.profiles.keys()))
        ext = formats[i]
        
        print(f"   [{i+1}/{num_docs}] Processing {node_name} as [{doc_type}] -> {ext}")
        
        # Generate Markdown Text
        t0 = time.time()
        text = await compiler.compile_document(G, node_id, doc_type=doc_type)
        t_text = time.time() - t0
        metrics["llm_text"].append(t_text)
        print(f"      📝 Text Gen (gpt-5.6-luna): {t_text:.2f}s")
        
        with open(os.path.join(corpus_dir, f"{node_name}_RAW.md"), "w") as f:
            f.write(text)
        with open(os.path.join(corpus_dir, f"{node_name}_CONTEXT.txt"), "w") as f:
            f.write(compiler.extract_subgraph_context(G, node_id))
            
        # Image Asset Generation (Guaranteed Distribution)
        embedded_img_path = None
        if i in image_indices:
            print(f"      🖌️ Generating visual asset for {node_name}...")
            t0 = time.time()
            try:
                img_prompt = f"A rough chalk sketch or technical blueprint of an Arcane Industrial entity named {node_name}. Monochromatic, highly detailed, parchment background."
                response = await llm_client.image_client.images.generate(
                    model=settings.image_generation_deployment,
                    prompt=img_prompt,
                    n=1,
                    size="1024x1024"
                )
                img_b64 = response.data[0].b64_json
                embedded_img_path = os.path.join(corpus_dir, f"{node_name}_drawing.png")
                with open(embedded_img_path, "wb") as fh:
                    fh.write(base64.b64decode(img_b64))
                t_img = time.time() - t0
                metrics["llm_image"].append(t_img)
                print(f"      ✅ Asset Downloaded (gpt-image-2): {t_img:.2f}s")
            except Exception as e:
                print(f"      ❌ Image generation failed: {e}")
                
        # Render Document
        out_path = os.path.join(corpus_dir, f"{node_name}{ext}")
        t0 = time.time()
        
        if ext in [".png", ".pdf"]:
            renderer.render_document(text, doc_type, out_path, embedded_image_path=embedded_img_path)
        elif ext == ".docx":
            doc = docx.Document()
            doc.add_heading(f"{node_name} ({doc_type})", 0)
            doc.add_paragraph(text)
            if embedded_img_path:
                doc.add_picture(embedded_img_path, width=docx.shared.Inches(5.0))
            doc.save(out_path)
        elif ext == ".txt":
            with open(out_path, "w") as f:
                f.write(text)
        
        t_render = time.time() - t0
        metrics["render"].append(t_render)
        print(f"      ✅ Rendered ({ext}): {t_render:.2f}s")

    await llm_client.close()
    
    total_time = time.time() - pipeline_start
    avg_txt = sum(metrics['llm_text'])/len(metrics['llm_text']) if metrics['llm_text'] else 0
    avg_img = sum(metrics['llm_image'])/len(metrics['llm_image']) if metrics['llm_image'] else 0
    avg_render = sum(metrics['render'])/len(metrics['render']) if metrics['render'] else 0
    
    print("\n" + "="*60)
    print("📊 PIPELINE METRICS & ETA CALCULATIONS")
    print("="*60)
    print(f"Output Directory: {corpus_dir}")
    print(f"Total Pipeline Execution Time: {total_time:.2f}s")
    print(f"Average Graph Generation:      {graph_time:.2f}s (Static)")
    print(f"Average Text Gen (gpt-5.6-luna):  {avg_txt:.2f}s per doc")
    print(f"Average Image Gen (gpt-image-2): {avg_img:.2f}s per image")
    print(f"Average Rendering Time:        {avg_render:.2f}s per doc")
    print("="*60)
    print(f"🎉 CORPUS COMPLETE! Generated {num_docs} documents.")

if __name__ == "__main__":
    asyncio.run(generate_corpus(10))
