#!/usr/bin/env python3
"""
PubMed parser for ImmortyX system
Uses PubMed E-utilities API to fetch biomedical literature
"""

import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from datetime import datetime
import time
import re
from parsers.base_parser import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

class PubMedParser(BaseParser):
    """Parser for PubMed E-utilities API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("pubmed", config)
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = self.config.get('email', 'immortyx@example.com')
        self.tool = "ImmortyX"
        self.api_key = self.config.get('api_key')  # Optional NCBI API key
        self.rate_limit = self.config.get('rate_limit', 3)  # Requests per second
        self.last_request_time = 0
    
    def _rate_limit_delay(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse documents from PubMed"""
        try:
            # Check cache first
            cached_results = self.load_from_cache(query, max_age=3600)
            if cached_results:
                return cached_results[:max_results]
            
            logger.info(f"Searching PubMed for: {query}")
            
            # Step 1: Search for article IDs
            pmids = self._search_pmids(query, max_results)
            if not pmids:
                logger.warning(f"No results found for query: {query}")
                return []
            
            # Step 2: Fetch article details
            documents = self._fetch_articles(pmids)
            
            # Validate documents
            valid_documents = [doc for doc in documents if self.validate_document(doc)]
            
            # Cache results
            self.save_to_cache(query, valid_documents)
            self.mark_updated()
            
            logger.info(f"Retrieved {len(valid_documents)} valid documents from PubMed")
            return valid_documents
        
        except Exception as e:
            logger.error(f"Error parsing PubMed for query '{query}': {e}")
            return []
    
    def _search_pmids(self, query: str, max_results: int) -> List[str]:
        """Search for PubMed IDs using esearch"""
        self._rate_limit_delay()
        
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml',
            'email': self.email,
            'tool': self.tool,
            'sort': 'pub+date'  # Sort by publication date
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}esearch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            pmids = [id_elem.text for id_elem in root.findall('.//Id')]
            
            logger.info(f"Found {len(pmids)} PMIDs for query: {query}")
            return pmids
        
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    def _fetch_articles(self, pmids: List[str]) -> List[ParsedDocument]:
        """Fetch article details using efetch"""
        if not pmids:
            return []
        
        self._rate_limit_delay()
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'email': self.email,
            'tool': self.tool
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}efetch.fcgi", params=params, timeout=60)
            response.raise_for_status()
            
            return self._parse_articles_xml(response.content)
        
        except Exception as e:
            logger.error(f"Error fetching PubMed articles: {e}")
            return []
    
    def _parse_articles_xml(self, xml_content: bytes) -> List[ParsedDocument]:
        """Parse XML response from PubMed"""
        documents = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract basic information
                    pmid = article.find('.//PMID').text
                    
                    # Title
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else "No title"
                    
                    # Abstract
                    abstract_texts = []
                    for abstract in article.findall('.//AbstractText'):
                        if abstract.text:
                            label = abstract.get('Label', '')
                            text = f"{label}: {abstract.text}" if label else abstract.text
                            abstract_texts.append(text)
                    
                    content = " ".join(abstract_texts) if abstract_texts else "No abstract available"
                    
                    # Authors
                    authors = []
                    for author_elem in article.findall('.//Author'):
                        last_name = author_elem.find('LastName')
                        first_name = author_elem.find('ForeName')
                        if last_name is not None and first_name is not None:
                            authors.append(f"{first_name.text} {last_name.text}")
                    
                    # Publication date
                    pub_date = None
                    date_elem = article.find('.//PubDate')
                    if date_elem is not None:
                        year_elem = date_elem.find('Year')
                        month_elem = date_elem.find('Month')
                        day_elem = date_elem.find('Day')
                        
                        if year_elem is not None:
                            try:
                                year = int(year_elem.text)
                                month = self._parse_month(month_elem.text) if month_elem is not None else 1
                                day = int(day_elem.text) if day_elem is not None else 1
                                pub_date = datetime(year, month, day)
                            except (ValueError, TypeError):
                                logger.warning(f"Could not parse date for PMID {pmid}")
                    
                    # Journal information
                    journal_elem = article.find('.//Title')
                    journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                    
                    # DOI
                    doi = None
                    for article_id in article.findall('.//ArticleId'):
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    # Create URL
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    
                    # Metadata
                    metadata = {
                        'pmid': pmid,
                        'journal': journal,
                        'doi': doi,
                        'source_type': 'peer_reviewed'
                    }
                    
                    # Create document
                    document = ParsedDocument(
                        title=title,
                        content=content,
                        source=self.name,
                        url=url,
                        authors=authors,
                        publication_date=pub_date,
                        document_type="research_article",
                        metadata=metadata
                    )
                    
                    documents.append(document)
                
                except Exception as e:
                    logger.warning(f"Error parsing individual article: {e}")
                    continue
        
        except ET.ParseError as e:
            logger.error(f"Error parsing PubMed XML: {e}")
        
        return documents
    
    def _parse_month(self, month_str: str) -> int:
        """Parse month string to number"""
        if not month_str:
            return 1
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        try:
            # Try parsing as number first
            return int(month_str)
        except ValueError:
            # Try parsing as month name
            return month_map.get(month_str[:3], 1)
    
    def validate_document(self, document: ParsedDocument) -> bool:
        """Validate PubMed document"""
        try:
            # Basic validation
            if not document.title or len(document.title.strip()) < 5:
                return False
            
            if not document.content or len(document.content.strip()) < 10:
                return False
            
            # Check for longevity/aging related content
            longevity_keywords = [
                'aging', 'ageing', 'longevity', 'lifespan', 'senescence',
                'gerontology', 'anti-aging', 'life extension', 'cellular aging',
                'telomere', 'caloric restriction', 'rapamycin', 'metformin',
                'centenarian', 'longevity genes', 'aging biomarkers'
            ]
            
            text_lower = (document.title + " " + document.content).lower()
            if not any(keyword in text_lower for keyword in longevity_keywords):
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Error validating document: {e}")
            return False
