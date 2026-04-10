import unittest
from unittest.mock import MagicMock, patch
from infra.vast_manager import VastManager
from orchestrator import Orchestrator
import asyncio

class TestTemplateLogic(unittest.TestCase):
    def test_vast_manager_template(self):
        sdk_mock = MagicMock()
        with patch('infra.vast_manager.VastAI', return_value=sdk_mock):
            mgr = VastManager(api_key="fake")
            mgr.rent_instance(123, template_hash="hash123", disk=40)
            sdk_mock.create_instance.assert_called_with(id=123, template_hash="hash123", disk=40)

            mgr.rent_instance(456, image="img456", disk=20)
            sdk_mock.create_instance.assert_called_with(id=456, image="img456", disk=20)

    @patch('orchestrator.VastManager')
    def test_orchestrator_template_pass_through(self, mock_vast_mgr_class):
        mock_vast_mgr = mock_vast_mgr_class.return_value
        mock_vast_mgr.find_offers.return_value = [{'id': 789}]
        mock_vast_mgr.rent_instance.return_value = 1010
        mock_vast_mgr.wait_for_ssh.return_value = {'ssh_host': 'localhost', 'ssh_port': 8000}

        orch = Orchestrator(api_key="fake")
        # Mock wait_for_api_ready to return True immediately
        orch.wait_for_api_ready = MagicMock(return_value=asyncio.Future())
        orch.wait_for_api_ready.return_value.set_result(True)

        # Mock tester.run_benchmark
        with patch('orchestrator.LoadTester') as mock_tester_class:
            mock_tester = mock_tester_class.return_value
            mock_tester.run_benchmark.return_value = asyncio.Future()
            mock_tester.run_benchmark.return_value.set_result({'total_tps': 10})

            asyncio.run(orch.run_suite("GPU", "MODEL", template_hash="myhash", concurrency_levels=[1], requests_per_level=1))

            mock_vast_mgr.rent_instance.assert_called_with(789, template_hash="myhash")

if __name__ == '__main__':
    unittest.main()
