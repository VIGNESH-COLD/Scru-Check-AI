"""
LLM Client Module
Handles Mistral API calls for intelligent analysis
"""

import os
from typing import Dict, Any, List, Optional
import json

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """
    LLM client for Mistral API.
    Provides intelligent analysis capabilities for scrutiny system.
    """
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.client = None
        self.model_name = "mistral-small-latest"
        self._initialize()
    
    def _initialize(self):
        """Initialize Mistral client."""
        if not MISTRAL_AVAILABLE:
            print("⚠️ mistralai library not available")
            return
        
        if not self.api_key or self.api_key == "your_mistral_api_key_here":
            print("⚠️ MISTRAL_API_KEY not configured")
            return
        
        try:
            self.client = Mistral(api_key=self.api_key)
            print(f"✅ Mistral LLM initialized ({self.model_name})")
        except Exception as e:
            print(f"⚠️ Mistral initialization failed: {e}")
    
    async def classify_bloom_level(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify question into Bloom's Taxonomy level using LLM.
        """
        if not self.client:
            print("⚠️ LLM not available - using rule-based fallback")
            return {"bloom_level": None, "confidence": 0, "error": "LLM not available"}
        
        print(f"🤖 Mistral API call: Classifying Bloom's level for question: '{question[:50]}...'")
        
        prompt = f"""Analyze this exam question and classify it into ONE Bloom's Taxonomy level.

Question: "{question}"

{f'Context from syllabus: {context}' if context else ''}

Respond in JSON format ONLY:
{{
    "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_verb": "the action verb that determined this",
    "suggested_improvement": "how to raise to higher level (if applicable)"
}}"""

        try:
            response = await self._generate(prompt)
            result = self._parse_json_response(response)
            print(f"✅ Mistral response: {result.get('bloom_level')} (confidence: {result.get('confidence')})")
            return result
        except Exception as e:
            print(f"❌ Mistral API error: {e}")
            return {"level": None, "confidence": 0, "error": str(e)}
    
    async def check_syllabus_alignment(self, question: str, syllabus_context: str) -> Dict[str, Any]:
        """
        Check if question aligns with syllabus using LLM.
        """
        if not self.client:
            return {"aligned": None, "confidence": 0, "error": "LLM not available"}
        
        prompt = f"""Analyze if this exam question is within the scope of the given syllabus.

Question: "{question}"

Syllabus Content:
{syllabus_context[:2000]}

Respond in JSON format ONLY:
{{
    "is_aligned": true|false,
    "confidence": 0.0-1.0,
    "matched_unit": "Unit number if aligned",
    "matched_topic": "specific topic from syllabus",
    "reasoning": "brief explanation",
    "out_of_scope_reason": "explanation if not aligned"
}}"""

        try:
            response = await self._generate(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            return {"aligned": None, "confidence": 0, "error": str(e)}
    
    async def check_grammar_clarity(self, question: str) -> Dict[str, Any]:
        """
        Check grammar and clarity of question using LLM.
        """
        if not self.client:
            return {"issues": [], "confidence": 0, "error": "LLM not available"}
        
        prompt = f"""Analyze this exam question for grammar, clarity, and potential ambiguity.

Question: "{question}"

Respond in JSON format ONLY:
{{
    "is_clear": true|false,
    "grammar_score": 0.0-1.0,
    "issues": [
        {{"type": "grammar|ambiguity|clarity", "description": "issue", "suggestion": "fix"}}
    ],
    "improved_version": "rewritten question if issues found"
}}"""

        try:
            response = await self._generate(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            return {"issues": [], "confidence": 0, "error": str(e)}
    
    async def estimate_difficulty(self, question: str, marks: int) -> Dict[str, Any]:
        """
        Estimate question difficulty and time required.
        """
        if not self.client:
            return {"difficulty": None, "error": "LLM not available"}
        
        prompt = f"""Analyze this exam question's difficulty and time requirement.

Question: "{question}"
Marks: {marks}

Respond in JSON format ONLY:
{{
    "difficulty_level": "Easy|Medium|Hard|Very Hard",
    "estimated_time_minutes": number,
    "cognitive_load": "Low|Medium|High",
    "is_time_balanced": true|false,
    "reasoning": "explanation",
    "recommendation": "adjustment suggestion if unbalanced"
}}"""

        try:
            response = await self._generate(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            return {"difficulty": None, "error": str(e)}
    
    async def suggest_improvement(self, question: str, issue_type: str, current_finding: str) -> Dict[str, Any]:
        """
        Generate improvement suggestion for a flagged question.
        """
        if not self.client:
            return {"suggestion": None, "error": "LLM not available"}
        
        prompt = f"""An exam question was flagged with an issue. Suggest how to improve it.

Question: "{question}"
Issue Type: {issue_type}
Current Finding: {current_finding}

Respond in JSON format ONLY:
{{
    "improved_question": "rewritten version",
    "changes_made": ["list of changes"],
    "reasoning": "why these changes help",
    "alternative_approaches": ["other ways to ask this"]
}}"""

        try:
            response = await self._generate(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            return {"suggestion": None, "error": str(e)}
    
    async def _generate(self, prompt: str) -> str:
        """Generate response from LLM."""
        if not self.client:
            raise Exception("Model not initialized")
        
        # Mistral usage
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Note: Mistral chat method is sync, but we wrap in async function
        # For true async, we'd need aync client, but standard client is fine for now
        chat_response = self.client.chat.complete(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"}  # Mistral supports JSON mode
        )
        
        return chat_response.choices[0].message.content
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        return json.loads(response.strip())


# Singleton instance
llm_client = LLMClient()
