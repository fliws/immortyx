#!/usr/bin/env python3
"""
arXiv parser for ImmortyX system
Fetches papers from arXiv in quantitative biology and related fields
"""

import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from datetime import datetime
from parsers.base_parser import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

class ArxivParser(BaseParser):
    """Parser for arXiv preprint server"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("arxiv", config)
        self.base_url = "http://export.arxiv.org/api/query"
        self.rate_limit = self.config.get('rate_limit', 1)  # 1 request per second
        
        # Focus on biology-related categories
        self.categories = [
            "q-bio.MN",  # Molecular Networks
            "q-bio.CB",  # Cell Behavior
            "q-bio.GN",  # Genomics
            "q-bio.TO",  # Tissues and Organs
            "physics.bio-ph",  # Biological Physics
            "stat.AP"  # Statistics Applications
        ]
    
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse documents from arXiv"""
        try:
            # Check cache first
            cached_results = self.load_from_cache(query, max_age=3600)
            if cached_results:
                return cached_results[:max_results]
            
            logger.info(f"Searching arXiv for: {query}")
            
            documents = self._search_arxiv(query, max_results)
            
            # Validate documents
            valid_documents = [doc for doc in documents if self.validate_document(doc)]
            
            # Cache results
            self.save_to_cache(query, valid_documents)
            self.mark_updated()
            
            logger.info(f"Retrieved {len(valid_documents)} valid documents from arXiv")
            return valid_documents
        
        except Exception as e:
            logger.error(f"Error parsing arXiv for query '{query}': {e}")
            return []
    
    def _search_arxiv(self, query: str, max_results: int) -> List[ParsedDocument]:
        """Search arXiv using API"""
        documents = []
        
        try:
            # Construct search query
            search_query = f"all:{query}"
            
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Title
                    title_elem = entry.find('atom:title', namespaces)
                    title = title_elem.text.strip() if title_elem is not None else "No title"
                    
                    # Abstract
                    summary_elem = entry.find('atom:summary', namespaces)
                    abstract = summary_elem.text.strip() if summary_elem is not None else "No abstract"
                    
                    # Authors
                    authors = []
                    for author_elem in entry.findall('atom:author', namespaces):
                        name_elem = author_elem.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # Publication date
                    pub_date = None
                    published_elem = entry.find('atom:published', namespaces)
                    if published_elem is not None:
                        try:
                            pub_date = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                        except ValueError:
                            logger.warning(f"Could not parse date: {published_elem.text}")
                    
                    # arXiv ID and URL
                    id_elem = entry.find('atom:id', namespaces)
                    arxiv_url = id_elem.text if id_elem is not None else None
                    arxiv_id = arxiv_url.split('/')[-1] if arxiv_url else None
                    
                    # Categories
                    categories = []
                    for category_elem in entry.findall('atom:category', namespaces):
                        term = category_elem.get('term')
                        if term:
                            categories.append(term)
                    
                    # DOI if available
                    doi = None
                    doi_elem = entry.find('arxiv:doi', namespaces)
                    if doi_elem is not None:
                        doi = doi_elem.text
                    
                    # Metadata
                    metadata = {
                        'arxiv_id': arxiv_id,
                        'categories': categories,
                        'doi': doi,
                        'source_type': 'preprint'
                    }
                    
                    # Create document
                    document = ParsedDocument(
                        title=title,
                        content=abstract,
                        source=self.name,
                        url=arxiv_url,
                        authors=authors,
                        publication_date=pub_date,
                        document_type="preprint",
                        metadata=metadata
                    )
                    
                    documents.append(document)
                
                except Exception as e:
                    logger.warning(f"Error parsing individual arXiv entry: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
        
        return documents
    
    def validate_document(self, document: ParsedDocument) -> bool:
        """Validate arXiv document"""
        try:
            # Basic validation
            if not document.title or len(document.title.strip()) < 10:
                return False
            
            if not document.content or len(document.content.strip()) < 50:
                return False
            
            # Check for longevity/aging related content
            longevity_keywords = [
                'aging', 'ageing', 'longevity', 'lifespan', 'senescence',
                'gerontology', 'life extension', 'cellular aging', 'mortality',
                'survival', 'age-related', 'telomere', 'caloric restriction',
                'healthspan', 'rejuvenation', 'autophagy', 'oxidative stress',
                'mitochondrial', 'dna damage', 'protein aggregation'
            ]
            
            text_lower = (document.title + " " + document.content).lower()
            matches = sum(1 for keyword in longevity_keywords if keyword in text_lower)
            
            return matches > 0
        
        except Exception as e:
            logger.warning(f"Error validating document: {e}")
            return False
