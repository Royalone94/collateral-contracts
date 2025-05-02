import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import patch, MagicMock
from scripts.slash_collateral import slash_collateral, SlashCollateralError


class TestSlashCollateral(unittest.TestCase):

    @patch("slash_collateral.calculate_md5_checksum")
    @patch("slash_collateral.wait_for_receipt")
    @patch("slash_collateral.build_and_send_transaction")
    @patch("slash_collateral.load_contract_abi")
    def test_slash_collateral_success(
        self,
        mock_load_abi,
        mock_build_tx,
        mock_wait_receipt,
        mock_md5_checksum,
    ):
        # Arrange
        mock_w3 = MagicMock()
        mock_account = MagicMock()

        contract_mock = MagicMock()
        event_mock = MagicMock()

        mock_w3.eth.contract.return_value = contract_mock
        mock_contract_fn = MagicMock()
        contract_mock.functions.slashCollateral.return_value = mock_contract_fn

        mock_md5_checksum.return_value = "a" * 32
        mock_tx_hash = "0xabc"
        mock_build_tx.return_value = mock_tx_hash

        expected_receipt = {"status": 1, "transactionHash": b"\x01" * 32, "blockNumber": 100}
        mock_wait_receipt.return_value = expected_receipt

        # Mock event log
        contract_mock.events.Slashed().process_receipt.return_value = [{
            "args": {
                "account": "0xMiner",
                "amount": 1000000000000000000,
                "url": "https://example.com",
                "urlContentMd5Checksum": b"\xaa" * 16
            }
        }]

        # Act
        receipt, event = slash_collateral(
            mock_w3,
            mock_account,
            "0xMiner",
            1.0,
            "0xCollateral",
            "https://example.com",
            "uuid-123"
        )

        # Assert
        self.assertEqual(receipt["status"], 1)
        self.assertEqual(event["args"]["account"], "0xMiner")
        mock_build_tx.assert_called_once()
        mock_wait_receipt.assert_called_once_with(mock_w3, mock_tx_hash)

    @patch("slash_collateral.calculate_md5_checksum")
    @patch("slash_collateral.wait_for_receipt")
    @patch("slash_collateral.build_and_send_transaction")
    @patch("slash_collateral.load_contract_abi")
    def test_slash_collateral_tx_failure(
        self,
        mock_load_abi,
        mock_build_tx,
        mock_wait_receipt,
        mock_md5_checksum,
    ):
        # Arrange
        mock_w3 = MagicMock()
        mock_account = MagicMock()
        contract_mock = MagicMock()
        mock_w3.eth.contract.return_value = contract_mock
        contract_mock.functions.slashCollateral.return_value = MagicMock()

        mock_md5_checksum.return_value = "b" * 32
        mock_tx_hash = "0xdead"
        mock_build_tx.return_value = mock_tx_hash

        # Simulate failed transaction
        mock_wait_receipt.return_value = {"status": 0}

        # Act & Assert
        with self.assertRaises(SlashCollateralError):
            slash_collateral(
                mock_w3,
                mock_account,
                "0xMiner",
                2.0,
                "0xCollateral",
                "https://example.com",
                "uuid-456"
            )


if __name__ == "__main__":
    unittest.main()
