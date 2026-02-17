import onnxruntime as ort
import numpy as np
import os
from transformers import AutoTokenizer

def test_onnx():
    model_path = os.path.expanduser("~/.memento/models/all-MiniLM-L6-v2.onnx")
    print(f"Testing model at: {model_path}")
    
    try:
        session = ort.InferenceSession(model_path)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    text = "This is a test sentence."
    inputs = tokenizer(text, return_tensors="np", padding=True, truncation=True)
    
    input_feed = {
        "input_ids": inputs["input_ids"].astype(np.int64),
        "attention_mask": inputs["attention_mask"].astype(np.int64),
        "token_type_ids": inputs["token_type_ids"].astype(np.int64)
    }
    
    print("Running inference...")
    try:
        outputs = session.run(None, input_feed)
        print("Inference successful!")
        print(f"Output shape: {outputs[0].shape}")
        # Check if output is all zeros (which would be bad)
        if np.all(outputs[0] == 0):
            print("WARNING: Output is all zeros!")
        else:
            print("Output looks reasonable (non-zero).")
    except Exception as e:
        print(f"Inference failed: {e}")

if __name__ == "__main__":
    test_onnx()
