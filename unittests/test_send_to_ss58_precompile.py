import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
from scripts.send_to_ss58_precompile import send_tao_to_ss58


class TestSendTaoToSS58(unittest.TestCase):

    @patch("send_tao_to_ss58.ss58_to_pubkey")
    @patch("send_tao_to_ss58.wait_for_receipt")
    @patch("send_tao_to_ss58.build_and_send_transaction")
    def test_send_tao_success(
        self, mock_build_tx, mock_wait_receipt, mock_ss58_to_pubkey
    ):
        # Arrange
        mock_w3 = MagicMock()
        mock_contract = MagicMock()
        mock_transfer_fn = MagicMock()

        mock_pubkey = b"\x12" * 32
        mock_ss58_to_pubkey.return_value = mock_pubkey

        mock_w3.eth.contract.return_value.functions.transfer.return_value = mock_transfer_fn
        mock_w3.eth.contract.return_value = mock_contract

        mock_account = MagicMock()
        mock_account.address = "0x123"

        mock_tx_hash = "0xabc"
        mock_build_tx.return_value = mock_tx_hash

        expected_receipt = {
            "status": 1,
            "gasUsed": 21000
        }
        mock_wait_receipt.return_value = expected_receipt

        # Act
        receipt = send_tao_to_ss58(
            w3=mock_w3,
            sender_account=mock_account,
            recipient_ss58="5F3sa2TJcP5EUXyz",
            amount_wei=1_000_000_000_000_000_000
        )

        # Assert
        self.assertEqual(receipt["status"], 1)
        self.assertEqual(receipt["gasUsed"], 21000)
        mock_ss58_to_pubkey.assert_called_once()
        mock_build_tx.assert_called_once_with(
            mock_w3,
            mock_transfer_fn,
            mock_account,
            value=1_000_000_000_000_000_000
        )
        mock_wait_receipt.assert_called_once_with(mock_w3, mock_tx_hash)


if __name__ == "__main__":
    unittest.main()
