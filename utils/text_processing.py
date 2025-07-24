#!/usr/bin/env python3
"""
Text processing utilities for ImmortyX system
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)

class TextProcessor:
    """Utilities for text processing and analysis"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.,!?;:()\-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
        
        # Common stop words to filter out
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its',
            'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man',
            'end', 'few', 'got', 'let', 'put', 'say', 'she', 'too', 'use', 'been', 'from',
            'have', 'here', 'they', 'will', 'with', 'this', 'that', 'what', 'when', 'where',
            'were', 'said', 'each', 'make', 'most', 'over', 'such', 'very', 'well', 'work'
        }
        
        # Filter stop words and count frequency
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Return most common keywords
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Extract sentences from text"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def find_citations(text: str) -> List[str]:
        """Find citation patterns in text"""
        # Look for various citation patterns
        patterns = [
            r'\(([^)]*\d{4}[^)]*)\)',  # (Author 2023)
            r'\[(\d+)\]',              # [1]
            r'doi:\s*([^\s]+)',        # doi: 10.1000/182
            r'PMID:\s*(\d+)',          # PMID: 12345678
        ]
        
        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return citations
    
    @staticmethod
    def extract_authors(text: str) -> List[str]:
        """Extract author names from text"""
        # Look for patterns like "Smith et al." or "John Smith"
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.?',  # Smith et al.
            r'([A-Z][a-z]+,\s+[A-Z]\.(?:\s+[A-Z]\.)*)',       # Smith, J. A.
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',                   # John Smith
        ]
        
        authors = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            authors.extend(matches)
        
        return list(set(authors))  # Remove duplicates
    
    @staticmethod
    def calculate_readability_score(text: str) -> float:
        """Calculate a simple readability score (0-100, higher = more readable)"""
        if not text:
            return 0.0
        
        sentences = TextProcessor.extract_sentences(text)
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple formula (lower values = more readable)
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 4.7)
        
        # Normalize to 0-100 range
        return max(0, min(100, score))
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Simple language detection (English/Russian/Other)"""
        if not text:
            return "unknown"
        
        cyrillic_chars = len(re.findall(r'[а-яё]', text.lower()))
        latin_chars = len(re.findall(r'[a-z]', text.lower()))
        
        total_chars = cyrillic_chars + latin_chars
        if total_chars == 0:
            return "unknown"
        
        if cyrillic_chars / total_chars > 0.5:
            return "russian"
        elif latin_chars / total_chars > 0.5:
            return "english"
        else:
            return "mixed"
