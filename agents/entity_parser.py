#!/usr/bin/env python3
"""
Entity Parser agent for ImmortyX system
Extracts and processes named entities from collected documents
"""

import logging
import re
from typing import Dict, List, Any, Optional
from utils.llm_client import LLMClient
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)

class EntityParser:
    """Agent for extracting and processing named entities"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.llm_client = LLMClient()
        self.text_processor = TextProcessor()
        
        # Define entity categories relevant to longevity research
        self.entity_categories = {
            'genes': ['gene', 'protein', 'enzyme'],
            'drugs': ['drug', 'compound', 'medication', 'supplement'],
            'methods': ['method', 'technique', 'protocol', 'assay'],
            'organisms': ['organism', 'species', 'model'],
            'diseases': ['disease', 'condition', 'disorder', 'syndrome'],
            'researchers': ['researcher', 'scientist', 'author'],
            'companies': ['company', 'organization', 'institution'],
            'concepts': ['concept', 'theory', 'mechanism', 'pathway']
        }
        
        logger.info("Entity Parser initialized")
    
    def extract_entities(self, document) -> Dict[str, List[str]]:
        """Extract named entities from a document"""
        try:
            text = f"{document.title} {document.content}"
            
            # Combine rule-based and LLM-based extraction
            rule_based_entities = self._extract_rule_based_entities(text)
            
            if self.llm_client.is_available():
                llm_entities = self._extract_llm_entities(text)
                entities = self._merge_entities(rule_based_entities, llm_entities)
            else:
                entities = rule_based_entities
            
            # Clean and validate entities
            entities = self._clean_entities(entities)
            
            logger.debug(f"Extracted entities from document {document.document_id}: {sum(len(v) for v in entities.values())} total")
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def _extract_rule_based_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using rule-based patterns"""
        entities = {category: [] for category in self.entity_categories}
        
        try:
            # Gene/Protein patterns
            gene_patterns = [
                r'\b[A-Z][A-Z0-9]{2,10}\b',  # Gene symbols like FOXO3, TP53
                r'\bp\d{2,3}\b',  # p21, p53, etc.
                r'\b[A-Z]{2,}\d+[A-Z]?\b'  # SIRT1, mTOR, etc.
            ]
            
            for pattern in gene_patterns:
                matches = re.findall(pattern, text)
                entities['genes'].extend(matches)
            
            # Drug/Compound patterns
            drug_patterns = [
                r'\b(?:rapamycin|metformin|resveratrol|aspirin|statins?)\b',
                r'\b[A-Z][a-z]+-\d+\b',  # Compound names like NAD-83
                r'\b[A-Z]{2,}-\d+\b'  # Compound codes
            ]
            
            for pattern in drug_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['drugs'].extend(matches)
            
            # Method patterns
            method_patterns = [
                r'\b(?:qPCR|RNA-seq|ChIP-seq|immunofluorescence|flow cytometry)\b',
                r'\b(?:ELISA|Western blot|Northern blot|Southern blot)\b',
                r'\b[A-Z]{2,}-[A-Z]{2,}\b'  # Method abbreviations
            ]
            
            for pattern in method_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['methods'].extend(matches)
            
            # Organism patterns
            organism_patterns = [
                r'\b(?:C\. elegans|D\. melanogaster|S\. cerevisiae)\b',
                r'\b(?:mouse|mice|rat|human|zebrafish)\b',
                r'\b[A-Z]\. [a-z]+\b'  # Scientific names
            ]
            
            for pattern in organism_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['organisms'].extend(matches)
            
            # Disease patterns
            disease_patterns = [
                r'\b(?:cancer|diabetes|alzheimer|parkinson|cardiovascular)\b',
                r'\b(?:aging|senescence|neurodegeneration|inflammation)\b',
                r'\b[a-z]+ disease\b'
            ]
            
            for pattern in disease_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities['diseases'].extend(matches)
            
        except Exception as e:
            logger.warning(f"Error in rule-based entity extraction: {e}")
        
        return entities
    
    def _extract_llm_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using LLM"""
        entities = {category: [] for category in self.entity_categories}
        
        try:
            # Truncate text if too long
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            response = self.llm_client.extract_entities(text)
            
            # Parse LLM response (this is a simplified parser)
            lines = response.split('\n')
            current_category = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for category headers
                for category in self.entity_categories:
                    if category.lower() in line.lower():
                        current_category = category
                        break
                
                # Extract entities from lists
                if current_category and ('•' in line or '-' in line or ':' in line):
                    # Clean up the line and extract entity
                    entity = re.sub(r'^[•\-:\s]+', '', line)
                    entity = re.sub(r'\s+\([^)]+\)$', '', entity)  # Remove parenthetical info
                    
                    if entity and len(entity) > 2:
                        entities[current_category].append(entity)
        
        except Exception as e:
            logger.warning(f"Error in LLM entity extraction: {e}")
        
        return entities
    
    def _merge_entities(self, rule_entities: Dict[str, List[str]], 
                       llm_entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge entities from different extraction methods"""
        merged = {}
        
        for category in self.entity_categories:
            merged[category] = list(set(
                rule_entities.get(category, []) + 
                llm_entities.get(category, [])
            ))
        
        return merged
    
    def _clean_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean and filter extracted entities"""
        cleaned = {}
        
        for category, entity_list in entities.items():
            cleaned_list = []
            
            for entity in entity_list:
                # Basic cleaning
                entity = entity.strip()
                if not entity or len(entity) < 2:
                    continue
                
                # Remove common false positives
                false_positives = ['the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with']
                if entity.lower() in false_positives:
                    continue
                
                # Length limits
                if len(entity) > 50:  # Too long to be a meaningful entity
                    continue
                
                cleaned_list.append(entity)
            
            # Remove duplicates and sort
            cleaned[category] = sorted(list(set(cleaned_list)))
        
        return cleaned
    
    def get_entity_summary(self, entities: Dict[str, List[str]]) -> Dict[str, int]:
        """Get summary statistics of extracted entities"""
        return {category: len(entity_list) for category, entity_list in entities.items()}
    
    def find_entity_relationships(self, entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Find potential relationships between entities (simplified)"""
        relationships = []
        
        try:
            # Simple co-occurrence based relationships
            genes = entities.get('genes', [])
            drugs = entities.get('drugs', [])
            diseases = entities.get('diseases', [])
            
            # Gene-drug relationships
            for gene in genes[:5]:  # Limit to avoid too many combinations
                for drug in drugs[:5]:
                    relationships.append({
                        'type': 'gene_drug_interaction',
                        'entities': [gene, drug],
                        'confidence': 0.5  # Placeholder
                    })
            
            # Gene-disease relationships
            for gene in genes[:5]:
                for disease in diseases[:3]:
                    relationships.append({
                        'type': 'gene_disease_association',
                        'entities': [gene, disease],
                        'confidence': 0.4  # Placeholder
                    })
        
        except Exception as e:
            logger.warning(f"Error finding entity relationships: {e}")
        
        return relationships[:20]  # Limit results
