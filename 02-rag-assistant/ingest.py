"""Index every .md/.txt/.pdf in ./docs into ChromaDB.  Usage: python ingest.py [folder]"""
import sys
from rag import build_index

folder = sys.argv[1] if len(sys.argv) > 1 else "docs"
n = build_index(folder)
print(f"Indexed {n} chunks from '{folder}' ✅")
