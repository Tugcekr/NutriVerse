# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 04:08:25 2025

@author: Tugce
"""

# main_coordinator.py
from vision_agent import VisionAgent
from search_agent import SearchAgent
from rag_agent import RAGAnalysisAgent

class ProductAnalysisCoordinator:
    def __init__(self):
        self.vision_agent = VisionAgent()
        self.search_agent = SearchAgent()
        self.rag_agent = RAGAnalysisAgent("C:/Users/Tugce/OneDrive/Masaüstü/hazard_ingredients_short.docx")
    
    def full_analysis(self, image_path, user_preferences):
        print(" 3-AJANLI ANALİZ BAŞLATILDI")
        brand = self.vision_agent.detect_brand(image_path)
        print(f"Tespit edilen marka: {brand}")
        
        if "UNKNOWN" in brand or "Hata" in brand:
            return {"error": "Marka tespit edilemedi"}
        product_data = self.search_agent.search_product(brand)
        
        if "error" in product_data:
            return {"error": "Ürün bulunamadı"}
        

        ingredients = product_data.get('ingredients', '')
        risk_analysis = self.rag_agent.analyze_ingredients(ingredients, user_preferences)
        risk_score = self.rag_agent.calculate_risk_score(risk_analysis)
        
        return {
            'brand': brand,
            'product_name': product_data.get('product_name'),
            'ingredients': ingredients,
            'risk_analysis': risk_analysis,
            'risk_score': risk_score,
            'overall_safety': "GÜVENLİ" if risk_score > 80 else "ORTA" if risk_score > 50 else "RİSKLİ"
        }