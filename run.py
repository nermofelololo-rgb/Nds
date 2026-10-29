#!/usr/bin/env python3
"""
تشغيل نظام نيو دنت للمحاسبة والمخزون
"""
import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("  نيو دنت NDS - نظام المحاسبة والمخزون")
    print("=" * 50)
    print(f"\nالبرنامج شغال على المنفذ: {port}\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
