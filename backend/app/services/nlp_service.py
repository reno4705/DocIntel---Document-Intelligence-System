from transformers import pipeline
from typing import List, Dict, Tuple
import torch
import os

from app.core import logger
from app.schemas import EntityItem, AnalysisResult

# Model paths - use local if available, otherwise download from HuggingFace
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_NER_MODEL = os.path.join(BASE_DIR, "models", "bert-ner")
LOCAL_SUMMARIZER_MODEL = os.path.join(BASE_DIR, "models", "bart-summarizer")

# Fallback to HuggingFace hub if local not found
NER_MODEL = LOCAL_NER_MODEL if os.path.exists(LOCAL_NER_MODEL) else "dslim/bert-base-NER"
SUMMARIZER_MODEL = LOCAL_SUMMARIZER_MODEL if os.path.exists(LOCAL_SUMMARIZER_MODEL) else "facebook/bart-large-cnn"


class NLPService:
    def __init__(self):
        self._ner_pipeline = None
        self._summarizer_pipeline = None
        self._device = 0 if torch.cuda.is_available() else -1
        
        # Log which models will be used
        logger.info(f"NER model: {NER_MODEL}")
        logger.info(f"Summarizer model: {SUMMARIZER_MODEL}")
    
    @property
    def ner_pipeline(self):
        if self._ner_pipeline is None:
            logger.info(f"Loading NER pipeline from {NER_MODEL}...")
            self._ner_pipeline = pipeline(
                "ner",
                model=NER_MODEL,
                aggregation_strategy="simple",
                device=self._device
            )
        return self._ner_pipeline
    
    @property
    def summarizer_pipeline(self):
        if self._summarizer_pipeline is None:
            logger.info(f"Loading Summarization pipeline from {SUMMARIZER_MODEL}...")
            self._summarizer_pipeline = pipeline(
                "summarization",
                model=SUMMARIZER_MODEL,
                device=self._device
            )
        return self._summarizer_pipeline
    
    def _extract_entities(self, text: str) -> List[EntityItem]:
        try:
            truncated_text = text[:512]
            results = self.ner_pipeline(truncated_text)
            entities = []
            seen = set()
            for entity in results:
                key = (entity["word"], entity["entity_group"])
                if key not in seen:
                    seen.add(key)
                    entities.append(EntityItem(
                        text=entity["word"],
                        label=entity["entity_group"],
                        score=round(entity["score"], 4)
                    ))
            return entities
        except Exception as e:
            logger.error(f"NER extraction failed: {str(e)}")
            return []
    
    def _generate_summary(self, text: str) -> str:
        try:
            if len(text) < 100:
                return text
            
            max_input_length = 1024
            truncated_text = text[:max_input_length]
            
            summary_result = self.summarizer_pipeline(
                truncated_text,
                max_length=150,
                min_length=30,
                do_sample=False
            )
            return summary_result[0]["summary_text"]
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def analyze_text(self, text: str) -> AnalysisResult:
        if not text or not text.strip():
            return AnalysisResult(summary="", entities=[])
        
        summary = self._generate_summary(text)
        entities = self._extract_entities(text)
        
        return AnalysisResult(summary=summary, entities=entities)


nlp_service = NLPService()
