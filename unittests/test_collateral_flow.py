import sys
import os
import time
import subprocess
import unittest
from eth_account import Account
from web3 import Web3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.address_conversion import h160_to_ss58

class TestCollateralContractLifecycle(unittest.TestCase):
    def setUp(self):
        # Use the local RPC URL here
        self.RPC_URL = "http://127.0.0.1:9945"
        self.w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.assertTrue(self.w3.is_connected(), "Cannot connect to local Bittensor RPC")
        print("Connected to local Bittensor RPC")

    def test_lifecycle(self):
        # === Step 1: Create Validator Account ===
        # validator = Account.create("extra entropy collateral contract ComputeHorde")
        # validator_address = validator.address
        # validator_key = validator.key.hex()
        # validator_ss58 = h160_to_ss58(validator_address)
        # print("Validator Address:", validator_address)
        # print("Validator Key:", validator_key)


        # # === Step 2: Create Miner Account ===
        # miner = Account.create("extra entropy MINER ComputeHorde")
        # miner_address = miner.address
        # miner_key = miner.key.hex()
        # miner_ss58 = h160_to_ss58(miner_address)

        # print("Miner Address:", miner_address)
        # print("Miner Key:", miner_key)
        # Validator Address: 0x94C54725D6c8500aFf59716F33EdE6AA1FaD86CF
        # Validator Key: 618e740bdba177da3624f0fd16a6fff1eed21c8b11c7b2d232ea7f71d88bc172
        # Miner Address: 0x6b21765A50CfacE104333F7eB0731aB0F002B6d7
        # Miner Key: 0ced2debe3d770b4405bb673b3d05836a3d1c4ad1ce14f744a5af52ea2202924
        validator_address = "0x94C54725D6c8500aFf59716F33EdE6AA1FaD86CF"
        validator_key = "618e740bdba177da3624f0fd16a6fff1eed21c8b11c7b2d232ea7f71d88bc172"
        miner_address = "0x6b21765A50CfacE104333F7eB0731aB0F002B6d7"
        miner_key = "0ced2debe3d770b4405bb673b3d05836a3d1c4ad1ce14f744a5af52ea2202924"
        validator_ss58 = h160_to_ss58(validator_address)
        miner_ss58 = h160_to_ss58(miner_address)
        print("Validator Address:", validator_address)
        print("Validator Key:", validator_key)
        print("Miner Address:", miner_address)
        print("Miner Key:", miner_key)
        print("Validator SS58:", validator_ss58)
        print("Miner SS58:", miner_ss58)

        
        balance = self.w3.eth.get_balance(validator_address)
        print("Validator Balance:", self.w3.from_wei(balance, 'ether'))
        # === Step 3: Fund Validator ===
        # subprocess.run(["btcli", "w", "transfer", "--network", "local", "--dest", validator_ss58, "--amount", "1"])
        time.sleep(3)

        # === Step 4: Deploy Contract ===
        os.environ["RPC_URL"] = self.RPC_URL  # Setting the RPC URL for deployment
        os.environ["DEPLOYER_PRIVATE_KEY"] = validator_key  # Setting the deployer's private key
        
        # Define the arguments for deployment
        netuid = 1  # Example netuid
        trustee_address = validator_address
        min_collateral_increase = 1000000000000000  # Example amount in wei
        deny_timeout = 120  # Example deny timeout in seconds

        # Validate the required environment variables
        if not os.environ.get("RPC_URL"):
            raise ValueError("RPC_URL environment variable not set.")
        if not os.environ.get("DEPLOYER_PRIVATE_KEY"):
            raise ValueError("DEPLOYER_PRIVATE_KEY environment variable not set.")
        
        # Deploy using the `forge` command directly
        deploy_result = subprocess.run(
            [
                "forge", "create", "src/Collateral.sol:Collateral",
                "--broadcast",
                "--rpc-url", self.RPC_URL,
                "--private-key", validator_key,
                "--constructor-args", str(netuid), trustee_address, str(min_collateral_increase), str(deny_timeout)
            ],
            capture_output=True, text=True
        )
        self.assertIn("Deployed to:", deploy_result.stdout, deploy_result.stderr)
        contract_line = [line for line in deploy_result.stdout.splitlines() if "Deployed to:" in line][0]
        contract_address = contract_line.split(": ")[-1]
        self.assertTrue(Web3.is_address(contract_address))
        os.environ["CONTRACT_ADDRESS"] = contract_address

        # === Step 5: Fund Miner ===
        subprocess.run(["btcli", "w", "transfer", "--network", "local", "--dest", miner_ss58, "--amount", "0.5"])
        time.sleep(3)
        self.assertGreater(self.w3.eth.get_balance(miner_address), 0, "Miner not funded")

        # === Step 6: Miner Deposits Collateral ===
        os.environ["PRIVATE_KEY"] = miner_key
        subprocess.run(["python", "deposit_collateral.py", contract_address, "0.01", validator_address])
        time.sleep(3)

        # === Step 7: Verify Collateral ===
        check = subprocess.run(["python", "get_miners_collateral.py", contract_address, miner_address],
                               capture_output=True, text=True)
        self.assertIn("0.01", check.stdout, f"Deposit failed: {check.stdout}")

        # === Step 8: Validator Slashes Miner ===
        os.environ["PRIVATE_KEY"] = validator_key
        subprocess.run(["python", "slash_collateral.py", contract_address, miner_address, "0.0001", "slashit"])
        time.sleep(1)

        # === Step 9: Miner Reclaims Collateral ===
        os.environ["PRIVATE_KEY"] = miner_key
        subprocess.run(["python", "reclaim_collateral.py", contract_address, "0.003", "please gimme money back"])
        time.sleep(3)

        # === Step 10: Validator Checks Requests ===
        latest_block = self.w3.eth.block_number
        subprocess.run([
            "python", "get_reclaim_requests.py", contract_address,
            str(latest_block - 10), str(latest_block + 10)
        ])

        # === Step 11: Validator Denies Request 1, Finalizes Request 2 ===
        os.environ["PRIVATE_KEY"] = validator_key
        subprocess.run(["python", "deny_request.py", contract_address, "1", "no, i will not"])
        subprocess.run(["python", "finalize_reclaim.py", contract_address, "2"])
        time.sleep(1)

        # === Step 12: Final Collateral Check ===
        result = subprocess.run(["python", "get_miners_collateral.py", contract_address, miner_address],
                                capture_output=True, text=True)
        print("[FINAL COLLATERAL]:", result.stdout.strip())

        # === Step 13: Send to SS58 Precompile ===
        subprocess.run([
            "python", "send_to_ss58_precompile.py",
            "5CoZwx53nNzfnDLqxYjntvggyPw3Xee1r9b68HFw1N6UEa1X",
            "490000000000000000"
        ])

        print("✅ Contract lifecycle test completed successfully.")


if __name__ == "__main__":
    unittest.main()
