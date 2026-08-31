// Compile the Time Vault contracts and write the artefacts to contracts/out.
//
//   cd contracts && npm install && node build.js
//
// The settings here are the settings a verifier needs, so they live in one
// place rather than in someone's memory:
//
//   solc 0.8.24, optimizer on, 200 runs, evmVersion paris.
//
// paris rather than the 0.8.24 default of shanghai, because shanghai emits the
// PUSH0 opcode and Robinhood Chain has not been confirmed to accept it. A
// contract that deploys and then reverts on every call is a bad way to find
// out. Once PUSH0 is confirmed this can move to shanghai, but the deployed
// bytecode must be compiled with whatever is written here or verification will
// not match.
const fs = require('fs');
const path = require('path');
const solc = require('solc');

const SOURCES = ['src/TimeVaultEscrow.sol'];
const OUT = path.join(__dirname, 'out');

const input = {
    language: 'Solidity',
    sources: Object.fromEntries(SOURCES.map(f => [
        f, { content: fs.readFileSync(path.join(__dirname, f), 'utf8') },
    ])),
    settings: {
        optimizer: { enabled: true, runs: 200 },
        evmVersion: 'paris',
        outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object', 'evm.deployedBytecode.object'] } },
    },
};

const out = JSON.parse(solc.compile(JSON.stringify(input)));

const errors = (out.errors || []).filter(e => e.severity === 'error');
const warnings = (out.errors || []).filter(e => e.severity !== 'error');

for (const w of warnings) console.log(w.formattedMessage.trim() + '\n');
for (const e of errors) console.error(e.formattedMessage.trim() + '\n');
if (errors.length) process.exit(1);

fs.mkdirSync(OUT, { recursive: true });

// The standard-json input is what Blockscout wants for verification, so write
// it out next to the artefacts instead of reconstructing it by hand later.
fs.writeFileSync(path.join(OUT, 'standard-input.json'), JSON.stringify(input, null, 2));

let total = 0;
for (const file of SOURCES) {
    for (const [name, c] of Object.entries(out.contracts[file] || {})) {
        const bytecode = '0x' + c.evm.bytecode.object;
        const size = c.evm.deployedBytecode.object.length / 2;
        total += size;
        fs.writeFileSync(path.join(OUT, name + '.abi.json'), JSON.stringify(c.abi, null, 2));
        fs.writeFileSync(path.join(OUT, name + '.bin'), bytecode);
        // 24576 is the EIP-170 limit. Print the headroom so it is obvious when
        // the contract is getting close rather than on the failing deploy.
        console.log(
            `${name.padEnd(18)} ${String(size).padStart(6)} bytes deployed` +
            `   ${(24576 - size).toLocaleString()} under the limit`
        );
    }
}

console.log(`\n${warnings.length} warning(s), 0 errors. Artefacts in contracts/out.`);
if (total === 0) process.exit(1);
