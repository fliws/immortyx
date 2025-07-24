#!/usr/bin/env python3
"""
Test suite for ImmortyX parsers
"""

import unittest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.pubmed_parser import PubMedParser
from parsers.biorxiv_parser import BioRxivParser
from parsers.nature_parser import NatureParser
from parsers.base_parser import ParsedDocument

class TestParsers(unittest.TestCase):
    """Test cases for data source parsers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            'use_cache': False,  # Disable cache for testing
            'enabled': True
        }
    
    def test_parsed_document_creation(self):
        """Test ParsedDocument creation and methods"""
        doc = ParsedDocument(
            title="Test Article",
            content="This is a test article about aging research.",
            source="test",
            url="https://example.com/test",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime.now(),
            document_type="article"
        )
        
        self.assertEqual(doc.title, "Test Article")
        self.assertEqual(doc.source, "test")
        self.assertEqual(len(doc.authors), 2)
        self.assertIsNotNone(doc.document_id)
        
        # Test to_dict method
        doc_dict = doc.to_dict()
        self.assertIn('document_id', doc_dict)
        self.assertIn('title', doc_dict)
        self.assertIn('authors', doc_dict)
    
    def test_pubmed_parser_initialization(self):
        """Test PubMed parser initialization"""
        parser = PubMedParser(self.test_config)
        
        self.assertEqual(parser.name, "pubmed")
        self.assertTrue(parser.is_enabled)
        self.assertIsNotNone(parser.base_url)
    
    def test_biorxiv_parser_initialization(self):
        """Test bioRxiv parser initialization"""
        parser = BioRxivParser(self.test_config)
        
        self.assertEqual(parser.name, "biorxiv")
        self.assertTrue(parser.is_enabled)
        self.assertIsNotNone(parser.base_url)
    
    def test_nature_parser_initialization(self):
        """Test Nature parser (stub) initialization"""
        parser = NatureParser(self.test_config)
        
        self.assertEqual(parser.name, "nature_aging")
        self.assertTrue(parser.is_enabled)
        self.assertEqual(parser.sample_file, "nature_aging_sample.json")
    
    def test_nature_parser_sample_data(self):
        """Test Nature parser sample data generation"""
        parser = NatureParser(self.test_config)
        
        # Test sample data creation
        samples = parser._create_default_samples()
        
        self.assertGreater(len(samples), 0)
        
        for doc in samples:
            self.assertIsInstance(doc, ParsedDocument)
            self.assertEqual(doc.source, "nature_aging")
            self.assertGreater(len(doc.title), 5)
            self.assertGreater(len(doc.content), 50)
    
    def test_parser_validation(self):
        """Test document validation methods"""
        # Create a valid document
        valid_doc = ParsedDocument(
            title="Cellular senescence and aging mechanisms in longevity research",
            content="This study investigates the role of cellular senescence in aging processes. We found that senescent cells accumulate with age and contribute to age-related pathologies through inflammatory pathways.",
            source="test",
            authors=["Researcher A", "Researcher B"]
        )
        
        # Create an invalid document (too short, no aging keywords)
        invalid_doc = ParsedDocument(
            title="Short",
            content="Brief content about cars.",
            source="test"
        )
        
        parser = NatureParser(self.test_config)
        
        self.assertTrue(parser.validate_document(valid_doc))
        self.assertFalse(parser.validate_document(invalid_doc))
    
    def test_parser_should_update(self):
        """Test parser update timing logic"""
        parser = NatureParser(self.test_config)
        
        # Initially should update
        self.assertTrue(parser.should_update())
        
        # After marking updated, should not update immediately
        parser.mark_updated()
        self.assertFalse(parser.should_update())
        
        # Test disabled parser
        parser.is_enabled = False
        self.assertFalse(parser.should_update())
    
    def test_cache_path_generation(self):
        """Test cache path generation"""
        parser = NatureParser(self.test_config)
        
        query = "aging research"
        cache_path = parser.get_cache_path(query)
        
        self.assertIn(parser.name, cache_path)
        self.assertTrue(cache_path.endswith('.json'))
    
    def test_parser_status(self):
        """Test parser status reporting"""
        parser = NatureParser(self.test_config)
        
        status = parser.get_status()
        
        self.assertIn('name', status)
        self.assertIn('enabled', status)
        self.assertIn('should_update', status)
        self.assertEqual(status['name'], parser.name)

class TestParserIntegration(unittest.TestCase):
    """Integration tests for parsers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            'use_cache': False,
            'enabled': True
        }
    
    def test_nature_parser_query_filtering(self):
        """Test query filtering in Nature parser"""
        parser = NatureParser(self.test_config)
        
        # Get sample documents
        all_docs = parser._create_default_samples()
        
        # Test filtering with relevant query
        filtered_docs = parser._filter_by_query(all_docs, "senescence")
        self.assertGreater(len(filtered_docs), 0)
        
        # Test filtering with irrelevant query
        filtered_docs = parser._filter_by_query(all_docs, "quantum physics")
        self.assertEqual(len(filtered_docs), 0)
    
    def test_multiple_parser_consistency(self):
        """Test consistency across different parsers"""
        parsers = [
            NatureParser(self.test_config),
        ]
        
        for parser in parsers:
            # All parsers should have consistent interface
            self.assertTrue(hasattr(parser, 'parse'))
            self.assertTrue(hasattr(parser, 'validate_document'))
            self.assertTrue(hasattr(parser, 'should_update'))
            self.assertTrue(hasattr(parser, 'get_status'))
            
            # Status should have consistent format
            status = parser.get_status()
            required_keys = ['name', 'enabled', 'should_update']
            for key in required_keys:
                self.assertIn(key, status)

if __name__ == '__main__':
    unittest.main()
