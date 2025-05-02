import unittest
from unittest.mock import patch, MagicMock
from scripts.finalize_reclaim import finalize_reclaim, FinalizeReclaimError
from web3 import Web3

class TestFinalizeReclaim(unittest.TestCase):
    @patch('scripts.finalize_reclaim.build_and_send_transaction')
    @patch('scripts.finalize_reclaim.wait_for_receipt')
    @patch('scripts.finalize_reclaim.get_web3_connection')
    @patch('scripts.finalize_reclaim.get_account')
    @patch('scripts.finalize_reclaim.load_contract_abi')
    def test_finalize_reclaim_success(self, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Reclaimed.return_value.process_receipt.return_value = [{'args': {'reclaimRequestId': 1, 'account': '0x123', 'amount': Web3.to_wei(1, 'ether')}}]
        mock_wait_for_receipt.return_value = {'status': 1, 'transactionHash': b'\x00', 'blockNumber': 1}

        # Test successful finalization
        reclaim_event, receipt = finalize_reclaim(
            w3=mock_w3,
            account=mock_account,
            reclaim_request_id=1,
            contract_address='0x1234567890abcdef1234567890abcdef12345678'
        )
        self.assertEqual(reclaim_event['args']['reclaimRequestId'], 1)
        self.assertEqual(receipt['status'], 1)

    @patch('scripts.finalize_reclaim.build_and_send_transaction')
    @patch('scripts.finalize_reclaim.wait_for_receipt')
    @patch('scripts.finalize_reclaim.get_web3_connection')
    @patch('scripts.finalize_reclaim.get_account')
    @patch('scripts.finalize_reclaim.load_contract_abi')
    def test_finalize_reclaim_failure(self, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Reclaimed.return_value.process_receipt.return_value = [{'args': {'reclaimRequestId': 1, 'account': '0x123', 'amount': Web3.to_wei(1, 'ether')}}]
        mock_wait_for_receipt.return_value = {'status': 0, 'transactionHash': b'\x00', 'blockNumber': 1}

        # Test transaction failure
        with self.assertRaises(FinalizeReclaimError):
            finalize_reclaim(
                w3=mock_w3,
                account=mock_account,
                reclaim_request_id=1,
                contract_address='0x1234567890abcdef1234567890abcdef12345678'
            )

if __name__ == '__main__':
    unittest.main() 