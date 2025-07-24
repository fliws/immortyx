#!/usr/bin/env python3
"""
bioRxiv parser for ImmortyX system
Fetches preprints from bioRxiv server
"""

import logging
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
from parsers.base_parser import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)

class BioRxivParser(BaseParser):
    """Parser for bioRxiv preprint server"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("biorxiv", config)
        self.base_url = "https://api.biorxiv.org/details/biorxiv"
        self.rate_limit = self.config.get('rate_limit', 1)  # 1 request per second
    
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse documents from bioRxiv"""
        try:
            # Check cache first
            cached_results = self.load_from_cache(query, max_age=1800)  # 30 minutes
            if cached_results:
                return cached_results[:max_results]
            
            logger.info(f"Searching bioRxiv for: {query}")
            
            # bioRxiv API doesn't support direct search, so we'll fetch recent papers
            # and filter by keywords
            documents = self._fetch_recent_papers(max_results * 3)  # Fetch more to filter
            
            # Filter by query
            filtered_docs = self._filter_by_query(documents, query)
            
            # Validate documents
            valid_documents = [doc for doc in filtered_docs if self.validate_document(doc)]
            
            # Cache results
            self.save_to_cache(query, valid_documents)
            self.mark_updated()
            
            logger.info(f"Retrieved {len(valid_documents)} valid documents from bioRxiv")
            return valid_documents[:max_results]
        
        except Exception as e:
            logger.error(f"Error parsing bioRxiv for query '{query}': {e}")
            return []
    
    def _fetch_recent_papers(self, max_results: int) -> List[ParsedDocument]:
        """Fetch recent papers from bioRxiv"""
        documents = []
        
        try:
            # Get recent papers (last 30 days)
            from_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/{from_date}/{to_date}/0"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'collection' not in data:
                logger.warning("No collection found in bioRxiv response")
                return documents
            
            papers = data['collection'][:max_results]
            
            for paper in papers:
                try:
                    # Extract paper information
                    title = paper.get('title', 'No title')
                    abstract = paper.get('abstract', 'No abstract available')
                    authors_list = paper.get('authors', '').split(';')
                    authors = [author.strip() for author in authors_list if author.strip()]
                    
                    # Parse date
                    pub_date = None
                    date_str = paper.get('date')
                    if date_str:
                        try:
                            pub_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            logger.warning(f"Could not parse date: {date_str}")
                    
                    # Create URL
                    doi = paper.get('doi', '')
                    url = f"https://www.biorxiv.org/content/{doi}v1" if doi else None
                    
                    # Metadata
                    metadata = {
                        'doi': doi,
                        'server': paper.get('server', 'bioRxiv'),
                        'category': paper.get('category'),
                        'source_type': 'preprint'
                    }
                    
                    # Create document
                    document = ParsedDocument(
                        title=title,
                        content=abstract,
                        source=self.name,
                        url=url,
                        authors=authors,
                        publication_date=pub_date,
                        document_type="preprint",
                        metadata=metadata
                    )
                    
                    documents.append(document)
                
                except Exception as e:
                    logger.warning(f"Error parsing individual bioRxiv paper: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching bioRxiv papers: {e}")
        
        return documents
    
    def _filter_by_query(self, documents: List[ParsedDocument], query: str) -> List[ParsedDocument]:
        """Filter documents by query relevance"""
        if not query:
            return documents
        
        query_words = [word.lower() for word in query.split()]
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
        """Validate bioRxiv document"""
        try:
            # Basic validation
            if not document.title or len(document.title.strip()) < 10:
                return False
            
            if not document.content or len(document.content.strip()) < 50:
                return False
            
            # Check for longevity/aging related content
            longevity_keywords = [
                'aging', 'ageing', 'longevity', 'lifespan', 'senescence',
                'gerontology', 'anti-aging', 'life extension', 'cellular aging',
                'telomere', 'caloric restriction', 'rapamycin', 'metformin',
                'centenarian', 'longevity genes', 'aging biomarkers',
                'healthspan', 'age-related', 'rejuvenation', 'autophagy'
            ]
            
            text_lower = (document.title + " " + document.content).lower()
            matches = sum(1 for keyword in longevity_keywords if keyword in text_lower)
            
            return matches > 0
        
        except Exception as e:
            logger.warning(f"Error validating document: {e}")
            return False
