#!/usr/bin/env python3
"""
Document ingestion pipeline
Handles chunking, embedding, and storing documents
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    doc_id: str
    chunk_idx: int
    total_chunks: int
    metadata: Dict[str, Any]

def chunk_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 50,
    max_tokens: int = 384,
    use_semantic: bool = True
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Target chunk size in tokens (approximate) - used for non-semantic
        overlap: Number of tokens to overlap between chunks - used for non-semantic
        max_tokens: Hard limit on chunk size
        use_semantic: Use semantic chunking (respects paragraph/sentence boundaries)
    
    Returns:
        List of text chunks
    """
    if use_semantic:
        # Use new semantic chunker
        try:
            from scripts.semantic_chunker import chunk_text_semantic
        except ImportError:
            from semantic_chunker import chunk_text_semantic
        return chunk_text_semantic(
            text,
            max_tokens=max_tokens,
            target_tokens=min(chunk_size, max_tokens - 50),
            overlap_sentences=1
        )
    else:
        # Legacy word-based chunking
        words = text.split()
        chunks = []
        
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Move forward by chunk_size - overlap
            start += (chunk_size - overlap)
        
        return chunks

def read_file(filepath: str) -> Optional[str]:
    """Read text from various file formats."""
    path = Path(filepath)
    
    if not path.exists():
        return None
    
    suffix = path.suffix.lower()
    
    try:
        if suffix == '.txt' or suffix == '.md':
            return path.read_text(encoding='utf-8')
        
        elif suffix == '.pdf':
            # Would need PyPDF2 or similar
            return _read_pdf(filepath)
        
        elif suffix in ['.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css']:
            # Code files
            return path.read_text(encoding='utf-8')
        
        else:
            # Try as text
            return path.read_text(encoding='utf-8', errors='ignore')
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def _read_pdf(filepath: str) -> str:
    """Extract text from PDF (requires PyPDF2)."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        print("PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"PDF read error: {e}")
        return ""

def ingest_file(
    filepath: str,
    chunk_size: int = 256,
    overlap: int = 50,
    use_semantic: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Chunk]:
    """
    Ingest a file and return chunks ready for embedding.
    
    Args:
        filepath: Path to file
        chunk_size: Chunk size in tokens (approximate)
        overlap: Overlap between chunks (legacy, semantic uses sentence overlap)
        use_semantic: Use semantic chunking (respects boundaries)
        metadata: Additional metadata to attach
    
    Returns:
        List of Chunk objects
    """
    # Read file
    text = read_file(filepath)
    if text is None:
        return []
    
    # Generate document ID from file path and content hash
    content_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    doc_id = f"{Path(filepath).stem}_{content_hash}"
    
    if use_semantic:
        # Use semantic chunker for better boundaries
        try:
            from scripts.semantic_chunker import SemanticChunker
        except ImportError:
            from semantic_chunker import SemanticChunker
        
        chunker = SemanticChunker(
            max_tokens=384,  # MiniLM limit
            target_tokens=chunk_size,
            overlap_sentences=1
        )
        
        semantic_chunks = chunker.chunk_with_context(
            text,
            doc_title=Path(filepath).stem,
            doc_source=filepath
        )
        
        # Convert to Chunk objects
        chunks = []
        base_metadata = metadata or {}
        
        for idx, schunk in enumerate(semantic_chunks):
            chunk = Chunk(
                text=schunk.text,
                doc_id=doc_id,
                chunk_idx=idx,
                total_chunks=len(semantic_chunks),
                metadata={
                    **base_metadata,
                    **schunk.metadata,
                    'source_file': filepath,
                    'file_type': Path(filepath).suffix,
                    'char_start': schunk.start_idx,
                    'char_end': schunk.end_idx,
                }
            )
            chunks.append(chunk)
        
        return chunks
    else:
        # Legacy chunking
        chunks_text = chunk_text(text, chunk_size, overlap, use_semantic=False)
        
        # Build Chunk objects
        chunks = []
        base_metadata = metadata or {}
        
        for idx, chunk_text_str in enumerate(chunks_text):
            chunk = Chunk(
                text=chunk_text_str,
                doc_id=doc_id,
                chunk_idx=idx,
                total_chunks=len(chunks_text),
                metadata={
                    **base_metadata,
                    'source_file': filepath,
                    'file_type': Path(filepath).suffix,
                }
            )
            chunks.append(chunk)
        
        return chunks

def ingest_directory(
    dirpath: str,
    pattern: str = "*",
    recursive: bool = True,
    **kwargs
) -> Dict[str, List[Chunk]]:
    """
    Ingest all matching files in a directory.
    
    Returns:
        Dict mapping filepath to list of chunks
    """
    from pathlib import Path
    
    results = {}
    path = Path(dirpath)
    
    if not path.exists():
        return results
    
    # Find files
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
    
    # Filter to files only
    files = [f for f in files if f.is_file()]
    
    # Ingest each
    for f in files:
        chunks = ingest_file(str(f), **kwargs)
        if chunks:
            results[str(f)] = chunks
    
    return results

def store_chunks(store, chunks: List[Chunk], collection: str = "documents"):
    """
    Store chunks in memory store.
    
    Args:
        store: MemoryStore instance
        chunks: List of Chunk objects
        collection: Target collection
    """
    from scripts.embed import embed_chunks
    
    if not chunks:
        return []
    
    # Embed all chunks
    texts = [c.text for c in chunks]
    embeddings = embed_chunks(texts)
    
    # Store each
    ids = []
    for chunk, embedding in zip(chunks, embeddings):
        doc_id = store.remember(
            text=chunk.text,
            collection=collection,
            source=chunk.metadata.get('source_file', 'unknown'),
            importance=0.6,  # Documents are moderately important
            **chunk.metadata
        )
        ids.append(doc_id)
    
    return ids

if __name__ == "__main__":
    print("Testing document ingestion...")
    
    # Create a test file
    test_content = """
    This is a test document about vector databases.
    Vector databases are used for semantic search.
    They store embeddings which are numerical representations of text.
    Zvec is a new embedded vector database from Alibaba.
    It is lightweight and fast.
    """
    
    test_file = "/tmp/test_doc.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Ingest
    chunks = ingest_file(test_file, chunk_size=20, overlap=5)
    print(f"\nCreated {len(chunks)} chunks:")
    for c in chunks:
        print(f"  Chunk {c.chunk_idx + 1}/{c.total_chunks}: {c.text[:50]}...")
    
    # Cleanup
    os.remove(test_file)
