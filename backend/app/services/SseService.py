import json
from typing import Dict, Optional
from ..utils.SSEManager import SSEManager
from anyio import from_thread

sse_manager: Optional[SSEManager] = None


def set_sse_manager(manager: SSEManager):
    global sse_manager
    sse_manager = manager

def send_to_client_update(data_dict: Optional[Dict] = None, event_type: Optional[str] = None):
    if sse_manager is None:
        return
    data = data_dict or {} 

    print('Sent sse trigger')

    if event_type is None:
        from_thread.run(sent_only_data, data)
    else:
        from_thread.run(sent_data_and_type, data, event_type)


async def sent_only_data(data: dict) -> None:
    await sse_manager.broadcast(json.dumps(data))


async def sent_data_and_type(data: dict, event_type: str) -> None:
    await sse_manager.broadcast(json.dumps(data), event_type=event_type)

