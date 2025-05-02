import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from scripts.get_collaterals import get_deposit_events, DepositEvent
from web3 import Web3

class TestGetCollaterals(unittest.TestCase):
    @patch('scripts.get_collaterals.load_contract_abi')
    @patch('scripts.get_collaterals.Web3')
    def test_get_deposit_events_success(self, MockWeb3, mock_load_abi):
        # Mock Web3 and contract
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # Mock logs and event processing
        mock_log = {
            "topics": [b'\x00', b'\x00' * 32, b'\x00' * 32],
            "blockNumber": 1,
            "transactionHash": b'\x00' * 32
        }
        mock_contract.events.Deposit.return_value.process_log.return_value = {
            'args': {'amount': Web3.to_wei(1, 'ether')}
        }
        mock_w3.eth.get_logs.return_value = [mock_log]

        # Test successful retrieval of deposit events
        events = get_deposit_events(mock_w3, '0x' + '1' * 40, 0, 10)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], DepositEvent)

    @patch('scripts.get_collaterals.load_contract_abi')
    @patch('scripts.get_collaterals.Web3')
    def test_get_deposit_events_failure(self, MockWeb3, mock_load_abi):
        # Mock Web3 and contract
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        # Mock get_logs to raise an exception
        mock_w3.eth.get_logs.side_effect = Exception('Blockchain query failed')

        # Test failure in retrieving deposit events
        with self.assertRaises(Exception):
            get_deposit_events(mock_w3, '0x' + '1' * 40, 0, 10)

if __name__ == '__main__':
    unittest.main() 