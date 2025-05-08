import os
import unittest
from web3 import Web3
from scripts.address_conversion import h160_to_ss58
import uuid
import subprocess
import time


def uuid_to_bytes16(uuid_str):
    u = uuid.UUID(uuid_str)
    return "0x" + u.bytes.hex()


class TestExistingAccounts(unittest.TestCase):
    def setUp(self):
        self.RPC_URL = "https://test.chain.opentensor.ai"
        self.w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.assertTrue(self.w3.is_connected(), "Cannot connect to RPC")
        print("Connected to RPC")

        os.environ["RPC_URL"] = self.RPC_URL
        self.env = os.environ.copy()

    def test_existing_accounts_flow(self):
        # Use existing accounts
        validator_address = "0xE1A07A44ac6f8423bA3b734F0cAfC6F87fd385Fc"
        validator_key = "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3"
        miner_address = "0x19F71e76B34A8Dc01944Cf3B76478B45DE05B75b"
        miner_key = "259e0eded00353f71eb6be89d8749ad12bf693cbd8aeb6b80cd3a343c0dc8faf"

        validator_ss58 = h160_to_ss58(validator_address)
        miner_ss58 = h160_to_ss58(miner_address)

        print("Validator SS58:", validator_ss58)
        print("Miner SS58:", miner_ss58)

        # Check balances
        validator_balance = self.w3.eth.get_balance(validator_address)
        miner_balance = self.w3.eth.get_balance(miner_address)

        print("Validator Balance:", self.w3.from_wei(validator_balance, 'ether'))
        print("Miner Balance:", self.w3.from_wei(miner_balance, 'ether'))

        # Use existing contract address
        print("Deploying contract with forge...")
        netuid = 1  # Example netuid
        min_collateral_increase = 10  # Example amount in wei
        deny_timeout = 120  # Example deny timeout in seconds

        deploy_result = subprocess.run(
            [
                "forge", "create", "src/Collateral.sol:Collateral",
                "--broadcast",
                "--rpc-url", self.RPC_URL,
                "--private-key", miner_key,
                "--constructor-args", str(netuid), str(min_collateral_increase), str(deny_timeout)
            ],
            capture_output=True, text=True
        )
        self.assertIn("Deployed to:", deploy_result.stdout, deploy_result.stderr)
        contract_line = [line for line in deploy_result.stdout.splitlines() if "Deployed to:" in line][0]
        contract_address = contract_line.split(": ")[-1]
        print("Using Contract Address:", contract_address)

        # Miner deposits collateral
        self.env["PRIVATE_KEY"] = miner_key
        deposit_tasks = [
            "3a5ce92a-a066-45f7-b07d-58b3b7986464",
            "72a1d228-3c8c-45cb-8b84-980071592589",
            "15c2ff27-0a4d-4987-bbc9-fa009ef9f7d2"
        ]

        for uuid_str in deposit_tasks:
            executor_uuid = uuid_to_bytes16(uuid_str)
            print(f"Depositing collateral for executor UUID: {executor_uuid}")
            result = subprocess.run(
                [
                    "python", "scripts/deposit_collateral.py",
                    contract_address, "0.0001", validator_address, executor_uuid
                ],
                env=self.env, capture_output=True, text=True
            )
            print(result.stdout.strip())

        # Verify miner's collateral
        result = subprocess.run(
            ["python", "scripts/get_miners_collateral.py", contract_address, miner_address],
            env=self.env, capture_output=True, text=True
        )
        print("Miner Collateral:", result.stdout.strip())
        self.assertEqual(result.returncode, 0, "Failed to retrieve miner collateral")



if __name__ == "__main__":
    # If running via unittest discovery, custom flags will not be recognized.
    unittest.main()
