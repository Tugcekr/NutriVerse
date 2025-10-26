# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 04:08:56 2025

@author: Tugce
"""

# app.py
import streamlit as st
import tempfile
import os
from main_coordinator import ProductAnalysisCoordinator
import ollama
from datetime import datetime

st.set_page_config(page_title="NutriVerse", page_icon="🔍", layout="wide")

st.title("🔍 NutriVerse")
st.markdown("Upload product photo, choose preferences → Get risk analysis!")

class EnhancedChatbot:
    def __init__(self):
        self.model_name = "llama3.2:3b"
        self.user_profiles = {}
        self.conversation_histories = {}
        
    def get_user_profile(self, user_id):
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'age': None,
                'gender': None,
                'has_children': None,
                'children_ages': [],
                'medical_conditions': [],
                'allergies': [],
                'dietary_preferences': [],
                'known_info': set(),
                'conversation_count': 0
            }
        return self.user_profiles[user_id]
    
    def update_profile(self, user_id, updates):
        profile = self.get_user_profile(user_id)
        profile.update(updates)
        profile['conversation_count'] += 1
    
    def extract_profile_info(self, message, user_id):
        profile = self.get_user_profile(user_id)
        message_lower = message.lower()
        age_pattern = r'(\d+)\s*(years?|year|yaş|yaşındayım)'
        import re
        age_match = re.search(age_pattern, message_lower)
        if age_match and not profile['age']:
            profile['age'] = int(age_match.group(1))
        
        if any(word in message_lower for word in ['baby', 'bebek', 'child', 'çocuk', 'infant', '6-month', '6 month']):
            if '6-month' in message_lower or '6 month' in message_lower:
                profile['has_children'] = True
                if 6 not in profile['children_ages']:
                    profile['children_ages'].append(6)
        
        medical_keywords = {
            'diabetes': ['diabet', 'şeker'],
            'allergy': ['allerg', 'alerj'],
            'lactose': ['lactose', 'laktoz'],
            'gluten': ['gluten', 'çölyak'],
            'heart': ['heart', 'kalp']
        }
        
        for condition, keywords in medical_keywords.items():
            if any(keyword in message_lower for keyword in keywords) and condition not in profile['medical_conditions']:
                profile['medical_conditions'].append(condition)
    
    def get_missing_info(self, user_id):
        profile = self.get_user_profile(user_id)
        missing = []
        
        if profile['age'] is None:
            missing.append("age")
        if profile['has_children'] is None and profile['conversation_count'] > 1:
            missing.append("has_children")
        if not profile['children_ages'] and profile['has_children']:
            missing.append("children_ages")
        
        return missing
    
    def ask_clarifying_question(self, missing_info):
        questions = {
            "age": "To give you better advice, could you tell me your age?",
            "has_children": "Do you have children? This helps me provide age-appropriate advice.",
            "children_ages": "How old are your children? Please specify in months for babies or years for older children.",
            "medical_conditions": "Do you have any medical conditions or allergies I should know about?"
        }
        
        for info in missing_info:
            if info in questions:
                return questions[info]
        return None
    
    def generate_personalized_response(self, user_id, message):
        profile = self.get_user_profile(user_id)
        
        # Enhanced prompt with user context
        prompt = f"""
        You are a helpful health and nutrition assistant. Provide personalized advice based on the user's profile.
        
        USER PROFILE:
        - Age: {profile['age'] or 'Not specified'}
        - Has children: {profile['has_children'] or 'Not specified'}
        - Children ages: {profile['children_ages']}
        - Medical conditions: {profile['medical_conditions']}
        - Allergies: {profile['allergies']}
        
        USER QUESTION: {message}
        
        CONVERSATION HISTORY: {self.get_conversation_history(user_id)}
        
        Please provide:
        1. Direct answer to the question
        2. Personalized advice based on their profile
        3. Specific safety recommendations if applicable
        4. Ask one relevant follow-up question if needed
        
        Answer in English but be understanding if user speaks other languages.
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.3, 'num_predict': 500}
            )
            return response['message']['content'].strip()
        except Exception as e:
            return f"I apologize, but I'm having trouble responding right now. Please try again. Error: {str(e)}"
    
    def get_conversation_history(self, user_id, max_messages=5):
        if user_id not in self.conversation_histories:
            return "No previous conversation"
        history = self.conversation_histories[user_id][-max_messages:]
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    
    def add_to_history(self, user_id, role, content):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        self.conversation_histories[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def chat(self, user_id, message):
        # Extract profile information from message
        self.extract_profile_info(message, user_id)
        self.add_to_history(user_id, "user", message)
        missing_info = self.get_missing_info(user_id)
        if missing_info and len(self.conversation_histories.get(user_id, [])) < 10:
            clarifying_question = self.ask_clarifying_question(missing_info[:1])  # Ask one at a time
            if clarifying_question:
                self.add_to_history(user_id, "assistant", clarifying_question)
                return clarifying_question
        
        response = self.generate_personalized_response(user_id, message)
        self.add_to_history(user_id, "assistant", response)
        
        return response


@st.cache_resource
def initialize_agents():
    coordinator = ProductAnalysisCoordinator()
    chatbot = EnhancedChatbot()
    return coordinator, chatbot

coordinator, chatbot = initialize_agents()
tab1, tab2 = st.tabs(["📊 Product Analysis", "💬 Health Assistant"])

with tab1:
    st.header("Product Risk Analysis")
    st.sidebar.header("🎯 Diet and Allergen Preferences")
    
    user_preferences = st.sidebar.multiselect(
        "Allergen/Diet Preferences:",
        ['celiac', 'vegan', 'vegetarian', 'lactose', 'nut', 'soy', 'diabetes', 'heart_disease'],
        help="Select ingredients that are not suitable for you")
    uploaded_file = st.file_uploader("Upload product photo", type=['jpg', 'jpeg', 'png'])

    if uploaded_file and user_preferences:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            image_path = tmp_file.name
        
        try:
            if st.button("🔍 Analyze Product", type="primary"):
                with st.spinner("3-agent system analyzing..."):
                    result = coordinator.full_analysis(image_path, user_preferences)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.success("✅ Analysis completed!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(" Product Information")
                        st.write(f"**Brand:** {result['brand']}")
                        st.write(f"**Product Name:** {result['product_name']}")
                        st.write(f"**Ingredients:** {result['ingredients'][:300]}...")
                    
                    with col2:
                        st.subheader("Risk Analysis")
                        risk_score = result['risk_score']
                        st.metric("Safety Score", f"{risk_score:.1f}%")
                        st.write(f"**Overall Status:** {result['overall_safety']}")
                    
                    st.subheader(" Detailed Risk Analysis")
                    
                    for preference, analysis in result['risk_analysis'].items():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        
                        with col1:
                            if analysis['suitable']:
                                st.success("✅ SUITABLE")
                            else:
                                st.error("❌ RISKY")
                        
                        with col2:
                            description = analysis.get('explanation', 'No explanation available')
                            st.write(f"**{preference.upper()}** - {description}")
                            
                            if not analysis['suitable']:
                                hazardous_ingredients = analysis.get('hazardous_ingredients', [])
                                if hazardous_ingredients:
                                    st.write(f"Hazardous ingredients: {', '.join(hazardous_ingredients)}")
                        
                        with col3:
                            risk_level = analysis.get('risk_level', 'UNKNOWN')
                            st.write(f"Risk: {risk_level}")
                    
                    st.subheader(" Recommendations")
                    if risk_score > 80:
                        st.info("This product appears suitable for your preferences!")
                    elif risk_score > 50:
                        st.warning(" Consume this product carefully. There might be some risks.")
                    else:
                        st.error("This product is not suitable for your preferences!")
                        
        finally:
            os.unlink(image_path)

    elif uploaded_file and not user_preferences:
        st.warning("Please select allergen/diet preferences")

with tab2:
    st.header("💬 Interactive Health Assistant")
    st.markdown("Ask me anything about nutrition, baby care, or product safety!")
    if 'user_id' not in st.session_state:
        import random
        st.session_state.user_id = f"user_{random.randint(1000, 9999)}"
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        welcome_msg = "Hello! I'm your health and nutrition assistant. I can help you with:\n\n• Baby feeding and safety advice\n• Product ingredient analysis\n• Dietary recommendations\n• Allergy information\n\nTo give you the best advice, I might ask a few questions about your situation. How can I help you today?"
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})
    user_profile = chatbot.get_user_profile(st.session_state.user_id)
    with st.sidebar.expander("👤 Your Profile"):
        st.write(f"**Age:** {user_profile['age'] or 'Not specified'}")
        st.write(f"**Children:** {'Yes' if user_profile['has_children'] else 'No' if user_profile['has_children'] is False else 'Not specified'}")
        if user_profile['children_ages']:
            st.write(f"**Children Ages:** {user_profile['children_ages']}")
        if user_profile['medical_conditions']:
            st.write(f"**Conditions:** {', '.join(user_profile['medical_conditions'])}")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ask about health, nutrition, or baby care..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.chat(st.session_state.user_id, prompt)
            st.markdown(response)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 New Conversation"):
            st.session_state.chat_messages = []
            welcome_msg = "Hello! I'm your health and nutrition assistant. How can I help you today?"
            st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg})
            st.rerun()
    
    with col2:
        if st.button("📊 Show My Profile"):
            profile = chatbot.get_user_profile(st.session_state.user_id)
            profile_text = f"""
            **Your Current Profile:**
            - Age: {profile['age'] or 'Not specified'}
            - Has children: {profile['has_children'] or 'Not specified'}
            - Children ages: {profile['children_ages'] or 'Not specified'}
            - Medical conditions: {', '.join(profile['medical_conditions']) or 'None'}
            - Conversations: {profile['conversation_count']}
            """
            st.session_state.chat_messages.append({"role": "assistant", "content": profile_text})
            st.rerun()
    
    with col3:
        if st.button("❓ Example Questions"):
            examples = """
            **Try asking me:**
            • "Can I give egg to my 6-month-old baby?"
            • "What foods should I avoid during pregnancy?"
            • "Is this product safe for lactose intolerance?"
            • "How to introduce solid foods to my baby?"
            • "What are common food allergies in children?"
            """
            st.session_state.chat_messages.append({"role": "assistant", "content": examples})
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
**System Works with 3 Agents:**
1. 🔍 Vision - Brand recognition
2. 🌐 Search - Content finding  
3. 🧠 RAG - Risk analysis

**Enhanced Chatbot Features:**
- Personal profile building
- Context-aware conversations
- Baby and child safety advice
- Dietary recommendations
- Interactive Q&A
""")