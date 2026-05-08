import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import asyncio

# Add the root directory to sys.path to import benchmark
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import benchmark

class TestRemoteLogic(unittest.IsolatedAsyncioTestCase):
    @patch("benchmark.os.getenv")
    @patch("benchmark.os.path.exists")
    @patch("benchmark.open")
    async def test_run_remote_logic(self, mock_file, mock_exists, mock_getenv):
        # Configure mocks
        mock_getenv.side_effect = lambda k, default=None: "mock-api-key" if k == "VAST_AI_API_KEY" else default
        mock_exists.side_effect = lambda path: True if path in [".vast_instance_id", "results.json"] else False

        # Mock file reads: first for .vast_instance_id, second for results.json
        mock_results = [{"concurrency": 1, "total_tps": 10.0}]
        mock_file.side_effect = [
            mock_open(read_data="2001").return_value,
            mock_open(read_data=json.dumps(mock_results)).return_value
        ]

        mock_sdk = MagicMock()

        # Patch the local import of VastAI inside run_remote by patching sys.modules or just the import
        # Since it's imported inside the function, we can patch the module where it's imported from.
        with patch("vastai.sdk.VastAI", return_value=mock_sdk):
            args = MagicMock()
            args.remote = True
            args.model = "facebook/opt-125m"
            args.gpu = "RTX 4090"
            args.concurrency_levels = [1]
            args.requests_per_level = 1

            # sys.argv is used inside run_remote
            with patch("sys.argv", ["benchmark.py", "--model", "facebook/opt-125m", "--gpu", "RTX 4090", "--remote"]):
                result = await benchmark.run_remote(args)

            # 1. Verify file copy to remote
            mock_sdk.copy.assert_any_call("local:benchmark.py", "2001:benchmark.py")

            # 2. Verify command execution and QUOTING
            args_call = mock_sdk.execute.call_args[0]
            self.assertEqual(args_call[0], 2001)
            cmd = args_call[1]
            self.assertIn("python3 benchmark.py", cmd)
            self.assertIn("--model facebook/opt-125m", cmd)
            self.assertIn("--gpu 'RTX 4090'", cmd)
            self.assertNotIn("--remote", cmd)
            self.assertIn("--url http://localhost:8000", cmd)
            self.assertIn("--output-dir results_remote", cmd)

            # 3. Verify download
            mock_sdk.copy.assert_any_call("2001:results_remote/", "local:.")

            # 4. Verify return value
            self.assertEqual(result, mock_results)

if __name__ == "__main__":
    unittest.main()
