"""Contracts, functions, protocols, and relationships.

CONTRACTS: name, address (None when not publicly pinned), chain, kind, protocol.
FUNCTIONS: per contract, with optional CALLS targets ("Contract.function") and
vulnerabilities: list of (swc, source, status) where status is one of
exploited | patched | pattern | theoretical.

Protocol list is derived from the protocols field.
"""

CONTRACTS = [
    # --- audited live protocols (15) ---
    dict(name="TheDAO", address="0xbb9bc244d798123fde783fcc1c72d3bb8c189413", chain="Ethereum", kind="legacy", protocol="DAO"),
    dict(name="UniswapV2Router02", address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", chain="Ethereum", kind="dex", protocol="Uniswap"),
    dict(name="UniswapV3Router2", address="0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", chain="Ethereum", kind="dex", protocol="Uniswap"),
    dict(name="AaveV3Pool", address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2", chain="Ethereum", kind="lending", protocol="Aave"),
    dict(name="AaveV2LendingPool", address="0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9", chain="Ethereum", kind="lending", protocol="Aave"),
    dict(name="CompoundComptroller", address="0x3d9819210A31b48718aC728fB26cBbB3CCdd9197", chain="Ethereum", kind="lending", protocol="Compound"),
    dict(name="cUSDC", address="0x39aa39c021dfbae8fac545936693ac917d5e7563", chain="Ethereum", kind="lending", protocol="Compound"),
    dict(name="Curve3pool", address="0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7", chain="Ethereum", kind="dex", protocol="Curve"),
    dict(name="BalancerVault", address="0xba100000625a570e4145b50d0339185608d6a16f", chain="Ethereum", kind="dex", protocol="Balancer"),
    dict(name="MakerVault", address="0x0d500B1d8E8eF31E21C99d1Db9A7c3793F7Fe872", chain="Ethereum", kind="cdp", protocol="MakerDAO"),
    dict(name="SushiswapRouter02", address="0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", chain="Ethereum", kind="dex", protocol="Sushiswap"),
    dict(name="1inchv3", address="0x1111111254EEB25477B68fb85Ed929f73A960582", chain="Ethereum", kind="aggregator", protocol="1inch"),
    dict(name="OpenSeaSeaport", address="0x000000000000AAE66B6446Eab63D0992A9741058", chain="Ethereum", kind="nft_marketplace", protocol="OpenSea"),
    dict(name="GMXExchange", address=None, chain="Ethereum", kind="perp_dex", protocol="GMX"),
    dict(name="KyberSwapPool", address="0x9ac6cdfe2aa434fb7487aa37ba4c6ffcd6eaa91a", chain="Ethereum", kind="dex", protocol="KyberSwap"),
    # --- exploit-target protocols (historical) ---
    dict(name="RoninBridge", address="0xe6f7565a24e747582e0b7b05e1a64a8f293041e4", chain="Ronin", kind="bridge", protocol="Ronin"),
    dict(name="PolyBridge", address=None, chain="BSC", kind="bridge", protocol="PolyNetwork"),
    dict(name="WormholeNft", address="wormhole:attestation", chain="Solana", kind="bridge", protocol="Wormhole"),
    dict(name="bZx", address=None, chain="Ethereum", kind="leverage", protocol="bZx"),
    dict(name="CreamFinance", address="0xd5475b4938ff176713304592703bee0402a7149e", chain="Ethereum", kind="lending", protocol="Cream Finance"),
    dict(name="MangoMarkets", address="MangoCzJ36AjEerPj49L3F72ZfxLwCgEj9An6429e", chain="Solana", kind="perp_dex", protocol="Mango Markets"),
    dict(name="Beanstalk", address="0x123F1BE8914278471b82132F8F8614B5255212FC", chain="Ethereum", kind="yield", protocol="Beanstalk"),
    dict(name="EulerFinance", address="0x27327c5bbf2f9ce874ba2c2949c63a130d863a42", chain="Ethereum", kind="lending", protocol="Euler Finance"),
]

# function_name -> (contract_name, description, calls, vulns)
FUNCTIONS = {
    # TheDAO
    "TheDAO.withdraw": ("TheDAO", "Share withdrawal; the fallback re-entry path", ["TheDAO.fallback"], [("SWC-107", "exploit post-mortem", "exploited"), ("SWC-102", "source review", "patched")]),
    "TheDAO.fallback": ("TheDAO", "Recursive token issuance entry", [], [("SWC-104", "exploit post-mortem", "exploited")]),
    "TheDAO.convertToShares": ("TheDAO", "Weierstrass conversion of ETH to shares", ["TheDAO.withdraw"], [("SWC-113", "source review", "patched")]),

    # Uniswap V2
    "UniswapV2Router02.swapExactTokensForTokens": ("UniswapV2Router02", "Token-to-token swap via pair route", ["UniswapV2Router02._swap"], [("SWC-103", "slither detector", "pattern")]),
    "UniswapV2Router02.addLiquidity": ("UniswapV2Router02", "Add liquidity to a pair", [], []),
    "UniswapV2Router02.removeLiquidity": ("UniswapV2Router02", "Remove liquidity from a pair", [], []),
    "UniswapV2Router02._swap": ("UniswapV2Router02", "Internal multi-hop swap; pair.swap emits a price that can be warped by large flows", [], [("SWC-106", "exploit analysis", "theoretical")]),

    # Uniswap V3
    "UniswapV3Router2.exactInputSingle": ("UniswapV3Router2", "Single-hop exact input swap", [], [("SWC-103", "slither detector", "theoretical")]),
    "UniswapV3Router2.exactInput": ("UniswapV3Router2", "Multi-hop exact input swap", [], []),
    "UniswapV3Router2.addLiquidity": ("UniswapV3Router2", "Add liquidity to a pool", [], []),

    # Aave V3
    "AaveV3Pool.supply": ("AaveV3Pool", "Deposit an asset into the pool", [], []),
    "AaveV3Pool.borrow": ("AaveV3Pool", "Borrow against collateral; health factor from oracle", ["AaveV3Pool.executeOperation"], [("SWC-128", "audit report", "theoretical")]),
    "AaveV3Pool.liquidationCall": ("AaveV3Pool", "Liquidate undercollateralized positions at oracle prices", ["AaveV3Pool.repay"], [("SWC-128", "audit report", "theoretical")]),
    "AaveV3Pool.repay": ("AaveV3Pool", "Repay a borrowed position (seize collateral path)", [], []),
    "AaveV3Pool.flashLoanSimple": ("AaveV3Pool", "Interest-free flash loan with callback", ["AaveV3Pool.executeOperation"], [("SWC-105", "audit report", "pattern")]),
    "AaveV3Pool.executeOperation": ("AaveV3Pool", "Flash-loan callback executed in the same tx", [], [("SWC-107", "source review", "theoretical")]),

    # Aave V2
    "AaveV2LendingPool.deposit": ("AaveV2LendingPool", "Deposit to a reserve", [], []),
    "AaveV2LendingPool.borrow": ("AaveV2LendingPool", "Borrow against collateral", ["AaveV2LendingPool.flashLoan"], [("SWC-128", "audit report", "patched")]),
    "AaveV2LendingPool.liquidationCall": ("AaveV2LendingPool", "Close unhealthy positions at liquidation rate", ["cUSDC.redeem"], [("SWC-106", "exploit analysis", "theoretical")]),
    "AaveV2LendingPool.flashLoan": ("AaveV2LendingPool", "Flash loan with callback (v2.0+)", ["AaveV2LendingPool.executeOperation"], [("SWC-105", "audit report", "pattern")]),
    "AaveV2LendingPool.executeOperation": ("AaveV2LendingPool", "Flash-loan callback executed in the same tx", [], []),

    # Compound
    "CompoundComptroller.mint": ("CompoundComptroller", "Mint cTokens for an underlying deposit", ["cUSDC.mint"], []),
    "CompoundComptroller.redeem": ("CompoundComptroller", "Redeem cTokens for the underlying", ["cUSDC.redeem"], []),
    "CompoundComptroller.liquidateBorrow": ("CompoundComptroller", "Seize collateral and repay borrow at close factor", ["cUSDC.redeem"], [("SWC-128", "exploit analysis", "patched")]),
    "cUSDC.mint": ("cUSDC", "Deposit USDC and mint cUSDC", [], []),
    "cUSDC.borrow": ("cUSDC", "Borrow USDC against cUSDC (underlying exposure)", [], []),
    "cUSDC.redeem": ("cUSDC", "Burn cUSDC and withdraw USDC", [], [("SWC-115", "source review", "patched")]),
    "cUSDC.exchange": ("cUSDC", "Exchange cUSDC at a calculated rate", [], [("SWC-115", "slither detector", "theoretical")]),

    # Curve
    "Curve3pool.exchange": ("Curve3pool", "Swap between pool coins at pool price", [], [("SWC-106", "exploit analysis", "theoretical")]),
    "Curve3pool.deposit": ("Curve3pool", "Deposit coins and mint LP", [], []),
    "Curve3pool.withdraw": ("Curve3pool", "Burn LP and withdraw coins", [], []),

    # Balancer
    "BalancerVault.depositSingle": ("BalancerVault", "Single-asset pool deposit", [], []),
    "BalancerVault.withdrawSingle": ("BalancerVault", "Single-asset pool withdrawal", [], []),
    "BalancerVault.flashLoan": ("BalancerVault", "Flash loan with onExit callback", ["BalancerVault.onExit"], [("SWC-105", "audit report", "pattern")]),
    "BalancerVault.onExit": ("BalancerVault", "Flash-loan exit callback executed in the same tx", [], [("SWC-107", "source review", "theoretical")]),

    # MakerDAO
    "MakerVault.depositETH": ("MakerVault", "Deposit ETH as collateral", [], []),
    "MakerVault.generateDAI": ("MakerVault", "Mint DAI against collateral", [], []),
    "MakerVault.liquidate": ("MakerVault", "Cut undercollateralized vaults in the liquidation window", ["AaveV2LendingPool.liquidationCall"], [("SWC-103", "exploit analysis", "theoretical")]),
    "MakerVault.withdrawETH": ("MakerVault", "Withdraw released collateral", [], []),

    # Sushiswap
    "SushiswapRouter02.swapExactTokensForTokens": ("SushiswapRouter02", "Swap via SushiPair clone of the V2 router", ["UniswapV2Router02._swap"], [("SWC-103", "slither detector", "pattern")]),
    "SushiswapRouter02.swapExactTokensForETHSupportingFeeOnTransferTokens": ("SushiswapRouter02", "Fee-on-transfer-aware swap to ETH", [], []),
    "SushiswapRouter02.addLiquidity": ("SushiswapRouter02", "Add liquidity to a SushiPair", [], []),

    # 1inch
    "1inchv3.swap": ("1inchv3", "Route a swap across multiple DEXes in one tx", ["UniswapV2Router02.swapExactTokensForTokens", "Curve3pool.exchange", "SushiswapRouter02.swapExactTokensForTokens"], [("SWC-103", "slither detector", "pattern"), ("SWC-125", "slither detector", "theoretical")]),
    "1inchv3.getBestSwap": ("1inchv3", "Off-chain routed best-path lookup (on-chain verification)", [], []),

    # OpenSea
    "OpenSeaSeaport.fulfillExactOrder": ("OpenSeaSeaport", "Settle a maker/taker order with consideration transfer", [], [("SWC-125", "audit report", "theoretical")]),
    "OpenSeaSeaport.executeAllOrders": ("OpenSeaSeaport", "Bundle order execution in a single call", ["OpenSeaSeaport.fulfillExactOrder"], [("SWC-108", "audit report", "theoretical")]),

    # GMX
    "GMXExchange.openLong": ("GMXExchange", "Open a leveraged long position", [], [("SWC-122", "slither detector", "theoretical")]),
    "GMXExchange.close": ("GMXExchange", "Close a position and settle PnL at oracle price", [], [("SWC-128", "audit report", "theoretical")]),
    "GMXExchange.withdraw": ("GMXExchange", "Withdraw collateral from a position", [], []),

    # KyberSwap
    "KyberSwapPool.convertWithSlippage": ("KyberSwapPool", "Convert token pairs at the pool's last-traded price", ["KyberSwapPool.getAmountsOut"], [("SWC-106", "exploit post-mortem", "exploited")]),
    "KyberSwapPool.getAmountsOut": ("KyberSwapPool", "Quote from the pool's oracle (last trade)", [], [("SWC-128", "exploit post-mortem", "exploited")]),
    "KyberSwapPool.addLiquidity": ("KyberSwapPool", "Add liquidity to the pool", [], []),

    # Ronin
    "RoninBridge.mint": ("RoninBridge", "Mint destination tokens after a validator-verified attestation", ["RoninBridge.verifySignatures"], []),
    "RoninBridge.burn": ("RoninBridge", "Burn source tokens to emit a cross-chain event", [], []),
    "RoninBridge.verifySignatures": ("RoninBridge", "5-of-9 validator signature check over the attestation", [], [("SWC-120", "exploit post-mortem", "exploited"), ("SWC-108", "source review", "exploited")]),

    # Poly
    "PolyBridge.deposit": ("PolyBridge", "Deposit on source chain, emit cross-chain message", [], [("SWC-101", "source review", "patched")]),
    "PolyBridge.mintOnDestination": ("PolyBridge", "Mint on destination after cross-chain proof", ["PolyBridge.verifySignatures"], []),
    "PolyBridge.verifySignatures": ("PolyBridge", "Signature check over cross-chain messages (key compromised)", [], [("SWC-120", "exploit post-mortem", "exploited")]),

    # Wormhole
    "WormholeNft.attest": ("WormholeNft", "Emit a token attestation message", [], []),
    "WormholeNft.verifySignatures": ("WormholeNft", "Guardian set signature verification over attestations", [], [("SWC-100", "exploit post-mortem", "exploited"), ("SWC-125", "source review", "exploited")]),
    "WormholeNft.transferToken": ("WormholeNft", "Mint bridged token against a verified attestation", ["WormholeNft.verifySignatures"], []),

    # bZx
    "bZx.executeTrade": ("bZx", "Flash-loan funded trade execution", ["UniswapV2Router02.swapExactTokensForTokens", "AaveV2LendingPool.borrow"], [("SWC-106", "exploit post-mortem", "exploited"), ("SWC-105", "exploit post-mortem", "exploited")]),
    "bZx.liquidate": ("bZx", "Liquidate leveraged positions", ["CreamFinance.liquidate"], []),

    # Cream
    "CreamFinance.flashLoanSimple": ("CreamFinance", "Aave-style flash loan entry", ["cUSDC.borrow", "AaveV2LendingPool.liquidationCall", "cUSDC.mint"], [("SWC-105", "exploit post-mortem", "exploited")]),
    "CreamFinance.liquidate": ("CreamFinance", "Liquidate unhealthy positions at oracle-derived rate", ["AaveV2LendingPool.liquidationCall"], [("SWC-128", "exploit analysis", "patched")]),
    "CreamFinance.priceOracle": ("CreamFinance", "Price sourced from a c-token rate (manipulable)", [], [("SWC-128", "exploit post-mortem", "exploited")]),
    "CreamFinance.mint": ("CreamFinance", "Mint cToken against a deposit", [], []),

    # Mango
    "MangoMarkets.liquidate": ("MangoMarkets", "Liquidate at oracle mark price (stale after depeg)", ["MangoMarkets.spotPrice"], [("SWC-128", "exploit post-mortem", "exploited")]),
    "MangoMarkets.spotPrice": ("MangoMarkets", "Spot mark from the price cache", [], [("SWC-128", "source review", "exploited")]),
    "MangoMarkets.deposit": ("MangoMarkets", "Deposit collateral", [], []),

    # Beanstalk
    "Beanstalk.sow": ("Beanstalk", "Plant beans (stake) and harvest based on the oracle price", [], [("SWC-122", "exploit analysis", "exploited")]),
    "Beanstalk.pull": ("Beanstalk", "Pull yield at the current spot-derived price", ["Beanstalk.oracle"], [("SWC-106", "exploit post-mortem", "exploited")]),
    "Beanstalk.oracle": ("Beanstalk", "Internal oracle fed by the market spot price", [], [("SWC-128", "exploit post-mortem", "exploited")]),

    # Euler
    "EulerFinance.flashLoan": ("EulerFinance", "Euler flash loan with callback", ["UniswapV2Router02.swapExactTokensForTokens"], [("SWC-107", "exploit post-mortem", "exploited"), ("SWC-128", "exploit post-mortem", "exploited")]),
    "EulerFinance.borrow": ("EulerFinance", "Borrow at aave-derived price", [], [("SWC-128", "exploit post-mortem", "exploited")]),
    "EulerFinance.liquidate": ("EulerFinance", "Liquidate at a cross-chain oracle price", ["AaveV2LendingPool.liquidationCall"], [("SWC-107", "exploit post-mortem", "exploited")]),
}

LIBRARIES = [
    dict(name="OpenZeppelin", version="4.x", usage="Upgradeable + security libraries used across Compound, MakerDAO, Balancer, OpenSea"),
    dict(name="UniswapV2Core", version="1.0", usage="Pair/factory logic cloned by Sushiswap and called by aggregators"),
    dict(name="UniswapV3Core", version="1.0", usage="Pool + callback infrastructure for V3 routers"),
    dict(name="Solmate", version="7.x", usage="Token + transfer helpers used by Uniswap V3 ecosystem contracts"),
    dict(name="AavePeriphery", version="1.x", usage="Flash loan + position helpers around the Aave pool"),
    dict(name="ChainlinkDataFeeds", version="varies", usage="Price oracles for lending and perp settlement"),
    dict(name="SafeMultisig", version="1.3", usage="Operator key management for marketplace and CDP integrations"),
    dict(name="BalancerCore", version="2.x", usage="Weighted pool math shared by the Balancer vault"),
    dict(name="Gearbox", version="0.4", usage="Leverage vault primitives used by perp and CDP systems"),
    dict(name="MorphoBlue", version="0.5", usage="Flash-loan-friendly isolated market primitives"),
]

# (library, contract) edges
USES_LIBRARY = [
    ("OpenZeppelin", "CompoundComptroller"), ("OpenZeppelin", "MakerVault"),
    ("OpenZeppelin", "BalancerVault"), ("OpenZeppelin", "OpenSeaSeaport"),
    ("OpenZeppelin", "AaveV2LendingPool"), ("OpenZeppelin", "KyberSwapPool"),
    ("UniswapV2Core", "UniswapV2Router02"), ("UniswapV2Core", "SushiswapRouter02"),
    ("UniswapV2Core", "1inchv3"),
    ("UniswapV3Core", "UniswapV3Router2"),
    ("Solmate", "UniswapV3Router2"), ("Solmate", "GMXExchange"),
    ("AavePeriphery", "AaveV3Pool"), ("AavePeriphery", "AaveV2LendingPool"),
    ("ChainlinkDataFeeds", "GMXExchange"), ("ChainlinkDataFeeds", "KyberSwapPool"),
    ("ChainlinkDataFeeds", "MangoMarkets"), ("ChainlinkDataFeeds", "EulerFinance"),
    ("ChainlinkDataFeeds", "bZx"), ("ChainlinkDataFeeds", "1inchv3"),
    ("SafeMultisig", "OpenSeaSeaport"), ("SafeMultisig", "MakerVault"),
    ("BalancerCore", "BalancerVault"),
    ("Gearbox", "GMXExchange"), ("MorphoBlue", "EulerFinance"),
]

# (auditor, contract) edges
AUDITORS = [
    ("Code4rena", "AaveV3Pool"), ("Code4rena", "OpenSeaSeaport"), ("Code4rena", "BalancerVault"),
    ("Sherlock", "1inchv3"), ("Sherlock", "BalancerVault"), ("Sherlock", "GMXExchange"),
    ("Trail of Bits", "UniswapV3Router2"), ("Trail of Bits", "AaveV2LendingPool"),
    ("OpenZeppelin", "CompoundComptroller"), ("OpenZeppelin", "MakerVault"),
    ("ConsensysDiligence", "UniswapV2Router02"), ("ConsensysDiligence", "BalancerVault"),
]
