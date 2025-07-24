#!/usr/bin/env python3
"""
Knowledge Synthesis database for ImmortyX system
Main knowledge base for storing and retrieving processed information
"""

import logging
import json
import os
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.text_processing import TextProcessor
from utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

class KnowledgeSynthesis:
    """Main knowledge base for the ImmortyX system"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "data/knowledge_base.db"
        self.text_processor = TextProcessor()
        self.llm_client = LLMClient()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Knowledge synthesis database initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize the SQLite database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT NOT NULL,
                        url TEXT,
                        authors TEXT,
                        publication_date TEXT,
                        document_type TEXT,
                        research_theme TEXT,
                        search_query TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        embedding_vector TEXT
                    )
                ''')
                
                # Entities table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id TEXT,
                        category TEXT,
                        entity TEXT,
                        confidence REAL,
                        context TEXT,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                ''')
                
                # Knowledge graph table (simplified)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_graph (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT,
                        predicate TEXT,
                        object TEXT,
                        confidence REAL,
                        source_documents TEXT,
                        created_at TEXT
                    )
                ''')
                
                # User queries and responses
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_profile TEXT,
                        query TEXT,
                        response TEXT,
                        relevant_documents TEXT,
                        created_at TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Database schema initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def store_documents(self, documents: List, theme: str = None):
        """Store documents in the knowledge base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for doc in documents:
                    # Prepare document data
                    doc_data = (
                        doc.document_id,
                        doc.title,
                        doc.content,
                        doc.source,
                        doc.url,
                        json.dumps(doc.authors),
                        doc.publication_date.isoformat() if doc.publication_date else None,
                        doc.document_type,
                        theme or doc.metadata.get('research_theme'),
                        doc.metadata.get('search_query'),
                        json.dumps(doc.metadata),
                        datetime.now().isoformat(),
                        None  # embedding_vector - to be implemented
                    )
                    
                    # Insert or update document
                    cursor.execute('''
                        INSERT OR REPLACE INTO documents 
                        (id, title, content, source, url, authors, publication_date, 
                         document_type, research_theme, search_query, metadata, created_at, embedding_vector)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', doc_data)
                    
                    # Store entities if available
                    entities = doc.metadata.get('entities', {})
                    if entities:
                        self._store_entities(cursor, doc.document_id, entities)
                
                conn.commit()
                logger.info(f"Stored {len(documents)} documents in knowledge base")
        
        except Exception as e:
            logger.error(f"Error storing documents: {e}")
    
    def _store_entities(self, cursor, document_id: str, entities: Dict[str, List[str]]):
        """Store extracted entities"""
        try:
            # Clear existing entities for this document
            cursor.execute('DELETE FROM entities WHERE document_id = ?', (document_id,))
            
            # Insert new entities
            for category, entity_list in entities.items():
                for entity in entity_list:
                    cursor.execute('''
                        INSERT INTO entities (document_id, category, entity, confidence, context)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (document_id, category, entity, 0.8, None))  # Default confidence
        
        except Exception as e:
            logger.warning(f"Error storing entities for document {document_id}: {e}")
    
    def search(self, query: str, user_profile: str = None, limit: int = 10) -> str:
        """Search the knowledge base and return relevant information"""
        try:
            # Find relevant documents
            documents = self._search_documents(query, limit * 2)
            
            if not documents:
                return "I couldn't find any relevant information about that topic in the knowledge base."
            
            # Generate summary based on user profile
            summary = self._generate_user_specific_summary(documents, query, user_profile)
            
            # Store interaction
            self._store_interaction(user_profile, query, summary, [doc['id'] for doc in documents])
            
            return summary
        
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"I encountered an error while searching: {str(e)}"
    
    def _search_documents(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for relevant documents using keyword matching"""
        try:
            query_words = self.text_processor.clean_text(query).lower().split()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Simple keyword search (can be enhanced with full-text search)
                placeholders = ' OR '.join(['LOWER(title) LIKE ? OR LOWER(content) LIKE ?' for _ in query_words])
                search_terms = []
                for word in query_words:
                    search_terms.extend([f'%{word}%', f'%{word}%'])
                
                cursor.execute(f'''
                    SELECT id, title, content, source, url, authors, publication_date, 
                           document_type, research_theme, metadata
                    FROM documents 
                    WHERE {placeholders}
                    ORDER BY publication_date DESC
                    LIMIT ?
                ''', search_terms + [limit])
                
                columns = [description[0] for description in cursor.description]
                documents = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return documents
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _generate_user_specific_summary(self, documents: List[Dict], query: str, user_profile: str) -> str:
        """Generate a summary tailored to the user's profile"""
        if not self.llm_client.is_available():
            return self._generate_simple_summary(documents)
        
        try:
            # Prepare document context
            doc_summaries = []
            for doc in documents[:5]:  # Limit to top 5 documents
                summary = f"Title: {doc['title']}\nSource: {doc['source']}\nSummary: {doc['content'][:300]}..."
                doc_summaries.append(summary)
            
            context = "\n\n".join(doc_summaries)
            
            # Profile-specific instructions
            profile_instructions = {
                'researcher': "Focus on methodologies, statistical significance, and implications for further research.",
                'student': "Explain key concepts clearly and highlight important learning points.",
                'journalist': "Emphasize newsworthy aspects, potential impact, and expert opinions.",
                'investor': "Highlight commercial potential, market opportunities, and financial implications.",
                'entrepreneur': "Focus on business opportunities, implementation challenges, and market potential.",
                'policy_maker': "Emphasize societal impact, policy implications, and economic considerations.",
                'philosopher': "Explore ethical implications, existential questions, and philosophical perspectives.",
                'writer': "Highlight creative potential, narrative possibilities, and interesting story angles."
            }
            
            instruction = profile_instructions.get(user_profile, "Provide a comprehensive overview.")
            
            messages = [
                {
                    "role": "system",
                    "content": f"You are an AI assistant specializing in longevity research. Based on the following research documents, provide a comprehensive answer to the user's question. {instruction}"
                },
                {
                    "role": "user",
                    "content": f"Question: {query}\n\nRelevant Research:\n{context}"
                }
            ]
            
            return self.llm_client.chat_completion(messages, max_tokens=500)
        
        except Exception as e:
            logger.error(f"Error generating LLM summary: {e}")
            return self._generate_simple_summary(documents)
    
    def _generate_simple_summary(self, documents: List[Dict]) -> str:
        """Generate a simple summary without LLM"""
        if not documents:
            return "No relevant documents found."
        
        summary_parts = [f"Found {len(documents)} relevant documents:"]
        
        for i, doc in enumerate(documents[:3], 1):  # Top 3 documents
            authors = json.loads(doc.get('authors', '[]'))
            author_str = ", ".join(authors[:2]) if authors else "Unknown authors"
            
            summary_parts.append(
                f"{i}. {doc['title']} ({doc['source']}) - {author_str}\n"
                f"   {doc['content'][:200]}..."
            )
        
        return "\n\n".join(summary_parts)
    
    def _store_interaction(self, user_profile: str, query: str, response: str, document_ids: List[str]):
        """Store user interaction for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions 
                    (user_profile, query, response, relevant_documents, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_profile, query, response, json.dumps(document_ids), datetime.now().isoformat()))
                conn.commit()
        
        except Exception as e:
            logger.warning(f"Error storing interaction: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Document counts
                cursor.execute('SELECT COUNT(*) FROM documents')
                total_docs = cursor.fetchone()[0]
                
                cursor.execute('SELECT source, COUNT(*) FROM documents GROUP BY source')
                source_counts = dict(cursor.fetchall())
                
                cursor.execute('SELECT research_theme, COUNT(*) FROM documents WHERE research_theme IS NOT NULL GROUP BY research_theme')
                theme_counts = dict(cursor.fetchall())
                
                # Entity counts
                cursor.execute('SELECT category, COUNT(*) FROM entities GROUP BY category')
                entity_counts = dict(cursor.fetchall())
                
                return {
                    'total_documents': total_docs,
                    'documents_by_source': source_counts,
                    'documents_by_theme': theme_counts,
                    'entities_by_category': entity_counts
                }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
