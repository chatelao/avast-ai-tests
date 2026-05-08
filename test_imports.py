import sys
try:
    import ray
    import llmperf
    from llmperf.ray_clients.openai_chat_completions_client import OpenAIChatCompletionsClient
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
