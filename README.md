# RagDocs

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Node](https://img.shields.io/badge/node-20.17.0-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-teal)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

</div>

**RagDocs** is a cutting-edge open-source solution that revolutionizes how you interact with documentation. By combining the power of **local LLMs** with state-of-the-art **Retrieval-Augmented Generation (RAG)**, developers can instantly get accurate answers from their documentation without any API costs.

Say goodbye to expensive API calls and privacy concerns. With **RagDocs**, all your documentation stays private while providing ChatGPT-like interactions. Built with Milvus vector search and Next.js, it's production-ready and easy to deploy. Experience the future of documentation search with complete data privacy and no usage fees.

https://github.com/user-attachments/assets/24c25726-6599-4be5-9fa5-c7b8af6a4c55

## 🌟 Features

- **🤖 Intelligent Chat Interface**: Conversational interface tailored for technical documentation.
- **🔍 Cutting-Edge Retrieval Augmented Generation**: Accurate and context-aware responses.
- **💾 Local LLM Support**: Integrated with Ollama for privacy and efficiency.
- **🎯 Vector Search Powered by Milvus**: Rapid and scalable document querying.
- **🚀 Modern Next.js Frontend**: Sleek, real-time user experience.
- **📚 Multi-Document Support**: Seamless handling of diverse tech stacks.
- **⚡ Fast Document Processing**: Efficient ingestion and analysis of updates.
- **🔄 Incremental Updates**: Keep your documentation in sync effortlessly.

---

## 🏗️ Architecture

```
ragdocs/
├── data/                         # Documentation storage
│   ├── milvus_docs/              # Milvus documentation
│   ├── qdrant_docs/              # Qdrant documentation
│   └── weaviate_docs/            # Weaviate documentation
├── milvus/                       # Milvus standalone setup
│   └── standalone_embed.sh       # Milvus standalone script
├── ragdocs_api/                  # FastAPI backend
│   ├── conversation_api.py       # Chat API endpoints
│   ├── file_tracker.py           # Document change tracking
│   ├── llm_provider.py           # LLM integration (Ollama)
│   ├── markdown_processor.py     # Markdown processing
│   └── rag_system.py             # Core RAG implementation
└── ragdocs_frontend/             # Next.js frontend
    └── src/                      # Frontend source code
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20.17.0
- Milvus 2.0+
- Ollama (for local LLM support)

Install Node.js with **nvm**:

```bash
nvm install 20.17.0
nvm use 20.17.0
```

---

### Installation

1. **Clone the Repository**:

```bash
git clone https://github.com/AlexisBalayre/RagDocs.git
cd RagDocs
```

2. **Install Python Dependencies**:

```bash
# Install poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
poetry shell
```

> **Key Dependencies:**
> - llama-index: 0.11.22
> - fastapi: 0.115.4
> - milvus-lite: 2.4.10
> - sentence-transformers: 2.7.0
> - torch: 2.5.1

3. **Install Frontend Dependencies**:

```bash
cd ragdocs_frontend
yarn
```

4. **Set Up Environment Variables**:

```bash
cp example.env.local .env.local
# Edit .env.local with your configuration
```

5. **Start Milvus**:

```bash
cd milvus
bash standalone_embed.sh start
```

6. **Run the Backend**:

```bash
poetry run uvicorn ragdocs_api.conversation_api:app --reload
```

7. **Run the Frontend**:

```bash
cd ragdocs_frontend
yarn dev
```

---

## 💡 Usage

1. **Add Documentation**: Place files in the respective folders under `data/`.
2. **Start Chatting**: Use the frontend to chat with and explore your documentation.
3. **Compare Tech Stacks**: Leverage built-in comparison features for analysis.

---

## 🔧 Configuration

Edit the `.env.local` file for key settings:

```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
OLLAMA_MODEL=llama3.2
```

---

## 🤝 Contributing

Contributions are encouraged! Follow these steps:

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/AmazingFeature
```

3. Commit your changes:

```bash
git commit -m 'Add some AmazingFeature'
```

4. Push your branch:

```bash
git push origin feature/AmazingFeature
```

5. Open a Pull Request.

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Vercel AI Chatbot](https://github.com/vercel/ai-chatbot) - Template inspiration for the frontend.
- [LlamaIndex](https://github.com/jerryjliu/llama_index) - Powering RAG capabilities.
- [Milvus](https://github.com/milvus-io/milvus) - Efficient vector search backend.
- [Ollama](https://github.com/jmorganca/ollama) - Local LLM support.

---

## ⭐ Support

If this project adds value to your work, **please give it a star!**

Your support makes a difference and encourages further development. Feedback and feature suggestions are always welcome!

