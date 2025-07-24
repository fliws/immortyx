#!/usr/bin/env python3
"""
Spider Orchestrator for ImmortyX system
Main coordination agent that manages data collection from various sources
"""

import logging
import threading
import time
from typing import Dict, List, Any
from datetime import datetime
from parsers.pubmed_parser import PubMedParser
from parsers.biorxiv_parser import BioRxivParser
from parsers.nature_parser import NatureParser
from parsers.clinicaltrials_parser import ClinicalTrialsParser
from agents.entity_parser import EntityParser
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class SpiderOrchestrator:
    """Main orchestrator for coordinating data collection agents"""
    
    def __init__(self, config: Dict[str, Any], knowledge_base):
        self.config = config
        self.knowledge_base = knowledge_base
        self.is_running = False
        self.collection_threads = {}
        
        # Initialize parsers
        self.parsers = {
            'pubmed': PubMedParser(config.get('parsers', {}).get('pubmed', {})),
            'biorxiv': BioRxivParser(config.get('parsers', {}).get('biorxiv', {})),
            'nature_aging': NatureParser(config.get('parsers', {}).get('nature_aging', {})),
            'clinicaltrials': ClinicalTrialsParser(config.get('parsers', {}).get('clinicaltrials', {}))
        }
        
        # Initialize processing agents
        self.entity_parser = EntityParser()
        
        # Collection statistics
        self.stats = {
            'total_documents': 0,
            'successful_parsings': 0,
            'failed_parsings': 0,
            'last_update': None
        }
        
        logger.info("Spider Orchestrator initialized with {} parsers".format(len(self.parsers)))
    
    def start(self):
        """Start the orchestration process"""
        if self.is_running:
            logger.warning("Spider Orchestrator is already running")
            return
        
        self.is_running = True
        logger.info("Starting Spider Orchestrator")
        
        try:
            # Start collection cycle
            self._run_collection_cycle()
        except KeyboardInterrupt:
            logger.info("Collection interrupted by user")
        except Exception as e:
            logger.error(f"Error in orchestration: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the orchestration process"""
        logger.info("Stopping Spider Orchestrator")
        self.is_running = False
        
        # Wait for threads to complete
        for thread_name, thread in self.collection_threads.items():
            if thread.is_alive():
                logger.info(f"Waiting for {thread_name} to complete...")
                thread.join(timeout=30)
    
    def _run_collection_cycle(self):
        """Run a single collection cycle"""
        research_themes = self.config.get('research_themes', [])
        query_templates = self.config.get('query_templates', {})
        
        logger.info(f"Starting collection cycle for {len(research_themes)} research themes")
        
        for theme in research_themes:
            if not self.is_running:
                break
            
            theme_queries = query_templates.get(theme, [theme])
            logger.info(f"Processing theme: {theme} with {len(theme_queries)} queries")
            
            for query in theme_queries:
                if not self.is_running:
                    break
                
                self._collect_for_query(query, theme)
        
        self.stats['last_update'] = datetime.now()
        logger.info("Collection cycle completed")
        self._log_statistics()
    
    def _collect_for_query(self, query: str, theme: str):
        """Collect documents for a specific query"""
        logger.info(f"Collecting documents for query: '{query}' (theme: {theme})")
        
        all_documents = []
        
        # Collect from each parser
        for parser_name, parser in self.parsers.items():
            if not self.is_running:
                break
            
            if not parser.should_update():
                logger.debug(f"Skipping {parser_name} - update not needed")
                continue
            
            try:
                logger.info(f"Running parser: {parser_name}")
                documents = parser.parse(query, max_results=10)
                
                if documents:
                    logger.info(f"{parser_name} returned {len(documents)} documents")
                    all_documents.extend(documents)
                    self.stats['successful_parsings'] += 1
                else:
                    logger.warning(f"{parser_name} returned no documents")
                
            except Exception as e:
                logger.error(f"Error running parser {parser_name}: {e}")
                self.stats['failed_parsings'] += 1
            
            # Rate limiting between parsers
            time.sleep(1)
        
        # Process collected documents
        if all_documents:
            self._process_documents(all_documents, query, theme)
        
        self.stats['total_documents'] += len(all_documents)
    
    def _process_documents(self, documents: List, query: str, theme: str):
        """Process collected documents through analysis pipeline"""
        logger.info(f"Processing {len(documents)} documents for theme: {theme}")
        
        try:
            # Entity extraction and analysis
            for document in documents:
                try:
                    # Extract entities using NLP
                    entities = self.entity_parser.extract_entities(document)
                    document.metadata['entities'] = entities
                    
                    # Add theme information
                    document.metadata['research_theme'] = theme
                    document.metadata['search_query'] = query
                    
                except Exception as e:
                    logger.warning(f"Error processing document {document.document_id}: {e}")
            
            # Store in knowledge base
            if self.knowledge_base:
                self.knowledge_base.store_documents(documents, theme)
                logger.info(f"Stored {len(documents)} documents in knowledge base")
        
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
    
    def get_parser_status(self) -> Dict[str, Any]:
        """Get status of all parsers"""
        status = {}
        for name, parser in self.parsers.items():
            status[name] = parser.get_status()
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            'stats': self.stats,
            'is_running': self.is_running,
            'parsers': self.get_parser_status()
        }
    
    def _log_statistics(self):
        """Log current statistics"""
        logger.info("=== Collection Statistics ===")
        logger.info(f"Total documents collected: {self.stats['total_documents']}")
        logger.info(f"Successful parser runs: {self.stats['successful_parsings']}")
        logger.info(f"Failed parser runs: {self.stats['failed_parsings']}")
        if self.stats['last_update']:
            logger.info(f"Last update: {self.stats['last_update']}")
        logger.info("============================")
    
    def run_single_query(self, query: str, max_results: int = 20) -> List:
        """Run a single query across all parsers (for interactive use)"""
        logger.info(f"Running single query: '{query}'")
        
        all_documents = []
        
        for parser_name, parser in self.parsers.items():
            try:
                logger.info(f"Querying {parser_name}...")
                documents = parser.parse(query, max_results=max_results//len(self.parsers))
                
                if documents:
                    all_documents.extend(documents)
                    logger.info(f"{parser_name}: {len(documents)} documents")
                
            except Exception as e:
                logger.error(f"Error querying {parser_name}: {e}")
        
        # Process documents
        if all_documents:
            self._process_documents(all_documents, query, "interactive")
        
        logger.info(f"Single query completed: {len(all_documents)} total documents")
        return all_documents
