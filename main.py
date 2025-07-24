#!/usr/bin/env python3
"""
ImmortyX - Multi-Agent Longevity Research System
Main application entry point
"""

import logging
from agents.spider_orchestrator import SpiderOrchestrator
from databases.knowledge_synthesis import KnowledgeSynthesis
from utils.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Initialize and start the ImmortyX system"""
    logger.info("Starting ImmortyX Multi-Agent System")
    
    try:
        # Load configuration
        config = ConfigLoader.load_config()
        logger.info(f"Loaded configuration for {len(config['research_themes'])} research themes")
        
        # Initialize knowledge base
        knowledge_base = KnowledgeSynthesis()
        logger.info("Knowledge synthesis system initialized")
        
        # Initialize and start spider orchestrator
        orchestrator = SpiderOrchestrator(config, knowledge_base)
        logger.info("Spider orchestrator initialized")
        
        # Start the orchestration process
        orchestrator.start()
        
    except Exception as e:
        logger.error(f"Failed to start ImmortyX system: {e}")
        raise

if __name__ == "__main__":
    main()
