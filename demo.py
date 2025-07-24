#!/usr/bin/env python3
"""
ImmortyX System Demo
Demonstrates the multi-agent longevity research system
"""

import logging
from utils.config_loader import ConfigLoader
from parsers.nature_parser import NatureParser
from parsers.biorxiv_parser import BioRxivParser
from parsers.cochrane_parser import CochraneParser
from agents.entity_parser import EntityParser
from agents.randy_collector import RandyCollector
from databases.knowledge_synthesis import KnowledgeSynthesis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def demo_parsers():
    """Demonstrate parser functionality"""
    print("=" * 60)
    print("ImmortyX PARSER DEMONSTRATION")
    print("=" * 60)
    
    # Initialize parsers
    parsers = {
        'Nature Aging (Stub)': NatureParser(),
        'Cochrane Library (Stub)': CochraneParser(),
        # 'bioRxiv': BioRxivParser(),  # Commented out for demo to avoid API calls
    }
    
    query = "cellular senescence"
    print(f"\nSearching for: '{query}'")
    print("-" * 40)
    
    all_documents = []
    
    for parser_name, parser in parsers.items():
        try:
            print(f"\n🔍 Testing {parser_name}...")
            documents = parser.parse(query, max_results=3)
            
            print(f"   ✅ Found {len(documents)} documents")
            
            for i, doc in enumerate(documents, 1):
                print(f"   {i}. {doc.title[:60]}...")
                print(f"      Source: {doc.source} | Authors: {len(doc.authors)} | Type: {doc.document_type}")
            
            all_documents.extend(documents)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return all_documents

def demo_agents(documents):
    """Demonstrate agent functionality"""
    print("\n" + "=" * 60)
    print("ImmortyX AGENT DEMONSTRATION")
    print("=" * 60)
    
    if not documents:
        print("No documents to process with agents.")
        return
    
    # Entity Parser
    print("\n🧠 Entity Parser Agent")
    print("-" * 30)
    entity_parser = EntityParser()
    
    for i, doc in enumerate(documents[:2], 1):  # Process first 2 documents
        print(f"\nProcessing document {i}: {doc.title[:50]}...")
        entities = entity_parser.extract_entities(doc)
        
        for category, entity_list in entities.items():
            if entity_list:
                print(f"   {category.capitalize()}: {len(entity_list)} entities")
                if len(entity_list) <= 3:
                    print(f"      {', '.join(entity_list)}")
                else:
                    print(f"      {', '.join(entity_list[:3])}... (+{len(entity_list)-3} more)")
    
    # Randy Collector (Pseudoscience Detection)
    print("\n🔬 Randy Collector Agent (Pseudoscience Detection)")
    print("-" * 50)
    randy = RandyCollector()
    
    for i, doc in enumerate(documents[:2], 1):
        print(f"\nAssessing document {i}: {doc.title[:50]}...")
        assessment = randy.assess_document(doc)
        
        risk_level = assessment.get('risk_level', 'unknown')
        warning_count = assessment.get('total_warnings', 0)
        
        risk_emoji = {'very_low': '✅', 'low': '🟢', 'medium': '🟡', 'high': '🔴', 'unknown': '❓'}
        
        print(f"   Risk Level: {risk_emoji.get(risk_level, '❓')} {risk_level.upper()}")
        print(f"   Warnings: {warning_count}")
        
        if assessment.get('risk_factors'):
            print(f"   Risk Factors: {assessment['risk_factors'][:2]}")

def demo_knowledge_base(documents):
    """Demonstrate knowledge base functionality"""
    print("\n" + "=" * 60)
    print("ImmortyX KNOWLEDGE BASE DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Initialize knowledge base
        kb = KnowledgeSynthesis()
        
        # Store documents
        print(f"\n📚 Storing {len(documents)} documents in knowledge base...")
        kb.store_documents(documents, theme="demo_theme")
        
        # Get statistics
        stats = kb.get_statistics()
        print(f"   Total documents in KB: {stats.get('total_documents', 0)}")
        print(f"   Documents by source: {stats.get('documents_by_source', {})}")
        
        # Test search
        print("\n🔍 Testing knowledge base search...")
        test_queries = [
            "What is cellular senescence?",
            "How does aging affect cells?",
            "Tell me about longevity research"
        ]
        
        for query in test_queries[:1]:  # Test only first query for demo
            print(f"\nQuery: '{query}'")
            result = kb.search(query, user_profile="researcher", limit=3)
            print(f"Response: {result[:200]}...")
    
    except Exception as e:
        print(f"❌ Knowledge base demo error: {e}")

def main():
    """Run the complete demo"""
    print("🧬 Welcome to ImmortyX - Multi-Agent Longevity Research System")
    print("This demo showcases the core functionality of the system.")
    
    try:
        # Load configuration
        config = ConfigLoader.load_config()
        print(f"\n✅ Configuration loaded: {len(config.get('research_themes', []))} research themes")
        
        # Demo parsers
        documents = demo_parsers()
        
        if documents:
            # Demo agents
            demo_agents(documents)
            
            # Demo knowledge base
            demo_knowledge_base(documents)
        
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTo start the Flask chatbot interface, run:")
        print("   python app.py")
        print("\nThen open your browser to: http://localhost:5000")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()
