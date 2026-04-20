from aiohttp import web
import json
import asyncio
import time

# In-memory store for instances
instances = {}
next_instance_id = 1000

async def get_models(request):
    return web.json_response({
        "object": "list",
        "data": [
            {
                "id": "tiny-model",
                "object": "model",
                "created": 1677610602,
                "owned_by": "organization-owner"
            }
        ]
    })

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
        await asyncio.sleep(0.05) # Simulate some ITL

    await response.write(b"data: [DONE]\n\n")
    return response

async def search_offers(request):
    # Mock search results
    return web.json_response({
        "offers": [
            {
                "id": 1,
                "gpu_name": "RTX 4090",
                "dph_total": 0.5,
                "num_gpus": 1,
                "rentable": True,
                "verified": True
            }
        ]
    })

async def create_instance(request):
    global next_instance_id
    offer_id = request.match_info.get('id')
    data = await request.json()

    instance_id = next_instance_id
    next_instance_id += 1

    instances[str(instance_id)] = {
        "id": instance_id,
        "actual_status": "loading",
        "public_ipaddr": "127.0.0.1",
        "status_msg": "Creating instance",
        "ports": {
            "8000/tcp": [{"HostPort": "8000"}]
        }
    }

    # Simulate instance becoming ready after a short delay
    async def set_ready(id):
        await asyncio.sleep(2)
        if str(id) in instances:
            instances[str(id)]["actual_status"] = "running"
            instances[str(id)]["status_msg"] = "Running"

    asyncio.create_task(set_ready(instance_id))

    return web.json_response({
        "success": True,
        "new_contract": instance_id
    })

async def list_instances(request):
    # The SDK calls /instances with query_args={"owner": "me"}
    # which results in /api/v0/instances?owner=me
    return web.json_response({
        "instances": list(instances.values())
    })

async def get_instance_direct(request):
    instance_id = request.match_info.get('id')
    inst = instances.get(str(instance_id))
    if inst:
        return web.json_response({"instance": inst})
    return web.json_response({"error": "Not found"}, status=404)

async def destroy_instance(request):
    instance_id = request.match_info.get('id')
    if str(instance_id) in instances:
        del instances[str(instance_id)]
        return web.json_response({"success": True})
    return web.json_response({"error": "Not found"}, status=404)

app = web.Application()

# vLLM API
app.router.add_get('/v1/models', get_models)
app.router.add_post('/v1/chat/completions', chat_completions)

# Vast.ai API (handles both /bundles/ and /api/v0/bundles/)
app.router.add_post('/bundles/', search_offers)
app.router.add_post('/api/v0/bundles/', search_offers)
app.router.add_put('/asks/{id}/', create_instance)
app.router.add_put('/api/v0/asks/{id}/', create_instance)
app.router.add_get('/instances', list_instances)
app.router.add_get('/api/v0/instances', list_instances)
app.router.add_get('/api/v0/instances/', list_instances)
app.router.add_get('/api/v0/instances/{id}/', get_instance_direct)
app.router.add_delete('/instances/{id}/', destroy_instance)
app.router.add_delete('/api/v0/instances/{id}/', destroy_instance)

if __name__ == '__main__':
    print("Starting mock server on port 8000...")
    web.run_app(app, port=8000)
