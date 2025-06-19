from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sentence_transformers import SentenceTransformer
import faiss
import json
import httpx

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

                user_embedding = model.encode([user_input])
                D, I = index.search(user_embedding, k=3)

                retrieved = []
                for i in I[0]:
                    task = tasks[i]["task"]
                    wymaga = tasks[i].get("requires_human_intervention", False)
                    flag_text = "TAK" if wymaga else "NIE"
                    retrieved.append(f"- Task: {task}\n  Requires human intervention: {flag_text}")
                retrieved_text = "\n".join(retrieved)

                prompt = f"""
Jesteś agentem decyzyjnym, którego jedynym zadaniem jest ocena, czy dane zadanie można zautomatyzować, czy wymaga interwencji człowieka.

Zasady, których musisz przestrzegać:
1. Oceniaj wyłącznie pytania związane z technicznymi zadaniami, procesami lub automatyzacją.
2. Jeśli wiadomość nie dotyczy tych obszarów (np. pogoda, small talk, podróże, zakupy) — jasno poinformuj, że nie jesteś do tego stworzony.
3. Jeśli wiadomość jest zbyt ogólna, możesz **raz** poprosić o doprecyzowanie. Jeśli jednak użytkownik podał już wystarczająco jasne informacje, nie pytaj dalej.
4. Uzasadniaj odpowiedzi tylko wtedy, gdy wyjaśnienie może pomóc użytkownikowi.

Przed udzieleniem odpowiedzi sprawdź, czy użytkownik wyraźnie wskazał preferowany język odpowiedzi — jeśli tak, dostosuj się do niego. W przeciwnym razie odpowiedz w języku wiadomości użytkownika.

Treść wiadomości użytkownika: "{user_input}"

Poniżej znajdują się podobne zadania wraz z informacją, czy wymagały interwencji człowieka:
{retrieved_text}
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
                print("Stop received")
                await websocket.send_json({"type": "stream", "done": True})
                continue

    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
