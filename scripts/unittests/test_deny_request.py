import unittest
from unittest.mock import patch, MagicMock
from scripts.deny_request import deny_reclaim_request, DenyReclaimRequestError
from web3 import Web3

class TestDenyRequest(unittest.TestCase):
    @patch('scripts.deny_request.build_and_send_transaction')
    @patch('scripts.deny_request.wait_for_receipt')
    @patch('scripts.deny_request.get_web3_connection')
    @patch('scripts.deny_request.get_account')
    @patch('scripts.deny_request.load_contract_abi')
    @patch('scripts.deny_request.calculate_md5_checksum')
    def test_deny_reclaim_request_success(self, mock_md5, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Denied.return_value.process_receipt.return_value = [{'args': {'reclaimRequestId': 1, 'url': 'http://example.com', 'urlContentMd5Checksum': b'\x00'}}]
        mock_wait_for_receipt.return_value = {'status': 1, 'transactionHash': b'\x00', 'blockNumber': 1}
        mock_md5.return_value = '0' * 32

        # Test successful denial
        deny_event, receipt = deny_reclaim_request(
            w3=mock_w3,
            account=mock_account,
            reclaim_request_id=1,
            url='http://example.com',
            contract_address='0x1234567890abcdef1234567890abcdef12345678'
        )
        self.assertEqual(deny_event['args']['reclaimRequestId'], 1)
        self.assertEqual(receipt['status'], 1)

    @patch('scripts.deny_request.build_and_send_transaction')
    @patch('scripts.deny_request.wait_for_receipt')
    @patch('scripts.deny_request.get_web3_connection')
    @patch('scripts.deny_request.get_account')
    @patch('scripts.deny_request.load_contract_abi')
    @patch('scripts.deny_request.calculate_md5_checksum')
    def test_deny_reclaim_request_failure(self, mock_md5, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Denied.return_value.process_receipt.return_value = [{'args': {'reclaimRequestId': 1, 'url': 'http://example.com', 'urlContentMd5Checksum': b'\x00'}}]
        mock_wait_for_receipt.return_value = {'status': 0, 'transactionHash': b'\x00', 'blockNumber': 1}
        mock_md5.return_value = '0' * 32

        # Test transaction failure
        with self.assertRaises(DenyReclaimRequestError):
            deny_reclaim_request(
                w3=mock_w3,
                account=mock_account,
                reclaim_request_id=1,
                url='http://example.com',
                contract_address='0x1234567890abcdef1234567890abcdef12345678'
            )

if __name__ == '__main__':
    unittest.main() 