import os
import pytest
from src.generation.visual_renderer import VisualRenderer

def test_visual_renderer():
    renderer = VisualRenderer()
    out_path = "test_render.png"
    
    # Render a dummy document
    text = "This is a test document.\nIt has multiple lines.\n\nAnd paragraphs."
    result_path = renderer.render_document(text, "Guild Ledger", out_path)
    
    assert os.path.exists(result_path)
    os.remove(result_path) # Cleanup
