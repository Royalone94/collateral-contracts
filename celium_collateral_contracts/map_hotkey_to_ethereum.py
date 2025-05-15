import argparse
import sys
from web3 import Web3
from eth_account import Account
from celium_collateral_contracts.common import get_web3_connection, get_account, build_and_send_transaction, wait_for_receipt


def map_hotkey_to_ethereum(w3: Web3, contract_address: str, sender_account: Account, hotkey: str) -> dict:
    """
    Map a Bittensor hotkey to an Ethereum address.

    Args:
        w3: Web3 instance
        contract_address: Address of the Collateral contract
        sender_account: Account instance of the sender
        hotkey: Bittensor hotkey (as bytes32)

    Returns:
        dict: Transaction receipt
    """
    abi = [
        {
            "inputs": [
                {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"},
                {"internalType": "address", "name": "ethereumAddress", "type": "address"},
            ],
            "name": "mapHotkeyToEthereumAddress",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]
    contract = w3.eth.contract(address=contract_address, abi=abi)

    tx_hash = build_and_send_transaction(
        w3,
        contract.functions.mapHotkeyToEthereumAddress(Web3.toBytes(hexstr=hotkey), sender_account.address),
        sender_account,
    )

    # Wait for transaction receipt
    receipt = wait_for_receipt(w3, tx_hash)

    return receipt


def main():
    parser = argparse.ArgumentParser(description="Map a Bittensor hotkey to an Ethereum address.")
    parser.add_argument("--contract-address", required=True, help="Address of the Collateral contract.")
    parser.add_argument("--hotkey", required=True, help="Bittensor hotkey (as bytes32).")
    parser.add_argument("--ethereum-address", required=True, help="Ethereum address to associate with the hotkey.")
    parser.add_argument("--keystr", help="Keystring of the account to use.")
    parser.add_argument("--network", default="finney", help="The Subtensor Network to connect to.")
    args = parser.parse_args()

    w3 = get_web3_connection(args.network)
    account = get_account(args.keystr)
    print(f"Using account: {account.address}")

    receipt = map_hotkey_to_ethereum(
        w3=w3,
        contract_address=args.contract_address,
        sender_account=account,
        hotkey=args.hotkey,
        ethereum_address=args.ethereum_address,
    )

    print(f"Transaction status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    print(f"Gas used: {receipt['gasUsed']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
