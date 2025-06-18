const { JsonRpcProvider, Wallet, ContractFactory, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");

// Load compiled artifacts
const CollateralArtifact = require("./out/Collateral.sol/Collateral.json");
// Use OpenZeppelin's precompiled proxy artifact!
const ERC1967ProxyArtifact = require("./node_modules/@openzeppelin/contracts/build/contracts/ERC1967Proxy.json");

const collateralAbi = CollateralArtifact.abi;
const collateralBytecode = CollateralArtifact.bytecode.object;
const proxyAbi = ERC1967ProxyArtifact.abi;
const proxyBytecode = ERC1967ProxyArtifact.bytecode;

// To use ethers.getContractAt (common in Hardhat), we might need to expose it
// or replicate its behavior if not in a Hardhat environment script runner.
// Assuming a Hardhat environment where `ethers` is globally available:
// If not, you would need to setup ethers provider/signer and manually get ABI/Bytecode
// For this refactor, we assume `ethers` is available similar to a Hardhat script.
const ethers = require("ethers"); // Or assumes global `ethers` from Hardhat environment

// Config
const RPC_URL = process.env.RPC_URL || "http://127.0.0.1:9944"; 
// const RPC_URL = process.env.RPC_URL || "https://test.finney.opentensor.ai";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3"; // Your deployer private key
const DEPLOYMENTS_FILE = path.join(__dirname, "deployments.json");

const netuid = process.env.NET_UID || 1;
const minCollateralIncrease = process.env.MIN_COLLATERAL_INCREASE ? BigInt(process.env.MIN_COLLATERAL_INCREASE) : BigInt("1000000000000000"); // 1 ether
const decisionTimeout = process.env.DENY_TIMEOUT || 20;

function loadDeployments() {
    if (fs.existsSync(DEPLOYMENTS_FILE)) {
        return JSON.parse(fs.readFileSync(DEPLOYMENTS_FILE, "utf8"));
    }
    return {};
}

function saveDeployments(deployments) {
    fs.writeFileSync(DEPLOYMENTS_FILE, JSON.stringify(deployments, null, 2));
}

async function deployImplementation(wallet) {
    const CollateralFactory = new ContractFactory(collateralAbi, collateralBytecode, wallet);
    const collateralImpl = await CollateralFactory.deploy();
    await collateralImpl.waitForDeployment();
    const newImplAddress = collateralImpl.target;
    console.log("New Collateral implementation deployed at:", newImplAddress);
    return newImplAddress;
}

async function deployProxy(wallet, implAddress) {
    const CollateralFactory = new ContractFactory(collateralAbi, collateralBytecode, wallet);
    const initData = CollateralFactory.interface.encodeFunctionData(
        "initialize",
        [netuid, wallet.address, minCollateralIncrease, decisionTimeout]
    );
    const ProxyFactory = new ContractFactory(proxyAbi, proxyBytecode, wallet);
    console.log("Deploying proxy with implementation", implAddress);
    const proxy = await ProxyFactory.deploy(implAddress, initData);
    await proxy.waitForDeployment();
    const proxyAddress = proxy.target;

    console.log(`Contract Address: ${proxyAddress}`);

    // Verify owner after deployment and initialization
    const ownerAfterInit = await getProxyOwner(proxyAddress, wallet);
    console.log("Proxy owner after initialization:", ownerAfterInit);
    if (ownerAfterInit.toLowerCase() !== wallet.address.toLowerCase()) {
        console.error("Owner mismatch after initial deployment!");
    }

    return proxyAddress;
}

async function getProxyOwner(proxyAddress, wallet) {
    // In UUPS, the owner is managed by the implementation contract.
    // We interact with the proxy using the implementation's ABI to query state.
    try {
        // Use the full collateral ABI to interact with the proxy for state queries
        const proxyAsCollateral = new Contract(proxyAddress, collateralAbi, wallet);
        const owner = await proxyAsCollateral.owner();
        return owner;
    } catch (e) {
        console.warn("Could not fetch proxy owner (this is expected if proxy is not initialized or implementation is not deployed/compatible):", e.message);
        return null;
    }
}

async function upgradeProxy(proxyAddress, newImplAddress, wallet) {
    // Check owner using the full ABI via the proxy before attempting upgrade
    const owner = await getProxyOwner(proxyAddress, wallet);
    console.log(`Owner check before upgrade: Proxy owner = ${owner}, Wallet = ${wallet.address}`);
    if (owner && owner.toLowerCase() !== wallet.address.toLowerCase()) {
        throw new Error(`Wallet is not the owner of the proxy. Proxy owner: ${owner}, Wallet: ${wallet.address}`);
    }

    // Use the full Collateral ABI to interact with the proxy for the upgrade call
    const proxyAsCollateral = new Contract(proxyAddress, collateralAbi, wallet);
    
    console.log("Attempting to upgrade proxy...");
    const tx = await proxyAsCollateral.upgradeToAndCall(newImplAddress, "0x");
    await tx.wait();
    console.log(`Proxy at ${proxyAddress} upgraded to new implementation: ${newImplAddress}`);
    console.log(`Contract Address: ${proxyAddress}`);

    // Verify owner after upgrade (should remain the same)
    const ownerAfterUpgrade = await getProxyOwner(proxyAddress, wallet);
    console.log("Proxy owner after upgrade:", ownerAfterUpgrade);
    if (ownerAfterUpgrade && ownerAfterUpgrade.toLowerCase() !== wallet.address.toLowerCase()) {
        console.error("Owner mismatch after upgrade!");
    }
}

async function main() {
    const provider = new JsonRpcProvider(RPC_URL);
    const wallet = new Wallet(PRIVATE_KEY, provider);
    let deployments = loadDeployments();

    // 1. Deploy new implementation
    const newImplAddress = await deployImplementation(wallet);

    // 2. Deploy proxy if needed, else upgrade
    let proxyAddress = deployments.proxy;
    if (!proxyAddress) {
        proxyAddress = await deployProxy(wallet, newImplAddress);
        deployments.proxy = proxyAddress;
        deployments.collateralImpl = newImplAddress;
        saveDeployments(deployments);
    } else {
        // Check current implementation using storage slot
        const implSlot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"; // Standard UUPS storage slot
        const currentImpl = await provider.getStorage(proxyAddress, implSlot);
        const formattedCurrentImpl = "0x" + currentImpl.slice(26).toLowerCase();

        if (formattedCurrentImpl !== newImplAddress.toLowerCase()) {
            try {
                await upgradeProxy(proxyAddress, newImplAddress, wallet);
                deployments.collateralImpl = newImplAddress;
                saveDeployments(deployments);
            } catch (e) {
                console.error("Upgrade failed:", e.message);
                // Print diagnostics
                const owner = await getProxyOwner(proxyAddress, wallet);
                console.error(`Proxy owner diagnostic: Proxy owner = ${owner}, Wallet = ${wallet.address}`);
                process.exit(1);
            }
        } else {
            console.log("Proxy already uses the latest implementation.");
        }
    }

    // 3. Interact with the contract via the proxy
    const proxyToUse = deployments.proxy;
    // Interact with the proxy using the latest implementation ABI
    const collateral = new Contract(proxyToUse, collateralAbi, wallet);

    try {
        const netuidValue = await collateral.NETUID();
        console.log("Proxy NETUID value:", netuidValue.toString());
    } catch (e) {
        console.error("Error reading NETUID from proxy:", e.message);
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});