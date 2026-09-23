"""
Moteur de Recherche et d'Indexation RAG pour les Données UC3
Gère le découpage sémantique (chunking) et la recherche ciblée par ODD / Indicateur
"""

import re
from typing import Dict, Any, List, Optional

class UC3DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        source_title: str,
        source_url_or_path: str,
        source_type: str,
        entity: str = "UC3",
        date: str = "",
        is_public: bool = True
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.source_title = source_title
        self.source_url_or_path = source_url_or_path
        self.source_type = source_type
        self.entity = entity
        self.date = date
        self.is_public = is_public

class UC3KnowledgeStore:
    def __init__(self):
        self.chunks: List[UC3DocumentChunk] = []

    def add_document(
        self,
        text: str,
        source_title: str,
        source_url_or_path: str,
        source_type: str,
        entity: str = "UC3",
        date: str = "",
        is_public: bool = True,
        chunk_size: int = 500
    ):
        # Découpage par paragraphes ou fenêtres textuelles
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_chunk = []
        current_len = 0
        chunk_count = 0

        for p in paragraphs:
            current_chunk.append(p)
            current_len += len(p)
            if current_len >= chunk_size:
                chunk_id = f"{source_title}_{chunk_count}"
                chunk_text = "\n\n".join(current_chunk)
                self.chunks.append(UC3DocumentChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source_title=source_title,
                    source_url_or_path=source_url_or_path,
                    source_type=source_type,
                    entity=entity,
                    date=date,
                    is_public=is_public
                ))
                current_chunk = []
                current_len = 0
                chunk_count += 1

        if current_chunk:
            chunk_id = f"{source_title}_{chunk_count}"
            self.chunks.append(UC3DocumentChunk(
                chunk_id=chunk_id,
                text="\n\n".join(current_chunk),
                source_title=source_title,
                source_url_or_path=source_url_or_path,
                source_type=source_type,
                entity=entity,
                date=date,
                is_public=is_public
            ))

    def retrieve_relevant_chunks(
        self,
        query_text: str,
        top_k: int = 3,
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Recherche par pertinence sémantique & lexicale (BM25 / Overlap).
        """
        if not self.chunks:
            return []

        query_tokens = set(re.findall(r"\b[a-zA-Z\u0600-\u06FF]{3,}\b", query_text.lower()))
        scores = []

        for chunk in self.chunks:
            chunk_tokens = set(re.findall(r"\b[a-zA-Z\u0600-\u06FF]{3,}\b", chunk.text.lower()))
            if not chunk_tokens:
                continue
            
            # Calcul du score d'intersection
            intersection = query_tokens.intersection(chunk_tokens)
            score = len(intersection) / (len(query_tokens) + 1e-5)
            
            # Bonus si le nom d'entité ou l'année correspond
            if "2025" in chunk.text:
                score *= 1.2
            if "constantine" in chunk.text.lower() or "uc3" in chunk.text.lower():
                score *= 1.1

            if score > threshold:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scores[:top_k]:
            results.append({
                "score": round(score, 3),
                "text": chunk.text,
                "source_title": chunk.source_title,
                "source_url_or_path": chunk.source_url_or_path,
                "source_type": chunk.source_type,
                "entity": chunk.entity,
                "date": chunk.date,
                "is_public": chunk.is_public
            })
        return results
