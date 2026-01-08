"""
Thai NLP Service for ML Inference

Integrates 3 Hugging Face models:
1. ABSA - Aspect-Based Sentiment Analysis
2. Intent Classification
3. Sentiment Analysis
"""
import json
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)


# =====================================================
# MODEL CONFIGURATION
# =====================================================

MODEL_CONFIGS = {
    "absa": {
        "repo_id": "unduood/phayathaibert-absa-sports-facility-v2",
        "description": "Aspect-Based Sentiment Analysis for Sports Facility"
    },
    "intent": {
        "repo_id": "unduood/phayathaibert-intent-classification-sports-facility",
        "description": "Intent Classification (Feedback/Complaint/Question/Off-topic)"
    },
    "sentiment": {
        "repo_id": "poom-sci/WangchanBERTa-finetuned-sentiment",
        "description": "General Thai Sentiment Analysis"
    }
}


# =====================================================
# RESULT DATA CLASSES
# =====================================================

@dataclass
class ABSAResult:
    """Result structure for ABSA prediction"""
    aspect: str
    aspect_thai: str
    sentiment: str
    confidence: float


@dataclass
class IntentResult:
    """Result structure for Intent Classification"""
    labels: List[str]
    probabilities: Dict[str, float]


@dataclass
class SentimentResult:
    """Result structure for Sentiment Analysis"""
    label: str
    confidence: float
    probabilities: Dict[str, float]


# =====================================================
# SERVICE CLASSES
# =====================================================

class ABSAService:
    """
    Aspect-Based Sentiment Analysis Service

    Analyzes sentiment for different aspects:
    - Equipment (อุปกรณ์)
    - Staff (พนักงาน)
    - Cleanliness (ความสะอาด)
    - Atmosphere (บรรยากาศ)
    - Price (ราคา)
    - Location (ที่ตั้ง)
    - Programs (โปรแกรม/คลาส)
    - Amenities (สิ่งอำนวยความสะดวก)
    """

    def __init__(
        self,
        repo_id: str = MODEL_CONFIGS["absa"]["repo_id"],
        device: Optional[str] = None
    ):
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.repo_id = repo_id

        logger.info(f"Loading ABSA model from {repo_id}...")

        # Load tokenizer & model
        self.tokenizer = AutoTokenizer.from_pretrained(repo_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(repo_id)
        self.model.to(self.device)
        self.model.eval()

        # Load ABSA config (aspects, labels)
        config_path = hf_hub_download(repo_id=repo_id, filename="absa_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.aspects = config['aspects']  # {'Equipment': 'อุปกรณ์', ...}
        self.aspect_list = config['aspect_list']
        self.sentiment_labels = config['sentiment_labels']  # ['none', 'positive', 'negative', 'neutral']
        self.max_length = config.get('max_length', 128)

        logger.info(f"✅ ABSAService loaded - Aspects: {self.aspect_list}")

    def _predict_single_aspect(self, text: str, aspect_th: str) -> Dict:
        """Internal: predict sentiment for one aspect"""
        encoding = self.tokenizer(
            text,
            aspect_th,  # sentence pair: [text] [SEP] [aspect]
            return_tensors='pt',
            truncation=True,
            padding='max_length',
            max_length=self.max_length
        )

        with torch.no_grad():
            outputs = self.model(
                input_ids=encoding['input_ids'].to(self.device),
                attention_mask=encoding['attention_mask'].to(self.device)
            )
            probs = F.softmax(outputs.logits, dim=-1)[0]
            pred_idx = torch.argmax(probs).item()

        return {
            'sentiment': self.sentiment_labels[pred_idx],
            'confidence': probs[pred_idx].item(),
            'probabilities': {label: probs[i].item() for i, label in enumerate(self.sentiment_labels)}
        }

    def analyze(self, text: str, include_none: bool = False) -> List[Dict]:
        """
        Analyze sentiment for all aspects

        Args:
            text: Text to analyze
            include_none: Include aspects with 'none' sentiment (default: False)

        Returns:
            List of {aspect, aspect_thai, sentiment, confidence}
        """
        results = []

        for aspect_en in self.aspect_list:
            aspect_th = self.aspects[aspect_en]
            pred = self._predict_single_aspect(text, aspect_th)

            if include_none or pred['sentiment'] != 'none':
                results.append({
                    'aspect': aspect_en,
                    'aspect_thai': aspect_th,
                    'sentiment': pred['sentiment'],
                    'confidence': round(pred['confidence'], 4)
                })

        return results


class IntentClassificationService:
    """
    Multi-Label Intent Classification Service

    Classifies intent types:
    - Feedback: ความคิดเห็น/รีวิว
    - Complaint: ข้อร้องเรียนร้ายแรง
    - Question: คำถาม/สอบถาม
    - Off-topic: ไม่เกี่ยวข้อง

    Note: Multi-label - one text can have multiple intents
    """

    def __init__(
        self,
        repo_id: str = MODEL_CONFIGS["intent"]["repo_id"],
        device: Optional[str] = None,
        default_threshold: float = 0.5
    ):
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.repo_id = repo_id
        self.default_threshold = default_threshold

        logger.info(f"Loading Intent model from {repo_id}...")

        # Load tokenizer & model
        self.tokenizer = AutoTokenizer.from_pretrained(repo_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(repo_id)
        self.model.to(self.device)
        self.model.eval()

        # Get labels from model config
        self.labels = list(self.model.config.id2label.values())
        self.max_length = 128

        logger.info(f"✅ IntentClassificationService loaded - Labels: {self.labels}")

    def classify(
        self,
        text: Union[str, List[str]],
        threshold: Optional[float] = None
    ) -> Union[Dict, List[Dict]]:
        """
        Classify intent of text(s)

        Args:
            text: Text or list of texts
            threshold: Threshold for multi-label classification (default: 0.5)

        Returns:
            Dict or List[Dict] of {labels, probabilities}
        """
        threshold = threshold or self.default_threshold
        single_input = isinstance(text, str)
        texts = [text] if single_input else text

        # Tokenize
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Inference (Multi-label uses sigmoid, not softmax)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.sigmoid(outputs.logits).cpu().numpy()

        # Build results
        results = []
        for i, txt in enumerate(texts):
            predicted_labels = []
            probabilities = {}

            for j, label in enumerate(self.labels):
                prob = float(probs[i][j])
                probabilities[label] = round(prob, 4)
                if prob >= threshold:
                    predicted_labels.append(label)

            results.append({
                'text': txt,
                'labels': predicted_labels,
                'probabilities': probabilities
            })

        return results[0] if single_input else results

    def get_primary_intent(self, text: str) -> Dict:
        """
        Get primary intent (highest probability)

        Returns:
            {label, confidence}
        """
        result = self.classify(text, threshold=0.0)
        probs = result['probabilities']
        primary = max(probs, key=probs.get)
        return {
            'label': primary,
            'confidence': probs[primary]
        }


class SentimentAnalysisService:
    """
    Thai Sentiment Analysis Service (WangchanBERTa)

    Analyzes overall sentiment:
    - pos: เชิงบวก
    - neg: เชิงลบ
    - neu: กลางๆ
    """

    def __init__(
        self,
        repo_id: str = MODEL_CONFIGS["sentiment"]["repo_id"],
        device: Optional[str] = None
    ):
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.repo_id = repo_id

        logger.info(f"Loading Sentiment model from {repo_id}...")

        # Load tokenizer & model
        self.tokenizer = AutoTokenizer.from_pretrained(repo_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(repo_id)
        self.model.to(self.device)
        self.model.eval()

        # Get labels from model config
        self.id2label = self.model.config.id2label
        self.labels = list(self.id2label.values())
        self.max_length = 512

        logger.info(f"✅ SentimentAnalysisService loaded - Labels: {self.labels}")

    def analyze(
        self,
        text: Union[str, List[str]],
        return_all_probs: bool = True
    ) -> Union[Dict, List[Dict]]:
        """
        Analyze sentiment of text(s)

        Args:
            text: Text or list of texts
            return_all_probs: Return probabilities for all classes

        Returns:
            Dict or List[Dict] of {label, confidence, [probabilities]}
        """
        single_input = isinstance(text, str)
        texts = [text] if single_input else text

        # Tokenize
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Inference (Single-label uses softmax)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()

        # Build results
        results = []
        for i, txt in enumerate(texts):
            pred_idx = probs[i].argmax()
            result = {
                'text': txt,
                'label': self.id2label[pred_idx],
                'confidence': round(float(probs[i][pred_idx]), 4)
            }

            if return_all_probs:
                result['probabilities'] = {
                    self.id2label[j]: round(float(probs[i][j]), 4)
                    for j in range(len(self.labels))
                }

            results.append(result)

        return results[0] if single_input else results


# =====================================================
# UNIFIED NLP SERVICE
# =====================================================

class ThaiNLPService:
    """
    🇹🇭 Unified Thai NLP Service

    Combines 3 models for comprehensive text analysis:
    1. ABSA - Aspect-Based Sentiment Analysis
    2. Intent - Intent Classification
    3. Sentiment - Overall Sentiment Analysis

    Usage:
        # Initialize once (e.g., at worker startup)
        nlp_service = ThaiNLPService()

        # Analyze text
        result = nlp_service.analyze_all("ข้อความ feedback")
    """

    def __init__(self, device: Optional[str] = None, lazy_load: bool = False):
        """
        Initialize Thai NLP Service

        Args:
            device: 'cuda' or 'cpu' (auto-detect if None)
            lazy_load: True = load models on first use
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self._absa = None
        self._intent = None
        self._sentiment = None

        logger.info(f"Initializing ThaiNLPService on device: {self.device}")

        if not lazy_load:
            self._load_all_models()

    def _load_all_models(self):
        """Load all models"""
        logger.info("="*60)
        logger.info("🔄 Loading Thai NLP Models...")
        logger.info("="*60)

        self._absa = ABSAService(device=self.device)
        self._intent = IntentClassificationService(device=self.device)
        self._sentiment = SentimentAnalysisService(device=self.device)

        logger.info("="*60)
        logger.info("✅ All models loaded successfully!")
        logger.info("="*60)

    @property
    def absa(self) -> ABSAService:
        """Get ABSA service (lazy load if needed)"""
        if self._absa is None:
            self._absa = ABSAService(device=self.device)
        return self._absa

    @property
    def intent(self) -> IntentClassificationService:
        """Get Intent service (lazy load if needed)"""
        if self._intent is None:
            self._intent = IntentClassificationService(device=self.device)
        return self._intent

    @property
    def sentiment(self) -> SentimentAnalysisService:
        """Get Sentiment service (lazy load if needed)"""
        if self._sentiment is None:
            self._sentiment = SentimentAnalysisService(device=self.device)
        return self._sentiment

    def analyze_all(self, text: str) -> Dict:
        """
        🔮 Analyze text with all models

        Args:
            text: Text to analyze

        Returns:
            {
                "text": str,
                "sentiment": {label, confidence, probabilities},
                "intent": {labels, probabilities},
                "aspects": [{aspect, sentiment, confidence}, ...]
            }
        """
        sentiment_result = self.sentiment.analyze(text)
        intent_result = self.intent.classify(text)
        absa_results = self.absa.analyze(text, include_none=False)

        return {
            "text": text,
            "sentiment": {
                "label": sentiment_result['label'],
                "confidence": sentiment_result['confidence'],
                "probabilities": sentiment_result.get('probabilities', {})
            },
            "intent": {
                "labels": intent_result['labels'],
                "probabilities": intent_result['probabilities']
            },
            "aspects": absa_results
        }


# =====================================================
# SINGLETON INSTANCE
# =====================================================

_nlp_service: Optional[ThaiNLPService] = None


def get_nlp_service() -> ThaiNLPService:
    """
    Get or create NLP service singleton

    Returns:
        ThaiNLPService instance
    """
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = ThaiNLPService()
    return _nlp_service
