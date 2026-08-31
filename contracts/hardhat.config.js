// Hardhat is used for the test suite only. The bytecode that gets deployed and
// verified comes from build.js, which calls solc directly with the settings
// written down there. Keep the two in step: same version, same optimizer runs,
// same evmVersion.
require('@nomicfoundation/hardhat-ethers');

module.exports = {
    solidity: {
        version: '0.8.24',
        settings: {
            optimizer: { enabled: true, runs: 200 },
            evmVersion: 'paris',
        },
    },
    paths: { sources: './src', tests: './test', cache: './cache', artifacts: './artifacts' },
    mocha: { timeout: 120000 },
};
