import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from scripts.verify_contract import verify_contract


class TestVerifyContract(unittest.TestCase):

    @patch("verify_contract.deploy_on_devnet_and_get_bytecode")
    @patch("verify_contract.get_deployed_bytecode")
    @patch("verify_contract.get_contract_config")
    @patch("verify_contract.get_web3_connection")
    def test_verify_contract_success(
        self,
        mock_get_web3,
        mock_get_config,
        mock_get_deployed_bytecode,
        mock_deploy_devnet_bytecode,
    ):
        # Arrange
        mock_get_web3.return_value = MagicMock()
        mock_get_config.return_value = (42, "0x1234567890abcdef1234567890abcdef12345678", 100, 200)
        mock_get_deployed_bytecode.return_value = "0xdeadbeef"
        mock_deploy_devnet_bytecode.return_value = "0xdeadbeef"

        # Act
        result = verify_contract(
            contract_address="0xAbC1230000000000000000000000000000000000",
            expected_trustee="0x1234567890abcdef1234567890abcdef12345678",
            expected_netuid=42,
        )

        # Assert
        self.assertTrue(result)

    @patch("verify_contract.deploy_on_devnet_and_get_bytecode")
    @patch("verify_contract.get_deployed_bytecode")
    @patch("verify_contract.get_contract_config")
    @patch("verify_contract.get_web3_connection")
    def test_verify_contract_bytecode_mismatch(
        self,
        mock_get_web3,
        mock_get_config,
        mock_get_deployed_bytecode,
        mock_deploy_devnet_bytecode,
    ):
        mock_get_web3.return_value = MagicMock()
        mock_get_config.return_value = (42, "0x1234567890abcdef1234567890abcdef12345678", 100, 200)
        mock_get_deployed_bytecode.return_value = "0xdeadbeef"
        mock_deploy_devnet_bytecode.return_value = "0xBADBEEF"

        result = verify_contract(
            contract_address="0xAbC1230000000000000000000000000000000000",
            expected_trustee="0x1234567890abcdef1234567890abcdef12345678",
            expected_netuid=42,
        )

        self.assertFalse(result)

    @patch("verify_contract.get_contract_config")
    @patch("verify_contract.get_web3_connection")
    def test_verify_contract_netuid_mismatch(self, mock_get_web3, mock_get_config):
        mock_get_web3.return_value = MagicMock()
        mock_get_config.return_value = (99, "0x1234567890abcdef1234567890abcdef12345678", 100, 200)

        result = verify_contract(
            contract_address="0xAbC1230000000000000000000000000000000000",
            expected_trustee="0x1234567890abcdef1234567890abcdef12345678",
            expected_netuid=42,
        )

        self.assertFalse(result)

    @patch("verify_contract.get_contract_config")
    @patch("verify_contract.get_web3_connection")
    def test_verify_contract_trustee_mismatch(self, mock_get_web3, mock_get_config):
        mock_get_web3.return_value = MagicMock()
        mock_get_config.return_value = (42, "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", 100, 200)

        result = verify_contract(
            contract_address="0xAbC1230000000000000000000000000000000000",
            expected_trustee="0x1234567890abcdef1234567890abcdef12345678",
            expected_netuid=42,
        )

        self.assertFalse(result)

    @patch("verify_contract.get_contract_config", side_effect=Exception("Connection failed"))
    @patch("verify_contract.get_web3_connection")
    def test_verify_contract_exception_handling(self, mock_get_web3, mock_get_config):
        mock_get_web3.return_value = MagicMock()
        result = verify_contract(
            contract_address="0xAbC1230000000000000000000000000000000000",
            expected_trustee=None,
            expected_netuid=None,
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
