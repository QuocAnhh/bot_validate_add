"""Non-parametric memory implementation - adapted from Memento"""
import logging
from typing import List, Dict, Any, Tuple, Optional
import torch

from app.memory.case_storage import CaseStorage
from app.memory.embedding import EmbeddingModel

logger = logging.getLogger(__name__)


class NonParametricMemory:
    """Non-parametric memory for case-based reasoning"""
    
    def __init__(
        self,
        storage_path: str = "memory/cases.jsonl",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "auto",
        key_field: str = "user_message",
        value_field: str = "assistant_response"
    ):
        """
        Initialize non-parametric memory
        
        Args:
            storage_path: Path to JSONL file for cases
            embedding_model_name: HuggingFace model name for embeddings
            device: Device for embedding model
            key_field: Field name for query (default: "user_message")
            value_field: Field name for response (default: "assistant_response")
        """
        self.storage = CaseStorage(storage_path)
        self.embedding_model = EmbeddingModel(embedding_model_name, device)
        self.key_field = key_field
        self.value_field = value_field
        
        # Load cases and extract pairs
        self._cases: List[Dict[str, Any]] = []
        self._pairs: List[Tuple[str, Any, int]] = []
        self._reload_memory()
        
        logger.info(f"Non-parametric memory initialized with {len(self._cases)} cases")
    
    def _reload_memory(self):
        """Reload cases from storage and extract pairs"""
        self._cases = self.storage.load_cases()
        self._pairs = self._extract_pairs(self._cases)
        logger.debug(f"Reloaded memory: {len(self._cases)} cases, {len(self._pairs)} pairs")
    
    def _extract_pairs(
        self,
        cases: List[Dict[str, Any]]
    ) -> List[Tuple[str, Any, int]]:
        """
        Extract (key, value, index) pairs from cases
        
        Args:
            cases: List of case dictionaries
            
        Returns:
            List of (key, value, index) tuples
        """
        pairs = []
        for i, case in enumerate(cases):
            key = str(case.get(self.key_field, ""))
            value = case.get(self.value_field, "")
            if key and value:
                pairs.append((key, value, i))
        return pairs
    
    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        max_length: int = 256,
        filter_negative: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar cases for a query
        
        Args:
            query: Query text
            top_k: Number of top results to return
            max_length: Max sequence length for embedding
            
        Returns:
            List of retrieved cases with scores
        """
        if not self._pairs:
            logger.debug("No cases in memory, returning empty list")
            return []
        
        try:
            # Embed query
            query_vec = self.embedding_model.embed_texts(
                [query],
                max_length=max_length
            )[0].unsqueeze(0)
            
            # Embed all keys
            keys = [p[0] for p in self._pairs]
            key_vecs = self.embedding_model.embed_texts(
                keys,
                max_length=max_length
            )
            
            # Compute similarity (cosine similarity = dot product of normalized vectors)
            sims = (query_vec @ key_vecs.T).squeeze(0)
            
            # Get top-k
            k = min(top_k, len(self._pairs))
            topk_scores, topk_idx = torch.topk(sims, k)
            
            # Build results
            results = []
            for rank, (score, idx) in enumerate(zip(topk_scores.tolist(), topk_idx.tolist()), 1):
                key, value, line_index = self._pairs[idx]
                
                # Check reward if filtering negative cases
                if filter_negative and line_index < len(self._cases):
                    reward = self._cases[line_index].get('reward', 1)
                    if reward == 0:  # Skip negative cases
                        continue
                
                results.append({
                    "rank": rank,
                    "score": round(float(score), 6),
                    "user_message": key,
                    "assistant_response": value,
                    "line_index": line_index
                })
            
            # If filtered, we might have fewer results, so take top_k
            results = results[:top_k]
            
            logger.debug(
                f"Retrieved {len(results)} cases for query "
                f"(top_k={top_k}, filter_negative={filter_negative})"
            )
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving cases: {e}", exc_info=True)
            return []
    
    def add_case(
        self,
        user_message: str,
        assistant_response: str,
        reward: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new case to memory
        
        Args:
            user_message: User message
            assistant_response: Assistant response
            reward: Optional reward (1 for positive, 0 for negative)
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        success = self.storage.add_case(
            user_message=user_message,
            assistant_response=assistant_response,
            reward=reward,
            metadata=metadata
        )
        
        if success:
            # Reload memory to include new case
            self._reload_memory()
        
        return success
    
    def get_case_count(self) -> int:
        """Get total number of cases"""
        return len(self._cases)

