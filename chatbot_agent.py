# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 17:19:59 2025

@author: Tugce
"""

# chatbot_agent.py (English version - UPDATED)
import ollama
import re
from datetime import datetime

class ChatbotAgent:
    def __init__(self, rag_agent, memory_agent, vision_agent):
        self.rag_agent = rag_agent
        self.memory_agent = memory_agent
        self.vision_agent = vision_agent
        self.tools = ChatbotTools(rag_agent, memory_agent, vision_agent)
        self.model_name = "llama3.2:3b"
        self.conversation_histories = {}
        self.cot_prompts = {
            "health_advice_with_tools": """
            You are a health and nutrition expert. Analyze the user's question and use available tools to provide personalized advice.

            USER QUESTION: {question}
            USER PROFILE: {profile}
            USER SEGMENT: {segment}
            CONVERSATION HISTORY: {history}
            AVAILABLE TOOLS: {tools}
            RAG KNOWLEDGE: {rag_context}
            COMMUNITY INSIGHTS: {community_insights}

            Thinking process:
            1. First, understand the user's specific health context and profile
            2. Note their user segment: {segment}
            3. Use community insights to understand common problems in their segment
            4. If they mention a common problem, use find_similar_users tool to see how others solved it
            5. If they provide product ingredients, use analyze_ingredients tool
            6. If they mention a product image, use extract_ingredients_from_image tool
            7. Use RAG knowledge for hazard information and scientific data
            8. Reference similar users' experiences when relevant
            9. Provide final personalized recommendation in English

            Always mention in your response:
            - Their user segment and what it means
            - If you found similar users with same problem and what worked for them
            - Reference community insights when available
            - Provide clear, actionable safety recommendations

            Final answer in ENGLISH:
            """,
            
            "product_analysis_with_tools": """
            Analyze product safety using available tools and community knowledge:

            PRODUCT INFO: {product_info}
            USER QUESTION: {question}
            USER SEGMENT: {segment}
            TOOLS AVAILABLE: {tools}
            RAG CONTEXT: {rag_context}
            COMMUNITY DATA: {community_insights}

            Step-by-step reasoning:
            1. Extract product type and ingredients if available
            2. Check user segment to understand their specific needs
            3. Use RAG knowledge to check for known hazards
            4. Use community insights to understand common concerns in their segment
            5. Use analyze_ingredients tool for health risk assessment
            6. Check calculate_nutrition_risk for specific conditions
            7. Reference community data about what worked for similar users
            8. Provide clear safety recommendation in English
            9. Mention if similar users in their segment had issues with similar products

            RESPONSE in ENGLISH:
            """,
            
            "symptom_analysis_with_tools": """
            Analyze user symptoms using segmentation and community knowledge:

            SYMPTOMS: {question}
            USER PROFILE: {profile}
            USER SEGMENT: {segment}
            SIMILAR USERS: {similar_users}
            COMMUNITY INSIGHTS: {community_insights}

            Steps:
            1. Analyze the described symptoms
            2. Check user segment for common related issues
            3. Use similar users data to see how others managed similar symptoms
            4. Use community insights for segment-specific advice
            5. Ask clarifying questions if needed (age, duration, other symptoms)
            6. Provide evidence-based suggestions
            7. Always recommend consulting healthcare professional for medical issues

            Focus on:
            - Relating symptoms to user segment characteristics
            - Sharing what worked for similar users (anonymized)
            - Practical, actionable advice

            ANSWER in ENGLISH:
            """
        }
    
    def get_enhanced_context(self, user_id, question):
        user_profile = self.tools.get_user_profile(user_id)
        segment = user_profile.get('segment', 'general_health')
        rag_context = self.get_rag_context(question, user_profile)
        community_insights = self.memory_agent.get_community_insights(segment, self.extract_problem_type(question))
        similar_users = self.memory_agent.get_similar_users(user_id, 3)
        
        return {
            'rag_context': rag_context,
            'community_insights': community_insights,
            'similar_users': similar_users,
            'segment': segment,
            'user_profile': user_profile
        }
    
    def get_rag_context(self, question, user_profile):
        """Enhanced RAG context retrieval"""
        try:
            keywords = self.extract_keywords(question)
            if user_profile:
                keywords.extend(user_profile.get('medical_conditions', []))
                keywords.extend(user_profile.get('allergies', []))
            
            context = ""
            for keyword in set(keywords[:4]):
                try:
                    docs=self.rag_agent.vector_store.similarity_search(keyword, k=2)
                    for doc in docs:
                        context+= f"\n{keyword.upper()} KNOWLEDGE: {doc.page_content}\n"
                except:
                    continue
            
            return context[:1200]
        except Exception as e:
            return f"RAG context error: {str(e)}"
    
    def detect_tool_requirements(self, message, user_profile):
        """Detect which tools are needed based on message content"""
        required_tools =[]
        message_lower = message.lower()
        
        # Enhanced tool detection with segmentation
        if any(word in message_lower for word in ['similar','other', 'another', 'same', 'else']):
            required_tools.append("find_similar_users")
        
        if any(word in message_lower for word in ['ingredient', 'content', 'material', 'contains']):
            required_tools.append("analyze_ingredients")
        
        if any(word in message_lower for word in ['photo', 'image', 'picture']):
            required_tools.append("extract_ingredients_from_image")
        
        if any(word in message_lower for word in ['baby', 'child', 'infant', 'toddler']):
            required_tools.append("check_baby_safety")
            required_tools.append("get_age_specific_advice")
        
        if any(word in message_lower for word in ['risk', 'safe', 'dangerous', 'healthy']):
            required_tools.append("calculate_nutrition_risk")
        
        # Symptom detection
        if any(word in message_lower for word in ['bloating', 'pain', 'hurt', 'symptom', 'feel bad']):
            required_tools.append("find_similar_users")
            # Update user profile with reported symptom
            self.memory_agent.update_from_chat_interaction(
                user_profile.get('user_id', 'unknown'), 
                "symptom_report", 
                "neutral"
            )
        
        # Always include user profile for personalization
        required_tools.append("get_user_profile")
        
        return list(set(required_tools))
    
    def execute_tools(self, user_id, required_tools, message):
        """Execute required tools and collect results"""
        tool_results = {}
        user_profile = self.tools.get_user_profile(user_id)
        
        for tool in required_tools:
            try:
                if tool == "get_user_profile":
                    tool_results[tool] = user_profile
                
                elif tool == "find_similar_users":
                    similar_users = self.memory_agent.get_similar_users(user_id, 5)
                    tool_results[tool] = {
                        "similar_users_count": len(similar_users),
                        "users": similar_users[:3],  # Top 3 most similar
                        "common_solutions": self.extract_common_solutions(similar_users)
                    }
                
                elif tool == "analyze_ingredients":
                    ingredients = self.extract_ingredients_from_text(message)
                    if ingredients:
                        tool_results[tool] = self.tools.analyze_ingredients(ingredients, user_profile)
                
                elif tool == "extract_ingredients_from_image":
                    tool_results[tool] = {"message": "Image analysis requires uploaded image"}
                
                elif tool == "calculate_nutrition_risk":
                    ingredients = self.extract_ingredients_from_text(message)
                    if ingredients:
                        tool_results[tool] = self.tools.calculate_nutrition_risk(ingredients, user_profile)
                
                elif tool == "get_age_specific_advice":
                    tool_results[tool] = self.tools.get_age_specific_advice(
                        user_profile.get('age_group', 'general'), 
                        self.extract_product_type(message)
                    )
                
                elif tool == "check_baby_safety":
                    if user_profile.get('has_children'):
                        ingredients = self.extract_ingredients_from_text(message)
                        baby_age = self.extract_baby_age(message)
                        if ingredients and baby_age:
                            tool_results[tool] = self.tools.check_baby_safety(ingredients, baby_age)
                
            except Exception as e:
                tool_results[tool] = f"Tool error: {str(e)}"
        
        return tool_results
    
    def extract_ingredients_from_text(self, text):
        ingredient_keywords = ['ingredients', 'contains', 'made with', 'composition', 'made from']
        for keyword in ingredient_keywords:
            if keyword in text.lower():
                start_idx = text.lower().find(keyword) + len(keyword)
                return text[start_idx:start_idx+200]
        return None
    
    def extract_keywords(self, text):
        health_keywords = [
            'diabetes', 'sugar', 'heart', 'blood pressure', 'allergy', 'diet', 
            'nutrition', 'vitamin', 'mineral', 'protein', 'fat', 'carbohydrate',
            'baby', 'child', 'pregnant', 'elderly', 'sport', 'exercise',
            'medicine', 'treatment', 'symptom', 'diagnosis', 'cholesterol', 'obesity',
            'celiac', 'gluten', 'lactose', 'vegan', 'vegetarian', 'bloating', 'pain'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in health_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords if found_keywords else ['general health']
    
    def extract_problem_type(self, text):
        text_lower = text.lower()
        if any(word in text_lower for word in ['baby', 'infant', 'child']):
            return "child_health"
        elif any(word in text_lower for word in ['bloating', 'stomach', 'digest']):
            return "digestive_issues"
        elif any(word in text_lower for word in ['sugar', 'diabet']):
            return "diabetes"
        elif any(word in text_lower for word in ['heart', 'blood pressure']):
            return "heart_health"
        else:
            return "general_health"
    
    def extract_product_type(self, text):
        product_types = ['formula', 'cereal', 'yogurt', 'milk', 'cheese', 'bread', 'drink', 'snack', 'baby food']
        for p_type in product_types:
            if p_type in text.lower():
                return p_type
        return "general"
    
    def extract_baby_age(self, text):
        age_pattern = r'(\d+)\s*(month|months|monthly|mo)'
        match = re.search(age_pattern, text)
        if match:
            return int(match.group(1))
        return 6  # Default age
    
    def extract_common_solutions(self, similar_users):
        all_solutions = []
        for user in similar_users:
            for rec in user.get('successful_recommendations', []):
                if isinstance(rec, dict):
                    all_solutions.append(rec.get('recommendation', ''))
                else:
                    all_solutions.append(rec)
        
        from collections import Counter
        common = Counter([s for s in all_solutions if s]).most_common(3)
        return [solution for solution, count in common]
    
    def generate_enhanced_prompt(self, user_id, question, tool_results):
        history = self.get_conversation_history(user_id)
        history_text = "\n".join([f"{msg['role']}: {msg['message']}" for msg in history])
        context = self.get_enhanced_context(user_id, question)
        prompt_type = self.determine_prompt_type(question)
        base_prompt = self.cot_prompts.get(prompt_type + "_with_tools", self.cot_prompts["health_advice_with_tools"])
        tools_text = "\n".join([f"{tool}: {result}" for tool, result in tool_results.items()])
        
        if prompt_type == "health_advice":
            return base_prompt.format(
                question=question,
                profile=context['user_profile'],
                segment=context['segment'],
                history=history_text,
                tools=tools_text,
                rag_context=context['rag_context'],
                community_insights=context['community_insights']
            )
        elif prompt_type == "symptom_analysis":
            return base_prompt.format(
                question=question,
                profile=context['user_profile'],
                segment=context['segment'],
                similar_users=context['similar_users'],
                community_insights=context['community_insights']
            )
        else:
            return base_prompt.format(
                question=question,
                product_info=question,
                segment=context['segment'],
                tools=tools_text,
                rag_context=context['rag_context'],
                community_insights=context['community_insights']
            )
    
    def chat(self, user_id, message, image_path=None):
        self.add_to_history(user_id, "user", message)
        self.memory_agent.get_or_create_user_profile(user_id)

        user_profile = self.tools.get_user_profile(user_id)
        required_tools = self.detect_tool_requirements(message, user_profile)
        if image_path:
            required_tools.append("extract_ingredients_from_image")
            image_result = self.tools.extract_ingredients_from_image(image_path)
            tool_results = {"extract_ingredients_from_image": image_result}
            if not image_result.get('success', False):
                community_advice = self.memory_agent.get_community_insights(
                    user_profile.get('segment', 'general_health'),
                    self.extract_problem_type(message)
                )
                tool_results["community_advice"] = community_advice
        else:
            tool_results = self.execute_tools(user_id, required_tools, message)
        enhanced_prompt = self.generate_enhanced_prompt(user_id, message, tool_results)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': enhanced_prompt
                }],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'num_predict': 600
                }
            )
            
            answer = response['message']['content'].strip()
            self.add_to_history(user_id, "assistant", answer)
            if "similar users" in str(tool_results):
                self.memory_agent.add_successful_recommendation(user_id, "consulted_similar_users")
            return answer
            
        except Exception as e:
            error_msg = f"Sorry, I encountered a technical issue. Please try again later. Error: {str(e)}"
            self.add_to_history(user_id, "assistant", error_msg)
            return error_msg
    
    def get_conversation_history(self, user_id, max_messages=10):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        return self.conversation_histories[user_id][-max_messages:]
    
    def add_to_history(self, user_id, role, message):
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = []
        
        self.conversation_histories[user_id].append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.conversation_histories[user_id]) > 20:
            self.conversation_histories[user_id] = self.conversation_histories[user_id][-20:]
    
    def determine_prompt_type(self, message):
        message_lower = message.lower()
        if any(word in message_lower for word in ['product', 'brand', 'ingredient', 'material']):
            return "product_analysis"
        elif any(word in message_lower for word in ['sick', 'disease', 'treatment', 'medicine', 'symptom', 'pain', 'hurt', 'feel']):
            return "symptom_analysis"
        else:
            return "health_advice"
    
    def get_chat_summary(self, user_id):
        history = self.get_conversation_history(user_id, max_messages=50)
        if not history:
            return "No conversation history yet."
        
        user_profile = self.memory_agent.get_or_create_user_profile(user_id)
        
        summary_prompt = f"""
        Summarize this health conversation in English:
        
        User Segment: {user_profile.get('segment', 'Unknown')}
        User Conditions: {', '.join(user_profile.get('medical_conditions', []))}
        
        Conversation:
        {''.join([f"{msg['role']}: {msg['message']}\n" for msg in history])}
        
        Provide a concise summary focusing on:
        - Main health concerns discussed
        - Products or ingredients analyzed
        - Recommendations provided
        - User segment insights
        - Any tools or community insights used
        
        SUMMARY:
        """
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': summary_prompt}]
            )
            return response['message']['content'].strip()
        except:
            return "Summary could not be generated."