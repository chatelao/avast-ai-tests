import pytest
import asyncio
from unittest.mock import MagicMock, patch
import benchmark
from benchmark import LoadTester, run_benchmark, report_results
import os
import json

class MockResponse:
    def __init__(self, content):
        self.content = content
        self.status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_run_benchmark():
    # Mock tester
    tester = MagicMock()
    # Define a sync helper that returns a future
    def mock_run(c, n):
        f = asyncio.Future()
        f.set_result({
            "concurrency": c,
            "success_rate": 1.0,
            "avg_ttft": 0.1,
            "avg_tps": 10.0,
            "total_tps": 10.0
        })
        return f

    tester.run = MagicMock(side_effect=mock_run)

    concurrency_levels = [1, 2]
    requests_per_level = 5

    results = await run_benchmark(tester, concurrency_levels, requests_per_level)

    assert len(results) == 2
    assert results[0]["concurrency"] == 1
    assert results[1]["concurrency"] == 2
    # Verify Saturation Rule (num_requests = max(c, requests_per_level))
    tester.run.assert_any_call(1, 5)
    tester.run.assert_any_call(2, 5)

def test_report_results(tmp_path):
    all_results = [
        {"concurrency": 1, "success_rate": 1.0, "avg_ttft": 0.1, "avg_tps": 10.0, "total_tps": 10.0}
    ]

    # Mock environment and file operations
    with patch("os.getenv", return_value=str(tmp_path / "summary.md")), \
         patch("benchmark.log") as mock_log:

        report_results(all_results, "test-model", "RTX_4090", 1)

        # Check if JSON files are created (they are created in current dir in report_results)
        assert os.path.exists("results.json")
        with open("results.json", "r") as f:
            data = json.load(f)
            assert data[0]["concurrency"] == 1

        # Cleanup
        if os.path.exists("results.json"):
            os.remove("results.json")
        # Cleanup other benchmark_*.json files
        for f in os.listdir("."):
            if f.startswith("benchmark_") and f.endswith(".json"):
                os.remove(f)
