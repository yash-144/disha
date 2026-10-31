// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title DishaDocumentRegistry
 * @dev Stores immutable document hash anchors for DISHA intervention records.
 */
contract DishaDocumentRegistry {
    event DocumentAnchored(bytes32 indexed documentHash, address indexed anchorer, uint256 timestamp);

    mapping(bytes32 => uint256) public documentAnchors;

    function anchorDocument(bytes32 documentHash) external {
        require(documentAnchors[documentHash] == 0, "DISHA: Document already anchored");
        documentAnchors[documentHash] = block.timestamp;
        emit DocumentAnchored(documentHash, msg.sender, block.timestamp);
    }

    function verifyDocument(bytes32 documentHash) external view returns (bool, uint256) {
        uint256 timestamp = documentAnchors[documentHash];
        return (timestamp > 0, timestamp);
    }
}
