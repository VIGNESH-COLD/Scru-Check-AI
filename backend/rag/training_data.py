"""
Training Data Manager
Learns from user override decisions to improve future analysis
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class TrainingDataManager:
    """
    Manages training data collected from user override decisions.
    Used to improve analyzer accuracy over time.
    """
    
    DATA_DIR = "./training_data"
    
    def __init__(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.overrides = self._load_overrides()
        self.false_positives = self._load_false_positives()
        self.accepted_findings = self._load_accepted_findings()
    
    # ==================== OVERRIDE RECORDING ====================
    
    def record_override(
        self,
        criterion: str,
        question_text: str,
        original_status: str,
        override_action: str,  # ACCEPT, REJECT, FALSE_POSITIVE
        justification: str,
        context: Optional[Dict] = None
    ):
        """
        Record a user override decision for training.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "criterion": criterion,
            "question_text": question_text,
            "original_status": original_status,
            "override_action": override_action,
            "justification": justification,
            "context": context or {}
        }
        
        if override_action == "FALSE_POSITIVE":
            self.false_positives.append(record)
            self._save_false_positives()
        else:
            self.overrides.append(record)
            self._save_overrides()
        
        print(f"📝 Training data recorded: {criterion} - {override_action}")
    
    def record_accepted_finding(
        self,
        criterion: str,
        question_text: str,
        finding_status: str,
        context: Optional[Dict] = None
    ):
        """Record when user accepts an AI finding (positive training data)."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "criterion": criterion,
            "question_text": question_text,
            "status": finding_status,
            "context": context or {}
        }
        
        self.accepted_findings.append(record)
        self._save_accepted_findings()
    
    # ==================== TRAINING DATA RETRIEVAL ====================
    
    def get_false_positives_for_criterion(self, criterion: str) -> List[Dict]:
        """Get all false positives for a specific criterion."""
        return [fp for fp in self.false_positives if fp["criterion"] == criterion]
    
    def get_override_examples(self, criterion: str, limit: int = 10) -> List[Dict]:
        """Get recent override examples for a criterion."""
        criterion_overrides = [o for o in self.overrides if o["criterion"] == criterion]
        return criterion_overrides[-limit:]
    
    def should_suppress_finding(self, criterion: str, question_text: str, threshold: float = 0.8) -> bool:
        """
        Check if a finding should be suppressed based on similar false positives.
        Uses text similarity to find matching false positives.
        """
        false_positives = self.get_false_positives_for_criterion(criterion)
        
        for fp in false_positives:
            similarity = self._calculate_similarity(question_text, fp["question_text"])
            if similarity >= threshold:
                return True
        
        return False
    
    def get_learned_patterns(self, criterion: str) -> Dict[str, Any]:
        """
        Extract learned patterns from training data.
        Returns patterns that help improve classification.
        """
        overrides = self.get_override_examples(criterion, limit=50)
        false_positives = self.get_false_positives_for_criterion(criterion)
        
        # Analyze patterns
        patterns = {
            "total_overrides": len(overrides),
            "total_false_positives": len(false_positives),
            "common_justifications": self._extract_common_phrases(overrides),
            "fp_keywords": self._extract_keywords(false_positives)
        }
        
        return patterns
    
    def get_training_prompt_context(self, criterion: str) -> str:
        """
        Generate context for LLM prompts based on training data.
        Helps LLM understand institutional preferences.
        """
        overrides = self.get_override_examples(criterion, limit=5)
        false_positives = self.get_false_positives_for_criterion(criterion)[-5:]
        
        context_parts = []
        
        if overrides:
            context_parts.append("Previous override decisions:")
            for o in overrides:
                context_parts.append(f"- '{o['question_text'][:50]}...' was marked {o['override_action']}: {o['justification']}")
        
        if false_positives:
            context_parts.append("\nKnown false positives (don't flag these patterns):")
            for fp in false_positives:
                context_parts.append(f"- '{fp['question_text'][:50]}...' was incorrectly flagged")
        
        return "\n".join(context_parts) if context_parts else ""
    
    # ==================== ANALYSIS HELPERS ====================
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union
    
    def _extract_common_phrases(self, records: List[Dict]) -> List[str]:
        """Extract common phrases from justifications."""
        justifications = [r.get("justification", "") for r in records]
        
        # Simple word frequency
        word_counts = {}
        for j in justifications:
            for word in j.lower().split():
                if len(word) > 3:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:10]]
    
    def _extract_keywords(self, records: List[Dict]) -> List[str]:
        """Extract keywords from question texts."""
        keywords = []
        for r in records:
            text = r.get("question_text", "").lower()
            words = [w for w in text.split() if len(w) > 4]
            keywords.extend(words)
        
        # Return unique keywords
        return list(set(keywords))[:20]
    
    # ==================== PERSISTENCE ====================
    
    def _load_overrides(self) -> List[Dict]:
        path = os.path.join(self.DATA_DIR, "overrides.json")
        return self._load_json_file(path)
    
    def _save_overrides(self):
        path = os.path.join(self.DATA_DIR, "overrides.json")
        self._save_json_file(path, self.overrides)
    
    def _load_false_positives(self) -> List[Dict]:
        path = os.path.join(self.DATA_DIR, "false_positives.json")
        return self._load_json_file(path)
    
    def _save_false_positives(self):
        path = os.path.join(self.DATA_DIR, "false_positives.json")
        self._save_json_file(path, self.false_positives)
    
    def _load_accepted_findings(self) -> List[Dict]:
        path = os.path.join(self.DATA_DIR, "accepted_findings.json")
        return self._load_json_file(path)
    
    def _save_accepted_findings(self):
        path = os.path.join(self.DATA_DIR, "accepted_findings.json")
        self._save_json_file(path, self.accepted_findings)
    
    def _load_json_file(self, path: str) -> List[Dict]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_json_file(self, path: str, data: List[Dict]):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Save error: {e}")
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get training data statistics."""
        return {
            "total_overrides": len(self.overrides),
            "total_false_positives": len(self.false_positives),
            "total_accepted": len(self.accepted_findings),
            "by_criterion": self._count_by_criterion()
        }
    
    def _count_by_criterion(self) -> Dict[str, int]:
        counts = {}
        for record in self.overrides + self.false_positives:
            criterion = record.get("criterion", "unknown")
            counts[criterion] = counts.get(criterion, 0) + 1
        return counts


# Singleton instance
training_data = TrainingDataManager()
