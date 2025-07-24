#!/usr/bin/env python3
"""
Cochrane Library parser (stub) for ImmortyX system
Loads sample data instead of actual API calls for paid content
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from parsers.base_parser import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

class CochraneParser(BaseParser):
    """Stub parser for Cochrane Library systematic reviews"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("cochrane", config)
        self.sample_file = "cochrane_sample.json"
    
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse documents from sample data"""
        try:
            logger.info(f"Loading Cochrane Library sample data for query: {query}")
            
            # Load sample data
            documents = self.load_sample_data(self.sample_file)
            
            if not documents:
                # Create some default sample data if file doesn't exist
                documents = self._create_default_samples()
            
            # Filter by query relevance
            filtered_docs = self._filter_by_query(documents, query)
            
            # Validate documents
            valid_documents = [doc for doc in filtered_docs if self.validate_document(doc)]
            
            self.mark_updated()
            
            logger.info(f"Retrieved {len(valid_documents)} sample systematic reviews from Cochrane")
            return valid_documents[:max_results]
        
        except Exception as e:
            logger.error(f"Error loading Cochrane sample data: {e}")
            return []
    
    def _create_default_samples(self) -> List[ParsedDocument]:
        """Create default sample systematic reviews"""
        samples = [
            {
                "title": "Exercise interventions for preventing and treating age-related frailty: a systematic review and meta-analysis",
                "content": "Background: Frailty is a common geriatric syndrome characterized by decreased reserve and resistance to stressors. Exercise interventions have been proposed as effective treatments. Objectives: To assess the effects of exercise interventions on frailty in older adults. Methods: We searched multiple databases and included randomized controlled trials comparing exercise interventions with control conditions in adults aged 65 years and older. Results: 45 studies with 4,231 participants were included. Exercise interventions showed significant improvements in frailty scores (SMD -0.34, 95% CI -0.49 to -0.19), physical performance, and muscle strength. Conclusion: Exercise interventions are effective for preventing and treating frailty in older adults.",
                "authors": ["Maria Rodriguez", "John Smith", "Elena Chen", "David Wilson"],
                "url": "https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD012345",
                "metadata": {
                    "doi": "10.1002/14651858.CD012345",
                    "review_type": "Systematic review",
                    "participants": 4231,
                    "studies_included": 45,
                    "quality_grade": "High",
                    "source_type": "systematic_review"
                }
            },
            {
                "title": "Vitamin D supplementation for preventing mortality and morbidity in older adults: a systematic review",
                "content": "Background: Vitamin D deficiency is common in older adults and has been associated with increased mortality and morbidity. Objectives: To assess the effects of vitamin D supplementation on mortality and major morbidity in older adults. Methods: We included randomized controlled trials comparing vitamin D supplementation with placebo or no treatment in adults aged 65 years and older. Results: 81 studies with 53,897 participants were included. Vitamin D supplementation reduced all-cause mortality (RR 0.93, 95% CI 0.88 to 0.99) and hip fractures (RR 0.84, 95% CI 0.74 to 0.96). No significant effects were found for cardiovascular events or cancer incidence.",
                "authors": ["Sarah Johnson", "Michael Brown", "Lisa Wang", "Robert Davis"],
                "url": "https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD007469",
                "metadata": {
                    "doi": "10.1002/14651858.CD007469",
                    "review_type": "Systematic review",
                    "participants": 53897,
                    "studies_included": 81,
                    "quality_grade": "Moderate",
                    "source_type": "systematic_review"
                }
            },
            {
                "title": "Caloric restriction and intermittent fasting for longevity: a systematic review of human studies",
                "content": "Background: Caloric restriction and intermittent fasting have shown promise for extending lifespan in animal models. Human evidence is limited. Objectives: To evaluate the effects of caloric restriction and intermittent fasting on longevity biomarkers and health outcomes in humans. Methods: We searched for randomized controlled trials and cohort studies examining caloric restriction or intermittent fasting interventions in healthy adults. Results: 28 studies with 2,413 participants were included. Interventions showed improvements in body weight (MD -3.2 kg, 95% CI -4.1 to -2.3), insulin sensitivity, and inflammatory markers. Long-term mortality data were limited but suggested potential benefits.",
                "authors": ["Jennifer Taylor", "Thomas Anderson", "Maria Garcia", "Christopher Lee"],
                "url": "https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD013496",
                "metadata": {
                    "doi": "10.1002/14651858.CD013496",
                    "review_type": "Systematic review",
                    "participants": 2413,
                    "studies_included": 28,
                    "quality_grade": "Moderate",
                    "source_type": "systematic_review"
                }
            }
        ]
        
        documents = []
        for i, sample in enumerate(samples):
            # Create realistic publication dates (recent but not too recent)
            pub_date = datetime.now() - timedelta(days=30 + i*60)
            
            doc = ParsedDocument(
                title=sample["title"],
                content=sample["content"],
                source=self.name,
                url=sample["url"],
                authors=sample["authors"],
                publication_date=pub_date,
                document_type="systematic_review",
                metadata=sample["metadata"]
            )
            documents.append(doc)
        
        return documents
    
    def _filter_by_query(self, documents: List[ParsedDocument], query: str) -> List[ParsedDocument]:
        """Filter documents by query relevance"""
        if not query:
            return documents
        
        query_words = query.lower().split()
        filtered = []
        
        for doc in documents:
            text = (doc.title + " " + doc.content).lower()
            # Calculate relevance score
            matches = sum(1 for word in query_words if word in text)
            if matches > 0:
                filtered.append((doc, matches))
        
        # Sort by relevance and return documents
        filtered.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in filtered]
    
    def validate_document(self, document: ParsedDocument) -> bool:
        """Validate Cochrane systematic review"""
        try:
            # Basic validation
            if not document.title or len(document.title.strip()) < 20:
                return False
            
            if not document.content or len(document.content.strip()) < 100:
                return False
            
            # Check for systematic review quality indicators
            quality_indicators = [
                'systematic review', 'meta-analysis', 'randomized', 'controlled',
                'participants', 'studies', 'confidence interval', 'effect size',
                'cochrane', 'grade', 'quality', 'evidence'
            ]
            
            text_lower = (document.title + " " + document.content).lower()
            quality_score = sum(1 for indicator in quality_indicators if indicator in text_lower)
            
            # Require high quality indicators for systematic reviews
            return quality_score >= 3
        
        except Exception as e:
            logger.warning(f"Error validating document: {e}")
            return False
