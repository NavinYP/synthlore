import os
import sys
import json
import random
import asyncio
import base64
import docx
import time
import logging
from datetime import datetime
from tqdm.asyncio import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.config import WorldConfig
from src.graph.generator import KnowledgeGraphGenerator
from src.generation.llm_client import UnifiedAIClient
from src.generation.document_compiler import DocumentCompiler
from src.generation.visual_renderer import VisualRenderer
from src.settings import settings

TEXT_SEMAPHORE = asyncio.Semaphore(10)
IMAGE_SEMAPHORE = asyncio.Semaphore(3)
metrics = {"llm_text": [], "llm_image": [], "render": []}

async def process_document(llm_client, compiler, renderer, G, node_id, ext, doc_type, corpus_dir, needs_image, logger):
    node_name = G.nodes[node_id]['name']
    
    # Text Generation
    t0 = time.time()
    async with TEXT_SEMAPHORE:
        for attempt in range(3):
            try:
                text = await compiler.compile_document(G, node_id, doc_type=doc_type)
                break
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    logger.warning(f"[{node_name}] 429 Rate Limit on Text. Retrying (attempt {attempt+1})...")
                    await asyncio.sleep(2 ** attempt)
                elif attempt == 2:
                    logger.error(f"[{node_name}] Text Gen failed: {e}")
                    raise e
    
    t_text = time.time() - t0
    metrics["llm_text"].append(t_text)
    logger.info(f"[{node_name}] Text Gen: {t_text:.2f}s")
    
    with open(os.path.join(corpus_dir, f"{node_name}_RAW.md"), "w") as f:
        f.write(text)
    with open(os.path.join(corpus_dir, f"{node_name}_CONTEXT.txt"), "w") as f:
        f.write(compiler.extract_subgraph_context(G, node_id))
        
    # Image Generation
    embedded_img_path = None
    if needs_image:
        t0 = time.time()
        async with IMAGE_SEMAPHORE:
            for attempt in range(3):
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
                    break
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        logger.warning(f"[{node_name}] 429 Rate Limit on Image. Retrying (attempt {attempt+1})...")
                        await asyncio.sleep(4 ** attempt)
                    elif attempt == 2:
                        logger.error(f"[{node_name}] Image failed after retries: {e}")
        
        if embedded_img_path:
            t_img = time.time() - t0
            metrics["llm_image"].append(t_img)
            logger.info(f"[{node_name}] Asset Downloaded: {t_img:.2f}s")
            
    # Rendering
    t0 = time.time()
    out_path = os.path.join(corpus_dir, f"{node_name}{ext}")
    
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
    logger.info(f"[{node_name}] Rendered ({ext}): {t_render:.2f}s")
    return node_name

async def generate_corpus(num_docs=20):
    print("="*60)
    print("🏭 SYNTHLORE PIPELINE: GENERATING FRESH SAMPLE CORPUS")
    print("="*60)
    
    pipeline_start = time.time()
    metrics.clear()
    metrics.update({"llm_text": [], "llm_image": [], "render": []})
    
    # Setup Directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_dir = os.path.join(base_dir, "output", f"sample_corpus_{timestamp}")
    os.makedirs(corpus_dir, exist_ok=True)
    
    # Setup Logger
    log_file = os.path.join(corpus_dir, "generation.log")
    logger = logging.getLogger("SynthloreGenerator")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
    print(f"\n[Phase 1] Generating graph... (Logs saving to {log_file})")
    t0 = time.time()
    config = WorldConfig.default_arcane_industrial()
    generator = KnowledgeGraphGenerator(config)
    G = generator.generate(num_nodes=30)
    graph_time = time.time() - t0
    logger.info(f"Saved Ground Truth Graph in {graph_time:.2f}s")
    
    graph_path = os.path.join(corpus_dir, "ground_truth_graph.json")
    import networkx as nx
    with open(graph_path, "w") as f:
        json.dump(nx.node_link_data(G), f, indent=2)
    
    # Distributions
    dist = config.corpus_distribution
    num_with_image = int(num_docs * dist.image_injection_ratio)
    formats = []
    for ext, ratio in dist.format_ratios.items():
        formats.extend([ext] * int(num_docs * ratio))
    while len(formats) < num_docs:
        formats.append(list(dist.format_ratios.keys())[0])
    random.shuffle(formats)
    
    llm_client = UnifiedAIClient()
    await llm_client.initialize()
    compiler = DocumentCompiler(llm_client, config)
    renderer = VisualRenderer()
    
    target_nodes = list(G.nodes)[:num_docs]
    valid_image_indices = [i for i, ext in enumerate(formats) if ext != ".txt"]
    image_indices = set(random.sample(valid_image_indices, min(num_with_image, len(valid_image_indices))))
    
    print(f"\n[Phase 2 & 3] Compiling and Rendering {num_docs} Documents Concurrently...")
    
    tasks = []
    for i, node_id in enumerate(target_nodes):
        doc_type = random.choice(list(renderer.profiles.keys()))
        ext = formats[i]
        needs_image = i in image_indices
        tasks.append(asyncio.create_task(
            process_document(llm_client, compiler, renderer, G, node_id, ext, doc_type, corpus_dir, needs_image, logger)
        ))
        
    # Use tqdm to monitor progress of the concurrent tasks
    for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Processing Documents", unit="doc"):
        await coro
        
    await llm_client.close()
    
    total_time = time.time() - pipeline_start
    avg_txt = sum(metrics['llm_text'])/len(metrics['llm_text']) if metrics['llm_text'] else 0
    avg_img = sum(metrics['llm_image'])/len(metrics['llm_image']) if metrics['llm_image'] else 0
    avg_render = sum(metrics['render'])/len(metrics['render']) if metrics['render'] else 0
    
    logger.info(f"Total Pipeline Execution Time: {total_time:.2f}s")
    
    print("\n" + "="*60)
    print("📊 PARALLEL PIPELINE METRICS & ETA CALCULATIONS")
    print("="*60)
    print(f"Output Directory: {corpus_dir}")
    print(f"Total Pipeline Execution Time: {total_time:.2f}s (CONCURRENT)")
    print(f"Average Text Gen (gpt-5.6-luna):  {avg_txt:.2f}s per doc")
    print(f"Average Image Gen (gpt-image-2): {avg_img:.2f}s per image")
    print(f"Average Rendering Time:        {avg_render:.2f}s per doc")
    print("="*60)
    print(f"🎉 CORPUS COMPLETE! Generated {num_docs} documents.")

if __name__ == "__main__":
    asyncio.run(generate_corpus(20))
