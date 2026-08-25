import os
import sys
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.generation.visual_renderer import VisualRenderer

def run_phase3():
    print("="*50)
    print("🎨 Phase 3: Visual Generation & Layouts")
    print("="*50)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_dir = os.path.join(base_dir, "output", "samples")
    visuals_dir = os.path.join(samples_dir, "visuals")
    
    # Get all markdown files in samples_dir
    md_files = glob.glob(os.path.join(samples_dir, "*.md"))
    if not md_files:
        print("❌ No markdown files found in output/samples/. Run Phase 2 first.")
        return
        
    renderer = VisualRenderer()
    
    # Process up to 3 files
    for md_path in md_files[:3]:
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Extract doc type if printed in phase 2, otherwise randomize
        # Look for "📝 Format: [Type]" in phase 2 output, or just guess from text
        doc_type = "Technical Manual" # default fallback
        types = list(renderer.profiles.keys())
        for t in types:
            if t.lower() in text.lower():
                doc_type = t
                break
                
        # If we didn't find one in the text, just randomly assign one for testing
        if doc_type == "Technical Manual":
            import random
            doc_type = random.choice(types)
            
        filename = os.path.basename(md_path).replace(".md", ".png")
        out_path = os.path.join(visuals_dir, filename)
        
        print(f"🖼️ Rendering {os.path.basename(md_path)} as [{doc_type}]...")
        renderer.render_document(text, doc_type, out_path)
        print(f"   ✅ Saved to {out_path}")
        
    print("\n🎉 Phase 3 Sample Generation Complete!")
    print(f"Check {visuals_dir} for the outputs.")

if __name__ == "__main__":
    run_phase3()
