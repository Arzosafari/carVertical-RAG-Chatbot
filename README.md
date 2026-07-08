 Project Overview
This project implements an intelligent search and chatbot system based on RAG (Retrieval-Augmented Generation) technology for the carVertical.com website. The system automatically crawls the website, extracts textual content, stores it in a vector database, and answers user questions about the website's services and information.

✨ Key Features
🕷️ Smart Crawler: Automated website content extraction with internal link support

🧠 Vector Database: Semantic search and storage with ChromaDB

🤖 Intelligent Chatbot: Answering questions using Large Language Models (LLM)

🔒 Local Execution: No internet required, privacy-preserving

💬 Beautiful UI: Designed with Streamlit for excellent user experience

📊 Source Management: Display sources and related documents for each answer

🛠️ Technologies Used
Technology	Purpose
Python 3.8+	Main programming language
Streamlit	Web UI framework
ChromaDB	Local vector database
Sentence-Transformers	Semantic embedding generation (all-MiniLM-L6-v2)
BeautifulSoup	HTML parsing and content extraction
LM Studio	Local LLM execution
Requests	HTTP requests handling
🚀 Quick Start
Prerequisites
Python 3.8 or higher

LM Studio (for LLM execution)

Minimum 4GB free RAM

Installation
bash
# Clone the repository
git clone https://github.com/yourusername/carvertical-rag-chatbot.git
cd carvertical-rag-chatbot

# Install dependencies
pip install -r requirements.txt
Running the System
Run the crawler:

bash
python crawler_only.py
Start LM Studio:

Download and install LM Studio

Load your preferred model (e.g., Gemma)

Start the server on port 1234

Launch the chatbot:

bash
streamlit run app_chat_only.py
Visit http://localhost:8501 in your browser.

💡 Usage Examples
"What is carVertical and how does it work?"

"How can I check a vehicle's history?"

"What information does a carVertical report contain?"

"Is carVertical reliable for used car checks?"

🤝 Contributing
We welcome contributions! Please see our Contributing Guidelines.

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
