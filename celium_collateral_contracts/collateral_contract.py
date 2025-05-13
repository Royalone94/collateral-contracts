from web3 import Web3
from uuid import UUID
from celium_collateral_contracts.common import (
    get_web3_connection,
    get_account,
    validate_address_format,
    get_miner_collateral,
)
from celium_collateral_contracts.deposit_collateral import deposit_collateral
from celium_collateral_contracts.reclaim_collateral import reclaim_collateral
from celium_collateral_contracts.finalize_reclaim import finalize_reclaim
from celium_collateral_contracts.deny_request import deny_reclaim_request
from celium_collateral_contracts.slash_collateral import slash_collateral
from celium_collateral_contracts.get_collaterals import get_deposit_events
from celium_collateral_contracts.get_eligible_executors import get_eligible_executors


class CollateralContract:
    def __init__(self, network: str, contract_address: str, validator_keystr=None, miner_keystr=None):
        self.w3 = get_web3_connection(network)
        self.validator_account = get_account(validator_keystr)
        self.miner_account = get_account(miner_keystr)
        self.contract_address = contract_address

    def deposit_collateral(self, amount_tao, validator_address, executor_uuid):
        """Deposit collateral into the contract."""
        return deposit_collateral(
            self.w3,
            self.miner_account,
            amount_tao,
            self.contract_address,
            validator_address,
            executor_uuid,
        )

    def reclaim_collateral(self, amount_tao, url, executor_uuid):
        """Initiate reclaiming collateral."""
        return reclaim_collateral(
            self.w3,
            self.miner_account,
            amount_tao,
            self.contract_address,
            url,
            executor_uuid,
        )

    def finalize_reclaim(self, reclaim_request_id):
        """Finalize a reclaim request."""
        return finalize_reclaim(
            self.w3,
            self.miner_account,
            reclaim_request_id,
            self.contract_address,
        )

    def deny_reclaim_request(self, reclaim_request_id, url):
        """Deny a reclaim request."""
        return deny_reclaim_request(
            self.w3,
            self.validator_account,
            reclaim_request_id,
            url,
            self.contract_address,
        )

    def slash_collateral(self, miner_address, amount_tao, url, executor_uuid):
        """Slash collateral from a miner."""
        return slash_collateral(
            self.w3,
            self.validator_account,
            miner_address,
            amount_tao,
            self.contract_address,
            url,
            executor_uuid,
        )

    def get_miner_collateral(self, miner_address):
        """Get the collateral amount for a miner."""
        return get_miner_collateral(self.w3, self.contract_address, miner_address)

    def get_deposit_events(self, block_start, block_end):
        """Fetch deposit events within a block range."""
        return get_deposit_events(
            self.w3,
            self.contract_address,
            block_start,
            block_end,
        )

    def get_eligible_executors(self, miner_address, executor_uuids):
        """Get the list of eligible executors for a miner."""
        return get_eligible_executors(
            self.w3,
            self.contract_address,
            miner_address,
            executor_uuids,
        )

    def get_balance(self, address):
        """Get the balance of an Ethereum address."""
        validate_address_format(address)
        balance = self.w3.eth.get_balance(address)
        return self.w3.from_wei(balance, "ether")


def main():
    import os
    import time

    # Configuration
    network = "test"
    contract_address = "0x354DbD43c977A59a3EeFeAd3Cb3de0a4E0E62b6D"
    validator_key = "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3"
    miner_key = "259e0eded00353f71eb6be89d8749ad12bf693cbd8aeb6b80cd3a343c0dc8faf"

    # Initialize CollateralContract instance
    contract = CollateralContract(network, contract_address, validator_key, miner_key)

    # Verify chain ID
    chain_id = contract.w3.eth.chain_id
    print(f"Verified chain ID: {chain_id}")

    # Check balances
    validator_address = contract.validator_account.address
    miner_address = contract.miner_account.address
    print("Validator Balance:", contract.get_balance(validator_address))
    print("Miner Balance:", contract.get_balance(miner_address))

    # Deposit collateral
    deposit_tasks = [
        ("3a5ce92a-a066-45f7-b07d-58b3b7986464", 0.0001),
        ("72a1d228-3c8c-45cb-8b84-980071592589", 0.0001),
        ("15c2ff27-0a4d-4987-bbc9-fa009ef9f7d2", 0.0001),
        ("335453ad-246c-4ad5-809e-e2013ca6c07e", 0.0001),
        ("89c66519-244f-4db0-b4a7-756014d6fd24", 0.0001),
        ("af3f1b82-ff98-44c8-b130-d948a2a56b44", 0.0001),
        ("ee3002d9-71f8-4a83-881d-48bd21b6bdd1", 0.0001),
    ]
    # for uuid_str, amount in deposit_tasks:
    #     print(f"Depositing collateral for executor {uuid_str}...")
    #     contract.deposit_collateral(amount, validator_address, uuid_str)

    # Verify collateral
    collateral = contract.get_miner_collateral(miner_address)
    print("[COLLATERAL]:", collateral)

    # List eligible executors
    executor_uuids = [uuid for uuid, _ in deposit_tasks]
    eligible_executors = contract.get_eligible_executors(miner_address, executor_uuids)
    print("Eligible Executors:", eligible_executors)

    # Reclaim collateral
    reclaim_uuid = "72a1d228-3c8c-45cb-8b84-980071592589"
    print("Reclaiming collateral...")
    reclaim_result = contract.reclaim_collateral(0.00001, "please gimme money back", reclaim_uuid)
    print("Reclaim Result:", reclaim_result)

    # Fetch reclaim requests
    latest_block = contract.w3.eth.block_number
    print(f"Fetching reclaim requests between blocks {latest_block - 10} and {latest_block + 10}...")
    reclaim_requests = contract.get_deposit_events(latest_block - 10, latest_block + 10)
    print("Reclaim Requests:", reclaim_requests)

    # Deny and finalize reclaim requests
    print("Denying reclaim request...")
    contract.deny_reclaim_request(reclaim_request_id=2, url="no, i will not")
    print("Finalizing reclaim request...")
    contract.finalize_reclaim(reclaim_request_id=1)

    # Final collateral check
    final_collateral = contract.get_miner_collateral(miner_address)
    print("[FINAL COLLATERAL]:", final_collateral)

    # Check transferrable balances
    print("Validator Balance:", contract.get_balance(validator_address))
    print("Miner Balance:", contract.get_balance(miner_address))

    print("✅ Contract lifecycle completed successfully.")

if __name__ == "__main__":
    main()