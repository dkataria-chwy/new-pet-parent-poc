"""
Hybrid Search Module - Combines Vector Search with BM25 for Better Results

This module provides hybrid search functionality that combines:
1. Vector similarity search (semantic matching)
2. BM25 keyword search (lexical matching)
3. Weighted fusion of results for optimal relevance
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class BM25Searcher:
    """BM25 keyword search implementation."""
    
    def __init__(self, documents: List[str], k1: float = 1.2, b: float = 0.75):
        """
        Initialize BM25 searcher.
        
        Args:
            documents: List of document texts to search
            k1: BM25 parameter controlling term frequency saturation
            b: BM25 parameter controlling length normalization
        """
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Build TF-IDF vectorizer for preprocessing
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9\-]*\b',  # Include hyphens
            max_features=10000
        )
        
        # Fit vectorizer and get vocabulary
        self.vectorizer.fit(documents)
        self.vocab = self.vectorizer.vocabulary_
        
        # Precompute document statistics
        self._precompute_stats()
        
    def _precompute_stats(self):
        """Precompute document statistics for BM25."""
        # Tokenize documents
        self.doc_tokens = []
        self.doc_lengths = []
        
        for doc in self.documents:
            tokens = self.vectorizer.build_analyzer()(doc)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
        
        # Average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        
        # Document frequencies for each term
        self.doc_frequencies = {}
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token in self.vocab:
                    self.doc_frequencies[token] = self.doc_frequencies.get(token, 0) + 1
    
    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (document_index, bm25_score) tuples
        """
        # Tokenize query
        query_tokens = self.vectorizer.build_analyzer()(query)
        
        # Handle NOT operators
        positive_terms = []
        negative_terms = []
        
        tokens = query_tokens
        i = 0
        while i < len(tokens):
            if tokens[i].upper() == 'NOT' and i + 1 < len(tokens):
                negative_terms.append(tokens[i + 1])
                i += 2
            else:
                positive_terms.append(tokens[i])
                i += 1
        
        # Calculate BM25 scores
        scores = []
        
        for doc_idx in range(self.doc_count):
            doc_tokens = self.doc_tokens[doc_idx]
            doc_length = self.doc_lengths[doc_idx]
            
            # Check negative terms first (exclusion)
            has_negative = any(neg_term in doc_tokens for neg_term in negative_terms)
            if has_negative:
                scores.append((doc_idx, 0.0))  # Exclude documents with negative terms
                continue
            
            # Calculate BM25 score for positive terms
            score = 0.0
            
            for term in positive_terms:
                if term not in self.vocab:
                    continue
                    
                # Term frequency in document
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue
                
                # Document frequency
                df = self.doc_frequencies.get(term, 0)
                if df == 0:
                    continue
                
                # IDF component
                idf = np.log((self.doc_count - df + 0.5) / (df + 0.5))
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                score += idf * (numerator / denominator)
            
            scores.append((doc_idx, score))
        
        # Sort by score and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridSearchEngine:
    """Hybrid search combining vector similarity and BM25."""
    
    def __init__(self, vector_searcher, storage_loader):
        """
        Initialize hybrid search engine.
        
        Args:
            vector_searcher: Vector search instance (e.g., SpeciesAwareVectorSearch)
            storage_loader: EmbeddingStorageLoader instance
        """
        self.vector_searcher = vector_searcher
        self.storage_loader = storage_loader
        self.bm25_searcher = None
        self._initialize_bm25()
        
    def _initialize_bm25(self):
        """Initialize BM25 searcher with product documents."""
        try:
            # Get all product search texts for BM25 indexing
            df = self.storage_loader.full_df
            if df is None or df.empty:
                logger.warning("No product data available for BM25 indexing")
                return
                
            # Use search_text column for BM25 indexing
            documents = df['search_text'].fillna('').tolist()
            
            logger.info(f"Initializing BM25 with {len(documents)} product documents")
            self.bm25_searcher = BM25Searcher(documents)
            logger.info("✅ BM25 searcher initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize BM25 searcher: {e}")
            self.bm25_searcher = None
    
    def hybrid_search(self, 
                     embedding_query: str,
                     bm25_query: str,
                     species: str,
                     top_k: int = 20,
                     vector_weight: float = 0.7,
                     bm25_weight: float = 0.3,
                     brand_preferences: List[str] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and BM25 results.
        
        Args:
            embedding_query: Natural language query for vector search
            bm25_query: Keyword query for BM25 search
            species: Pet species for filtering
            top_k: Number of results to return
            vector_weight: Weight for vector search scores (0-1)
            bm25_weight: Weight for BM25 scores (0-1)
            brand_preferences: List of preferred brands
            
        Returns:
            List of product results with hybrid scores
        """
        if not self.bm25_searcher:
            logger.warning("BM25 not available, falling back to vector search only")
            return self.vector_searcher.search_products(
                embedding_query=embedding_query,
                species=species,
                top_k=top_k,
                brand_preferences=brand_preferences
            )
        
        try:
            # Get species-filtered data
            species_df = self.storage_loader.get_species_data(species)
            if species_df.empty:
                logger.warning(f"No products found for species: {species}")
                return []
            
            # 1. Vector search
            logger.info(f"🔍 Vector search: '{embedding_query[:50]}...'")
            vector_results = self.vector_searcher.search_products(
                embedding_query=embedding_query,
                species=species,
                top_k=min(top_k * 3, 100),  # Get more candidates for fusion
                brand_preferences=brand_preferences
            )
            
            # 2. BM25 search on species-filtered data
            logger.info(f"🔍 BM25 search: '{bm25_query}'")
            species_documents = species_df['search_text'].fillna('').tolist()
            species_indices = species_df.index.tolist()
            
            # Create temporary BM25 searcher for species subset
            species_bm25 = BM25Searcher(species_documents)
            bm25_results = species_bm25.search(bm25_query, top_k=min(top_k * 3, 100))
            
            # 3. Normalize scores and combine
            hybrid_scores = {}
            
            # Add vector scores (normalized)
            if vector_results:
                max_vector_score = max(r.get('similarity', 0) for r in vector_results)
                for result in vector_results:
                    sku = result['sku']
                    normalized_score = result.get('similarity', 0) / max_vector_score if max_vector_score > 0 else 0
                    hybrid_scores[sku] = {
                        'vector_score': normalized_score,
                        'bm25_score': 0.0,
                        'product_data': result
                    }
            
            # Add BM25 scores (normalized)
            if bm25_results:
                max_bm25_score = max(score for _, score in bm25_results if score > 0)
                for doc_idx, score in bm25_results:
                    if score <= 0:
                        continue
                        
                    # Get actual dataframe index
                    actual_idx = species_indices[doc_idx]
                    product_row = species_df.loc[actual_idx]
                    sku = product_row['product_part_number']
                    
                    normalized_score = score / max_bm25_score if max_bm25_score > 0 else 0
                    
                    if sku in hybrid_scores:
                        hybrid_scores[sku]['bm25_score'] = normalized_score
                    else:
                        # Create product data for BM25-only results
                        product_data = {
                            'rank': 0,
                            'sku': sku,
                            'parentSKU': product_row.get('parent_product_part_number', ''),
                            'name': self._extract_product_name(product_row['search_text']),
                            'similarity': 0.0,
                            'search_text': product_row['search_text'],
                            'species_flags': {
                                'dog': product_row['species_dog_flag'],
                                'cat': product_row['species_cat_flag']
                            }
                        }
                        hybrid_scores[sku] = {
                            'vector_score': 0.0,
                            'bm25_score': normalized_score,
                            'product_data': product_data
                        }
            
            # 4. Calculate hybrid scores and rank
            final_results = []
            for sku, scores in hybrid_scores.items():
                hybrid_score = (vector_weight * scores['vector_score'] + 
                               bm25_weight * scores['bm25_score'])
                
                if hybrid_score > 0:  # Only include products with some relevance
                    product = scores['product_data'].copy()
                    product['similarity'] = hybrid_score
                    product['vector_score'] = scores['vector_score']
                    product['bm25_score'] = scores['bm25_score']
                    final_results.append(product)
            
            # Sort by hybrid score and re-rank
            final_results.sort(key=lambda x: x['similarity'], reverse=True)
            for i, product in enumerate(final_results[:top_k], 1):
                product['rank'] = i
            
            logger.info(f"✅ Hybrid search: {len(vector_results)} vector + {len(bm25_results)} BM25 → {len(final_results[:top_k])} hybrid results")
            
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to vector search
            return self.vector_searcher.search_products(
                embedding_query=embedding_query,
                species=species,
                top_k=top_k,
                brand_preferences=brand_preferences
            )
    
    def _extract_product_name(self, search_text: str) -> str:
        """Extract product name from search text."""
        if ' Brand:' in search_text:
            return search_text.split(' Brand:')[0].strip()
        else:
            # Remove trailing period if present
            name = search_text.strip()
            if name.endswith('.'):
                name = name[:-1].strip()
            return name


def main():
    """Test hybrid search functionality."""
    try:
        import os
        from dotenv import load_dotenv
        from storage_loader import EmbeddingStorageLoader
        from vector_search import SpeciesAwareVectorSearch
        from qdrant_vector_search_rest import QdrantVectorSearch
        
        load_dotenv()
        
        # Check if we should use Qdrant
        use_qdrant = os.getenv("USE_QDRANT", "false").lower() == "true"
        
        # Initialize components
        if use_qdrant:
            print("🚀 Using Qdrant vector database")
            vector_searcher = QdrantVectorSearch()
            storage_loader = None  # Not needed for Qdrant
        else:
            print("📁 Using JSONL in-memory vector search")
            embeddings_path = "embeddings_pipeline/artifacts/catalog_embeds.jsonl"
            storage_loader = EmbeddingStorageLoader(embeddings_path)
            vector_searcher = SpeciesAwareVectorSearch(storage_loader)
        
        # Initialize hybrid search
        hybrid_engine = HybridSearchEngine(vector_searcher, storage_loader)
        
        # Test search
        embedding_query = "Puppy dry kibble small bites growth formula high protein"
        bm25_query = "puppy dry kibble small bites protein NOT chicken"
        
        results = hybrid_engine.hybrid_search(
            embedding_query=embedding_query,
            bm25_query=bm25_query,
            species="dog",
            top_k=10,
            vector_weight=0.7,
            bm25_weight=0.3
        )
        
        print(f"\n🎉 Hybrid Search Results ({len(results)} products):")
        for i, product in enumerate(results, 1):
            print(f"{i}. {product['sku']} - {product['name'][:60]}...")
            print(f"   Hybrid: {product['similarity']:.3f} (Vector: {product.get('vector_score', 0):.3f}, BM25: {product.get('bm25_score', 0):.3f})")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
