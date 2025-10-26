# memory_agent.py
import json
from datetime import datetime, timedelta
import hashlib

class MemoryAgent:
    def __init__(self):
        self.user_profiles = {}
        self.user_segments = {}
        self.anonymized_data = {}
        self.initialize_default_segments()
    
    def initialize_default_segments(self):
        self.segment_definitions = {
            "baby_parents_0_6": {
                "conditions": ["has_baby_0_6"],
                "description": "Parents with babies 0-6 months"
            },
            "baby_parents_6_12": {
                "conditions": ["has_baby_6_12"], 
                "description": "Parents with babies 6-12 months"
            },
            "diabetes_management": {
                "conditions": ["diabetes"],
                "description": "Users managing diabetes"
            },
            "heart_health": {
                "conditions": ["heart_disease", "hypertension"],
                "description": "Users with heart conditions"
            },
            "digestive_issues": {
                "conditions": ["bloating", "ibs", "lactose_intolerant"],
                "description": "Users with digestive problems"
            },
            "allergy_management": {
                "conditions": ["nut_allergy", "soy_allergy", "gluten_sensitivity"],
                "description": "Users managing food allergies"
            },
            "general_health": {
                "conditions": [],
                "description": "General health conscious users"
            }
        }
    
    def get_or_create_user_profile(self, user_id):
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'segment': 'general_health',
                'age_group': 'adult',
                'medical_conditions': [],
                'allergies': [],
                'diet_preferences': [],
                'has_children': False,
                'baby_age_months': None,
                'previous_analyses': [],
                'chat_interactions': 0,
                'common_complaints': [],
                'successful_recommendations': [],
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            self.assign_user_segment(user_id)
        
        self.user_profiles[user_id]['last_active'] = datetime.now().isoformat()
        self.user_profiles[user_id]['chat_interactions'] += 1
        
        return self.user_profiles[user_id]
    
    def assign_user_segment(self, user_id):
        profile = self.user_profiles[user_id]
        best_segment = 'general_health'
        max_matches = 0
        
        for segment_name, segment_def in self.segment_definitions.items():
            condition_matches = 0
            for condition in segment_def['conditions']:
                if condition in profile['medical_conditions'] or condition in profile['allergies']:
                    condition_matches += 1
                elif condition == 'has_baby_0_6' and profile.get('baby_age_months') and profile['baby_age_months'] <= 6:
                    condition_matches += 1
                elif condition == 'has_baby_6_12' and profile.get('baby_age_months') and 6 < profile['baby_age_months'] <= 12:
                    condition_matches += 1
            
            if condition_matches > max_matches:
                max_matches = condition_matches
                best_segment = segment_name
        
        profile['segment'] = best_segment
        self.user_segments[user_id] = best_segment
    
    def update_from_chat_interaction(self, user_id, interaction_type, sentiment):
        profile = self.get_or_create_user_profile(user_id)
        
        # Extract potential medical conditions from chat
        if interaction_type == "symptom_report":
            if "bloating" in interaction_type.lower() and "bloating" not in profile['common_complaints']:
                profile['common_complaints'].append("bloating")
                profile['medical_conditions'].append("digestive_issues")
            
            if "baby" in interaction_type.lower() and not profile['has_children']:
                profile['has_children'] = True
        
        self.assign_user_segment(user_id)
    
    def update_user_profile(self, user_id, updates):
        profile = self.get_or_create_user_profile(user_id)
        profile.update(updates)
        self.assign_user_segment(user_id)
    
    def add_product_analysis(self, user_id, product_analysis):
        profile = self.get_or_create_user_profile(user_id)
        profile['previous_analyses'].append({
            'timestamp': datetime.now().isoformat(),
            'product_analysis': product_analysis
        })
    
    def get_similar_users(self, user_id, max_users=5):
        if user_id not in self.user_profiles:
            return []
        
        current_profile = self.user_profiles[user_id]
        current_segment = current_profile['segment']
        
        similar_users = []
        for other_id, profile in self.user_profiles.items():
            if other_id == user_id:
                continue
            if profile['segment'] == current_segment:
                similarity_score = self.calculate_similarity(current_profile, profile)
                similar_users.append({
                    'user_id': other_id,
                    'similarity_score': similarity_score,
                    'segment': profile['segment'],
                    'common_conditions': list(set(current_profile['medical_conditions']) & set(profile['medical_conditions'])),
                    'successful_recommendations': profile.get('successful_recommendations', [])[:3]
                })
        similar_users.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_users[:max_users]
    
    def calculate_similarity(self, profile1, profile2):
        score = 0
        conditions1 = set(profile1['medical_conditions'])
        conditions2 = set(profile2['medical_conditions'])
        if conditions1 and conditions2:
            condition_similarity = len(conditions1.intersection(conditions2)) / len(conditions1.union(conditions2))
            score += condition_similarity * 0.4
        if profile1['age_group'] == profile2['age_group']:
            score += 0.3
        diets1 = set(profile1['diet_preferences'])
        diets2 = set(profile2['diet_preferences'])
        if diets1 and diets2:
            diet_similarity = len(diets1.intersection(diets2)) / len(diets1.union(diets2))
            score += diet_similarity * 0.3
        
        return min(score, 1.0)
    
    def get_community_insights(self, segment, problem_type):
        segment_users = [uid for uid, profile in self.user_profiles.items() 
                        if profile['segment'] == segment]
        
        if not segment_users:
            return f"No community data available for {segment} segment"
        
        insights = {
            "total_users_in_segment": len(segment_users),
            "common_complaints": [],
            "successful_solutions": [],
            "segment_description": self.segment_definitions.get(segment, {}).get('description', '')}
        all_complaints = []
        for uid in segment_users:
            all_complaints.extend(self.user_profiles[uid].get('common_complaints', []))
        
        from collections import Counter
        common_complaints = Counter(all_complaints).most_common(3)
        insights["common_complaints"] = [complaint for complaint, count in common_complaints]
        all_recommendations = []
        for uid in segment_users:
            all_recommendations.extend(self.user_profiles[uid].get('successful_recommendations', []))
        
        common_recommendations = Counter(all_recommendations).most_common(3)
        insights["successful_solutions"] = [solution for solution, count in common_recommendations]
        
        return insights
    
    def add_successful_recommendation(self, user_id, recommendation):
        profile = self.get_or_create_user_profile(user_id)
        if 'successful_recommendations' not in profile:
            profile['successful_recommendations'] = []
        
        profile['successful_recommendations'].append({
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        })