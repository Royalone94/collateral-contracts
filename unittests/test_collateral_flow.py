import sys
import os
import time
import subprocess
import unittest
from eth_account import Account
from web3 import Web3
import uuid
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.address_conversion import h160_to_ss58

def uuid_to_bytes16(uuid_str):
    u = uuid.UUID(uuid_str)
    return "0x" + u.bytes.hex()

def get_transferrable_balance(w3: Web3, sender: str, recipient: str):
    # Build a dummy transaction to estimate gas
    nonce = w3.eth.get_transaction_count(sender)

    tx = {
        'from': sender,
        'to': recipient,
        'value': 1,
        'nonce': nonce  # include nonce for accuracy
    }

    try:
        gas_estimate = w3.eth.estimate_gas(tx)
    except Exception as e:
        print(f"Gas estimation failed: {e}")
        gas_estimate = 21000  # Fallback to standard ETH transfer gas

    try:
        # For EIP-1559 networks
        fee_history = w3.eth.fee_history(1, 'latest', [50])
        base_fee = fee_history['baseFeePerGas'][-1]
        priority_fee = w3.eth.max_priority_fee
        gas_price = base_fee + priority_fee
    except Exception:
        # For legacy networks
        gas_price = w3.eth.gas_price

    print(f"Gas estimate: {gas_estimate}, Gas price: {gas_price}")
    gas_cost = gas_estimate * gas_price
    balance = w3.eth.get_balance(sender)
    buffer = Web3.to_wei(0.001, 'ether')
    transferrable = max(0, balance - gas_cost - buffer)  # Subtract a small buffer
    return transferrable
    
class TestCollateralContractLifecycle(unittest.TestCase):
    def setUp(self):
        # Use the local RPC URL here
        self.RPC_URL = "https://test.chain.opentensor.ai"
        self.w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.assertTrue(self.w3.is_connected(), "Cannot connect to Bittensor RPC")
        print("Connected to Bittensor RPC")

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
        # validator_address = "0x94C54725D6c8500aFf59716F33EdE6AA1FaD86CF"
        # validator_key = "618e740bdba177da3624f0fd16a6fff1eed21c8b11c7b2d232ea7f71d88bc172"
        # miner_address = "0x6b21765A50CfacE104333F7eB0731aB0F002B6d7"
        # miner_key = "0ced2debe3d770b4405bb673b3d05836a3d1c4ad1ce14f744a5af52ea2202924"
        # validator_ss58 = h160_to_ss58(validator_address)
        # miner_ss58 = h160_to_ss58(miner_address)
        # print("Validator Address:", validator_address)
        # print("Validator Key:", validator_key)
        # print("Miner Address:", miner_address)
        # print("Miner Key:", miner_key)
        # print("Validator SS58:", validator_ss58)
        # print("Miner SS58:", miner_ss58)

        
        # balance = self.w3.eth.get_balance(validator_address)
        # print("Validator Balance:", self.w3.from_wei(balance, 'ether'))
        # # === Step 3: Fund Validator ===
        # subprocess.run(["btcli", "w", "transfer", "--network", "test", "--dest", validator_ss58, "--amount", "0.5"])
        # time.sleep(3)

        # # === Step 4: Deploy Contract ===
        os.environ["RPC_URL"] = self.RPC_URL  # Setting the RPC URL for deployment
        # os.environ["DEPLOYER_PRIVATE_KEY"] = validator_key  # Setting the deployer's private key
        
        # # Define the arguments for deployment
        # netuid = 1  # Example netuid
        # trustee_address = validator_address
        # min_collateral_increase = 1000000000000000  # Example amount in wei
        # deny_timeout = 120  # Example deny timeout in seconds

        # # Validate the required environment variables
        # if not os.environ.get("RPC_URL"):
        #     raise ValueError("RPC_URL environment variable not set.")
        # if not os.environ.get("DEPLOYER_PRIVATE_KEY"):
        #     raise ValueError("DEPLOYER_PRIVATE_KEY environment variable not set.")
        
        # # Deploy using the `forge` command directly
        # deploy_result = subprocess.run(
        #     [
        #         "forge", "create", "src/Collateral.sol:Collateral",
        #         "--broadcast",
        #         "--rpc-url", self.RPC_URL,
        #         "--private-key", validator_key,
        #         "--constructor-args", str(netuid), trustee_address, str(min_collateral_increase), str(deny_timeout)
        #     ],
        #     capture_output=True, text=True
        # )
        # self.assertIn("Deployed to:", deploy_result.stdout, deploy_result.stderr)
        # contract_line = [line for line in deploy_result.stdout.splitlines() if "Deployed to:" in line][0]
        # contract_address = contract_line.split(": ")[-1]
        # print("Contract Address:", contract_address)
        # self.assertTrue(Web3.is_address(contract_address))
        # os.environ["CONTRACT_ADDRESS"] = contract_address

        # # === Step 5: Fund Miner ===
        # subprocess.run(["btcli", "w", "transfer", "--network", "test", "--dest", miner_ss58, "--amount", "0.5"])
        # time.sleep(3)
        # self.assertGreater(self.w3.eth.get_balance(miner_address), 0, "Miner not funded")
        env = os.environ.copy()
        validator_address = "0xF0f435fD02770E0628Ca899A9a4fee0A24d2dCfE"
        validator_key = "0e0a09fb4dc0799fa1d3fbdf1012cfc446839f643cccbbf637105550fdbd6be7"
        miner_address = "0xD2448e4B5C1bb68A5EF50687F12bd9dBFff8AeEc"
        miner_key = "5075fac9176884602301e5ca215d821f9a9c4ba5c6e69d0066faea32acea400c"
        validator_ss58 = h160_to_ss58(validator_address)
        miner_ss58 = h160_to_ss58(miner_address)
        print("Validator SS58:", validator_ss58)
        print("Miner SS58:", miner_ss58)
        
        contract_address = "0xD1fE39b5c584D9761E99DbCc5961484F2696F94f"
        # === Step 6: Miner Deposits Collateral ===
        env["PRIVATE_KEY"] = miner_key
        executor_uuid = "3a5ce92a-a066-45f7-b07d-58b3b7986464"
        executor_uuid = uuid_to_bytes16(executor_uuid)  # Convert UUID to bytes32

        print(f"UUID as bytes32: {executor_uuid}")

        print("Starting deposit collateral...")
        check = subprocess.run(["python", "scripts/deposit_collateral.py", contract_address, "0.01", validator_address, executor_uuid], capture_output=True, text=True, env=env)
        time.sleep(1)
        print(check.stdout.strip())
        self.assertIn("0.01", check.stdout, f"Deposit failed: {check.stdout}")

        # === Step 7: Verify Collateral ===
        check = subprocess.run(["python", "scripts/get_miners_collateral.py", contract_address, miner_address],
                               capture_output=True, text=True, env=env)
        time.sleep(2)

        print("[COLLATERAL]:", check.stdout.strip())
        print("Deposit collateral finished")

        print("Starting slash collateral...")
        # === Step 8: Validator Slashes Miner ===
        env["PRIVATE_KEY"] = validator_key
        subprocess.run(["python", "scripts/slash_collateral.py", contract_address, miner_address, "0.001", "slashit", executor_uuid], env=env)
        time.sleep(1)
        print("Slash collateral finished")

        # === Step 9: Miner Reclaims Collateral ===
        print("Starting reclaim collateral...")

        env["PRIVATE_KEY"] = miner_key
        result = subprocess.run(["python", "scripts/reclaim_collateral.py", contract_address, "0.003", "please gimme money back. this reclaim will be denied", executor_uuid], capture_output=True, text=True, env=env)
        time.sleep(1)
        print("Reclaim Result: ", result.stdout.strip())
        match = re.search(r"Reclaim ID:\s*(\d+)", result.stdout)
        if match:
            deny_reclaim_id = int(match.group(1))
            print("First Reclaim ID:", deny_reclaim_id)
        else:
            raise ValueError("Reclaim ID not found in the output.")

        reclaim_result = subprocess.run(["python", "scripts/reclaim_collateral.py", contract_address, "0.003", "please gimme money back. this reclaim will be finalized", executor_uuid], 
            capture_output=True, text=True, env=env)

        print("Reclaim Result: ", result.stdout.strip())
        time.sleep(1)

        match = re.search(r"Reclaim ID:\s*(\d+)", reclaim_result.stdout)
        if match:
            finalize_reclaim_id = int(match.group(1))
            print("Second Reclaim ID:", finalize_reclaim_id)
        else:
            raise ValueError("Reclaim ID not found in the output.")
        print("Reclaim collateral finished")
        
        # === Step 10: Validator Checks Requests ===
        latest_block = self.w3.eth.block_number
        print(f"All reclaim requests between these blocks: {latest_block - 10}, {latest_block + 10}")

        result = subprocess.run([
            "python", "scripts/get_reclaim_requests.py", contract_address,
            str(latest_block - 10), str(latest_block + 10)
        ], env=env)

        # === Step 11: Validator Denies Request 1, Finalizes Request 2 ===
        env["PRIVATE_KEY"] = validator_key
        print("Starting deny reclaim request")
        subprocess.run(["python", "scripts/deny_request.py", contract_address, str(deny_reclaim_id), "no, i will not"], env=env)
        time.sleep(1)

        print("Deny reclaim request finished")

        print("Starting finalize reclaim request")
        subprocess.run(["python", "scripts/finalize_reclaim.py", contract_address, str(finalize_reclaim_id)], env=env)
        time.sleep(1)

        print("Finalize reclaim request finished")

        env["PRIVATE_KEY"] = miner_key
        # === Step 12: Final Collateral Check ===
        result = subprocess.run(["python", "scripts/get_miners_collateral.py", contract_address, miner_address],
                                capture_output=True, text=True, env=env)
        time.sleep(1)
        print("[FINAL COLLATERAL]:", result.stdout.strip())

        print("Checking account balances before transfer...")
        print("Validator balance:", self.w3.from_wei(self.w3.eth.get_balance(validator_address), 'ether'))
        print("Miner balance:", self.w3.from_wei(self.w3.eth.get_balance(miner_address), 'ether'))

        celium_testnet_address = "5CoZwx53nNzfnDLqxYjntvggyPw3Xee1r9b68HFw1N6UEa1X"
        validator_transferrable = get_transferrable_balance(self.w3, validator_address, "0x0000000000000000000000000000000000000001")
        miner_transferrable = get_transferrable_balance(self.w3, miner_address, "0x0000000000000000000000000000000000000001")
        
        print("validator_transferrable:", validator_transferrable)
        print("miner_transferrable:", miner_transferrable)

        print("Validator transferrable balance:", self.w3.from_wei(validator_transferrable, 'ether'))
        print("Miner transferrable balance:", self.w3.from_wei(miner_transferrable, 'ether'))

        # === Step 13: Send to SS58 Precompile ===
        result = subprocess.run([
            "python", "scripts/send_to_ss58_precompile.py",
            "5CoZwx53nNzfnDLqxYjntvggyPw3Xee1r9b68HFw1N6UEa1X",
            str(miner_transferrable)
        ], capture_output=True, text=True, env=env)

        print("Send to celium testnet wallet from miner wallet:", result.stdout.strip())

        env["PRIVATE_KEY"] = validator_key

        result = subprocess.run([
            "python", "scripts/send_to_ss58_precompile.py",
            "5CoZwx53nNzfnDLqxYjntvggyPw3Xee1r9b68HFw1N6UEa1X",
            str(validator_transferrable)
        ], capture_output=True, text=True, env=env)

        print("Send to celium testnet wallet from validator wallet:", result.stdout.strip())

        print("Checking account balances after transfer...")

        print("Validator balance:", self.w3.from_wei(self.w3.eth.get_balance(validator_address), 'ether'))
        print("Miner balance:", self.w3.from_wei(self.w3.eth.get_balance(miner_address), 'ether'))

        print("✅ Contract lifecycle test completed successfully.")


if __name__ == "__main__":
    unittest.main()
