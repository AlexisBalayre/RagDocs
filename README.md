# RagDocs

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Node](https://img.shields.io/badge/node-20.17.0-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-teal)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

</div>

A powerful RAG-powered chatbot for technical documentation. Chat with your documentation using state-of-the-art retrieval augmented generation and local LLMs.

## 🌟 Features

- 🤖 Chat interface for technical documentation
- 🔍 Advanced RAG (Retrieval Augmented Generation) for accurate responses
- 💾 Local LLM support via Ollama
- 🎯 Vector search powered by Milvus
- 🚀 Modern Next.js frontend with real-time updates
- 📚 Multi-document support for different tech stacks
- ⚡ Fast and efficient document processing
- 🔄 Incremental updates for documentation changes

## 🏗️ Architecture

```
ragdocs/
├── api/                 # FastAPI backend
│   ├── conversation_api.py  # Chat API endpoints
│   ├── file_tracker.py     # Document change tracking
│   ├── llm_provider.py     # LLM integration (Ollama)
│   ├── markdown_processor.py# Markdown processing
│   └── rag_system.py       # Core RAG implementation
├── data/                # Documentation storage
│   ├── milvus_docs/    
│   ├── qdrant_docs/    
│   └── weaviate_docs/  
└── frontend/           # Next.js frontend
    └── src/            # Frontend source code
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20.17.0 (use nvm for version management)
  ```bash
  # Using nvm to install and use the correct Node.js version
  nvm install 20.17.0
  nvm use 20.17.0
  ```
- Milvus 2.0+
- Ollama (for local LLM)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AlexisBalayre/RagDocs.git
cd ragdocs
```

2. Install Python dependencies:
```bash
# Install poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Note: This project uses specific versions of many packages for compatibility.
# Key dependencies include:
# - llama-index: 0.11.22
# - fastapi: 0.115.4
# - milvus-lite: 2.4.10
# - sentence-transformers: 2.7.0
# - torch: 2.5.1
```

3. Install frontend dependencies:
```bash
cd frontend
yarn
```

4. Set up environment variables:
```bash
cp example.env.local .env.local
# Edit .env.local with your configuration
```

5. Start Milvus (standalone):
```bash
# Navigate to milvus directory
cd milvus

# Start Milvus standalone
bash standalone_embed.sh start

# To stop Milvus later:
# bash standalone_embed.sh stop
```

6. Start the backend:
```bash
poetry run uvicorn api.conversation_api:app --reload
```

7. Start the frontend:
```bash
cd frontend
yarn dev
```

## 💡 Usage

1. Add your documentation to the respective folders in `data/`
2. Start chatting with your documentation through the web interface
3. Use the comparison feature to analyze different tech stacks

### API Examples

```python
from ragdocs import ComparativeMarkdownRAG

# Initialize the RAG system
rag = ComparativeMarkdownRAG()

# Search across documentation
results = rag.search(
    query="How to handle scalability?",
    technologies=["milvus"],
    categories=["scalability", "deployment"],
    top_k=3
)
```

## 🔧 Configuration

Key configuration options in `.env.local`:

```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
OLLAMA_MODEL=llama3.2
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Vercel AI Chatbot](https://github.com/vercel/ai-chatbot) - Frontend UI based on this excellent template
- [LlamaIndex](https://github.com/jerryjliu/llama_index) for RAG capabilities
- [Milvus](https://github.com/milvus-io/milvus) for vector search
- [Ollama](https://github.com/jmorganca/ollama) for local LLM support

Special thanks to the Vercel team for providing the AI Chatbot template that served as the foundation for our frontend implementation.

## ⭐ Support

If you find this project useful, please consider giving it a star ⭐️!

