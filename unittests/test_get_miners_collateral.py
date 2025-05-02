import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from scripts.get_miners_collateral import get_miner_collateral
from web3 import Web3

class TestGetMinersCollateral(unittest.TestCase):
    @patch('scripts.get_miners_collateral.load_contract_abi')
    @patch('scripts.get_miners_collateral.Web3')
    def test_get_miner_collateral_success(self, MockWeb3, mock_load_abi):
        # Mock Web3 and contract
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.functions.collaterals.return_value.call.return_value = Web3.to_wei(1, 'ether')

        # Test successful retrieval of miner collateral
        collateral = get_miner_collateral(mock_w3, '0x' + '1' * 40, '0x' + '2' * 40)
        self.assertEqual(collateral, Web3.to_wei(1, 'ether'))

    @patch('scripts.get_miners_collateral.load_contract_abi')
    @patch('scripts.get_miners_collateral.Web3')
    def test_get_miner_collateral_failure(self, MockWeb3, mock_load_abi):
        # Mock Web3 and contract
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # Mock call to raise an exception
        mock_contract.functions.collaterals.return_value.call.side_effect = Exception('Blockchain query failed')

        # Test failure in retrieving miner collateral
        with self.assertRaises(Exception):
            get_miner_collateral(mock_w3, '0x' + '1' * 40, '0x' + '2' * 40)

if __name__ == '__main__':
    unittest.main() 