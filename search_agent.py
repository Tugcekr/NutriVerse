# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 04:07:41 2025

@author: Tugce
"""

# search_agent.py
import requests

class SearchAgent:
    def __init__(self):
        self.base_url = "https://world.openfoodfacts.org/api/v0/product"
    
    def search_product(self, brand_name):
        try:
            search_url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': brand_name,
                'search_simple': 1,
                'json': 1,
                'page_size': 1
            }
            
            response = requests.get(search_url, params=params)
            data = response.json()
            
            if data['products']:
                product = data['products'][0]
                return {
                    'product_name': product.get('product_name', 'Bilinmiyor'),
                    'brand': product.get('brands', 'Bilinmiyor'),
                    'ingredients': product.get('ingredients_text', 'Bilinmiyor')
                }
            return {"error": "Ürün bulunamadı"}
                
        except Exception as e:
            return {"error": f"Arama hatası: {str(e)}"}