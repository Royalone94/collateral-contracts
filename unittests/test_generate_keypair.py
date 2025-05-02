import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, mock_open, MagicMock
from scripts.generate_keypair import generate_and_save_keypair
import json
import os

class TestGenerateKeypair(unittest.TestCase):
    @patch('scripts.generate_keypair.Account.create')
    @patch('scripts.generate_keypair.open', new_callable=mock_open)
    @patch('scripts.generate_keypair.os.makedirs')
    def test_generate_and_save_keypair_success(self, mock_makedirs, mock_open, mock_create):
        # Mock account creation
        mock_account = MagicMock()
        mock_account.address = '0x123'
        mock_account.key = b'\x01' * 32
        mock_create.return_value = mock_account

        # Mock private key and public key
        mock_private_key = MagicMock()
        mock_private_key.public_key.to_hex.return_value = '0x456'
        mock_private_key.to_hex.return_value = '0x789'

        with patch('scripts.generate_keypair.keys.PrivateKey', return_value=mock_private_key):
            keypair_data = generate_and_save_keypair('path/to/keypair.json')

        # Check if the file was written with correct data
        mock_open().write.assert_called_once_with(json.dumps({
            "address": '0x123',
            "private_key": '0x789',
            "public_key": '0x456'
        }, indent=2))

        # Check if the returned data is correct
        self.assertEqual(keypair_data['address'], '0x123')
        self.assertEqual(keypair_data['private_key'], '0x789')
        self.assertEqual(keypair_data['public_key'], '0x456')

    @patch('scripts.generate_keypair.open', new_callable=mock_open)
    @patch('scripts.generate_keypair.os.makedirs')
    def test_generate_and_save_keypair_file_error(self, mock_makedirs, mock_open):
        # Mock file open to raise an IOError
        mock_open.side_effect = IOError

        with self.assertRaises(IOError):
            generate_and_save_keypair('path/to/keypair.json')

if __name__ == '__main__':
    unittest.main() 