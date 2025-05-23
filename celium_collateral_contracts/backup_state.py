#!/usr/bin/env python3

import json
import os
from web3 import Web3

# Configuration (replace with your actual values)
RPC_URL = "YOUR_RPC_URL"
CONTRACT_ADDRESS = "YOUR_CONTRACT_ADDRESS"
ABI_FILE = "abi.json"

def get_contract(rpc_url, contract_address, abi_file):
    """Connects to the blockchain and gets the contract instance."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise Exception(f"Failed to connect to web3 provider at {rpc_url}")

    with open(abi_file, "r") as f:
        abi = json.load(f)

    contract = w3.eth.contract(address=contract_address, abi=abi)
    return w3, contract

def backup_collateral_state(contract, output_file="collateral_backup.json"):
    """Reads and backs up the state of collateral-related mappings."""
    backup_data = {}

    # NOTE: Reading full mappings is not directly supported via RPC.
    # You typically need to know the keys (addresses, reclaimIds, executorUuids)
    # or iterate through relevant events to collect keys.
    # This is a basic example assuming you have a way to get the relevant keys.

    # Example: Querying a few known addresses (replace with actual logic to get keys)
    known_addresses = ["0x...", "0x..."] # Replace with logic to get miner addresses
    known_reclaim_ids = [1, 2] # Replace with logic to get reclaim IDs
    # known_executor_uuids = [...] # You would need to track these as well

    backup_data["collaterals"] = {}
    for address in known_addresses:
        try:
            collateral = contract.functions.collaterals(address).call()
            backup_data["collaterals"][address] = collateral
        except Exception as e:
            print(f"Could not read collateral for {address}: {e}")

    backup_data["collateralUnderPendingReclaims"] = {}
    for address in known_addresses:
         try:
            pending = contract.functions.collateralUnderPendingReclaims(address).call()
            backup_data["collateralUnderPendingReclaims"][address] = pending
         except Exception as e:
            print(f"Could not read pending collateral for {address}: {e}")


    backup_data["validatorOfMiner"] = {}
    for address in known_addresses:
         try:
            validator = contract.functions.validatorOfMiner(address).call()
            backup_data["validatorOfMiner"][address] = validator
         except Exception as e:
            print(f"Could not read validator for {address}: {e}")

    backup_data["reclaims"] = {}
    for reclaim_id in known_reclaim_ids:
        try:
            reclaim = contract.functions.reclaims(reclaim_id).call()
            # Reclaim struct might need conversion if it contains complex types
            backup_data["reclaims"][reclaim_id] = {
                "miner": reclaim[0],
                "amount": reclaim[1],
                "denyTimeout": reclaim[2],
                "executorUuid": bytes(reclaim[3]).hex() # Convert bytes16 to hex string
            }
        except Exception as e:
             # This will also catch cases where reclaim_id does not exist (amount == 0)
            # print(f"Could not read reclaim {reclaim_id}: {e}")
            pass # Ignore non-existent reclaims

    # Backing up collateralPerExecutor is more complex as it's a nested mapping.
    # You would need lists of both miner addresses and their associated executorUuids.
    # backup_data["collateralPerExecutor"] = {}
    # for miner_address in known_addresses:
    #     backup_data["collateralPerExecutor"][miner_address] = {}
    #     for executor_uuid in miners_known_executors.get(miner_address, []): # Need to know executors per miner
    #         try:
    #             collateral = contract.functions.collateralPerExecutor(miner_address, bytes.fromhex(executor_uuid)).call()
    #             backup_data["collateralPerExecutor"][miner_address][executor_uuid] = collateral
    #         except Exception as e:
    #              print(f"Could not read collateral per executor {executor_uuid} for {miner_address}: {e}")


    with open(output_file, "w") as f:
        json.dump(backup_data, f, indent=4)

    print(f"Backup saved to {output_file}")

if __name__ == "__main__":
    try:
        w3, contract = get_contract(RPC_URL, CONTRACT_ADDRESS, ABI_FILE)
        backup_collateral_state(contract)
    except Exception as e:
        print(f"An error occurred: {e}") 