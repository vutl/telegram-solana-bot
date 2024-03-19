from solana.rpc.api import Client
from construct import Bytes, Int64ul
from construct import Struct as cStruct

#for test.py
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