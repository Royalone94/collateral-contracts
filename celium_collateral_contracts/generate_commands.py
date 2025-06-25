import argparse
import os
from rich.console import Console
from rich.table import Table
from eth_account import Account

def main():
    parser = argparse.ArgumentParser(description="Generate command strings for collateral contract scripts.")
    parser.add_argument("--network", required=True, help="Network to use (e.g., local, test)")
    parser.add_argument("--contract-address", required=True, help="Address of the deployed collateral contract")
    parser.add_argument("--owner-private-key", required=True, help="Owner's private key")
    parser.add_argument("--miner-private-key", required=True, help="Miner's private key")
    parser.add_argument("--executor-uuid", help="UUID of a single executor", default="72a1d228-3c8c-45cb-8b84-980071592589")
    parser.add_argument("--executor-uuids", help="Comma-separated list of executor UUIDs", default="3a5ce92a-a066-45f7-b07d-58b3b7986464,72a1d228-3c8c-45cb-8b84-980071592589")
    parser.add_argument("--reclaim-request-id", type=int, help="ID of the reclaim request", default=1)
    parser.add_argument("--block-start", type=int, help="Starting block for reclaim requests", default=12345)
    parser.add_argument("--block-end", type=int, help="Ending block for reclaim requests", default=12355)
    parser.add_argument("--raw", action='store_true', help="Output raw command strings, one per line")
    # Amount is hardcoded for now as per test script example
    # URL is hardcoded for now as per test script example

    args = parser.parse_args()

    # Calculate addresses from private keys
    owner_address = Account.from_key(args.owner_private_key).address
    miner_address = Account.from_key(args.miner_private_key).address

    console = Console()
    commands_to_print = []

    # Define script paths relative to the current script
    script_dir = os.path.dirname(__file__)
    deposit_script = os.path.join(script_dir, "deposit_collateral.py")
    get_miners_collateral_script = os.path.join(script_dir, "get_miners_collateral.py")
    get_eligible_executors_script = os.path.join(script_dir, "get_eligible_executors.py")
    reclaim_collateral_script = os.path.join(script_dir, "reclaim_collateral.py")
    deny_request_script = os.path.join(script_dir, "deny_request.py")
    finalize_reclaim_script = os.path.join(script_dir, "finalize_reclaim.py")
    get_reclaim_requests_script = os.path.join(script_dir, "get_reclaim_requests.py")
    slash_collateral_script = os.path.join(script_dir, "slash_collateral.py")
    get_executor_collateral_script = os.path.join(script_dir, "get_executor_collateral.py")


    # 1. deposit_collateral command
    if args.executor_uuid:
        deposit_command = (
            f'python {deposit_script} '
            f'--contract-address {args.contract_address} '
            f'--amount-tao "0.001" '
            f'--private-key {args.miner_private_key} '
            f'--network {args.network} '
            f'--executor-uuid {args.executor_uuid}'
        )
        commands_to_print.append(("deposit_collateral", deposit_command))

    # 2. get_miners_collateral command
    get_miners_collateral_command = (
        f'python {get_miners_collateral_script} '
        f'--contract-address {args.contract_address} '
        f'--miner-address {miner_address} '
        f'--network {args.network}'
    )
    commands_to_print.append(("get_miners_collateral", get_miners_collateral_command))

    # 3. get_eligible_executors command
    if args.executor_uuids:
        get_eligible_executors_command = (
            f'python {get_eligible_executors_script} '
            f'--contract-address {args.contract_address} '
            f'--miner-address {miner_address} '
            f'--executor-uuids {args.executor_uuids} '
            f'--network {args.network} '
            f'--private-key {args.miner_private_key}'
        )
        commands_to_print.append(("get_eligible_executors", get_eligible_executors_command))

    # 4. reclaim_collateral command
    if args.executor_uuid:
        reclaim_collateral_command = (
            f'python {reclaim_collateral_script} '
            f'--contract-address {args.contract_address} '
            f'--amount-tao "0.001" '
            f'--private-key {args.miner_private_key} '
            f'--url "reclaim_request_url" '
            f'--executor-uuid {args.executor_uuid} '
            f'--network {args.network}'
        )
        commands_to_print.append(("reclaim_collateral", reclaim_collateral_command))

    # 5. get_reclaim_requests command
    if args.block_start is not None and args.block_end is not None:
         get_reclaim_requests_command = (
            f'python {get_reclaim_requests_script} '
            f'--contract-address {args.contract_address} '
            f'--block-start {args.block_start} '
            f'--block-end {args.block_end} '
            f'--network {args.network}'
        )
         commands_to_print.append(("get_reclaim_requests", get_reclaim_requests_command))

    # 6. deny_request command
    if args.reclaim_request_id is not None:
        deny_request_command = (
            f'python {deny_request_script} '
            f'--contract-address {args.contract_address} '
            f'--reclaim-request-id {args.reclaim_request_id} '
            f'--url "deny_request_url" '
            f'--network {args.network} '
            f'--private-key {args.owner_private_key}' # Denied by owner
        )
        commands_to_print.append(("deny_request", deny_request_command))

    # 7. finalize_reclaim command
    if args.reclaim_request_id is not None:
        finalize_reclaim_command = (
            f'python {finalize_reclaim_script} '
            f'--contract-address {args.contract_address} '
            f'--reclaim-request-id {args.reclaim_request_id} '
            f'--network {args.network} '
            f'--private-key {args.owner_private_key}' # Finalized by owner
        )
        commands_to_print.append(("finalize_reclaim", finalize_reclaim_command))

    # 8. slash_collateral command
    if args.executor_uuid:
        slash_collateral_command = (
            f'python {slash_collateral_script} '
            f'--contract-address {args.contract_address} '
            f'--url "slash_url" '
            f'--private-key {args.owner_private_key} '
            f'--network {args.network} '
            f'--executor-uuid {args.executor_uuid}'
        )
        commands_to_print.append(("slash_collateral", slash_collateral_command))

    # 9. get_executor_collateral command
    if args.executor_uuid:
        get_executor_collateral_command = (
            f'python {get_executor_collateral_script} '
            f'--contract-address {args.contract_address} '
            f'--miner-address {miner_address} '
            f'--executor-uuid {args.executor_uuid} '
            f'--network {args.network}'
        )
        commands_to_print.append(("get_executor_collateral", get_executor_collateral_command))

    # Print the table
    if args.raw:
        for key, command in commands_to_print:
            print(command)
    else:
        table = Table(title="Generated Commands", show_lines=True, border_style="blue")
        table.add_column("Command Key", style="dim", width=30)
        table.add_column("Command", style="green", justify="left")
        for key, command in commands_to_print:
            table.add_row(key, command)
        console.print(table)

if __name__ == "__main__":
    main()