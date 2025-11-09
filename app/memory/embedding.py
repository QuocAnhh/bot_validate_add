"""Embedding utilities for memory retrieval"""
import logging
from typing import List, Tuple
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Embedding model wrapper for semantic search"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "auto"
    ):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name
            device: Device to use ("auto", "cpu", "cuda")
        """
        self.model_name = model_name
        
        # Determine device
        if device == "cpu":
            self.device = torch.device("cpu")
        elif device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Loading embedding model: {model_name} on {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            raise
    
    @torch.no_grad()
    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 64,
        max_length: int = 256
    ) -> torch.Tensor:
        """
        Embed texts into vectors
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            max_length: Max sequence length
            
        Returns:
            Tensor of embeddings (normalized)
        """
        if not texts:
            return torch.empty(0, self.model.config.hidden_size)
        
        vecs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            enc = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            )
            enc = {k: v.to(self.device) for k, v in enc.items()}
            
            out = self.model(**enc, return_dict=True)
            
            # Get embedding (pooler_output or first token)
            if hasattr(out, "pooler_output") and out.pooler_output is not None:
                e = out.pooler_output
            else:
                e = out.last_hidden_state[:, 0, :]
            
            # Normalize (L2 norm)
            e = F.normalize(e, p=2, dim=1)
            vecs.append(e.cpu())
        
        return torch.cat(vecs, dim=0) if vecs else torch.empty(0, self.model.config.hidden_size)

