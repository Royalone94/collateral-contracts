#!/usr/bin/env python3

"""
Reclaim Request Retrieval Script

This script retrieves and displays information about reclaim requests from the
Collateral smart contract. It fetches ReclaimProcessStarted events within a
specified block range and provides details about each reclaim request.
"""
import asyncio
import sys
import csv
import argparse
from dataclasses import dataclass
import bittensor.utils
from celium_collateral_contracts.common import get_web3_connection, load_contract_abi


@dataclass
class ReclaimProcessStartedEvent:
    """Represents a ReclaimProcessStarted event emitted by the Collateral contract."""

    reclaim_request_id: int
    account: str
    amount: int
    expiration_time: int
    url: str
    url_content_md5_checksum: str
    block_number: int
    executor_uuid: str

def get_next_reclaim_id(w3, contract_address):
    contract_abi = load_contract_abi()

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    # Call the new public getter function
    next_id = contract.functions.getNextReclaimId().call()
    return next_id

# Get all reclaim requests using the getReclaims() method from the contract
def get_all_reclaims(w3, contract_address):
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    # getReclaims returns an array of Reclaim structs
    reclaims = contract.functions.getReclaims().call()
    result = []
    for idx, reclaim in enumerate(reclaims):
        # reclaim is a tuple: (miner, amount, denyTimeout, executorUuid)
        if reclaim[1] > 0:
            result.append(
                ReclaimProcessStartedEvent(
                    reclaim_request_id=reclaim[0],  # Note: This index may not match the original reclaimRequestId
                    account=reclaim[1],
                    amount=reclaim[2],
                    expiration_time=reclaim[3],
                    executor_uuid=reclaim[4].hex(),
                    url='',
                    url_content_md5_checksum='',
                    block_number=0
                )
            )
    return result

def get_miner_reclaims(w3, contract_address, miner_address):
    contract_abi = load_contract_abi()
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    # getReclaimsOfMiner returns an array of Reclaim structs for the given miner
    reclaims = contract.functions.getReclaimsOfMiner(miner_address).call()
    result = []
    for idx, reclaim in enumerate(reclaims):
        # reclaim is a tuple: (miner, amount, denyTimeout, executorUuid)
        if reclaim[1] > 0:
            result.append(
                ReclaimProcessStartedEvent(
                    reclaim_request_id=reclaim[0],  # Index in this list, not global reclaimRequestId
                    account=reclaim[1],
                    amount=reclaim[2],
                    expiration_time=reclaim[3],
                    executor_uuid=reclaim[4].hex(),
                    url='',
                    url_content_md5_checksum='',
                    block_number=0
                )
            )
    return result

async def get_reclaim_process_started_events(
    w3, contract_address, block_num_low, block_num_high
):
    """Fetch all ReclaimProcessStarted events emitted by the Collateral contract within a block range.

    Args:
        w3 (Web3): Web3 instance to use for blockchain interaction
        contract_address (str): The address of the deployed Collateral contract
        block_num_low (int): The starting block number (inclusive)
        block_num_high (int): The ending block number (inclusive)

    Returns:
        list[ReclaimProcessStartedEvent]: List of ReclaimProcessStarted events
    """
    contract_abi = load_contract_abi()

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    checksum_address = w3.to_checksum_address(contract_address)

    event_signature = "ReclaimProcessStarted(uint256,address,uint256,uint64,string,bytes16)"
    event_topic = w3.keccak(text=event_signature).hex()

    filter_params = {
        "fromBlock": hex(block_num_low),
        "toBlock": hex(block_num_high),
        "address": checksum_address,
        "topics": [
            event_topic,  # Event signature topic
            None,  # reclaimRequestId (indexed)
            None,  # account (indexed)
        ]
    }
    logs = w3.eth.get_logs(filter_params)

    def get_reclaim_by_id(reclaim_id):
        """Fetch reclaim information using reclaim_id."""
        reclaim = contract.functions.reclaims(reclaim_id).call()
        return {
            "miner": reclaim[1],
            "amount": reclaim[2],
            "denyTimeout": reclaim[3],
            "executorUuid": reclaim[4].hex(),
        }

    formatted_events = []
    for log in logs:
        reclaim_request_id = int(log["topics"][1].hex(), 16)

        account_address = "0x" + log["topics"][2].hex()[-40:]
        account = w3.to_checksum_address(account_address)

        decoded_event = contract.events.ReclaimProcessStarted().process_log(log)

        reclaim_info = get_reclaim_by_id(reclaim_request_id)

        formatted_events.append(
            ReclaimProcessStartedEvent(
                reclaim_request_id=reclaim_request_id,
                account=account,
                amount=reclaim_info["amount"],
                expiration_time=reclaim_info["denyTimeout"],
                executor_uuid=reclaim_info["executorUuid"],
                url=decoded_event['args']['url'],
                url_content_md5_checksum=decoded_event['args']['urlContentMd5Checksum'].hex(),
                block_number=log["blockNumber"],
            ))

    return formatted_events


async def main():
    parser = argparse.ArgumentParser(
        description="Fetch ReclaimProcessStarted events from Collateral contract")
    parser.add_argument(
        "--contract-address", required=True, help="Address of the deployed Collateral contract"
    )
    parser.add_argument(
        "--block-start", required=True, type=int, help="Starting block number (inclusive)"
    )
    parser.add_argument(
        "--block-end", required=True, type=int, help="Ending block number (inclusive)"
    )
    parser.add_argument(
        "--network",
        default="finney",
        help="The Subtensor Network to connect to.",
    )

    args = parser.parse_args()

    w3 = get_web3_connection(args.network)
    events = await get_reclaim_process_started_events(
        w3, args.contract_address, args.block_start, args.block_end
    )

    fieldnames = [
        "reclaim_request_id",
        "account",
        "amount",
        "expiration_time",
        "url",
        "url_content_md5_checksum",
        "block_number",
    ]

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()

    for event in events:
        writer.writerow(
            {
                "reclaim_request_id": event.reclaim_request_id,
                "account": event.account,
                "amount": event.amount,
                "expiration_time": event.expiration_time,
                "url": event.url,
                "url_content_md5_checksum": event.url_content_md5_checksum,
                "block_number": event.block_number,
            }
        )


if __name__ == "__main__":
    asyncio.run(main())