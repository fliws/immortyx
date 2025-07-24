#!/usr/bin/env python3
"""
ImmortyX Flask Chatbot Interface
Web-based chat interface for interacting with the longevity research system
"""

from flask import Flask, render_template, request, jsonify, session
import uuid
from datetime import datetime
import logging
from utils.llm_client import LLMClient
from utils.config_loader import ConfigLoader
from databases.knowledge_synthesis import KnowledgeSynthesis

app = Flask(__name__)
app.secret_key = 'immortyx-secret-key-change-in-production'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
try:
    config = ConfigLoader.load_config()
    llm_client = LLMClient()
    knowledge_base = KnowledgeSynthesis()
    logger.info("ImmortyX chatbot components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    config = {}
    llm_client = None
    knowledge_base = None

@app.route('/')
def index():
    """Main chat interface"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['conversation_history'] = []
    
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        user_message = request.json.get('message', '').strip()
        user_profile = request.json.get('profile', 'researcher')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get session info
        session_id = session.get('session_id')
        conversation_history = session.get('conversation_history', [])
        
        # Add user message to history
        conversation_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat(),
            'profile': user_profile
        })
        
        # Generate response using LLM
        if llm_client:
            response_content = generate_response(user_message, user_profile, conversation_history)
        else:
            response_content = "System is initializing. Please try again later."
        
        # Add assistant response to history
        conversation_history.append({
            'role': 'assistant',
            'content': response_content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update session
        session['conversation_history'] = conversation_history[-20:]  # Keep last 20 messages
        
        return jsonify({
            'response': response_content,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def generate_response(user_message, user_profile, conversation_history):
    """Generate response using LLM and knowledge base"""
    try:
        # Create context based on user profile
        profile_context = get_profile_context(user_profile)
        
        # Search knowledge base for relevant information
        relevant_info = ""
        if knowledge_base:
            relevant_info = knowledge_base.search(user_message, user_profile)
        
        # Prepare conversation context
        recent_context = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            recent_context.append({"role": msg['role'], "content": msg['content']})
        
        # Create system prompt
        system_prompt = f"""You are ImmortyX, an AI assistant specialized in longevity and life extension research.

User Profile: {user_profile}
Profile Context: {profile_context}

Relevant Knowledge: {relevant_info}

Provide accurate, helpful responses based on scientific evidence. Adapt your response style to the user's profile."""

        # Generate response
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_context)
        messages.append({"role": "user", "content": user_message})
        
        response = llm_client.chat_completion(messages)
        return response
        
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return f"I apologize, but I encountered an error processing your request. Error: {str(e)}"

def get_profile_context(user_profile):
    """Get context information for different user profiles"""
    profiles = {
        'researcher': "Focus on cutting-edge research, methodologies, datasets, and scientific breakthroughs.",
        'student': "Provide educational content, key papers, fundamental concepts, and career guidance.",
        'journalist': "Emphasize newsworthy developments, expert opinions, and human interest stories.",
        'investor': "Highlight commercial opportunities, company pipelines, market analysis, and investment risks.",
        'entrepreneur': "Focus on commercialization potential, business models, and market opportunities.",
        'policy_maker': "Emphasize societal impact, economic implications, and policy considerations.",
        'philosopher': "Explore ethical implications, existential questions, and philosophical perspectives.",
        'writer': "Provide creative inspiration, scientific accuracy checks, and narrative possibilities."
    }
    return profiles.get(user_profile, "General longevity and life extension information.")

@app.route('/api/profiles')
def get_profiles():
    """Get available user profiles"""
    profiles = [
        {'id': 'researcher', 'name': 'Researcher', 'description': 'Scientific researcher in longevity field'},
        {'id': 'student', 'name': 'Student/Graduate', 'description': 'Academic student or graduate student'},
        {'id': 'journalist', 'name': 'Journalist', 'description': 'Science journalist or writer'},
        {'id': 'investor', 'name': 'Investor', 'description': 'Investment professional or analyst'},
        {'id': 'entrepreneur', 'name': 'Entrepreneur', 'description': 'Business entrepreneur or startup founder'},
        {'id': 'policy_maker', 'name': 'Policy Maker', 'description': 'Government official or policy analyst'},
        {'id': 'philosopher', 'name': 'Philosopher/Ethicist', 'description': 'Philosopher or ethics researcher'},
        {'id': 'writer', 'name': 'Writer/Screenwriter', 'description': 'Creative writer or screenwriter'}
    ]
    return jsonify(profiles)

@app.route('/api/status')
def system_status():
    """Get system status"""
    status = {
        'llm_client': llm_client is not None,
        'knowledge_base': knowledge_base is not None,
        'config_loaded': bool(config),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
