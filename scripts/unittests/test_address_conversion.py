import unittest
from scripts.address_conversion import ss58_to_pubkey, h160_to_ss58
from substrateinterface import Keypair

class TestAddressConversion(unittest.TestCase):
    def test_ss58_to_pubkey_valid(self):
        # Test with a valid SS58 address
        ss58_address = '5F3sa2TJAWMqDhXG6jhV4N8ko9rL7P6tU5v9vUo4h8uXRAxY'
        expected_pubkey = Keypair(ss58_address=ss58_address).public_key
        self.assertEqual(ss58_to_pubkey(ss58_address), expected_pubkey)

    def test_ss58_to_pubkey_invalid(self):
        # Test with an invalid SS58 address
        with self.assertRaises(ValueError):
            ss58_to_pubkey('invalid_address')

    def test_h160_to_ss58_valid(self):
        # Test with a valid H160 address
        h160_address = '0x5abfec25f74cd88437631a7731906932776356f9'
        ss58_address = h160_to_ss58(h160_address)
        self.assertTrue(ss58_address.startswith('5'))  # Check if it returns a valid SS58 address

    def test_h160_to_ss58_invalid(self):
        # Test with an invalid H160 address
        with self.assertRaises(ValueError):
            h160_to_ss58('invalid_address')

    def test_h160_to_ss58_different_format(self):
        # Test with a different SS58 format
        h160_address = '0x5abfec25f74cd88437631a7731906932776356f9'
        ss58_address = h160_to_ss58(h160_address, ss58_format=0)
        self.assertTrue(ss58_address.startswith('1'))  # Check if it returns a valid SS58 address

if __name__ == '__main__':
    unittest.main() 