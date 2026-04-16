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
            # чтобы клиент сразу понял, что соединение открыто
            yield "event: connected\ndata: ok\n\n"

            while True:
                if await request.is_disconnected():
                    break

                event = await queue.get()
                if event is None:
                    break

                yield event
        except asyncio.CancelledError:
            return
        except GeneratorExit:
            return
        finally:
            if queue in self.clients:
                self.clients.remove(queue)
            print(f"Client {client_id} disconnected")

    async def broadcast(self, data: str, event_type: str = default_type):
        dead_clients = []

        for queue in self.clients:
            try:
                queue.put_nowait(f"event: {event_type}\ndata: {data}\n\n")
            except Exception:
                dead_clients.append(queue)

        for queue in dead_clients:
            if queue in self.clients:
                self.clients.remove(queue)

    async def shutdown(self):
        for queue in self.clients[:]:
            try:
                queue.put_nowait(None)
            except Exception:
                pass

        self.clients.clear()
        await asyncio.sleep(0.01)
