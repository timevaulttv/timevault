// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/*
    TIME VAULT ESCROW

    A buyer funds an order in $TV before the work starts. The provider does the
    work. The money leaves this contract only in ways written below, and every
    one of them is triggered by the buyer, the provider, or the clock.

    THE PROPERTY THAT MATTERS

    In the normal path, no address controlled by Time Vault can move a single
    token. Not the owner, not KAIROS, not VORIAN. Release happens because the
    buyer accepted, or because the review window ran out. That is the whole
    point of putting this on chain instead of holding funds in a company bank
    account, so it is worth stating plainly rather than burying it.

    The one exception is a disputed order. If, and only if, the buyer raises a
    dispute, VORIAN may split that order's funds. VORIAN cannot touch any other
    order, cannot take a cut, cannot pay out more than the order holds, and
    loses the power entirely once the arbitration window closes.

    WHAT EACH PARTY CAN DO

      buyer     fund, cancel before work starts, accept (releases early),
                dispute during review, reclaim if nothing was delivered by the
                deadline
      provider  start, deliver, refund voluntarily at any point before release
      anyone    settle an order whose review window has run out, resolve a
                dispute VORIAN never answered
      KAIROS    write a confidence score and an evidence pointer. Nothing else.
                It cannot move money and cannot change a state.
      VORIAN    split a disputed order, inside the arbitration window only
      owner     set the fee (hard capped), set who receives it, rotate the
                KAIROS and VORIAN keys, and pause new funding. The owner has no
                function that touches an order that already exists.

    STATES, and the names the interface already uses for them

      Escrowed    money is in, the provider has not started
      InProgress  provider accepted, clock running to deliverBy
      Review      delivered, buyer is looking at it. Shown as KAIROS Verifying
      Released    provider paid
      Disputed    buyer objected, waiting on VORIAN
      Refunded    buyer got everything back
      Settled     closed by arbitration, or by arbitration timing out

    HONEST NOTES

    KAIROS and VORIAN are AI agents. On chain they are ordinary addresses whose
    keys Time Vault holds. Anyone reading this should treat VORIAN as a trusted
    arbiter with bounded powers, not as something trustless. The bounds are in
    the code: one order, one window, no fee, and a 50/50 fallback if it never
    answers. That fallback exists so the protocol cannot profit from staying
    silent.

    This contract does not yet know about Service NFTs. The buyer names the
    provider and the listing when funding. Wiring the listing to a minted NFT
    is a later step on the roadmap, and the listingId field is here so that
    step does not need a new escrow.

    Fees follow the published schedule: 0.5% on escrow settlement. The rate is
    snapshotted into each order when it is funded, so a later fee change can
    never reach back into money that is already escrowed. No fee is charged on
    a refund, and none on an arbitration timeout.
*/

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

contract TimeVaultEscrow {
    // ---------------------------------------------------------------- types

    enum State {
        None,
        Escrowed,
        InProgress,
        Review,
        Released,
        Disputed,
        Refunded,
        Settled
    }

    struct Order {
        address buyer;
        address provider;
        uint256 listingId;      // which set of hours this draws from
        uint128 amount;         // what actually arrived, not what was asked for
        uint64 deliverBy;
        uint64 reviewUntil;     // set when the provider delivers
        uint64 arbitrateUntil;  // set when the buyer disputes
        uint32 hoursBought;
        uint16 feeBps;          // snapshot, so a fee change cannot apply backwards
        State state;
    }

    // ------------------------------------------------------------ constants

    /// The buyer gets this long to look at the delivery before it settles.
    uint64 public constant REVIEW_WINDOW = 3 days;

    /// VORIAN gets this long to rule once a dispute is open.
    uint64 public constant ARBITRATION_WINDOW = 14 days;

    uint64 public constant MIN_DELIVERY_WINDOW = 1 hours;
    uint64 public constant MAX_DELIVERY_WINDOW = 365 days;

    /// The published rate is 50. This ceiling means governance cannot raise the
    /// fee past 2% no matter who ends up holding the owner key.
    uint16 public constant MAX_FEE_BPS = 200;

    uint16 private constant BPS = 10_000;

    // ---------------------------------------------------------------- state

    /// The escrowed asset. Immutable: this contract will only ever hold $TV.
    IERC20 public immutable TOKEN;

    address public owner;
    address public pendingOwner;
    address public kairos;
    address public vorian;
    address public feeRecipient;

    uint16 public feeBps = 50; // 0.5%
    bool public paused;        // blocks new funding only

    uint256 public orderCount;

    /// Sum of every live order. The contract's token balance is never allowed
    /// to fall below this, and rescue() cannot reach it. Anyone can check the
    /// invariant on the explorer: balanceOf(escrow) >= totalEscrowed.
    uint256 public totalEscrowed;

    mapping(uint256 => Order) private _orders;

    uint256 private _lock = 1;

    // --------------------------------------------------------------- events

    event OrderFunded(
        uint256 indexed id,
        address indexed buyer,
        address indexed provider,
        uint256 listingId,
        uint256 amount,
        uint32 hoursBought,
        uint64 deliverBy,
        uint16 feeBps
    );
    event OrderStarted(uint256 indexed id);
    event OrderDelivered(uint256 indexed id, string uri, uint64 reviewUntil);
    event Attested(uint256 indexed id, uint16 score, string uri);
    event OrderReleased(uint256 indexed id, address indexed by, uint256 toProvider, uint256 fee);
    event OrderRefunded(uint256 indexed id, address indexed by, uint256 toBuyer);
    event DisputeRaised(uint256 indexed id, string reason, uint64 arbitrateUntil);
    event DisputeResolved(uint256 indexed id, uint256 toProvider, uint256 toBuyer, uint256 fee, string uri);
    event DisputeTimedOut(uint256 indexed id, uint256 toProvider, uint256 toBuyer);

    event FeeChanged(uint16 bps);
    event FeeRecipientChanged(address recipient);
    event AgentChanged(bytes32 indexed role, address agent);
    event PausedChanged(bool paused);
    event OwnershipStarted(address indexed to);
    event OwnershipTransferred(address indexed from, address indexed to);
    event Rescued(address indexed token, address indexed to, uint256 amount);

    // --------------------------------------------------------------- errors

    error NotOwner();
    error NotBuyer();
    error NotProvider();
    error NotArbiter();
    error NotVerifier();
    error WrongState();
    error TooEarly();
    error TooLate();
    error BadInput();
    error Paused();
    error Reentrancy();
    error TransferFailed();
    error WouldTouchEscrow();

    // ------------------------------------------------------------ modifiers

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier guarded() {
        if (_lock != 1) revert Reentrancy();
        _lock = 2;
        _;
        _lock = 1;
    }

    // ---------------------------------------------------------- constructor

    constructor(address token_, address feeRecipient_, address kairos_, address vorian_) {
        if (token_ == address(0) || feeRecipient_ == address(0)) revert BadInput();
        if (kairos_ == address(0) || vorian_ == address(0)) revert BadInput();
        TOKEN = IERC20(token_);
        owner = msg.sender;
        feeRecipient = feeRecipient_;
        kairos = kairos_;
        vorian = vorian_;
        emit OwnershipTransferred(address(0), msg.sender);
        emit FeeRecipientChanged(feeRecipient_);
        emit AgentChanged("KAIROS", kairos_);
        emit AgentChanged("VORIAN", vorian_);
        emit FeeChanged(feeBps);
    }

    // ------------------------------------------------------------ the order

    /**
     * Lock a buyer's payment before the work starts.
     *
     * The buyer chooses deliveryWindow, so the deadline is theirs and not the
     * platform's. The amount recorded is the balance this contract actually
     * gained, which matters because $TV trades through a venue that takes a
     * cut, and a token that charges on transfer would otherwise leave the
     * contract promising more than it holds.
     */
    function fund(
        address provider,
        uint256 listingId,
        uint32 hoursBought,
        uint256 amount,
        uint64 deliveryWindow
    ) external guarded returns (uint256 id) {
        if (paused) revert Paused();
        if (provider == address(0) || provider == msg.sender) revert BadInput();
        if (amount == 0 || hoursBought == 0) revert BadInput();
        if (deliveryWindow < MIN_DELIVERY_WINDOW || deliveryWindow > MAX_DELIVERY_WINDOW) revert BadInput();

        uint256 received = _pull(msg.sender, amount);
        if (received == 0 || received > type(uint128).max) revert BadInput();

        id = ++orderCount;
        uint64 deliverBy = uint64(block.timestamp) + deliveryWindow;

        _orders[id] = Order({
            buyer: msg.sender,
            provider: provider,
            listingId: listingId,
            amount: uint128(received),
            deliverBy: deliverBy,
            reviewUntil: 0,
            arbitrateUntil: 0,
            hoursBought: hoursBought,
            feeBps: feeBps,
            state: State.Escrowed
        });

        totalEscrowed += received;

        emit OrderFunded(id, msg.sender, provider, listingId, received, hoursBought, deliverBy, feeBps);
    }

    /// The provider accepts the job. Until this happens the buyer can walk away
    /// for free, which is why starting is a separate step.
    function start(uint256 id) external {
        Order storage o = _orders[id];
        if (msg.sender != o.provider) revert NotProvider();
        if (o.state != State.Escrowed) revert WrongState();
        o.state = State.InProgress;
        emit OrderStarted(id);
    }

    /**
     * The provider hands the work over and the review clock starts.
     *
     * Delivering after deliverBy is allowed on purpose. Work that is five
     * minutes late should not destroy the order, and the buyer keeps every
     * protection: they can still dispute during review. If the buyer would
     * rather have their money back, reclaim() is open to them the moment the
     * deadline passes, and whichever transaction lands first wins.
     */
    function deliver(uint256 id, string calldata uri) external {
        Order storage o = _orders[id];
        if (msg.sender != o.provider) revert NotProvider();
        if (o.state != State.InProgress) revert WrongState();
        o.state = State.Review;
        o.reviewUntil = uint64(block.timestamp) + REVIEW_WINDOW;
        emit OrderDelivered(id, uri, o.reviewUntil);
    }

    /**
     * KAIROS records what it thinks of the delivery.
     *
     * This writes a number and a pointer to the evidence. It does not move
     * money and it does not change the state, so a compromised KAIROS key
     * cannot pay anyone. Score is in basis points, so 9870 reads as 98.7%.
     */
    function attest(uint256 id, uint16 score, string calldata uri) external {
        if (msg.sender != kairos) revert NotVerifier();
        if (score > BPS) revert BadInput();
        if (_orders[id].state != State.Review) revert WrongState();
        emit Attested(id, score, uri);
    }

    /// The buyer is happy and does not want to wait out the window.
    function accept(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (msg.sender != o.buyer) revert NotBuyer();
        if (o.state != State.Review) revert WrongState();
        _release(id, o);
    }

    /**
     * The review window ran out and nobody objected, so the provider gets paid.
     *
     * Anyone may call this. That is deliberate: the provider should not have to
     * be online, and Time Vault should not be the only party able to settle. It
     * is the line "the funds land without you having to ask anyone for them",
     * written as a function anyone can call.
     */
    function settle(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (o.state != State.Review) revert WrongState();
        if (block.timestamp <= o.reviewUntil) revert TooEarly();
        _release(id, o);
    }

    /// The buyer changes their mind before the provider has started.
    function cancel(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (msg.sender != o.buyer) revert NotBuyer();
        if (o.state != State.Escrowed) revert WrongState();
        _refund(id, o);
    }

    /// Nothing was delivered by the deadline, so the buyer takes their money back.
    function reclaim(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (msg.sender != o.buyer) revert NotBuyer();
        if (o.state != State.Escrowed && o.state != State.InProgress) revert WrongState();
        if (block.timestamp <= o.deliverBy) revert TooEarly();
        _refund(id, o);
    }

    /// The provider hands the money back. Always allowed, right up to release.
    function refund(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (msg.sender != o.provider) revert NotProvider();
        if (o.state != State.Escrowed && o.state != State.InProgress && o.state != State.Review) {
            revert WrongState();
        }
        _refund(id, o);
    }

    // ------------------------------------------------------------- disputes

    /// The buyer objects. Only during review, and the money stays put.
    function dispute(uint256 id, string calldata reason) external {
        Order storage o = _orders[id];
        if (msg.sender != o.buyer) revert NotBuyer();
        if (o.state != State.Review) revert WrongState();
        if (block.timestamp > o.reviewUntil) revert TooLate();
        o.state = State.Disputed;
        o.arbitrateUntil = uint64(block.timestamp) + ARBITRATION_WINDOW;
        emit DisputeRaised(id, reason, o.arbitrateUntil);
    }

    /**
     * VORIAN rules on a disputed order.
     *
     * toProvider is in tokens and is bounded by what the order holds, so the
     * arbiter can decide who gets what but can never conjure a payout or reach
     * another order. The fee applies only to the provider's share, because a
     * settlement fee on money going back to the buyer would be indefensible.
     */
    function resolve(uint256 id, uint256 toProvider, string calldata uri) external guarded {
        if (msg.sender != vorian) revert NotArbiter();
        Order storage o = _orders[id];
        if (o.state != State.Disputed) revert WrongState();
        if (block.timestamp > o.arbitrateUntil) revert TooLate();

        uint256 amount = o.amount;
        if (toProvider > amount) revert BadInput();

        uint256 toBuyer = amount - toProvider;
        uint256 fee = (toProvider * o.feeBps) / BPS;

        o.state = State.Settled;
        totalEscrowed -= amount;

        _push(feeRecipient, fee);
        _push(o.provider, toProvider - fee);
        _push(o.buyer, toBuyer);

        emit DisputeResolved(id, toProvider, toBuyer, fee, uri);
    }

    /**
     * VORIAN never answered, so the order splits down the middle.
     *
     * Anyone can call this once the window closes. No fee is taken: the
     * protocol does not get paid for failing to show up. An even split is the
     * one outcome neither side can engineer by waiting, and any remainder goes
     * to the buyer.
     */
    function resolveByTimeout(uint256 id) external guarded {
        Order storage o = _orders[id];
        if (o.state != State.Disputed) revert WrongState();
        if (block.timestamp <= o.arbitrateUntil) revert TooEarly();

        uint256 amount = o.amount;
        uint256 toProvider = amount / 2;
        uint256 toBuyer = amount - toProvider;

        o.state = State.Settled;
        totalEscrowed -= amount;

        _push(o.provider, toProvider);
        _push(o.buyer, toBuyer);

        emit DisputeTimedOut(id, toProvider, toBuyer);
    }

    // ---------------------------------------------------------------- views

    function getOrder(uint256 id) external view returns (Order memory) {
        return _orders[id];
    }

    /// What a given amount would pay out at the current fee, for the interface
    /// to show before a buyer commits.
    function quote(uint256 amount) external view returns (uint256 fee, uint256 net) {
        fee = (amount * feeBps) / BPS;
        net = amount - fee;
    }

    /// True once settle() would succeed. Saves the interface from repeating the
    /// timing rules and getting them slightly wrong.
    function settleable(uint256 id) external view returns (bool) {
        Order storage o = _orders[id];
        return o.state == State.Review && block.timestamp > o.reviewUntil;
    }

    /// Everything the contract holds beyond what it owes to open orders. Should
    /// normally be zero.
    function unallocated() public view returns (uint256) {
        uint256 balance = TOKEN.balanceOf(address(this));
        return balance > totalEscrowed ? balance - totalEscrowed : 0;
    }

    // ---------------------------------------------------------------- admin

    function setFee(uint16 bps) external onlyOwner {
        if (bps > MAX_FEE_BPS) revert BadInput();
        feeBps = bps;
        emit FeeChanged(bps);
    }

    function setFeeRecipient(address recipient) external onlyOwner {
        if (recipient == address(0)) revert BadInput();
        feeRecipient = recipient;
        emit FeeRecipientChanged(recipient);
    }

    function setKairos(address agent) external onlyOwner {
        if (agent == address(0)) revert BadInput();
        kairos = agent;
        emit AgentChanged("KAIROS", agent);
    }

    function setVorian(address agent) external onlyOwner {
        if (agent == address(0)) revert BadInput();
        vorian = agent;
        emit AgentChanged("VORIAN", agent);
    }

    /// Stops new orders being funded. Every order that already exists carries on
    /// exactly as before, including release and refund. There is no switch here
    /// that freezes somebody's money.
    function setPaused(bool value) external onlyOwner {
        paused = value;
        emit PausedChanged(value);
    }

    function transferOwnership(address to) external onlyOwner {
        pendingOwner = to;
        emit OwnershipStarted(to);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotOwner();
        emit OwnershipTransferred(owner, msg.sender);
        owner = msg.sender;
        pendingOwner = address(0);
    }

    /**
     * Recover tokens that were sent here by mistake.
     *
     * For $TV this is capped at the unallocated balance, so escrowed money is
     * out of reach by arithmetic rather than by promise. Send the wrong token
     * to this address and it can be returned; send $TV that belongs to an
     * order and nobody, including the owner, can take it.
     */
    function rescue(address token_, address to, uint256 amount) external onlyOwner guarded {
        if (to == address(0)) revert BadInput();
        if (token_ == address(TOKEN) && amount > unallocated()) revert WouldTouchEscrow();
        (bool ok, bytes memory ret) = token_.call(
            abi.encodeCall(IERC20.transfer, (to, amount))
        );
        if (!ok || (ret.length != 0 && !abi.decode(ret, (bool)))) revert TransferFailed();
        emit Rescued(token_, to, amount);
    }

    // -------------------------------------------------------------- private

    function _release(uint256 id, Order storage o) private {
        uint256 amount = o.amount;
        uint256 fee = (amount * o.feeBps) / BPS;

        o.state = State.Released;
        totalEscrowed -= amount;

        _push(feeRecipient, fee);
        _push(o.provider, amount - fee);

        emit OrderReleased(id, msg.sender, amount - fee, fee);
    }

    function _refund(uint256 id, Order storage o) private {
        uint256 amount = o.amount;

        o.state = State.Refunded;
        totalEscrowed -= amount;

        _push(o.buyer, amount);

        emit OrderRefunded(id, msg.sender, amount);
    }

    function _pull(address from, uint256 value) private returns (uint256 received) {
        uint256 before = TOKEN.balanceOf(address(this));
        _tokenCall(abi.encodeCall(IERC20.transferFrom, (from, address(this), value)));
        received = TOKEN.balanceOf(address(this)) - before;
    }

    function _push(address to, uint256 value) private {
        if (value == 0) return;
        _tokenCall(abi.encodeCall(IERC20.transfer, (to, value)));
    }

    /// Some ERC-20s return nothing instead of a bool. Treat an empty return as
    /// success and a false return as failure, and never ignore a revert.
    function _tokenCall(bytes memory data) private {
        (bool ok, bytes memory ret) = address(TOKEN).call(data);
        if (!ok || (ret.length != 0 && !abi.decode(ret, (bool)))) revert TransferFailed();
    }
}
