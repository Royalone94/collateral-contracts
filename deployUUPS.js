const { JsonRpcProvider, Wallet, ContractFactory, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { Command } = require("commander");

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
const DEPLOYMENTS_FILE = path.join(__dirname, "deployments.json");

const netuid = process.env.NET_UID || 1;
const minCollateralIncrease = process.env.MIN_COLLATERAL_INCREASE ? BigInt(process.env.MIN_COLLATERAL_INCREASE) : BigInt("1000000000000000"); // 1 ether
const decisionTimeout = process.env.DENY_TIMEOUT || 20;
const NEW_OWNER_PRIVATE_KEY = process.env.NEW_OWNER_PRIVATE_KEY;
const NEW_TRUSTEE_ADDRESS = process.env.NEW_TRUSTEE_ADDRESS;

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

async function deployProxy(wallet, implAddress, netuid, minCollateralIncrease, decisionTimeout) {
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

async function transferOwnershipAndSetTrustee(proxyAddress, currentWallet, newOwnerPrivateKey) {
    if (!newOwnerPrivateKey) {
        console.log("NEW_OWNER_PRIVATE_KEY not set. Skipping ownership transfer and trustee update.");
        return;
    }
    const provider = currentWallet.provider;
    const proxyAsCollateral = new Contract(proxyAddress, collateralAbi, currentWallet);
    const newOwnerWallet = new Wallet(newOwnerPrivateKey, provider);
    const newOwnerAddress = newOwnerWallet.address;

    // 1. Transfer ownership to new owner
    console.log(`Transferring ownership to new owner: ${newOwnerAddress} ...`);
    const tx1 = await proxyAsCollateral.transferOwnership(newOwnerAddress);
    await tx1.wait();
    console.log(`Ownership transferred to: ${newOwnerAddress}`);

    // 2. From new owner, set the new trustee to the new owner's address
    const proxyAsCollateralNewOwner = new Contract(proxyAddress, collateralAbi, newOwnerWallet);
    console.log(`Setting new trustee: ${newOwnerAddress} from new owner...`);
    const tx2 = await proxyAsCollateralNewOwner.setTrustee(newOwnerAddress);
    await tx2.wait();
    console.log(`Trustee updated to: ${newOwnerAddress}`);
}

// CLI logic
const program = new Command();
program
    .name("deployUUPS")
    .description("Deploy or upgrade UUPS proxy for Collateral contract")
    .version("1.0.0");

program
    .command("deploy-proxy")
    .description("Deploy a new implementation and proxy")
    .requiredOption("--rpc-url <url>", "RPC URL", process.env.RPC_URL || "http://127.0.0.1:9944")
    .requiredOption("--private-key <key>", "Deployer private key", process.env.PRIVATE_KEY || "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3")
    .requiredOption("--netuid <netuid>", "Netuid", process.env.NET_UID ? parseInt(process.env.NET_UID) : 1)
    .requiredOption("--min-collateral <amount>", "Minimum collateral increase (wei)", process.env.MIN_COLLATERAL_INCREASE ? BigInt(process.env.MIN_COLLATERAL_INCREASE) : BigInt("1000000000000000"))
    .requiredOption("--decision-timeout <timeout>", "Decision timeout (seconds)", process.env.DENY_TIMEOUT ? parseInt(process.env.DENY_TIMEOUT) : 20)
    .action(async (opts) => {
        const provider = new JsonRpcProvider(opts.rpcUrl);
        const wallet = new Wallet(opts.privateKey, provider);
        const deployments = loadDeployments();
        const newImplAddress = await deployImplementation(wallet);
        const proxyAddress = await deployProxy(wallet, newImplAddress, opts.netuid, opts.minCollateral, opts.decisionTimeout);
        deployments.proxy = proxyAddress;
        deployments.collateralImpl = newImplAddress;
        saveDeployments(deployments);
        console.log("Deployment complete.");
    });

program
    .command("upgrade-proxy")
    .description("Upgrade proxy to new implementation")
    .requiredOption("--rpc-url <url>", "RPC URL", process.env.RPC_URL || "http://127.0.0.1:9944")
    .requiredOption("--private-key <key>", "Current owner private key", process.env.PRIVATE_KEY || "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3")
    .requiredOption("--proxy <address>", "Proxy contract address", process.env.PROXY_ADDRESS)
    .action(async (opts) => {
        const provider = new JsonRpcProvider(opts.rpcUrl);
        const wallet = new Wallet(opts.privateKey, provider);
        const deployments = loadDeployments();
        const newImplAddress = await deployImplementation(wallet);
        await upgradeProxy(opts.proxy, newImplAddress, wallet);
        deployments.collateralImpl = newImplAddress;
        saveDeployments(deployments);
        console.log("Upgrade complete.");
    });

program
    .command("upgrade-proxy-with-new-owner")
    .description("Upgrade proxy, transfer ownership, and set trustee to new owner")
    .requiredOption("--rpc-url <url>", "RPC URL", process.env.RPC_URL || "http://127.0.0.1:9944")
    .requiredOption("--private-key <key>", "Current owner private key", process.env.PRIVATE_KEY || "434469242ece0d04889fdfa54470c3685ac226fb3756f5eaf5ddb6991e1698a3")
    .requiredOption("--proxy <address>", "Proxy contract address", process.env.PROXY_ADDRESS)
    .requiredOption("--new-owner-key <key>", "New owner private key", process.env.NEW_OWNER_PRIVATE_KEY || "259e0eded00353f71eb6be89d8749ad12bf693cbd8aeb6b80cd3a343c0dc8faf")
    .action(async (opts) => {
        const provider = new JsonRpcProvider(opts.rpcUrl);
        const wallet = new Wallet(opts.privateKey, provider);
        const deployments = loadDeployments();
        const newImplAddress = await deployImplementation(wallet);
        await upgradeProxy(opts.proxy, newImplAddress, wallet);
        deployments.collateralImpl = newImplAddress;
        saveDeployments(deployments);
        await transferOwnershipAndSetTrustee(opts.proxy, wallet, opts.newOwnerKey);
        console.log("Upgrade, ownership transfer, and trustee update complete.");
    });

program.showHelpAfterError();

if (!process.argv.slice(2).some(arg => !arg.startsWith('-'))) {
  // No command specified, default to deploy-proxy
  program.parse(['deploy-proxy', ...process.argv.slice(2)], { from: 'user' });
} else {
  program.parseAsync(process.argv);
}