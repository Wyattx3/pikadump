#!/usr/bin/env python
"""Quick Python check script"""
import sys

print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")

try:
    import pyrogram
    print("✓ Pyrogram installed")
except ImportError:
    print("✗ Pyrogram not installed")

try:
    import dotenv
    print("✓ python-dotenv installed")
except ImportError:
    print("✗ python-dotenv not installed")

try:
    import tgcrypto
    print("✓ tgcrypto installed")
except ImportError:
    print("✗ tgcrypto not installed")
