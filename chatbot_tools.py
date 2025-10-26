# chatbot_tools.py
import json
from datetime import datetime

class ChatbotTools:
    def __init__(self, rag_agent=None, memory_agent=None, vision_agent=None):
        self.rag_agent = rag_agent
        self.memory_agent = memory_agent
        self.vision_agent = vision_agent
        self.tool_descriptions = {
            "get_user_profile": "Get anonymized user profile and segment information",
            "find_similar_users": "Find users with similar health problems in anonymized segments",
            "analyze_ingredients": "Analyze product ingredients for health risks",
            "extract_ingredients_from_image": "Extract ingredients from product image using vision",
            "get_community_insights": "Get community feedback for similar health conditions",
            "calculate_nutrition_risk": "Calculate nutritional risks based on user profile",
            "get_age_specific_advice": "Get age-specific nutrition advice",
            "check_baby_safety": "Check product safety for babies/children"
        }
    
    def execute_tool(self, tool_name, **kwargs):
        tool_methods = {
            "get_user_profile": self.get_user_profile,
            "find_similar_users": self.find_similar_users,
            "analyze_ingredients": self.analyze_ingredients,
            "extract_ingredients_from_image": self.extract_ingredients_from_image,
            "get_community_insights": self.get_community_insights,
            "calculate_nutrition_risk": self.calculate_nutrition_risk,
            "get_age_specific_advice": self.get_age_specific_advice,
            "check_baby_safety": self.check_baby_safety
        }
        
        if tool_name in tool_methods:
            return tool_methods[tool_name](**kwargs)
        else:
            return f"Tool {tool_name} not found"
    
    def get_user_profile(self, user_id):
        if self.memory_agent:
            return self.memory_agent.get_or_create_user_profile(user_id)
        else:
            return {
                "segment": "general_health",
                "age_group": "adult",
                "medical_conditions": [],
                "allergies": [],
                "has_children": False
            }
    
    def find_similar_users(self, user_id, current_problem):
        if self.memory_agent:
            similar_users = self.memory_agent.get_similar_users(user_id, 3)
            return {
                "similar_users_count": len(similar_users),
                "message": f"Found {len(similar_users)} users with similar profiles"
            }
        else:
            return {
                "similar_users_count": 0,
                "message": "Memory agent not available"
            }
    
    def analyze_ingredients(self, ingredients, user_profile):
        if self.rag_agent and ingredients:
            user_preferences = user_profile.get('medical_conditions', []) + user_profile.get('allergies', [])
            if user_preferences:
                return self.rag_agent.analyze_ingredients(ingredients, user_preferences)
        
        return {"message": "No specific analysis available"}
    
    def extract_ingredients_from_image(self, image_path):
        return {
            "success": False,
            "message": "Image analysis requires full vision agent setup",
            "general_advice": "Please check the product label for ingredients"
        }
    
    def get_community_insights(self, product_type, user_segment):
        if self.memory_agent:
            return self.memory_agent.get_community_insights(user_segment, product_type)
        else:
            return "Community insights not available in current setup"
    
    def calculate_nutrition_risk(self, ingredients, user_profile):
        return self.analyze_ingredients(ingredients, user_profile)
    
    def get_age_specific_advice(self, age_group, product_type):
        age_advice = {
            "baby_0_6_months": "Only breast milk or formula recommended",
            "baby_6_8_months": "Pureed foods, no salt/sugar, avoid egg whites and honey",
            "baby_8_12_months": "Can introduce egg yolks, yogurt, soft fruits",
            "child_1_5_years": "Limit processed foods, watch for choking hazards",
            "50_plus": "Focus on heart-healthy, low-sodium, high-fiber options",
            "general": "Balanced diet with variety of fruits, vegetables, and whole grains"
        }
        
        return age_advice.get(age_group, age_advice["general"])
    
    def check_baby_safety(self, ingredients, baby_age_months):
        if self.rag_agent:
            return self.rag_agent.analyze_for_baby_age(ingredients, baby_age_months)
        else:
            return {
                "suitable": True,
                "risk_level": "UNKNOWN",
                "explanation": "Full baby safety analysis requires RAG agent",
                "hazardous_ingredients": []
            }