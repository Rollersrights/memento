import os
import torch
from sentence_transformers import SentenceTransformer
from pathlib import Path

def export_onnx():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    cache_dir = os.path.expanduser("~/.memento/models")
    os.makedirs(cache_dir, exist_ok=True)
    
    onnx_path = os.path.join(cache_dir, "all-MiniLM-L6-v2.onnx")
    
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Get the underlying transformer model and move to CPU
    transformer_model = model[0].auto_model
    transformer_model.cpu()
    transformer_model.eval()
    tokenizer = model[0].tokenizer
    
    print(f"Exporting to ONNX: {onnx_path}")
    
    # Create dummy input on CPU
    dummy_text = "This is a dummy input for ONNX export."
    inputs = tokenizer(dummy_text, padding=True, truncation=True, return_tensors="pt")
    inputs = {k: v.cpu() for k, v in inputs.items()}
    
    # Export the model
    torch.onnx.export(
        transformer_model,
        (inputs["input_ids"], inputs["attention_mask"], inputs["token_type_ids"]),
        onnx_path,
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "token_type_ids": {0: "batch_size", 1: "sequence_length"},
            "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
        },
        opset_version=14,
        do_constant_folding=True,
    )
    
    # Also save the tokenizer config
    tokenizer.save_pretrained(cache_dir)
    
    print("✅ Export complete!")

if __name__ == "__main__":
    export_onnx()
