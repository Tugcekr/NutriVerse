# 🔍 NutriVerse

AI-powered product safety analysis and health assistant with multi-agent system.

## 🚀 Features

- **Product Analysis**: Upload product photos for AI-powered safety analysis
- **Health Assistant**: Personalized health and nutrition advice
- **Multi-Agent System**: 3 specialized agents working together
- **Baby Safety**: Age-specific recommendations for children
- **Community Insights**: Learn from similar users' experiences

# Clone the repository
git clone https://github.com/Tugcekr/NutriVerse.git

cd NutriVerse

# Install dependencies
pip install -r requirements.txt

# Setup Ollama models (required for AI functionality)
ollama pull llama3.2:3b
ollama pull llava:7b

# Prepare knowledge base
# Place hazard_ingredients_short.docx in the project root directory
# Update the file path in main_coordinator.py if needed
1. Run the application:
streamlit run NutriVerse.py
2. Access the web interface at http://localhost:8501

3.Use Product Analysis Tab:

Upload product photo (jpg, jpeg, png)

Select dietary preferences (celiac, vegan, diabetes, etc.)

Get instant risk analysis and safety scores

4.Use Health Assistant Tab:

Chat about nutrition, baby care, or product safety

Get personalized advice based on your profile

Ask example questions like "Can I give egg to my 6-month-old baby?"

🤖 System Architecture
Agent Overview:
🔍 Vision Agent: Brand recognition from product images using LLaVA model

🌐 Search Agent: Product information retrieval from OpenFoodFacts API

🧠 RAG Agent: Risk analysis using document-based knowledge base with FAISS vector storage

💾 Memory Agent: User profiling, segmentation, and community insights

💬 Chatbot Agent: Interactive health assistant with tool integration
