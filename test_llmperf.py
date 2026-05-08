import ray
from llmperf.models import RequestConfig
from llmperf.ray_clients.openai_chat_completions_client import OpenAIChatCompletionsClient
from llmperf.requests_launcher import RequestsLauncher
import os

def test_llmperf_basic():
    try:
        # Initialize ray in a very minimal way for testing
        ray.init(ignore_reinit_error=True, num_cpus=1)

        prompt = ("What is 2+2?", 5)

        # We won't actually send a request because we don't have a live server here
        # that easily, but we can see if the objects can be instantiated.
        client = OpenAIChatCompletionsClient.remote()
        launcher = RequestsLauncher([client])

        print("Successfully instantiated llmperf objects")
        ray.shutdown()
    except Exception as e:
        print(f"llmperf test failed: {e}")

if __name__ == "__main__":
    test_llmperf_basic()
