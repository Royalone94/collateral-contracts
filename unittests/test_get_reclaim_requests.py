import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
from scripts.get_reclaim_requests import get_reclaim_process_started_events, ReclaimProcessStartedEvent


class TestReclaimEventRetrieval(unittest.TestCase):

    @patch("reclaim_event_retrieval.load_contract_abi")
    def test_get_reclaim_process_started_events(self, mock_load_contract_abi):
        # Mock ABI and contract
        mock_abi = [{"name": "ReclaimProcessStarted", "type": "event"}]
        mock_load_contract_abi.return_value = mock_abi

        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_w3.to_checksum_address.side_effect = lambda x: x
        mock_w3.keccak.return_value.hex.return_value = "0xEventTopicHash"

        # Simulated log
        mock_log = {
            "topics": [
                "0xEventTopicHash",
                bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000012"),
                bytes.fromhex("0000000000000000000000000123456789abcdef0123456789abcdef01234567"),
            ],
            "blockNumber": 123456
        }

        decoded_event_data = {
            "args": {
                "amount": 5000,
                "expirationTime": 17234567,
                "url": "https://example.com/reclaim",
                "urlContentMd5Checksum": bytes.fromhex("3e25960a79dbc69b674cd4ec67a72c62"),
            }
        }

        mock_contract.events.ReclaimProcessStarted().process_log.return_value = decoded_event_data
        mock_w3.eth.get_logs.return_value = [mock_log]

        # Call the function under test
        results = get_reclaim_process_started_events(mock_w3, "0xMockContract", 100, 200)

        # Assertions
        self.assertEqual(len(results), 1)
        event = results[0]
        self.assertEqual(event.reclaim_request_id, 18)
        self.assertEqual(event.account, "0x0123456789abcdef0123456789abcdef01234567")
        self.assertEqual(event.amount, 5000)
        self.assertEqual(event.expiration_time, 17234567)
        self.assertEqual(event.url, "https://example.com/reclaim")
        self.assertEqual(event.url_content_md5_checksum, "3e25960a79dbc69b674cd4ec67a72c62")
        self.assertEqual(event.block_number, 123456)


if __name__ == "__main__":
    unittest.main()
