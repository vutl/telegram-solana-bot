from solana.rpc.api import Client
from construct import Bytes, Int64ul
from construct import Struct as cStruct
from solders.pubkey import Pubkey

#for swap and create token
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string(
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
)

SYSTEM_PROGRAM_ID = Pubkey.from_string('11111111111111111111111111111111')

SYSTEM_RENT_ID = Pubkey.from_string('SysvarRent111111111111111111111111111111111')

TOKEN_METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

TOKEN_PROGRAM_ID: Pubkey = Pubkey.from_string(
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
)
TOKEN_PROGRAM_ID_2022: Pubkey = Pubkey.from_string(
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
)

RAY_V4 = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
RAY_AUTHORITY_V4 = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")

SERUM_PROGRAM_ID = Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')

LAMPORTS_PER_SOL = 1000000000

#for pool_info.py
API_RAYDIUM_LIQUIDITY_POOL = "https://api.raydium.io/v2/sdk/liquidity/mainnet.json"
wallet_address = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
solana_client = Client("https://mainnet.helius-rpc.com/?api-key=6dcb92e3-5222-4d11-9dc4-dbee6df8f373")
uri = "wss://mainnet.helius-rpc.com/?api-key=6dcb92e3-5222-4d11-9dc4-dbee6df8f373"
SERUM_MARKET_LAYOUT = cStruct(
	'None' / Bytes(5),
	'accountFlags' / Bytes(8),
	'ownAddress' / Bytes(32),
	'vaultSignerNonce' / Int64ul,
	'baseMint' / Bytes(32),
	'quoteMint' / Bytes(32),
	'baseVault' / Bytes(32),
	'baseDepositsTotal' / Int64ul,
	'baseFeesAccrued' / Int64ul,
	'quoteVault' / Bytes(32),
	'quoteDepositsTotal' / Int64ul,
	'quoteFeesAccrued' / Int64ul,
	'quoteDustThreshold' / Int64ul,
	'requestQueue' / Bytes(32),
	'eventQueue' / Bytes(32),
	'bids' / Bytes(32),
	'asks' / Bytes(32), 
	'baseLotSize' / Int64ul,
	'quoteLotSize' / Int64ul,
	'feeRateBps' / Int64ul,
	'referrerRebatesAccrued' / Int64ul,
	'dummy' / Bytes(7),
	)

#for botchat.py
api_id = '29398688'
api_hash = '2eb07147c2fd51961182419fb7c19ead'
bot_token = '7079490697:AAENOdhLs7PbvbugoLnANNvJthlzaw8beOc'