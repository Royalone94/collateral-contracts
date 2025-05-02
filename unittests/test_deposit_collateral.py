import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import MagicMock, patch
from scripts.deposit_collateral import check_minimum_collateral, verify_trustee, deposit_collateral, DepositCollateralError
from web3 import Web3

class TestDepositCollateral(unittest.TestCase):
    @patch('scripts.deposit_collateral.Web3')
    def test_check_minimum_collateral_valid(self, MockWeb3):
        # Mock contract with a minimum collateral requirement
        contract = MagicMock()
        contract.functions.MIN_COLLATERAL_INCREASE.return_value.call.return_value = Web3.to_wei(1, 'ether')
        
        # Test with a valid amount
        amount_wei = Web3.to_wei(2, 'ether')
        min_collateral = check_minimum_collateral(contract, amount_wei)
        self.assertEqual(min_collateral, Web3.to_wei(1, 'ether'))

    @patch('scripts.deposit_collateral.Web3')
    def test_check_minimum_collateral_invalid(self, MockWeb3):
        # Mock contract with a minimum collateral requirement
        contract = MagicMock()
        contract.functions.MIN_COLLATERAL_INCREASE.return_value.call.return_value = Web3.to_wei(1, 'ether')
        
        # Test with an invalid amount
        amount_wei = Web3.to_wei(0.5, 'ether')
        with self.assertRaises(ValueError):
            check_minimum_collateral(contract, amount_wei)

    @patch('scripts.deposit_collateral.Web3')
    def test_verify_trustee_valid(self, MockWeb3):
        # Mock contract with a trustee address
        contract = MagicMock()
        contract.functions.TRUSTEE.return_value.call.return_value = '0x1234567890abcdef1234567890abcdef12345678'
        
        # Test with a matching trustee address
        verify_trustee(contract, '0x1234567890abcdef1234567890abcdef12345678')

    @patch('scripts.deposit_collateral.Web3')
    def test_verify_trustee_invalid(self, MockWeb3):
        # Mock contract with a trustee address
        contract = MagicMock()
        contract.functions.TRUSTEE.return_value.call.return_value = '0x1234567890abcdef1234567890abcdef12345678'
        
        # Test with a non-matching trustee address
        with self.assertRaises(ValueError):
            verify_trustee(contract, '0xabcdefabcdefabcdefabcdefabcdefabcdef')

    @patch('scripts.deposit_collateral.build_and_send_transaction')
    @patch('scripts.deposit_collateral.wait_for_receipt')
    @patch('scripts.deposit_collateral.get_web3_connection')
    @patch('scripts.deposit_collateral.get_account')
    @patch('scripts.deposit_collateral.load_contract_abi')
    def test_deposit_collateral_success(self, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Deposit.return_value.process_receipt.return_value = [{'args': {'account': '0x123', 'amount': Web3.to_wei(1, 'ether')}}]
        mock_wait_for_receipt.return_value = {'status': 1, 'transactionHash': b'\x00', 'blockNumber': 1}

        # Test successful deposit
        deposit_event, receipt = deposit_collateral(
            w3=mock_w3,
            account=mock_account,
            amount_tao=1,
            contract_address='0x1234567890abcdef1234567890abcdef12345678',
            trustee_address='0x1234567890abcdef1234567890abcdef12345678',
            validator='0x1234567890abcdef1234567890abcdef12345678',
            executor_uuid='uuid'
        )
        self.assertEqual(deposit_event['args']['account'], '0x123')
        self.assertEqual(receipt['status'], 1)

    @patch('scripts.deposit_collateral.build_and_send_transaction')
    @patch('scripts.deposit_collateral.wait_for_receipt')
    @patch('scripts.deposit_collateral.get_web3_connection')
    @patch('scripts.deposit_collateral.get_account')
    @patch('scripts.deposit_collateral.load_contract_abi')
    def test_deposit_collateral_failure(self, mock_load_abi, mock_get_account, mock_get_w3, mock_wait_for_receipt, mock_build_tx):
        # Mock Web3, account, and contract
        mock_w3 = MagicMock()
        mock_get_w3.return_value = mock_w3
        mock_account = MagicMock()
        mock_get_account.return_value = mock_account
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.events.Deposit.return_value.process_receipt.return_value = [{'args': {'account': '0x123', 'amount': Web3.to_wei(1, 'ether')}}]
        mock_wait_for_receipt.return_value = {'status': 0, 'transactionHash': b'\x00', 'blockNumber': 1}

        # Test transaction failure
        with self.assertRaises(DepositCollateralError):
            deposit_collateral(
                w3=mock_w3,
                account=mock_account,
                amount_tao=1,
                contract_address='0x1234567890abcdef1234567890abcdef12345678',
                trustee_address='0x1234567890abcdef1234567890abcdef12345678',
                validator='0x1234567890abcdef1234567890abcdef12345678',
                executor_uuid='uuid'
            )

if __name__ == '__main__':
    unittest.main() 