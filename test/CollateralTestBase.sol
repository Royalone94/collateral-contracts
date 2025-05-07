// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {Collateral} from "../src/Collateral.sol";

abstract contract CollateralTestBase is Test {
    uint16 constant NETUID = 1;
    address constant TRUSTEE_1 = address(0x1000);
    address constant TRUSTEE_2 = address(0x1001);
    address constant TRUSTEE_3 = address(0x1002);
    uint64 constant DECISION_TIMEOUT = 1 days;
    uint256 constant MIN_COLLATERAL_INCREASE = 1 ether;
    string constant URL = "https://reclaimreason.io";
    string constant SLASH_REASON_URL = "https://slashreason.io";
    bytes16 constant URL_CONTENT_MD5_CHECKSUM = 0x12345678901234567890123456789012;

    Collateral public collateral;

    // this boilerplate code had to be copied from Collateral contract to be able to test events and errors
    // it's not possible to import events and errors from another contract
    event Deposit(address indexed account, uint256 amount);
    event ReclaimProcessStarted(
        uint256 indexed reclaimRequestId,
        address indexed account,
        uint256 amount,
        uint64 expirationTime,
        string url,
        bytes16 urlContentMd5Checksum
    );
    event Reclaimed(uint256 indexed reclaimRequestId, address indexed account, uint256 amount);
    event Denied(uint256 indexed reclaimRequestId, string url, bytes16 urlContentMd5Checksum);
    event Slashed(address indexed account, uint256 amount, string url, bytes16 urlContentMd5Checksum);

    error AmountZero();
    error BeforeDenyTimeout();
    error InsufficientAmount();
    error InvalidDepositMethod();
    error NotTrustee();
    error PastDenyTimeout();
    error ReclaimAmountTooLarge();
    error ReclaimAmountTooSmall();
    error ReclaimNotFound();
    error TransferFailed();

    function setUp() public virtual {
        collateral = new Collateral(NETUID, MIN_COLLATERAL_INCREASE, DECISION_TIMEOUT);
        payable(TRUSTEE_1).transfer(3 ether);
        payable(TRUSTEE_2).transfer(3 ether);
        payable(TRUSTEE_3).transfer(3 ether);
    }

    function verifyReclaim(
        uint256 reclaimRequestId,
        address expectedAccount,
        uint256 expectedAmount,
        uint256 expectedExpirationTime,
        bytes16 expectedExecutorUuid
    ) internal view {
        (address account, uint256 amount, uint256 expirationTime, bytes16 executorUuid) = collateral.reclaims(reclaimRequestId);
        assertEq(account, expectedAccount);
        assertEq(amount, expectedAmount);
        assertEq(expirationTime, expectedExpirationTime);
        assertEq(executorUuid, expectedExecutorUuid);
    }
}
