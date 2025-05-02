import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
from scripts.reclaim_collateral import reclaim_collateral, ReclaimCollateralError


class TestReclaimCollateral(unittest.TestCase):

    @patch("reclaim_collateral.load_contract_abi")
    @patch("reclaim_collateral.calculate_md5_checksum")
    @patch("reclaim_collateral.wait_for_receipt")
    @patch("reclaim_collateral.build_and_send_transaction")
    def test_reclaim_collateral_success(
        self, mock_build_tx, mock_wait_receipt, mock_md5, mock_load_abi
    ):
        # Setup mocks
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_function = MagicMock()
        mock_event = MagicMock()

        mock_md5.return_value = "3e25960a79dbc69b674cd4ec67a72c62"

        mock_contract.functions.reclaimCollateral.return_value = mock_function
        mock_w3.eth.contract.return_value = mock_contract
        mock_w3.to_wei.return_value = 1000000000000000000  # 1 TAO in Wei

        tx_hash = "0xabc123"
        mock_build_tx.return_value = tx_hash

        receipt = {
            "status": 1,
            "transactionHash": b"\x12" * 32,
            "blockNumber": 12345
        }

        mock_wait_receipt.return_value = receipt
        mock_contract.events.ReclaimProcessStarted().process_receipt.return_value = [{
            "args": {
                "reclaimRequestId": 42,
                "account": "0xabc",
                "amount": 1000000000000000000,
                "expirationTime": 9999999999,
                "url": "https://example.com",
                "urlContentMd5Checksum": bytes.fromhex("3e25960a79dbc69b674cd4ec67a72c62")
            }
        }]

        # Run test
        account = MagicMock()
        result_receipt, result_event = reclaim_collateral(
            mock_w3, account, 1.0, "0xContract", "https://example.com", "uuid-123"
        )

        # Assert results
        self.assertEqual(result_receipt["status"], 1)
        self.assertEqual(result_event["args"]["reclaimRequestId"], 42)
        mock_md5.assert_called_once_with("https://example.com")
        mock_build_tx.assert_called_once()
        mock_wait_receipt.assert_called_once_with(mock_w3, tx_hash)

    @patch("reclaim_collateral.load_contract_abi")
    @patch("reclaim_collateral.wait_for_receipt")
    @patch("reclaim_collateral.build_and_send_transaction")
    def test_reclaim_collateral_failure(
        self, mock_build_tx, mock_wait_receipt, mock_load_abi
    ):
        # Setup mocks
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_function = MagicMock()
        mock_contract.functions.reclaimCollateral.return_value = mock_function
        mock_w3.eth.contract.return_value = mock_contract
        mock_w3.to_wei.return_value = 1000000000000000000

        mock_build_tx.return_value = "0xabc123"
        mock_wait_receipt.return_value = {"status": 0}

        # Run test and assert exception
        with self.assertRaises(ReclaimCollateralError):
            reclaim_collateral(
                mock_w3, MagicMock(), 1.0, "0xContract", "https://fail.com", "uuid-xyz"
            )


if __name__ == "__main__":
    unittest.main()
