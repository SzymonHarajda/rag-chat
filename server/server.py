from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sentence_transformers import SentenceTransformer
import faiss
import json
import httpx
from langdetect import detect, LangDetectException

app = FastAPI()

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

with open("tasks.json") as f:
    tasks = json.load(f)

texts = [x["task"] for x in tasks]
embeddings = model.encode(texts)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "question":
                session_id = data["sessionId"]
                user_input = data["question"]

                detected_language = "en"
                try:
                    detected_language = detect(user_input)
                    print(f"Detected language: {detected_language}")
                except LangDetectException:
                    print("Could not detect language, defaulting to English.")
                user_embedding = model.encode([user_input])
                D, I = index.search(user_embedding, k=3)

                retrieved_tasks_info = []
                for i in I[0]:
                    task_description = tasks[i]["task"]
                    requires_human_intervention = tasks[i].get("requires_human_intervention", False)
                    flag_text = "Yes" if requires_human_intervention else "No"
                    retrieved_tasks_info.append(
                        f"- Task: {task_description}\n  Requires human intervention: {flag_text}")
                retrieved_text = "\n".join(retrieved_tasks_info)

                prompt = f"""
You are a decision-making assistant whose sole task is to assess whether a given task can be automated or requires human intervention.

Guidelines you must follow:
1. Only evaluate questions related to technical tasks, processes, or automation.
2. If the message is unrelated (e.g. weather, small talk, travel, shopping), clearly state that this is outside your scope.
3. If the message is too vague, you may ask for clarification **once**. However, if the user has already provided clear information, do not ask again.
4. Provide explanations only if they are helpful to the user.

User message content: "{user_input}"

Below are similar tasks along with information on whether they required human intervention:
{retrieved_text}

**The detected language of the user's message is: {detected_language}**
Please ensure your response is in this language unless the user explicitly asks for a different language.
"""
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                            "POST",
                            "http://localhost:11434/api/generate",
                            json={"model": "gemma2:9b", "prompt": prompt, "stream": True}
                    ) as resp:
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                chunk = json.loads(line)
                                word = chunk.get("response", "")
                                done = chunk.get("done", False)
                                await websocket.send_json({
                                    "type": "stream",
                                    "sessionId": session_id,
                                    "word": word,
                                    "done": done
                                })
                                if done:
                                    break
                            except Exception as e:
                                print("Error parsing chunk:", e)
                                continue

            elif data.get("type") == "stop":
                print("Stop signal received")
                await websocket.send_json({"type": "stream", "done": True})
                continue

    except WebSocketDisconnect:
        print("WebSocket disconnected")
