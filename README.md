
# 🧠 Task Automation Assistant

This project is a decision support tool that helps determine whether a given task can be automated or requires human intervention. It includes a React-based frontend, a FastAPI backend, semantic search using SentenceTransformers + FAISS, and integrates with local LLMs via [Ollama](https://ollama.com/).

---

## 📦 Requirements

- **Node.js** ≥ 16
- **Python** ≥ 3.9
- **pip** (Python package manager)
- **npm** (Node.js package manager)
- **Ollama** (for running local language models like Gemma or Mistral)

---

## 🚀 Getting Started

### ▶️ Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open your browser at [http://localhost:5173](http://localhost:5173)

---

### ⚙️ Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd server
   ```

2. Install Python dependencies:

   ```bash
   pip install fastapi sentence-transformers faiss-cpu httpx uvicorn langdetect
   ```

3. Make sure the file `tasks.json` is present in the same directory.

4. Start the FastAPI server:

   ```bash
   uvicorn server:app --reload
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000)

---

### 🧠 Running the Language Model (via Ollama)

This project relies on a local LLM to generate answers based on the prompt and task context.

1. **Install Ollama**:  
   Download and install from [https://ollama.com/download](https://ollama.com/download)

2. **Run a model** (choose one of the following):

    - Gemma 9B:

      ```bash
      ollama run gemma:9b
      ```

    - Mistral:

      ```bash
      ollama run mistral
      ```

3. Ollama will be available at `http://localhost:11434` by default — ensure it's running before starting the backend.

---

## 📁 Project Structure

```
project/
├── frontend/           # Frontend application (React + Vite)
│   └── ...
├── server/             # Backend (FastAPI)
│   ├── server.py       # Main server file
│   └── tasks.json      # Task definitions for semantic search
└── README.md           # This file
```

---

## 🧪 How It Works

- `tasks.json` contains predefined task descriptions and flags indicating if human input is needed.
- On startup, the backend embeds task descriptions using `sentence-transformers` and builds a FAISS vector index.
- When the user asks a question, the most similar tasks are retrieved.
- A structured prompt is built and sent to the local LLM via Ollama.
- The response is streamed back to the frontend via WebSocket.

---

## 🛠️ Troubleshooting

| Problem                         | Solution                                                                 |
|----------------------------------|--------------------------------------------------------------------------|
| Ollama not responding           | Make sure `ollama run gemma:9b` or `mistral` is running in a terminal   |
| WebSocket disconnects           | Ensure backend is running and listening on the correct port             |
| Model responses are empty       | Confirm that the model supports streaming responses                     |
| FAISS errors on install         | Use `faiss-cpu` if you don’t need GPU acceleration                      |

---

## 📄 License

MIT License — feel free to modify and adapt the project for your needs.

---
