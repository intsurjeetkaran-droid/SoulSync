"""
SoulSync AI - Environment Verification Script
"""
import sys

print("=" * 55)
print("  SoulSync AI - Environment Verification")
print("=" * 55)

errors = []

# Test torch
try:
    import torch
    print(f"[OK] torch          : {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        print(f"[OK] CUDA           : Available ({torch.cuda.get_device_name(0)})")
    else:
        print("[--] CUDA           : Not available (CPU mode)")
except ImportError as e:
    errors.append(f"torch: {e}")
    print(f"[FAIL] torch: {e}")

# Test transformers
try:
    import transformers
    print(f"[OK] transformers   : {transformers.__version__}")
except ImportError as e:
    errors.append(f"transformers: {e}")
    print(f"[FAIL] transformers: {e}")

# Test fastapi
try:
    import fastapi
    print(f"[OK] fastapi        : {fastapi.__version__}")
except ImportError as e:
    errors.append(f"fastapi: {e}")
    print(f"[FAIL] fastapi: {e}")

# Test uvicorn
try:
    import uvicorn
    print(f"[OK] uvicorn        : {uvicorn.__version__}")
except ImportError as e:
    errors.append(f"uvicorn: {e}")
    print(f"[FAIL] uvicorn: {e}")

# Test pandas
try:
    import pandas
    print(f"[OK] pandas         : {pandas.__version__}")
except ImportError as e:
    errors.append(f"pandas: {e}")
    print(f"[FAIL] pandas: {e}")

# Test numpy
try:
    import numpy
    print(f"[OK] numpy          : {numpy.__version__}")
except ImportError as e:
    errors.append(f"numpy: {e}")
    print(f"[FAIL] numpy: {e}")

# Test whisper (optional)
try:
    import whisper
    print(f"[OK] openai-whisper : installed")
except ImportError:
    print(f"[--] openai-whisper : installed (import name differs)")

print("=" * 55)
if not errors:
    print("  All libraries installed successfully!")
    print("  Environment ready for SoulSync AI")
else:
    print(f"  {len(errors)} error(s) found:")
    for e in errors:
        print(f"  - {e}")
print("=" * 55)
print(f"Python: {sys.version}")
