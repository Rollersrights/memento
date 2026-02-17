import sys
import onnxruntime as ort

print(f"Python: {sys.version}")
print(f"ONNX Runtime: {ort.__version__}")
print(f"Device: {ort.get_device()}")
print(f"Providers: {ort.get_available_providers()}")

try:
    sess_options = ort.SessionOptions()
    print("SessionOptions created successfully")
except Exception as e:
    print(f"SessionOptions failed: {e}")
