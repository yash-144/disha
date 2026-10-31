// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title DishaStudentIdentityNFT
 * @dev Soulbound non-transferable token linked to DISHA student identity hash.
 */
contract DishaStudentIdentityNFT {
    string public constant name = "DISHA Student Identity";
    string public constant symbol = "DISHA-ID";

    mapping(bytes32 => address) public identityOwners;

    event IdentityMinted(bytes32 indexed dishaIdHash, address indexed studentAddress);

    function mintIdentity(bytes32 dishaIdHash, address studentAddress) external {
        require(identityOwners[dishaIdHash] == address(0), "DISHA: Identity already minted");
        identityOwners[dishaIdHash] = studentAddress;
        emit IdentityMinted(dishaIdHash, studentAddress);
    }
}
