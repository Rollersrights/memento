#!/usr/bin/env python3
"""
Semantic Chunking for Document Ingestion
Respects paragraph boundaries, sentence boundaries, and token limits
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SemanticChunk:
    """A semantically coherent chunk of text."""
    text: str
    start_idx: int  # Character position in original text
    end_idx: int
    metadata: Dict[str, Any]
    
    @property
    def word_count(self) -> int:
        return len(self.text.split())
    
    @property
    def char_count(self) -> int:
        return len(self.text)


class SemanticChunker:
    """
    Intelligent document chunking that preserves semantic boundaries.
    
    Strategy:
    1. Split into paragraphs (respect blank lines)
    2. For long paragraphs, split into sentences
    3. Group sentences into chunks respecting token limits
    4. Add overlap at sentence boundaries (not mid-sentence)
    """
    
    def __init__(
        self,
        max_tokens: int = 384,  # MiniLM limit
        target_tokens: int = 256,  # Comfortable target
        overlap_sentences: int = 1,  # Overlap by N sentences
        min_chunk_size: int = 50  # Minimum chars per chunk
    ):
        self.max_tokens = max_tokens
        self.target_tokens = target_tokens
        self.overlap_sentences = overlap_sentences
        self.min_chunk_size = min_chunk_size
        
        # Approximate tokens: ~1.3 tokens per word for English
        self.words_per_token = 0.75
        self.target_words = int(target_tokens * self.words_per_token)
        self.max_words = int(max_tokens * self.words_per_token)
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs (separated by blank lines)."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean up and filter empty
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        Handles common abbreviations and edge cases.
        """
        # Simple sentence splitting (can be improved with NLTK/spacy if needed)
        # Pattern: period/question/exclamation followed by space and capital letter
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z"\'\(])'
        
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        words = len(text.split())
        return int(words / self.words_per_token)
    
    def chunk_paragraph(self, paragraph: str, start_offset: int) -> List[SemanticChunk]:
        """
        Chunk a single paragraph into semantically coherent pieces.
        
        If paragraph is short enough, return as-is.
        Otherwise, split by sentences and group intelligently.
        """
        # If paragraph fits in target size, keep it whole
        if self.estimate_tokens(paragraph) <= self.target_tokens:
            return [SemanticChunk(
                text=paragraph,
                start_idx=start_offset,
                end_idx=start_offset + len(paragraph),
                metadata={'type': 'paragraph'}
            )]
        
        # Split into sentences
        sentences = self.split_into_sentences(paragraph)
        
        if len(sentences) == 1:
            # Single long sentence - have to split it (rare case)
            return self._chunk_long_sentence(paragraph, start_offset)
        
        # Group sentences into chunks
        return self._group_sentences(sentences, start_offset)
    
    def _group_sentences(
        self,
        sentences: List[str],
        start_offset: int
    ) -> List[SemanticChunk]:
        """
        Group sentences into chunks respecting token limits.
        Adds overlap between chunks for context preservation.
        """
        chunks = []
        current_chunk_sentences = []
        current_word_count = 0
        current_start = start_offset
        char_pos = start_offset
        
        sentence_positions = []  # Track where each sentence starts
        
        for i, sentence in enumerate(sentences):
            sentence_words = len(sentence.split())
            sentence_positions.append((char_pos, sentence))
            
            # Check if adding this sentence exceeds max
            if current_word_count + sentence_words > self.max_words and current_chunk_sentences:
                # Finalize current chunk
                chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(SemanticChunk(
                    text=chunk_text,
                    start_idx=current_start,
                    end_idx=char_pos,
                    metadata={
                        'type': 'sentences',
                        'sentence_count': len(current_chunk_sentences)
                    }
                ))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk_sentences) - self.overlap_sentences)
                current_chunk_sentences = current_chunk_sentences[overlap_start:] + [sentence]
                current_word_count = sum(len(s.split()) for s in current_chunk_sentences)
                
                # Calculate new start position (start of overlap)
                if overlap_start > 0 and len(chunks) > 0:
                    # Find position of first overlap sentence
                    overlap_idx = len(current_chunk_sentences) - 1 - self.overlap_sentences
                    if overlap_idx >= 0:
                        current_start = sentence_positions[max(0, i - self.overlap_sentences)][0]
                    else:
                        current_start = char_pos - len(sentence) - len(' '.join(current_chunk_sentences[:-1]))
                else:
                    current_start = char_pos - len(sentence)
            else:
                current_chunk_sentences.append(sentence)
                current_word_count += sentence_words
            
            char_pos += len(sentence) + 1  # +1 for space
        
        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            chunks.append(SemanticChunk(
                text=chunk_text,
                start_idx=current_start,
                end_idx=char_pos,
                metadata={
                    'type': 'sentences',
                    'sentence_count': len(current_chunk_sentences)
                }
            ))
        
        return chunks
    
    def _chunk_long_sentence(
        self,
        sentence: str,
        start_offset: int
    ) -> List[SemanticChunk]:
        """
        Chunk a very long sentence by clauses (comma/semicolon boundaries).
        Last resort when sentences themselves are too long.
        """
        # Try to split on clause boundaries
        clauses = re.split(r'(?<=[,;])\s+', sentence)
        
        if len(clauses) == 1:
            # Really long clause - just word-split (rare)
            words = sentence.split()
            chunks = []
            start = 0
            
            while start < len(words):
                end = min(start + self.target_words, len(words))
                chunk_words = words[start:end]
                chunk_text = ' '.join(chunk_words)
                
                chunks.append(SemanticChunk(
                    text=chunk_text,
                    start_idx=start_offset + sum(len(w) + 1 for w in words[:start]),
                    end_idx=start_offset + sum(len(w) + 1 for w in words[:end]),
                    metadata={'type': 'partial_sentence'}
                ))
                
                start = end
            
            return chunks
        
        # Group clauses like sentences
        return self._group_sentences(clauses, start_offset)
    
    def chunk(self, text: str) -> List[SemanticChunk]:
        """
        Main entry point: chunk text semantically.
        
        Returns list of SemanticChunk objects preserving boundaries.
        """
        if not text or not text.strip():
            return []
        
        all_chunks = []
        char_offset = 0
        
        # First, split into paragraphs
        paragraphs = self.split_into_paragraphs(text)
        
        for paragraph in paragraphs:
            # Find position of this paragraph in original text
            para_start = text.find(paragraph, char_offset)
            if para_start == -1:
                para_start = char_offset
            
            # Chunk this paragraph
            para_chunks = self.chunk_paragraph(paragraph, para_start)
            all_chunks.extend(para_chunks)
            
            char_offset = para_start + len(paragraph)
        
        return all_chunks
    
    def chunk_with_context(
        self,
        text: str,
        doc_title: Optional[str] = None,
        doc_source: Optional[str] = None
    ) -> List[SemanticChunk]:
        """
        Chunk with additional context metadata for each chunk.
        
        Adds document context to help with retrieval.
        """
        chunks = self.chunk(text)
        
        # Add context to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'has_next': i < len(chunks) - 1,
                'has_prev': i > 0,
                'doc_title': doc_title,
                'doc_source': doc_source,
                'estimated_tokens': self.estimate_tokens(chunk.text)
            })
        
        return chunks


def chunk_text_semantic(
    text: str,
    max_tokens: int = 384,
    target_tokens: int = 256,
    overlap_sentences: int = 1
) -> List[str]:
    """
    Convenience function for simple semantic chunking.
    
    Returns list of text strings (not SemanticChunk objects).
    """
    chunker = SemanticChunker(
        max_tokens=max_tokens,
        target_tokens=target_tokens,
        overlap_sentences=overlap_sentences
    )
    
    chunks = chunker.chunk(text)
    return [c.text for c in chunks]


# Test
if __name__ == "__main__":
    test_text = """
    Vector databases are essential for modern AI applications.
    They store high-dimensional vectors that represent semantic meaning.
    This allows for similarity search and retrieval augmented generation.
    
    Traditional databases use exact matching.
    Vector databases use approximate nearest neighbor search.
    This is much more flexible for natural language queries.
    
    Zvec is a new embedded vector database from Alibaba.
    It runs locally without requiring external services.
    The database uses SQLite for storage and NumPy for computation.
    This makes it lightweight and suitable for edge devices.
    It can run on hardware without AVX2 support.
    """
    
    print("=== Semantic Chunking Test ===\n")
    
    chunker = SemanticChunker(target_tokens=100, max_tokens=150)
    chunks = chunker.chunk_with_context(test_text, doc_title="Vector DB Overview")
    
    print(f"Created {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}/{len(chunks)}:")
        print(f"  Type: {chunk.metadata['type']}")
        print(f"  Words: {chunk.word_count} (~{chunker.estimate_tokens(chunk.text)} tokens)")
        print(f"  Text: {chunk.text[:100]}...")
        print()
