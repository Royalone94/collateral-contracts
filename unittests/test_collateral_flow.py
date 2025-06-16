import sys
import os
import time
import subprocess
import unittest
from eth_account import Account
from web3 import Web3

# Update import to use the scripts package
from celium_collateral_contracts.address_conversion import h160_to_ss58


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
    USE_EXISTING_ACCOUNTS = True
    DEPLOY_CONTRACT = True

    # Add a helper to run subprocess commands with a sleep delay
    def run_cmd(self, cmd, env, capture=True, sleep_time=1):
        result = subprocess.run(cmd, capture_output=capture, text=True, env=env) if capture else subprocess.run(cmd, env=env)
        time.sleep(sleep_time)
        return result

    def setUp(self):
        # Use the local RPC URL here
        # self.RPC_URL = "https://test.finney.opentensor.ai"
        # self.network = "test"
        self.RPC_URL = "http://127.0.0.1:9944"
        self.network = "local"
        self.w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.assertTrue(self.w3.is_connected(), "Cannot connect to Bittensor RPC")
        print("Connected to Bittensor RPC")

    def test_lifecycle(self):
        os.environ["RPC_URL"] = self.RPC_URL  # Setting the RPC URL for deployment
        env = os.environ.copy() 

        chain_id = self.w3.eth.chain_id
        print(f"Verified chain ID: {chain_id}")

        # Update script paths to match the updated folder structure
        deposit_script = "celium_collateral_contracts/deposit_collateral.py"
        get_miners_collateral_script = "celium_collateral_contracts/get_miners_collateral.py"
        get_eligible_executors_script = "celium_collateral_contracts/get_eligible_executors.py"
        reclaim_collateral_script = "celium_collateral_contracts/reclaim_collateral.py"
        deny_request_script = "celium_collateral_contracts/deny_request.py"
        finalize_reclaim_script = "celium_collateral_contracts/finalize_reclaim.py"
        get_reclaim_requests_script = "celium_collateral_contracts/get_reclaim_requests.py"
        slash_collateral_script = "celium_collateral_contracts/slash_collateral.py"
        if self.USE_EXISTING_ACCOUNTS:
            owner_address = "0xE1A07A44ac6f8423bA3b734F0cAfC6F87fd385Fc"
            owner_key = "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3"
            miner_address = "0x19F71e76B34A8Dc01944Cf3B76478B45DE05B75b"
            miner_key = "259e0eded00353f71eb6be89d8749ad12bf693cbd8aeb6b80cd3a343c0dc8faf"
            owner_ss58 = h160_to_ss58(owner_address)
            miner_ss58 = h160_to_ss58(miner_address)
            print("Owner SS58:", owner_ss58)
            print("Miner SS58:", miner_ss58)

            balance = self.w3.eth.get_balance(owner_address)
            print("Owner Balance:", self.w3.from_wei(balance, 'ether'))
            
            balance = self.w3.eth.get_balance(miner_address)
            print("Miner Balance:", self.w3.from_wei(balance, 'ether'))

        else:
            # === Step 1: Create Owner Account ===
            owner = Account.create("extra entropy collateral contract Cellium")
            owner_address = owner.address
            owner_key = owner.key.hex()
            owner_ss58 = h160_to_ss58(owner_address)
            print("Owner Address:", owner_address)
            print("Owner Key:", owner_key)

            # === Step 2: Create Miner Account ===
            miner = Account.create("extra entropy MINER Cellium")
            miner_address = miner.address
            miner_key = miner.key.hex()
            miner_ss58 = h160_to_ss58(miner_address)
            print("Miner Address:", miner_address)
            print("Miner Key:", miner_key)

            # === Step 3: Fund Owner ===
            subprocess.run(["btcli", "w", "transfer", "--network", self.network, "--dest", owner_ss58, "--amount", "0.5"])
            time.sleep(3)

            chain_id = self.w3.eth.chain_id
            print(f"Verified chain ID: {chain_id}")

            balance = self.w3.eth.get_balance(owner_address)
            print("Owner Balance:", self.w3.from_wei(balance, 'ether'))
            # === Step 4: Deploy Contract ===
            os.environ["PRIVATE_KEY"] = owner_key  # Setting the deployer's private key
            os.environ["RPC_URL"] = self.RPC_URL  # Setting the RPC URL for deployment
            os.environ["DENY_TIMEOUT"] = 3600
            os.environ["MIN_COLLATERAL_INCREASE"] = 1000000000000000  # Example amount in wei
            # Validate the required environment variables
            if not os.environ.get("RPC_URL"):
                raise ValueError("RPC_URL environment variable not set.")
            if not os.environ.get("PRIVATE_KEY"):
                raise ValueError("PRIVATE_KEY environment variable not set.")
            
            # === Step 5: Fund Miner ===
            subprocess.run(["btcli", "w", "transfer", "--network", self.network, "--dest", miner_ss58, "--amount", "3.5"])
            time.sleep(3)
            self.assertGreater(self.w3.eth.get_balance(miner_address), 0, "Miner not funded")

            balance = self.w3.eth.get_balance(miner_address)
            print("Miner Balance:", self.w3.from_wei(balance, 'ether'))

         # Deploy using the `forge` command directly
        print("Deploying contract...", self.RPC_URL)

        if self.DEPLOY_CONTRACT:
            print("Deploying contract with node deployUUPS.js...")

            deploy_result = self.run_cmd(
                [
                    "node", "deployUUPS.js",
                ],
                env=env
            )
            
            print(
                f'node deployUUPS.js '
            )

            # Expect deployUUPS.js to print contract address in stdout, e.g. "Deployed to: 0x..."
            self.assertIn("Contract Address:", deploy_result.stdout, deploy_result.stderr)
            contract_line = [line for line in deploy_result.stdout.splitlines() if "Contract Address:" in line][0]
            contract_address = contract_line.split(": ")[-1]
            self.assertTrue(Web3.is_address(contract_address))
        else:
            contract_address = "0xf24D7d7185FCda6570D9c4b924af20b5e4A92019"

        print("Deployed Contract Address:", contract_address)
        # === Step 6: Miner Deposits Collateral ===
        env["PRIVATE_KEY"] = miner_key

        print("Owner Address:", owner_address)
        print("Owner Key:", owner_key)

        print("Miner Address:", miner_address)
        print("Miner Key:", miner_key)

        # Refactored deposit collateral steps as a loop
        deposit_tasks = [
            ("3a5ce92a-a066-45f7-b07d-58b3b7986464", False),
            ("72a1d228-3c8c-45cb-8b84-980071592589", False),
            ("15c2ff27-0a4d-4987-bbc9-fa009ef9f7d2", False),
            ("335453ad-246c-4ad5-809e-e2013ca6c07e", False),
            ("89c66519-244f-4db0-b4a7-756014d6fd24", False),
            ("af3f1b82-ff98-44c8-b130-d948a2a56b44", False),
            ("ee3002d9-71f8-4a83-881d-48bd21b6bdd1", False),
        ]
        for uuid_str, capture_output in deposit_tasks:
            print(f"Starting deposit collateral for executor {uuid_str}...")
            result = self.run_cmd(
                [
                    "python", deposit_script,
                    "--contract-address", contract_address,
                    "--amount-tao", "0.001",
                    "--private-key", miner_key,
                    "--network", self.network,
                    "--executor-uuid", uuid_str
                ],
                env=env, capture=capture_output
            )
            if capture_output:
                print(result.stdout.strip())

            print(
                f'python {deposit_script} '
                f'--contract-address {contract_address} '
                f'--amount-tao 0.001 '
                f'--private-key {miner_key} '
                f'--network {self.network} '
                f'--executor-uuid {uuid_str}'
            )

        print("Deposit collateral finished")

        get_executor_collateral_script = "celium_collateral_contracts/get_executor_collateral.py"
        for uuid_str, _ in deposit_tasks:
            print(f"Checking executor collateral for executor {uuid_str}...")
            result = self.run_cmd(
                [
                    "python", get_executor_collateral_script,
                    "--contract-address", contract_address,
                    "--miner-address", miner_address,
                    "--executor-uuid", uuid_str,
                    "--network", self.network
                ],
                capture=True, env=env
            )

            print(
                f'python {get_executor_collateral_script} '
                f'--contract-address {contract_address} '
                f'--miner-address {miner_address} '
                f'--executor-uuid {uuid_str} '
                f'--network {self.network}'
            )

            print(f"Executor collateral for {uuid_str}: ", result.stdout.strip())

        time.sleep(3)
        # === Step 9: Miner Reclaims Collateral ===
        print("Starting reclaim collateral...")
        for uuid_str, _ in deposit_tasks:
            print(f"Reclaiming collateral for executor UUID: {uuid_str}")
            result = self.run_cmd(
                [
                    "python", reclaim_collateral_script,
                    "--contract-address", contract_address,
                    "--private-key", miner_key,
                    "--url", f"Reclaiming for executor {uuid_str}",
                    "--executor-uuid", uuid_str,
                    "--network", self.network
                ],
                env=env
            )
            print(
                f'python {reclaim_collateral_script} '
                f'--contract-address {contract_address} '
                f'--private-key {miner_key} '
                f'--url "Reclaiming for executor {uuid_str}" '
                f'--executor-uuid {uuid_str} '
                f'--network {self.network}'
            )

            print("Reclaim Result:", result.stdout.strip())

        # === Step 10: Owner Checks Requests ===
        latest_block = self.w3.eth.block_number
        print(f"All reclaim requests between these blocks: {latest_block - 10}, {latest_block + 10}")

        result = self.run_cmd(
            [
                "python", get_reclaim_requests_script,
                "--contract-address", contract_address,
                "--block-start", str(latest_block - 100),
                "--block-end", str(latest_block + 10),
                "--network", self.network
            ],
            env=env
        )

        print(
            f'python {get_reclaim_requests_script} '
            f'--contract-address {contract_address} '
            f'--block-start {latest_block - 100} '
            f'--block-end {latest_block + 10} '
            f'--network {self.network}'
        )
        
        deny_reclaim_id = 2
        finalize_reclaim_id = 1
        # === Step 11: Owner Denies Request 1, Finalizes Request 2 ===
        env["PRIVATE_KEY"] = owner_key
        # print("Starting deny reclaim request")
        # self.run_cmd(
        #     [
        #         "python", deny_request_script,
        #         "--contract-address", contract_address,
        #         "--reclaim-request-id", str(deny_reclaim_id),
        #         "--url", "no, i will not",
        #         "--network", self.network,
        #         "--private-key", miner_key
        #     ],
        #     env=env
        # )

        # print(
        #     f'python {deny_request_script} '
        #     f'--contract-address {contract_address} '
        #     f'--reclaim-request-id {deny_reclaim_id} '
        #     f'--url "no, i will not" '
        #     f'--network {self.network} '
        #     f'--private-key {miner_key} '
        # )
        
        print("Deny reclaim request finished")

        print("Starting finalize reclaim request")
        self.run_cmd(
            [
                "python", finalize_reclaim_script,
                "--contract-address", contract_address,
                "--reclaim-request-id", str(finalize_reclaim_id),
                "--network", self.network,
                "--private-key", miner_key
            ],
            env=env
        )

        print(
            f'python {finalize_reclaim_script} '
            f'--contract-address {contract_address} '
            f'--reclaim-request-id {finalize_reclaim_id} '
            f'--network {self.network} '
            f'--private-key {miner_key} '
        )

        for uuid_str, capture_output in deposit_tasks:
            print(f"Starting slash collateral for executor {uuid_str}...")
            result = self.run_cmd(
                [
                    "python", slash_collateral_script,
                    "--contract-address", contract_address,
                    "--url", "slashit",
                    "--private-key", owner_key,
                    "--network", self.network,
                    "--executor-uuid", uuid_str
                ],
                env=env, capture=capture_output
            )
            if capture_output:
                print(result.stdout.strip())

            print(
                f'python {slash_collateral_script} '
                f'--contract-address {contract_address} '
                f'--private-key {owner_key} '
                f'--url "slashit" '
                f'--network {self.network} '
                f'--executor-uuid {uuid_str}'
            )

        # === Step 12: Final Collateral Check ===
        print("Checking account balances before transfer...")
        print("Owner balance:", self.w3.from_wei(self.w3.eth.get_balance(owner_address), 'ether'))
        print("Miner balance:", self.w3.from_wei(self.w3.eth.get_balance(miner_address), 'ether'))

        owner_transferrable = get_transferrable_balance(self.w3, owner_address, "0x0000000000000000000000000000000000000001")
        miner_transferrable = get_transferrable_balance(self.w3, miner_address, "0x0000000000000000000000000000000000000001")
        
        print("owner_transferrable:", owner_transferrable)
        print("miner_transferrable:", miner_transferrable)

        print("Owner transferrable balance:", self.w3.from_wei(owner_transferrable, 'ether'))
        print("Miner transferrable balance:", self.w3.from_wei(miner_transferrable, 'ether'))

        print("Checking account balances after transfer...")

        print("Owner balance:", self.w3.from_wei(self.w3.eth.get_balance(owner_address), 'ether'))
        print("Miner balance:", self.w3.from_wei(self.w3.eth.get_balance(miner_address), 'ether'))

        # === Step 8: Check executor collateral for each deposit ===
        get_executor_collateral_script = "celium_collateral_contracts/get_executor_collateral.py"
        for uuid_str, _ in deposit_tasks:
            print(f"Checking executor collateral for executor {uuid_str}...")
            result = self.run_cmd(
                [
                    "python", get_executor_collateral_script,
                    "--contract-address", contract_address,
                    "--miner-address", miner_address,
                    "--executor-uuid", uuid_str,
                    "--network", self.network
                ],
                capture=True, env=env
            )

            print(
                f'python {get_executor_collateral_script} '
                f'--contract-address {contract_address} '
                f'--miner-address {miner_address} '
                f'--executor-uuid {uuid_str} '
                f'--network {self.network}'
            )

            print(f"Executor collateral for {uuid_str}: ", result.stdout.strip())

        time.sleep(3)
        print("Result: ", result.stdout.strip())

        print("✅ Contract lifecycle test completed successfully.")


if __name__ == "__main__":
    # If running via unittest discovery, custom flags will not be recognized.
    if any(arg.startswith("--use_existing_accounts") or arg.startswith("--deploy_contract")
           for arg in sys.argv[1:]):
        print("WARNING: Custom flags are not supported when using 'python -m unittest'.")
        print("Run this file directly instead, for example:")
        print("  python unittests/test_collateral_flow.py --use_existing_accounts False")

    import argparse
    parser = argparse.ArgumentParser(description="Override test parameters")
    parser.add_argument("--use_existing_accounts", choices=["True", "False"],
                        help="Override USE_EXISTING_ACCOUNTS", default=None)
    parser.add_argument("--deploy_contract", choices=["True", "False"],
                        help="Override DEPLOY_CONTRACT", default=None)
    args, remaining = parser.parse_known_args()
    if args.use_existing_accounts is not None:
        TestCollateralContractLifecycle.USE_EXISTING_ACCOUNTS = (args.use_existing_accounts == "True")
    if args.deploy_contract is not None:
        TestCollateralContractLifecycle.DEPLOY_CONTRACT = (args.deploy_contract == "True")
    sys.argv = [sys.argv[0]] + remaining
    unittest.main()

    # --- Example usage of get_executor_collateral.py as a main method ---
    # This demonstrates how to call the script directly for a single executor UUID
    import subprocess
    print("\n[Standalone get_executor_collateral.py usage example]:")
    contract_address = "0x8b6A0598898255C48Cb73B21271bB47f2EEEE7c1"
    miner_address = "0x19F71e76B34A8Dc01944Cf3B76478B45DE05B75b"
    executor_uuid = "3a5ce92a-a066-45f7-b07d-58b3b7986464"
    network = "local"
    result = subprocess.run([
        "python", "celium_collateral_contracts/get_executor_collateral.py",
        "--contract-address", contract_address,
        "--miner-address", miner_address,
        "--executor-uuid", executor_uuid,
        "--network", network
    ], capture_output=True, text=True)
    print(result.stdout.strip())
