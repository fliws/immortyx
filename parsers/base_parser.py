#!/usr/bin/env python3
"""
Base parser class for ImmortyX system
Abstract base class for all data source parsers
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import os
import json

logger = logging.getLogger(__name__)

class ParsedDocument:
    """Data structure for parsed documents"""
    
    def __init__(self, 
                 title: str,
                 content: str,
                 source: str,
                 url: str = None,
                 authors: List[str] = None,
                 publication_date: datetime = None,
                 document_type: str = "article",
                 metadata: Dict[str, Any] = None):
        self.title = title
        self.content = content
        self.source = source
        self.url = url
        self.authors = authors or []
        self.publication_date = publication_date or datetime.now()
        self.document_type = document_type
        self.metadata = metadata or {}
        self.parsed_date = datetime.now()
        self.document_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique document ID"""
        import hashlib
        content_hash = hashlib.md5(f"{self.title}{self.source}{self.url}".encode()).hexdigest()
        return f"{self.source}_{content_hash[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'url': self.url,
            'authors': self.authors,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'document_type': self.document_type,
            'metadata': self.metadata,
            'parsed_date': self.parsed_date.isoformat()
        }

class BaseParser(ABC):
    """Abstract base class for all parsers"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.last_update = None
        self.update_interval = self.config.get('update_interval', 3600)  # Default 1 hour
        self.is_enabled = self.config.get('enabled', True)
        self.cache_dir = self.config.get('cache_dir', 'data/cache')
        self.sample_data_dir = self.config.get('sample_data_dir', 'data/sample_data')
        self.use_cache = self.config.get('use_cache', True)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.sample_data_dir, exist_ok=True)
        
        logger.info(f"Initialized parser: {self.name}")
    
    @abstractmethod
    def parse(self, query: str, max_results: int = 10) -> List[ParsedDocument]:
        """Parse documents from the data source"""
        pass
    
    @abstractmethod
    def validate_document(self, document: ParsedDocument) -> bool:
        """Validate that a document meets quality criteria"""
        pass
    
    def should_update(self) -> bool:
        """Check if parser should run based on update interval"""
        if not self.is_enabled:
            return False
        
        if self.last_update is None:
            return True
        
        time_diff = time.time() - self.last_update
        return time_diff >= self.update_interval
    
    def mark_updated(self):
        """Mark parser as updated"""
        self.last_update = time.time()
    
    def get_cache_path(self, query: str) -> str:
        """Get cache file path for a query"""
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{self.name}_{query_hash}.json")
    
    def load_from_cache(self, query: str, max_age: int = 3600) -> Optional[List[ParsedDocument]]:
        """Load results from cache if available and not expired"""
        if not self.use_cache:
            return None
        
        cache_path = self.get_cache_path(query)
        
        try:
            if os.path.exists(cache_path):
                # Check if cache is not expired
                cache_age = time.time() - os.path.getmtime(cache_path)
                if cache_age <= max_age:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    documents = []
                    for doc_data in cached_data:
                        doc = ParsedDocument(
                            title=doc_data['title'],
                            content=doc_data['content'],
                            source=doc_data['source'],
                            url=doc_data.get('url'),
                            authors=doc_data.get('authors', []),
                            publication_date=datetime.fromisoformat(doc_data['publication_date']) if doc_data.get('publication_date') else None,
                            document_type=doc_data.get('document_type', 'article'),
                            metadata=doc_data.get('metadata', {})
                        )
                        documents.append(doc)
                    
                    logger.info(f"Loaded {len(documents)} documents from cache for {self.name}")
                    return documents
        
        except Exception as e:
            logger.warning(f"Failed to load cache for {self.name}: {e}")
        
        return None
    
    def save_to_cache(self, query: str, documents: List[ParsedDocument]):
        """Save results to cache"""
        if not self.use_cache:
            return
        
        cache_path = self.get_cache_path(query)
        
        try:
            doc_data = [doc.to_dict() for doc in documents]
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(documents)} documents to cache for {self.name}")
        
        except Exception as e:
            logger.warning(f"Failed to save cache for {self.name}: {e}")
    
    def load_sample_data(self, filename: str) -> List[ParsedDocument]:
        """Load sample data from file (for paid/stub parsers)"""
        sample_path = os.path.join(self.sample_data_dir, filename)
        
        try:
            if os.path.exists(sample_path):
                with open(sample_path, 'r', encoding='utf-8') as f:
                    sample_data = json.load(f)
                
                documents = []
                for doc_data in sample_data:
                    doc = ParsedDocument(
                        title=doc_data['title'],
                        content=doc_data['content'],
                        source=doc_data['source'],
                        url=doc_data.get('url'),
                        authors=doc_data.get('authors', []),
                        publication_date=datetime.fromisoformat(doc_data['publication_date']) if doc_data.get('publication_date') else None,
                        document_type=doc_data.get('document_type', 'article'),
                        metadata=doc_data.get('metadata', {})
                    )
                    documents.append(doc)
                
                logger.info(f"Loaded {len(documents)} sample documents for {self.name}")
                return documents
            else:
                logger.warning(f"Sample data file not found: {sample_path}")
                return []
        
        except Exception as e:
            logger.error(f"Failed to load sample data for {self.name}: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get parser status information"""
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'last_update': self.last_update,
            'should_update': self.should_update(),
            'update_interval': self.update_interval
        }
