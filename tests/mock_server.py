from aiohttp import web
import json
import asyncio

# Mock state to track instances
instances = {}

async def chat_completions(request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    stream = data.get("stream", False)

    if not stream:
        return web.json_response({
            "choices": [{"message": {"content": "This is a mock response."}}]
        })

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        },
    )
    await response.prepare(request)

    tokens = ["This", " is", " a", " mock", " streaming", " response."]
    for token in tokens:
        chunk = {
            "choices": [{"delta": {"content": token}}]
        }
        await response.write(f"data: {json.dumps(chunk)}\n\n".encode('utf-8'))
        await asyncio.sleep(0.01) # Simulate some ITL

    await response.write(b"data: [DONE]\n\n")
    return response

async def get_models(request):
    return web.json_response({"data": [{"id": "tiny-model"}]})

async def search_offers(request):
    # VastAI SDK POSTs to /api/v0/bundles/
    return web.json_response({
        "offers": [
            {"id": 1001, "dph_total": 0.45, "gpu_name": "RTX 4090"}
        ]
    })

async def create_instance(request):
    offer_id = request.match_info['id']
    instance_id = 2001
    instances[str(instance_id)] = {
        "id": instance_id,
        "actual_status": "loading",
        "public_ipaddr": "127.0.0.1",
        "ports": {"8000/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8000"}]},
        "status_msg": "Loading..."
    }
    # Simulate transitioning to running after a short delay
    asyncio.create_task(make_instance_running(str(instance_id)))

    return web.json_response({"success": True, "new_contract": instance_id})

async def make_instance_running(instance_id):
    await asyncio.sleep(1)
    if instance_id in instances:
        instances[instance_id]["actual_status"] = "running"
        instances[instance_id]["status_msg"] = "Running"

async def list_instances(request):
    return web.json_response({"instances": list(instances.values())})

async def destroy_instance(request):
    instance_id = request.match_info['id']
    if instance_id in instances:
        del instances[instance_id]
        return web.json_response({"success": True})
    return web.json_response({"success": False, "error": "Not found"}, status=404)

app = web.Application()
# vLLM Endpoints
app.router.add_post('/v1/chat/completions', chat_completions)
app.router.add_get('/v1/models', get_models)
# Vast.ai Endpoints
app.router.add_post('/api/v0/bundles/', search_offers)
app.router.add_put('/api/v0/asks/{id}/', create_instance)
app.router.add_get('/api/v0/instances/', list_instances)
app.router.add_delete('/api/v0/instances/{id}/', destroy_instance)

if __name__ == '__main__':
    print("Starting combined mock server on port 8000...")
    web.run_app(app, port=8000)
