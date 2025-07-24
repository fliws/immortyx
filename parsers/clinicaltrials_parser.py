#!/usr/bin/env python3
"""
ClinicalTrials.gov parser for ImmortyX system
Fetches clinical trial information related to longevity research
"""

import logging
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
from parsers.base_parser import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

class ClinicalTrialsParser(BaseParser):
    """Parser for ClinicalTrials.gov API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("clinicaltrials", config)
        self.base_url = "https://clinicaltrials.gov/api/query/study_fields"
        self.rate_limit = self.config.get('rate_limit', 2)  # 2 requests per second
    
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse clinical trials from ClinicalTrials.gov"""
        try:
            # Check cache first
            cached_results = self.load_from_cache(query, max_age=3600)  # 1 hour
            if cached_results:
                return cached_results[:max_results]
            
            logger.info(f"Searching ClinicalTrials.gov for: {query}")
            
            documents = self._search_trials(query, max_results)
            
            # Validate documents
            valid_documents = [doc for doc in documents if self.validate_document(doc)]
            
            # Cache results
            self.save_to_cache(query, valid_documents)
            self.mark_updated()
            
            logger.info(f"Retrieved {len(valid_documents)} valid trials from ClinicalTrials.gov")
            return valid_documents
        
        except Exception as e:
            logger.error(f"Error parsing ClinicalTrials.gov for query '{query}': {e}")
            return []
    
    def _search_trials(self, query: str, max_results: int) -> List[ParsedDocument]:
        """Search for clinical trials"""
        documents = []
        
        try:
            # Prepare search parameters
            fields = [
                'NCTId', 'OfficialTitle', 'BriefSummary', 'DetailedDescription',
                'Condition', 'InterventionName', 'Phase', 'StudyType',
                'OverallStatus', 'StartDate', 'CompletionDate', 'Sponsor',
                'PrimaryOutcomeMeasure', 'SecondaryOutcomeMeasure'
            ]
            
            params = {
                'expr': query,
                'fields': ','.join(fields),
                'min_rnk': '1',
                'max_rnk': str(max_results),
                'fmt': 'json'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'StudyFieldsResponse' not in data:
                logger.warning("No StudyFieldsResponse found in API response")
                return documents
            
            study_fields = data['StudyFieldsResponse'].get('StudyFields', [])
            
            for study in study_fields:
                try:
                    # Extract study information
                    fields_dict = {}
                    for field in study.get('Fields', []):
                        field_name = field.get('FieldName', '')
                        field_values = field.get('FieldValues', [])
                        if field_values:
                            fields_dict[field_name] = field_values[0] if len(field_values) == 1 else field_values
                    
                    nct_id = fields_dict.get('NCTId', 'Unknown')
                    title = fields_dict.get('OfficialTitle', 'No title')
                    
                    # Combine summary and description
                    content_parts = []
                    if fields_dict.get('BriefSummary'):
                        content_parts.append(f"Brief Summary: {fields_dict['BriefSummary']}")
                    if fields_dict.get('DetailedDescription'):
                        content_parts.append(f"Detailed Description: {fields_dict['DetailedDescription']}")
                    if fields_dict.get('PrimaryOutcomeMeasure'):
                        content_parts.append(f"Primary Outcome: {fields_dict['PrimaryOutcomeMeasure']}")
                    
                    content = " ".join(content_parts) if content_parts else "No description available"
                    
                    # Parse dates
                    pub_date = None
                    start_date_str = fields_dict.get('StartDate')
                    if start_date_str:
                        try:
                            pub_date = datetime.strptime(start_date_str, '%B %d, %Y')
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(start_date_str, '%B %Y')
                            except ValueError:
                                logger.warning(f"Could not parse start date: {start_date_str}")
                    
                    # Create URL
                    url = f"https://clinicaltrials.gov/ct2/show/{nct_id}"
                    
                    # Extract sponsor/investigators as authors
                    authors = []
                    sponsor = fields_dict.get('Sponsor')
                    if sponsor:
                        authors.append(sponsor)
                    
                    # Metadata
                    metadata = {
                        'nct_id': nct_id,
                        'condition': fields_dict.get('Condition'),
                        'intervention': fields_dict.get('InterventionName'),
                        'phase': fields_dict.get('Phase'),
                        'study_type': fields_dict.get('StudyType'),
                        'status': fields_dict.get('OverallStatus'),
                        'completion_date': fields_dict.get('CompletionDate'),
                        'source_type': 'clinical_trial'
                    }
                    
                    # Create document
                    document = ParsedDocument(
                        title=title,
                        content=content,
                        source=self.name,
                        url=url,
                        authors=authors,
                        publication_date=pub_date,
                        document_type="clinical_trial",
                        metadata=metadata
                    )
                    
                    documents.append(document)
                
                except Exception as e:
                    logger.warning(f"Error parsing individual clinical trial: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching clinical trials: {e}")
        
        return documents
    
    def validate_document(self, document: ParsedDocument) -> bool:
        """Validate clinical trial document"""
        try:
            # Basic validation
            if not document.title or len(document.title.strip()) < 10:
                return False
            
            if not document.content or len(document.content.strip()) < 20:
                return False
            
            # Check for longevity/aging related content
            longevity_keywords = [
                'aging', 'ageing', 'longevity', 'lifespan', 'anti-aging',
                'age-related', 'elderly', 'geriatric', 'senescence',
                'healthspan', 'frailty', 'cognitive decline', 'sarcopenia',
                'osteoporosis', 'cardiovascular aging', 'metabolic aging',
                'rapamycin', 'metformin', 'caloric restriction', 'exercise',
                'hormone replacement', 'vitamin d', 'omega-3', 'resveratrol'
            ]
            
            text_lower = (document.title + " " + document.content).lower()
            matches = sum(1 for keyword in longevity_keywords if keyword in text_lower)
            
            # Also check if it's specifically related to older adults
            age_indicators = ['65', '70', '75', '80', 'older adult', 'senior', 'geriatric']
            age_matches = sum(1 for indicator in age_indicators if indicator in text_lower)
            
            return matches > 0 or age_matches > 0
        
        except Exception as e:
            logger.warning(f"Error validating document: {e}")
            return False
