import argparse
from web3 import Web3
from substrateinterface.utils.ss58 import ss58_decode

# Raw ABI text of the Collateral contract
COLLATERAL_CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"}
        ],
        "name": "hotkeyToEthereumAddress",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def get_eth_address_from_hotkey(w3: Web3, contract_address: str, hotkey: str):
    """Retrieve the Ethereum address mapped to a hotkey."""

    # Convert hotkey string to bytes32
    pubkey_hex = ss58_decode(hotkey)
    hotkey_bytes32 = bytes.fromhex(pubkey_hex)

    # Use raw ABI text
    contract = w3.eth.contract(address=contract_address, abi=COLLATERAL_CONTRACT_ABI)
    eth_address = contract.functions.hotkeyToEthereumAddress(hotkey_bytes32).call()

    return eth_address

def main():
    parser = argparse.ArgumentParser(description="Get Ethereum address from hotkey using Collateral smart contract.")
    parser.add_argument("--contract-address", required=True, help="Address of the Collateral smart contract.")
    parser.add_argument("--hotkey", required=True, help="Hotkey to query.")
    parser.add_argument("--provider-url", default="http://127.0.0.1:8545", help="Ethereum node provider URL.")
    args = parser.parse_args()

    eth_address = get_eth_address_from_hotkey(args.contract_address, args.hotkey, args.provider_url)
    if eth_address == "0x0000000000000000000000000000000000000000":
        print(f"No Ethereum address mapped to hotkey {args.hotkey}.")
    else:
        print(f"Ethereum address for hotkey {args.hotkey}: {eth_address}")

if __name__ == "__main__":
    main()
