import asyncio
from typing import List
from fastapi import Request


default_type = "update"

class SSEManager:
    def __init__(self):
        self.clients: List[asyncio.Queue] = []

    async def add_client(self, request: Request):
        queue = asyncio.Queue()
        self.clients.append(queue)

        client_id = id(queue)
        print(f"🔗 Client {client_id} connected") 

        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                yield f"{event}\n\n"
        except asyncio.CancelledError:
            return
        except GeneratorExit:
            return
        finally:
            if queue in self.clients:
                self.clients.remove(queue)

    async def broadcast(self, data: str, event_type: str = default_type):
        for queue in self.clients:
            try:
                await queue.put(f"event: {event_type}\ndata: {data}\n\n")
            except Exception:
                pass  

    async def shutdown(self):
        for queue in self.clients[:]:
            try:
                await queue.put("event: close\ndata: server_shutdown\n\n")
            except Exception:
                pass
        await asyncio.sleep(0.01)

