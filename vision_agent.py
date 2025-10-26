# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 17:00:26 2025

@author: Tugce
"""


# vision_agent.py
import ollama
from PIL import Image
import base64
import io
import os

class VisionAgent:
    def __init__(self, model_name='llava:7b'):
        self.model_name = model_name
    
    def detect_brand(self, image_path):
        try:
            with Image.open(image_path) as img:
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': 'WHAT IS THE BRAND NAME IN THIS PRODUCT? ANSWER ONLY WITH THE BRAND NAME.',
                    'images': [img_base64]}])
            brand = response['message']['content'].strip()
            return brand
            
        except Exception as e:
            return f"Hata: {str(e)}"