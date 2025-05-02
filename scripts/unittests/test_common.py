import unittest
from unittest.mock import patch, MagicMock
from scripts.common import (
    load_contract_abi, get_web3_connection, get_account,
    validate_address_format, build_and_send_transaction,
    wait_for_receipt, calculate_md5_checksum, get_miner_collateral
)
from web3 import Web3
import os
import requests

class TestCommon(unittest.TestCase):
    @patch('scripts.common.pathlib.Path.read_text')
    def test_load_contract_abi_success(self, mock_read_text):
        # Mock reading ABI file
        mock_read_text.return_value = '[{"type": "function", "name": "test"}]'
        abi = load_contract_abi()
        self.assertIsInstance(abi, list)

    @patch('scripts.common.pathlib.Path.read_text')
    def test_load_contract_abi_failure(self, mock_read_text):
        # Mock reading ABI file with invalid content
        mock_read_text.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            load_contract_abi()

    @patch.dict(os.environ, {'RPC_URL': 'http://localhost:8545'})
    @patch('scripts.common.Web3')
    def test_get_web3_connection_success(self, MockWeb3):
        # Mock successful connection
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_w3.is_connected.return_value = True
        w3 = get_web3_connection()
        self.assertTrue(w3.is_connected())

    @patch.dict(os.environ, {}, clear=True)
    def test_get_web3_connection_no_url(self):
        # Test with no RPC_URL set
        with self.assertRaises(KeyError):
            get_web3_connection()

    @patch.dict(os.environ, {'PRIVATE_KEY': '0x' + '1' * 64})
    @patch('scripts.common.Account')
    def test_get_account_success(self, MockAccount):
        # Mock successful account retrieval
        mock_account = MagicMock()
        MockAccount.from_key.return_value = mock_account
        account = get_account()
        self.assertEqual(account, mock_account)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_account_no_key(self):
        # Test with no PRIVATE_KEY set
        with self.assertRaises(KeyError):
            get_account()

    def test_validate_address_format_valid(self):
        # Test with a valid Ethereum address
        valid_address = '0x' + '1' * 40
        validate_address_format(valid_address)

    def test_validate_address_format_invalid(self):
        # Test with an invalid Ethereum address
        invalid_address = '0x' + '1' * 39
        with self.assertRaises(ValueError):
            validate_address_format(invalid_address)

    @patch('scripts.common.Web3')
    def test_build_and_send_transaction_success(self, MockWeb3):
        # Mock transaction building and sending
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_account = MagicMock()
        mock_function_call = MagicMock()
        mock_function_call.build_transaction.return_value = {}
        mock_w3.eth.account.sign_transaction.return_value.raw_transaction = b'tx'
        mock_w3.eth.send_raw_transaction.return_value = b'tx_hash'

        tx_hash = build_and_send_transaction(mock_w3, mock_function_call, mock_account)
        self.assertEqual(tx_hash, b'tx_hash')

    @patch('scripts.common.requests.get')
    def test_calculate_md5_checksum_success(self, mock_get):
        # Mock successful URL content fetching
        mock_response = MagicMock()
        mock_response.content = b'content'
        mock_get.return_value = mock_response
        checksum = calculate_md5_checksum('http://example.com')
        self.assertEqual(checksum, '9a0364b9e99bb480dd25e1f0284c8555')

    @patch('scripts.common.requests.get')
    def test_calculate_md5_checksum_failure(self, mock_get):
        # Mock URL fetching failure
        mock_get.side_effect = requests.exceptions.RequestException
        with self.assertRaises(requests.exceptions.RequestException):
            calculate_md5_checksum('http://example.com')

    @patch('scripts.common.load_contract_abi')
    @patch('scripts.common.Web3')
    def test_get_miner_collateral_success(self, MockWeb3, mock_load_abi):
        # Mock successful collateral retrieval
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.functions.collaterals.return_value.call.return_value = Web3.to_wei(1, 'ether')

        collateral = get_miner_collateral(mock_w3, '0x' + '1' * 40, '0x' + '2' * 40)
        self.assertEqual(collateral, Web3.to_wei(1, 'ether'))

if __name__ == '__main__':
    unittest.main() 