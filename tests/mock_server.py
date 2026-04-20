import json
import asyncio
from aiohttp import web

async def handle_models(request):
    return web.json_response({
        "object": "list",
        "data": [{
            "id": "tiny-model",
            "object": "model",
            "created": 1677610602,
            "owned_by": "openai"
        }]
    })

async def handle_chat_completions(request):
    data = await request.json()
    stream = data.get("stream", False)

    if stream:
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={'Content-Type': 'text/event-stream'},
        )
        await response.prepare(request)

        for i in range(5):
            chunk = {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": 1677652288,
                "model": "tiny-model",
                "choices": [{"index": 0, "delta": {"content": f"token {i} "}, "finish_reason": None}]
            }
            await response.write(f"data: {json.dumps(chunk)}\n\n".encode('utf-8'))
            await asyncio.sleep(0.1)

        await response.write(b"data: [DONE]\n\n")
        return response
    else:
        return web.json_response({
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "tiny-model",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 9,
                "completion_tokens": 12,
                "total_tokens": 21
            }
        })

app = web.Application()
app.router.add_get('/v1/models', handle_models)
app.router.add_post('/v1/chat/completions', handle_chat_completions)

if __name__ == '__main__':
    web.run_app(app, port=8000)
