# White Paper: Decentralized Collateral Management Smart Contract

## 1. Introduction

### 1.1 Project Overview
The **Collateral Management Smart Contract** is a decentralized Ethereum-based solution for managing, reclaiming, and slashing collateral in blockchain-based systems. It is specifically designed for platforms that rely on validators and miners (such as subnets or sidechains), where economic security and governance enforcement are paramount.

### 1.2 Purpose and Goals
This project aims to:
- Ensure transparent and secure deposit and withdrawal of collateral.
- Enable trust-based reclamation under trustee oversight.
- Provide slashing capabilities for validators to enforce accountability.
- Offer traceability and auditability through on-chain events and logs.

### 1.3 Key Features
- **Deposits:** Users (miners) deposit collateral tied to a specific validator and executor.
- **Reclaiming Collateral:** Users can reclaim deposited collateral through a time-based trust model.
- **Denial and Slashing:** Validators can deny or slash miners' funds if misbehavior is detected.
- **Executor-specific Tracking:** Deposits and slashes are tracked per executor UUID.
- **Immutable Parameters:** Governance settings are immutable post-deployment for integrity.

## 2. Architecture

### 2.1 High-Level Architecture Diagram
```
  ┌─────────────┐       ┌──────────────────┐
  │    Miner    │──────▶│   Collateral.sol │
  └─────────────┘       └──────────────────┘
         ▲                      ▲
         │                      │
         │                      ▼
  ┌─────────────┐       ┌──────────────────┐
  │  Validator  │◀──────│  Trustee Controls│
  └─────────────┘       └──────────────────┘
         ▲                      ▲
         │                      │
         ▼                      ▼
  ┌─────────────┐       ┌──────────────────┐
  │   Scripts   │──────▶│ Deployment/Test  │
  └─────────────┘       └──────────────────┘
```

### 2.2 Core Components
- **Collateral.sol**: The smart contract managing all logic for deposits, reclaims, denials, and slashes.
- **Miners**: Users who stake collateral and interact with validators.
- **Validators/Trustees**: Authorized entities to approve or deny reclaim requests or enforce slashing.
- **Executors**: Logical grouping tagged by UUIDs, which allow per-service tracking.

## 3. Smart Contract Details

### 3.1 Key Functions

#### `deposit(address validator, bytes16 executorUuid)`
Allows users to deposit ETH collateral linked to a specific validator and executor.

#### `reclaimCollateral(...)`
Starts the reclaim process with a delay for trustee denial.

#### `finalizeReclaim(uint256 reclaimRequestId)`
Allows users to finalize and withdraw their reclaim unless denied or slashed.

#### `denyReclaimRequest(...)`
Trustees can reject a reclaim during the timeout window.

#### `slashCollateral(...)`
Used by assigned validators to penalize misbehaving miners.

### 3.2 Events

| Event Name | Description |
|------------|-------------|
| `Deposit` | Triggered when a user deposits collateral. |
| `ReclaimProcessStarted` | Emitted when a reclaim process begins. |
| `Reclaimed` | Signals successful completion of a reclaim. |
| `Denied` | Indicates a reclaim was denied by a trustee. |
| `Slashed` | Notifies the network that a miner has been penalized. |

### 3.3 Errors

- `AmountZero`, `InsufficientAmount`, `ReclaimAmountTooLarge`, etc. offer granular failure feedback.

### 3.4 Security Best Practices

- **Check-Effects-Interactions Pattern** to prevent reentrancy.
- **Access Control Modifiers** for authorized actions.
- **Immutable Variables** for trusted governance.

## 4. Setup and Installation

### 4.1 Prerequisites
- Node.js v16+
- Hardhat
- Ethereum client (e.g., Ganache, Anvil)

### 4.2 Installation Guide
```bash
git clone https://github.com/your-org/collateral-contract
cd collateral-contract
npm install
```

### 4.3 Deploying the Smart Contract
```bash
npx hardhat run scripts/deploy.js --network goerli
```

## 5. Usage

### 5.1 Example: Deposit
```js
await contract.deposit(validatorAddress, executorUuid, { value: ethers.utils.parseEther("1") });
```

### 5.2 Reclaim Collateral
```js
await contract.reclaimCollateral(amount, url, md5, executorUuid);
```

### 5.3 Finalize Reclaim
```js
await contract.finalizeReclaim(reclaimRequestId);
```

### 5.4 Deny Reclaim
```js
await contract.denyReclaimRequest(reclaimRequestId, denialUrl, checksum);
```

### 5.5 Slash Collateral
```js
await contract.slashCollateral(miner, amount, url, checksum, executorUuid);
```

## 6. Testing and Validation

### 6.1 Strategy
- Unit tests with Hardhat + Chai
- Fuzz and boundary testing
- Attack simulations

### 6.2 Sample Test
```js
describe("Collateral.sol", function () {
  it("should allow a deposit above threshold", async function () {
    await collateral.connect(user).deposit(validator, executorUuid, { value: minCollateral });
    expect(await collateral.collaterals(user.address)).to.equal(minCollateral);
  });
});
```

## 7. Troubleshooting and FAQs

### Common Issues

| Problem | Solution |
|---------|----------|
| Reclaim fails with `BeforeDenyTimeout` | Wait for timeout. |
| `InvalidDepositMethod` | Use the `deposit()` function. |

### FAQs

- **Can a miner switch validators?** Yes, only if no pending reclaims.
- **Who can slash a miner?** Only the validator assigned to them.

## 8. Contributing

### 8.1 Guidelines
- Fork, test, PR with clear context.

### 8.2 Code of Conduct
- Respectful, inclusive, and transparent contributions.

## 9. Appendix

### 9.1 Glossary
- **Miner**: A participant who deposits collateral.
- **Validator**: Supervises miners and enforces slashing.
- **Reclaim**: Request to withdraw collateral.
- **Executor UUID**: Identifier for service tracking.
- **Slashing**: Burning collateral as penalty.

### 9.2 References
- Ethereum Yellow Paper
- Solidity Docs
- OpenZeppelin Contracts
