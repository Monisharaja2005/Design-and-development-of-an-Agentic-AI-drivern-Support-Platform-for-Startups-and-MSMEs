#!/usr/bin/env python3
"""
Standalone Scheme Recommendation + Document Verification Server
JSON Dataset → Soft Filter → BERT → FAISS Pipeline Live
"""

import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from doc_verify.api import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "doc_verify.api:app",
        # factory=True,
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )

