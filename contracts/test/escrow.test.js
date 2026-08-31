// Tests for TimeVaultEscrow.
//
// The contract header makes a set of promises. Every promise gets a test here,
// named so that the test output reads as the claim it is checking. If a claim
// on the website cannot be traced to a passing test in this file, one of the
// two is wrong.
//
//   cd contracts && npm install && npx hardhat test

const { expect } = require('chai');
const { ethers, network } = require('hardhat');

const ONE = 10n ** 18n;
const DAY = 24 * 60 * 60;
const WINDOW = 7 * DAY;      // delivery window used by most tests
const REVIEW = 3 * DAY;
const ARBITRATION = 14 * DAY;

const State = {
    None: 0n, Escrowed: 1n, InProgress: 2n, Review: 3n,
    Released: 4n, Disputed: 5n, Refunded: 6n, Settled: 7n,
};

// hardhat-chai-matchers is not installed on purpose: this repo keeps its
// dependency list short enough to read. Ethers already decodes the custom
// error name into the message when it knows the ABI, so a substring check is
// enough and it is obvious what it does.
async function reverts(promise, name) {
    try {
        await promise;
    } catch (err) {
        const text = err.message || String(err);
        expect(text, `expected ${name}, got: ${text}`).to.contain(name);
        return;
    }
    throw new Error(`expected revert ${name}, but the call succeeded`);
}

async function jump(seconds) {
    await network.provider.send('evm_increaseTime', [seconds]);
    await network.provider.send('evm_mine');
}

describe('TimeVaultEscrow', function () {
    let token, escrow;
    let owner, buyer, provider, kairos, vorian, treasury, stranger;

    // A whole order, funded and ready, so each test starts from the state it
    // actually cares about rather than repeating six lines of setup.
    async function fundOrder(amount = 100n * ONE, hours_ = 10) {
        await token.connect(buyer).approve(await escrow.getAddress(), amount);
        await escrow.connect(buyer).fund(provider.address, 1, hours_, amount, WINDOW);
        return escrow.orderCount();
    }

    beforeEach(async function () {
        [owner, buyer, provider, kairos, vorian, treasury, stranger] = await ethers.getSigners();

        token = await (await ethers.getContractFactory('MockERC20')).deploy(0);
        escrow = await (await ethers.getContractFactory('TimeVaultEscrow')).deploy(
            await token.getAddress(), treasury.address, kairos.address, vorian.address,
        );

        await token.mint(buyer.address, 1000n * ONE);
    });

    // ------------------------------------------------------------- funding

    describe('funding', function () {
        it('records the amount that actually arrived, not the amount requested', async function () {
            await token.setFee(500); // a token that keeps 5% in transit
            await token.connect(buyer).approve(await escrow.getAddress(), 100n * ONE);
            await escrow.connect(buyer).fund(provider.address, 1, 10, 100n * ONE, WINDOW);

            const order = await escrow.getOrder(1);
            expect(order.amount).to.equal(95n * ONE);
            expect(await escrow.totalEscrowed()).to.equal(95n * ONE);
            expect(await token.balanceOf(await escrow.getAddress())).to.equal(95n * ONE);
        });

        it('snapshots the fee so a later change cannot reach back into a funded order', async function () {
            const id = await fundOrder();
            await escrow.connect(owner).setFee(200); // the ceiling, four times the published rate

            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(buyer).accept(id);

            // Paid at 0.5%, the rate that was live when the money went in.
            expect(await token.balanceOf(treasury.address)).to.equal((100n * ONE * 50n) / 10000n);
        });

        it('refuses an order the token did not actually pay for', async function () {
            const bad = await (await ethers.getContractFactory('MockFalseERC20')).deploy();
            const e = await (await ethers.getContractFactory('TimeVaultEscrow')).deploy(
                await bad.getAddress(), treasury.address, kairos.address, vorian.address,
            );
            await reverts(
                e.connect(buyer).fund(provider.address, 1, 10, 100n * ONE, WINDOW),
                'TransferFailed',
            );
            expect(await e.orderCount()).to.equal(0n);
        });

        it('works with a token that returns nothing instead of a bool', async function () {
            const quiet = await (await ethers.getContractFactory('MockNoReturnERC20')).deploy();
            const e = await (await ethers.getContractFactory('TimeVaultEscrow')).deploy(
                await quiet.getAddress(), treasury.address, kairos.address, vorian.address,
            );
            await quiet.mint(buyer.address, 100n * ONE);
            await quiet.connect(buyer).approve(await e.getAddress(), 100n * ONE);
            await e.connect(buyer).fund(provider.address, 1, 10, 100n * ONE, WINDOW);
            expect(await e.totalEscrowed()).to.equal(100n * ONE);
        });

        it('rejects zero amounts, zero hours, self-dealing and silly deadlines', async function () {
            const at = await escrow.getAddress();
            await token.connect(buyer).approve(at, 1000n * ONE);

            await reverts(escrow.connect(buyer).fund(provider.address, 1, 10, 0, WINDOW), 'BadInput');
            await reverts(escrow.connect(buyer).fund(provider.address, 1, 0, ONE, WINDOW), 'BadInput');
            await reverts(escrow.connect(buyer).fund(buyer.address, 1, 10, ONE, WINDOW), 'BadInput');
            await reverts(escrow.connect(buyer).fund(ethers.ZeroAddress, 1, 10, ONE, WINDOW), 'BadInput');
            await reverts(escrow.connect(buyer).fund(provider.address, 1, 10, ONE, 60), 'BadInput');
            await reverts(escrow.connect(buyer).fund(provider.address, 1, 10, ONE, 400 * DAY), 'BadInput');
        });
    });

    // -------------------------------------------------------- the happy path

    describe('the happy path', function () {
        it('pays the provider when the buyer accepts, minus the published 0.5%', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'ipfs://delivery');
            await escrow.connect(buyer).accept(id);

            const fee = (100n * ONE * 50n) / 10000n;
            expect(await token.balanceOf(provider.address)).to.equal(100n * ONE - fee);
            expect(await token.balanceOf(treasury.address)).to.equal(fee);
            expect((await escrow.getOrder(id)).state).to.equal(State.Released);
            expect(await escrow.totalEscrowed()).to.equal(0n);
        });

        it('pays out on its own once the review window closes, called by a total stranger', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'ipfs://delivery');

            expect(await escrow.settleable(id)).to.equal(false);
            await reverts(escrow.connect(stranger).settle(id), 'TooEarly');

            await jump(REVIEW + 1);

            expect(await escrow.settleable(id)).to.equal(true);
            await escrow.connect(stranger).settle(id); // nobody from Time Vault involved
            expect((await escrow.getOrder(id)).state).to.equal(State.Released);
        });

        it('lets the provider deliver late rather than destroying the order', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await jump(WINDOW + DAY);

            await escrow.connect(provider).deliver(id, 'ipfs://late');
            expect((await escrow.getOrder(id)).state).to.equal(State.Review);
        });

        it('keeps the states in the order the interface shows them', async function () {
            const id = await fundOrder();
            expect((await escrow.getOrder(id)).state).to.equal(State.Escrowed);
            await escrow.connect(provider).start(id);
            expect((await escrow.getOrder(id)).state).to.equal(State.InProgress);
            await escrow.connect(provider).deliver(id, 'x');
            expect((await escrow.getOrder(id)).state).to.equal(State.Review);
            await escrow.connect(buyer).accept(id);
            expect((await escrow.getOrder(id)).state).to.equal(State.Released);
        });
    });

    // --------------------------------------------- what Time Vault cannot do

    describe('what nobody at Time Vault can do', function () {
        it('gives the owner no way to take escrowed money', async function () {
            const id = await fundOrder();
            await reverts(
                escrow.connect(owner).rescue(await token.getAddress(), owner.address, 1n),
                'WouldTouchEscrow',
            );
            expect(await escrow.unallocated()).to.equal(0n);
            expect((await escrow.getOrder(id)).state).to.equal(State.Escrowed);
        });

        it('lets the owner recover only what nobody is owed', async function () {
            await fundOrder();
            await token.mint(await escrow.getAddress(), 7n * ONE); // sent here by mistake

            expect(await escrow.unallocated()).to.equal(7n * ONE);
            await reverts(
                escrow.connect(owner).rescue(await token.getAddress(), owner.address, 8n * ONE),
                'WouldTouchEscrow',
            );
            await escrow.connect(owner).rescue(await token.getAddress(), owner.address, 7n * ONE);
            expect(await token.balanceOf(owner.address)).to.equal(7n * ONE);
        });

        it('gives KAIROS no power beyond writing a number', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');

            const before = await token.balanceOf(await escrow.getAddress());
            await escrow.connect(kairos).attest(id, 9870, 'ipfs://evidence');

            expect(await token.balanceOf(await escrow.getAddress())).to.equal(before);
            expect((await escrow.getOrder(id)).state).to.equal(State.Review);

            await reverts(escrow.connect(kairos).accept(id), 'NotBuyer');
            await reverts(escrow.connect(kairos).resolve(id, 0, 'x'), 'NotArbiter');
        });

        it('gives VORIAN nothing until the buyer opens a dispute', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');

            await reverts(escrow.connect(vorian).resolve(id, 100n * ONE, 'x'), 'WrongState');
            await reverts(escrow.connect(vorian).accept(id), 'NotBuyer');
            await reverts(escrow.connect(vorian).refund(id), 'NotProvider');
        });

        it('caps the fee below what any owner could set it to', async function () {
            await reverts(escrow.connect(owner).setFee(201), 'BadInput');
            await escrow.connect(owner).setFee(200);
            expect(await escrow.feeBps()).to.equal(200n);
        });

        it('keeps admin functions shut to everyone else', async function () {
            await reverts(escrow.connect(stranger).setFee(10), 'NotOwner');
            await reverts(escrow.connect(stranger).setFeeRecipient(stranger.address), 'NotOwner');
            await reverts(escrow.connect(stranger).setKairos(stranger.address), 'NotOwner');
            await reverts(escrow.connect(stranger).setVorian(stranger.address), 'NotOwner');
            await reverts(escrow.connect(stranger).setPaused(true), 'NotOwner');
            await reverts(
                escrow.connect(stranger).rescue(await token.getAddress(), stranger.address, 1n),
                'NotOwner',
            );
        });

        it('cannot freeze money that is already escrowed by pausing', async function () {
            const id = await fundOrder();
            await escrow.connect(owner).setPaused(true);

            // New orders stop.
            await token.connect(buyer).approve(await escrow.getAddress(), ONE);
            await reverts(escrow.connect(buyer).fund(provider.address, 2, 1, ONE, WINDOW), 'Paused');

            // The order that already exists carries on exactly as before.
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(buyer).accept(id);
            expect((await escrow.getOrder(id)).state).to.equal(State.Released);
        });

        it('hands ownership over in two steps, so it cannot be sent to a dead address', async function () {
            await escrow.connect(owner).transferOwnership(stranger.address);
            expect(await escrow.owner()).to.equal(owner.address);

            await reverts(escrow.connect(buyer).acceptOwnership(), 'NotOwner');
            await escrow.connect(stranger).acceptOwnership();
            expect(await escrow.owner()).to.equal(stranger.address);
        });
    });

    // -------------------------------------------------------------- refunds

    describe('getting the money back', function () {
        it('lets the buyer walk away for free before the provider starts', async function () {
            const id = await fundOrder();
            await escrow.connect(buyer).cancel(id);

            expect(await token.balanceOf(buyer.address)).to.equal(1000n * ONE);
            expect(await token.balanceOf(treasury.address)).to.equal(0n); // no fee on a refund
            expect((await escrow.getOrder(id)).state).to.equal(State.Refunded);
        });

        it('closes that exit once the provider has started work', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await reverts(escrow.connect(buyer).cancel(id), 'WrongState');
        });

        it('lets the buyer reclaim when nothing was delivered by the deadline', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);

            await reverts(escrow.connect(buyer).reclaim(id), 'TooEarly');
            await jump(WINDOW + 1);
            await escrow.connect(buyer).reclaim(id);

            expect(await token.balanceOf(buyer.address)).to.equal(1000n * ONE);
            expect(await escrow.totalEscrowed()).to.equal(0n);
        });

        it('lets the provider hand the money back at any point before release', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(provider).refund(id);

            expect(await token.balanceOf(buyer.address)).to.equal(1000n * ONE);
            expect(await token.balanceOf(treasury.address)).to.equal(0n);
        });

        it('will not pay the same order out twice', async function () {
            const id = await fundOrder();
            await escrow.connect(buyer).cancel(id);
            await reverts(escrow.connect(buyer).cancel(id), 'WrongState');
            await reverts(escrow.connect(provider).start(id), 'WrongState');
        });
    });

    // ------------------------------------------------------------- disputes

    describe('disputes', function () {
        async function disputed() {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(buyer).dispute(id, 'half the pages are missing');
            return id;
        }

        it('freezes the money the moment the buyer objects', async function () {
            const id = await disputed();
            expect((await escrow.getOrder(id)).state).to.equal(State.Disputed);
            expect(await escrow.totalEscrowed()).to.equal(100n * ONE);
            await reverts(escrow.connect(stranger).settle(id), 'WrongState');
            await reverts(escrow.connect(buyer).accept(id), 'WrongState');
        });

        it('closes the objection window when the review window closes', async function () {
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await jump(REVIEW + 1);
            await reverts(escrow.connect(buyer).dispute(id, 'too late'), 'TooLate');
        });

        it('lets VORIAN split it, charging the fee only on the provider share', async function () {
            const id = await disputed();
            const toProvider = 60n * ONE;
            await escrow.connect(vorian).resolve(id, toProvider, 'ipfs://ruling');

            const fee = (toProvider * 50n) / 10000n;
            expect(await token.balanceOf(provider.address)).to.equal(toProvider - fee);
            expect(await token.balanceOf(treasury.address)).to.equal(fee);
            expect(await token.balanceOf(buyer.address)).to.equal(900n * ONE + 40n * ONE);
            expect(await escrow.totalEscrowed()).to.equal(0n);
        });

        it('will not let VORIAN pay out more than the order holds', async function () {
            const id = await disputed();
            await reverts(escrow.connect(vorian).resolve(id, 100n * ONE + 1n, 'x'), 'BadInput');
        });

        it('takes the power away from VORIAN once its window closes', async function () {
            const id = await disputed();
            await jump(ARBITRATION + 1);
            await reverts(escrow.connect(vorian).resolve(id, 100n * ONE, 'x'), 'TooLate');
        });

        it('splits down the middle when VORIAN never answers, and charges nothing for it', async function () {
            const id = await disputed();
            await reverts(escrow.connect(stranger).resolveByTimeout(id), 'TooEarly');

            await jump(ARBITRATION + 1);
            await escrow.connect(stranger).resolveByTimeout(id); // anyone can unstick it

            expect(await token.balanceOf(provider.address)).to.equal(50n * ONE);
            expect(await token.balanceOf(buyer.address)).to.equal(950n * ONE);
            expect(await token.balanceOf(treasury.address)).to.equal(0n);
            expect((await escrow.getOrder(id)).state).to.equal(State.Settled);
        });

        it('gives the odd token to the buyer rather than the provider', async function () {
            const id = await fundOrder(101n, 1);
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(buyer).dispute(id, 'x');
            await jump(ARBITRATION + 1);
            await escrow.connect(stranger).resolveByTimeout(id);

            expect(await token.balanceOf(provider.address)).to.equal(50n);
            expect(await token.balanceOf(buyer.address)).to.equal(1000n * ONE - 101n + 51n);
        });
    });

    // ----------------------------------------------------------- accounting

    describe('the books', function () {
        it('never owes more than it holds, across a mixed run of orders', async function () {
            const at = await escrow.getAddress();
            await token.connect(buyer).approve(at, 1000n * ONE);

            // chai 4 will not compare BigInts with gte, and the invariant is
            // clearer stated outright than dressed up in a matcher.
            const check = async () => {
                const held = await token.balanceOf(at);
                const owed = await escrow.totalEscrowed();
                expect(held >= owed, `holds ${held}, owes ${owed}`).to.equal(true);
            };

            // released, refunded, reclaimed, arbitrated, and one left open
            for (let i = 0; i < 5; i++) {
                await escrow.connect(buyer).fund(provider.address, i, 4, 20n * ONE, WINDOW);
                await check();
            }
            expect(await escrow.totalEscrowed()).to.equal(100n * ONE);

            await escrow.connect(provider).start(1);
            await escrow.connect(provider).deliver(1, 'x');
            await escrow.connect(buyer).accept(1);
            await check();

            await escrow.connect(buyer).cancel(2);
            await check();

            await escrow.connect(provider).start(3);
            await jump(WINDOW + 1);
            await escrow.connect(buyer).reclaim(3);
            await check();

            await escrow.connect(provider).start(4);
            await escrow.connect(provider).deliver(4, 'x');
            await escrow.connect(buyer).dispute(4, 'x');
            await escrow.connect(vorian).resolve(4, 10n * ONE, 'x');
            await check();

            // Order 5 is untouched, and its money is still exactly where it was.
            expect(await escrow.totalEscrowed()).to.equal(20n * ONE);
            expect(await token.balanceOf(at)).to.equal(20n * ONE);
            expect(await escrow.unallocated()).to.equal(0n);
        });

        it('quotes the same fee it later charges', async function () {
            const [fee, net] = await escrow.quote(100n * ONE);
            const id = await fundOrder();
            await escrow.connect(provider).start(id);
            await escrow.connect(provider).deliver(id, 'x');
            await escrow.connect(buyer).accept(id);

            expect(await token.balanceOf(treasury.address)).to.equal(fee);
            expect(await token.balanceOf(provider.address)).to.equal(net);
        });
    });
});
