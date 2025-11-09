"""Case storage for memory - JSONL based"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CaseStorage:
    """Storage for memory cases in JSONL format"""
    
    def __init__(self, storage_path: str = "memory/cases.jsonl"):
        """
        Initialize case storage
        
        Args:
            storage_path: Path to JSONL file for storing cases
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Case storage initialized: {self.storage_path}")
    
    def load_cases(self) -> List[Dict[str, Any]]:
        """
        Load all cases from JSONL file
        
        Returns:
            List of case dictionaries
        """
        if not self.storage_path.exists():
            logger.info(f"Memory file not found: {self.storage_path}, returning empty list")
            return []
        
        cases = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        case = json.loads(line)
                        cases.append(case)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line {line_num} in {self.storage_path}: {e}")
                        continue
            logger.info(f"Loaded {len(cases)} cases from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading cases from {self.storage_path}: {e}", exc_info=True)
            return []
        
        return cases
    
    def add_case(
        self,
        user_message: str,
        assistant_response: str,
        reward: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new case to storage
        
        Args:
            user_message: User message (key field for retrieval)
            assistant_response: Assistant response (value field)
            reward: Optional reward (1 for positive, 0 for negative)
            metadata: Optional additional metadata
            
        Returns:
            True if successful
        """
        case = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat(),
        }
        
        if reward is not None:
            case["reward"] = reward
        
        if metadata:
            case.update(metadata)
        
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                json_line = json.dumps(case, ensure_ascii=False)
                f.write(json_line + '\n')
            logger.info(f"Added case to memory: {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error adding case to {self.storage_path}: {e}", exc_info=True)
            return False
    
    def get_case_count(self) -> int:
        """Get total number of cases"""
        cases = self.load_cases()
        return len(cases)

