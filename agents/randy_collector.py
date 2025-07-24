#!/usr/bin/env python3
"""
Randy Collector agent for ImmortyX system
Detects and flags potential pseudoscience content (Agent "James Randi")
"""

import logging
import re
from typing import Dict, List, Any, Tuple
from utils.llm_client import LLMClient
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)

class RandyCollector:
    """Agent for detecting pseudoscience patterns (named after James Randi)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.llm_client = LLMClient()
        self.text_processor = TextProcessor()
        
        # Pseudoscience warning patterns
        self.warning_patterns = {
            'extraordinary_claims': [
                r'miracle cure', r'fountain of youth', r'immortality breakthrough',
                r'aging reversed', r'eternal life', r'death defeated',
                r'100% effective', r'guaranteed results', r'secret discovered'
            ],
            'appeal_to_authority': [
                r'doctors hate this', r'scientists don\'t want you to know',
                r'suppressed by big pharma', r'hidden by medical establishment',
                r'ancient secret', r'traditional wisdom ignored'
            ],
            'cherry_picking': [
                r'one study shows', r'preliminary results suggest',
                r'initial findings indicate', r'early research hints',
                r'single case report', r'anecdotal evidence'
            ],
            'conspiracy_theories': [
                r'conspiracy', r'cover-up', r'suppressed research',
                r'silenced scientists', r'hidden truth', r'mainstream media ignores'
            ],
            'reject_peer_review': [
                r'peer review is corrupt', r'establishment bias',
                r'scientific dogma', r'paradigm resistance',
                r'alternative research', r'independent findings'
            ],
            'misleading_statistics': [
                r'up to \d+%', r'as much as \d+%', r'studies show',
                r'research proves', r'clinical studies confirm',
                r'laboratory tests reveal'
            ]
        }
        
        # High-risk sources and domains
        self.high_risk_domains = [
            'naturalnews', 'mercola', 'infowars', 'healthimpactnews',
            'naturalhealth365', 'greenmedinfo', 'thehealthsite'
        ]
        
        logger.info("Randy Collector (pseudoscience detector) initialized")
    
    def assess_document(self, document) -> Dict[str, Any]:
        """Assess a document for pseudoscience indicators"""
        try:
            text = f"{document.title} {document.content}"
            
            # Rule-based assessment
            rule_assessment = self._rule_based_assessment(text, document)
            
            # LLM-based assessment if available
            llm_assessment = {}
            if self.llm_client.is_available():
                llm_assessment = self._llm_assessment(text)
            
            # Combine assessments
            final_assessment = self._combine_assessments(rule_assessment, llm_assessment)
            
            # Add source credibility
            source_assessment = self._assess_source_credibility(document)
            final_assessment.update(source_assessment)
            
            logger.debug(f"Pseudoscience assessment for {document.document_id}: Risk level {final_assessment.get('risk_level', 'unknown')}")
            
            return final_assessment
        
        except Exception as e:
            logger.error(f"Error assessing document for pseudoscience: {e}")
            return {'risk_level': 'unknown', 'error': str(e)}
    
    def _rule_based_assessment(self, text: str, document) -> Dict[str, Any]:
        """Rule-based pseudoscience pattern detection"""
        assessment = {
            'pattern_matches': {},
            'total_warnings': 0,
            'risk_factors': []
        }
        
        try:
            text_lower = text.lower()
            
            # Check each warning pattern category
            for category, patterns in self.warning_patterns.items():
                matches = []
                for pattern in patterns:
                    found = re.findall(pattern, text_lower)
                    matches.extend(found)
                
                if matches:
                    assessment['pattern_matches'][category] = len(matches)
                    assessment['total_warnings'] += len(matches)
                    assessment['risk_factors'].append(f"{category}: {len(matches)} matches")
            
            # Check for lack of citations
            citations = self.text_processor.find_citations(text)
            if len(citations) < 2 and len(text) > 500:
                assessment['risk_factors'].append("Insufficient citations for length")
                assessment['total_warnings'] += 1
            
            # Check readability (pseudoscience often uses complex language to sound scientific)
            readability = self.text_processor.calculate_readability_score(text)
            if readability < 30:  # Very low readability
                assessment['risk_factors'].append("Very low readability score")
                assessment['total_warnings'] += 1
            
            # Check for sensationalist language
            sensational_words = [
                'breakthrough', 'revolutionary', 'shocking', 'amazing',
                'incredible', 'stunning', 'unbelievable', 'miracle'
            ]
            sensational_count = sum(1 for word in sensational_words if word in text_lower)
            if sensational_count > 3:
                assessment['risk_factors'].append(f"High sensationalist language: {sensational_count} words")
                assessment['total_warnings'] += 1
            
        except Exception as e:
            logger.warning(f"Error in rule-based assessment: {e}")
        
        return assessment
    
    def _llm_assessment(self, text: str) -> Dict[str, Any]:
        """LLM-based pseudoscience assessment"""
        try:
            # Truncate text if too long
            if len(text) > 1500:
                text = text[:1500] + "..."
            
            response = self.llm_client.detect_pseudoscience(text)
            
            # Parse LLM response for risk level
            response_lower = response.lower()
            if 'high' in response_lower and 'risk' in response_lower:
                risk_level = 'high'
            elif 'medium' in response_lower and 'risk' in response_lower:
                risk_level = 'medium'
            elif 'low' in response_lower and 'risk' in response_lower:
                risk_level = 'low'
            else:
                risk_level = 'unknown'
            
            return {
                'llm_risk_level': risk_level,
                'llm_explanation': response
            }
        
        except Exception as e:
            logger.warning(f"Error in LLM assessment: {e}")
            return {}
    
    def _assess_source_credibility(self, document) -> Dict[str, Any]:
        """Assess source credibility"""
        assessment = {
            'source_risk_factors': [],
            'source_credibility': 'unknown'
        }
        
        try:
            source = document.source.lower() if document.source else ''
            url = document.url.lower() if document.url else ''
            
            # Check against high-risk domains
            for domain in self.high_risk_domains:
                if domain in url or domain in source:
                    assessment['source_risk_factors'].append(f"High-risk domain: {domain}")
                    assessment['source_credibility'] = 'low'
                    break
            
            # Assess based on document type and metadata
            doc_type = document.document_type
            metadata = document.metadata or {}
            
            if doc_type == 'research_article' and metadata.get('source_type') == 'peer_reviewed':
                assessment['source_credibility'] = 'high'
            elif doc_type == 'preprint':
                assessment['source_credibility'] = 'medium'
            elif doc_type == 'news' or doc_type == 'blog':
                assessment['source_credibility'] = 'low'
            elif source in ['pubmed', 'biorxiv', 'arxiv', 'clinicaltrials']:
                assessment['source_credibility'] = 'high'
            elif source in ['nature_aging', 'cell', 'cochrane']:
                assessment['source_credibility'] = 'very_high'
            
            # Check for author credentials
            authors = document.authors or []
            if len(authors) == 0:
                assessment['source_risk_factors'].append("No authors listed")
            elif len(authors) == 1 and not any(metadata.get('source_type') == t for t in ['peer_reviewed', 'preprint']):
                assessment['source_risk_factors'].append("Single author, non-academic source")
        
        except Exception as e:
            logger.warning(f"Error assessing source credibility: {e}")
        
        return assessment
    
    def _combine_assessments(self, rule_assessment: Dict, llm_assessment: Dict) -> Dict[str, Any]:
        """Combine rule-based and LLM assessments"""
        # Calculate rule-based risk level
        warning_count = rule_assessment.get('total_warnings', 0)
        if warning_count >= 5:
            rule_risk = 'high'
        elif warning_count >= 3:
            rule_risk = 'medium'
        elif warning_count >= 1:
            rule_risk = 'low'
        else:
            rule_risk = 'very_low'
        
        # Get LLM risk level
        llm_risk = llm_assessment.get('llm_risk_level', 'unknown')
        
        # Combine risk levels (take the higher one)
        risk_hierarchy = {'very_low': 0, 'low': 1, 'medium': 2, 'high': 3, 'unknown': 1}
        
        final_risk_score = max(
            risk_hierarchy.get(rule_risk, 1),
            risk_hierarchy.get(llm_risk, 1)
        )
        
        risk_levels = {0: 'very_low', 1: 'low', 2: 'medium', 3: 'high'}
        final_risk = risk_levels[final_risk_score]
        
        # Compile final assessment
        final_assessment = {
            'risk_level': final_risk,
            'rule_based_risk': rule_risk,
            'total_warnings': warning_count,
            'risk_factors': rule_assessment.get('risk_factors', []),
            'pattern_matches': rule_assessment.get('pattern_matches', {})
        }
        
        # Add LLM assessment if available
        if llm_assessment:
            final_assessment.update(llm_assessment)
        
        return final_assessment
    
    def get_flagged_documents(self, documents: List) -> List[Tuple[Any, Dict]]:
        """Get documents flagged as potentially pseudoscientific"""
        flagged = []
        
        for document in documents:
            assessment = self.assess_document(document)
            risk_level = assessment.get('risk_level', 'unknown')
            
            if risk_level in ['medium', 'high']:
                flagged.append((document, assessment))
        
        return flagged
    
    def generate_report(self, documents: List) -> Dict[str, Any]:
        """Generate a pseudoscience assessment report"""
        report = {
            'total_documents': len(documents),
            'risk_distribution': {'very_low': 0, 'low': 0, 'medium': 0, 'high': 0, 'unknown': 0},
            'flagged_documents': [],
            'common_risk_factors': {},
            'generated_at': self.text_processor.extract_sentences("")[0] if self.text_processor.extract_sentences("") else "Unknown time"
        }
        
        try:
            all_risk_factors = []
            
            for document in documents:
                assessment = self.assess_document(document)
                risk_level = assessment.get('risk_level', 'unknown')
                report['risk_distribution'][risk_level] += 1
                
                if risk_level in ['medium', 'high']:
                    report['flagged_documents'].append({
                        'document_id': document.document_id,
                        'title': document.title[:100] + "..." if len(document.title) > 100 else document.title,
                        'source': document.source,
                        'risk_level': risk_level,
                        'risk_factors': assessment.get('risk_factors', [])
                    })
                
                all_risk_factors.extend(assessment.get('risk_factors', []))
            
            # Count common risk factors
            from collections import Counter
            risk_factor_counts = Counter(all_risk_factors)
            report['common_risk_factors'] = dict(risk_factor_counts.most_common(10))
        
        except Exception as e:
            logger.error(f"Error generating pseudoscience report: {e}")
            report['error'] = str(e)
        
        return report
