from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import traceback

# Import your existing project.py module
import project

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def send_personal(self, ws: WebSocket, message: dict):
        await ws.send_text(json.dumps(message))

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.send_personal(ws, {"type": "welcome", "message": "Connected to WebSocket server"})
    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(ws, {"error": "Invalid JSON"})
                continue

            # --- Main Integration Point ---
            # Try to call project.handle_ws_message(data) if it exists
            if hasattr(project, "handle_ws_message"):
                try:
                    result = project.handle_ws_message(payload)
                    await manager.send_personal(ws, {"type": "result", "data": result})
                except Exception as e:
                    traceback.print_exc()
                    await manager.send_personal(ws, {"error": f"Exception: {str(e)}"})
            else:
                # Fallback if no function found
                await manager.send_personal(ws, {
                    "type": "echo",
                    "data": payload,
                    "note": "No handle_ws_message() found in project.py"
                })
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/")
async def root():
    return {"message": "WebSocket server with project.py integration is running."}
