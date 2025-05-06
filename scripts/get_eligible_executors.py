#!/usr/bin/env python3

"""
Get Eligible Executors Script

This script allows users to retrieve the list of eligible executors (executors
with non-zero TAO in collateral and not slashed or penalized) for a given miner.
"""

import sys
import argparse
from common import (
    load_contract_abi,
    get_web3_connection,
    get_account,
    validate_address_format,
)


class GetEligibleExecutorsError(Exception):
    """Raised when fetching eligible executors fails."""
    pass


def get_eligible_executors(w3, contract_address, miner_address):
    """Get the list of eligible executors for a miner from the contract.

    Args:
        w3: Web3 instance
        contract_address: Address of the contract
        miner_address: Address of the miner to fetch executors for

    Returns:
        list: List of `bytes16` executor UUIDs for the given miner

    Raises:
        GetEligibleExecutorsError: If the contract call fails for any reason
    """
    validate_address_format(contract_address)
    validate_address_format(miner_address)

    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        executors = contract.functions.getEligibleExecutors(miner_address).call({'gas': 3000000})
        return executors
    except Exception as e:
        raise GetEligibleExecutorsError(f"Error getting eligible executors for miner {miner_address}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Get the list of eligible executors for a specific miner on the Collateral contract"
    )
    parser.add_argument(
        "contract_address", help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "miner_address", help="Address of the miner to fetch eligible executors for"
    )
    args = parser.parse_args()

    w3 = get_web3_connection()
    account = get_account()  # You may not need to use this for reading data, but it's useful for connection checks

    try:
        executors = get_eligible_executors(
            w3=w3,
            contract_address=args.contract_address,
            miner_address=args.miner_address,
        )

        print(f"Successfully fetched eligible executors for miner {args.miner_address}")
        if not executors:
            print("No eligible executors found.")
        else:
            print("Eligible Executors:")
            for executor in executors:
                print(f"  Executor UUID: {executor}")

    except GetEligibleExecutorsError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
