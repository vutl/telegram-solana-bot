import solana
import solders
import asyncio

from solana.rpc.api import Client
from solana.rpc.websocket_api import connect
from solana.rpc.types import TokenAccountOpts
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.rpc.config import RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions
import datetime
from time import sleep, time
import requests
import asyncio
import re

from argparse import ArgumentParser
from configparser import ConfigParser
import struct
from enum import IntEnum
from construct import Bytes, Flag, Int8ul, Int64ul, BytesInteger, Sequence, Array
from construct import Struct as cStruct

API_RAYDIUM_LIQUIDITY_POOL = "https://api.raydium.io/v2/sdk/liquidity/mainnet.json"

RAYDIUM_AUTHORITY_V4 = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")
RAY_V4_POOL = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")

API_RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=2e152a4d-ef02-4652-b922-517def1daf0c"
WS_RPC_ENDPOINT = "wss://mainnet.helius-rpc.com/?api-key=2e152a4d-ef02-4652-b922-517def1daf0c"

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


def is_raydium_listed_token(token, client):
	#client = Client(API_RPC_ENDPOINT)
	resp = client.get_token_accounts_by_owner_json_parsed(RAYDIUM_AUTHORITY_V4, TokenAccountOpts(mint=token)).value
	if resp != []:
		return True
	else:
		return False

def fetch_from_raydium(token):
	try:
		raydium_lp_list = requests.get(API_RAYDIUM_LIQUIDITY_POOL).json()
		for lp in raydium_lp_list["unOfficial"]:
			if lp["baseMint"] == token:
				[print("{}:			{}".format(key, lp[key])) for key in lp.keys()]
				return
		return None
	except:
		return None

async def listen_for_new_IDO(token, ws_end_point):
	config = ConfigParser()
	config.read('config.ini')
	RPC_WS_URL = config.get("RPC_URL", "ws_url")
	async with connect(RPC_WS_URL) as ws:
		await ws.logs_subscribe(RpcTransactionLogsFilterMentions(token))
		resp = await ws.recv()
		
		while True:
			print("\rĐang Đợi Bản Tin IDO | {}".format(datetime.datetime.now()),end="")
			resp = await ws.recv()
			for tx in resp:
				logs = tx.result.value.logs
				for log in logs:
					if re.search("init_pc_amount:", log) != None:
						print("Bắt Được Bản Tin IDO: {}".format(tx.result.value.signature))
						print("Thời Điểm List IDO: {}".format(datetime.datetime.now()))
						return tx.result.value.signature

def find_old_IDO(token, cli):
	print("Đang Tìm Bản Tin IDO ===============|")
	#cli = Client(api_end_point)
	start = time()
	sig_list = cli.get_signatures_for_address(token, commitment = Confirmed).value
	tx_list = []
	while True:
		if len(sig_list) < 1000:
			tx_list += sig_list
			break
		tx_list += sig_list	
		first_tx = sig_list[-1].signature
		sig_list = cli.get_signatures_for_address(token, before = first_tx, commitment = Confirmed).value
	IDO_tx = detect_ido_transaction_from_list(tx_list, cli)	
	print("Thời Điểm:{}, Thời Gian Tìm: {} giây".format(datetime.datetime.now(), time()-start))
	return IDO_tx

def is_ido_transaction(tx_inf):
	#tx_inf = cli.get_transaction(tx.signature,max_supported_transaction_version=0).value
	try:
		logs = tx_inf.transaction.meta.log_messages
	except AttributeError:
		logs = [""]
	for log in logs:		
		if re.search("init_pc_amount:", log) != None:
			return True
	return False

def detect_ido_transaction_from_list(txs, cli):
	for tx in txs[::-1]:
		if tx.err == None:
			#print("{}: {}".format(i, tx))
			tx_info = cli.get_transaction(tx.signature,max_supported_transaction_version=0).value
			if is_ido_transaction(tx_info):
				print("Đã Tìm Thấy Bản Tin IDO: {}".format(tx.signature))
				#print(datetime.datetime.now())
				return tx_info
	return False

def get_market_authority(program_id, market_id):
	seeds = [bytes(market_id)]
	nonce = 0
	public_key = Pubkey.default()
	while nonce < 100:
		try:
			seeds_with_nonce = seeds + [bytes([nonce]) + bytes(7)]
			public_key = Pubkey.create_program_address(seeds_with_nonce, program_id)
		except:
			nonce += 1
			continue
		return public_key

def get_ido_open_time(tx_info):
	try:
		logs = tx_info.transaction.meta.log_messages
	except AttributeError:
		logs = [""]
	for log in logs:
		start = re.search("open_time:", log)		
		if start != None:
			end = re.search(", init_pc_amount:", log)
			time_stamp = int(log[start.end()+1 : end.start()])
			open_time = datetime.datetime.fromtimestamp(time_stamp)
			return open_time, time_stamp 
	return None, None

def get_decimals(tx_info, pubkey):
	try:
		logs = tx_info.transaction.meta.pre_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubkey:
			return log.ui_token_amount.decimals

	try:
		logs = tx_info.transaction.meta.post_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubkey:
			return log.ui_token_amount.decimals
	return None

def fetch_pool_info_from_ido_transaction(tx_info, cli):
	#cli = Client(api_end_point) ####
	pool_info = {} 
	#tx_info = cli.get_transaction(tx.signature, max_supported_transaction_version=0) ######
	instructions = tx_info.transaction.transaction.message.instructions #####
	account_list = tx_info.transaction.transaction.message.account_keys #####
	for ins in instructions:
		if account_list[ins.program_id_index] == RAY_V4_POOL:
			instruction = ins
			break
	
	pool_info["id"] = account_list[instruction.accounts[4]]
	pool_info["baseMint"] = account_list[instruction.accounts[8]]
	pool_info["quoteMint"] = account_list[instruction.accounts[9]]
	pool_info["lpMint"] = account_list[instruction.accounts[7]]
	pool_info["baseDecimals"] = get_decimals(tx_info, pool_info["baseMint"]) ###############################
	pool_info["quoteDecimals"] = get_decimals(tx_info, pool_info["quoteMint"]) ###############################
	pool_info["lpDecimals"] = get_decimals(tx_info, pool_info["baseMint"]) ######################
	pool_info["version"] = 4
	pool_info["program_id"] = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
	pool_info["authority"] = account_list[instruction.accounts[5]]
	pool_info["openOrders"] = account_list[instruction.accounts[6]]
	pool_info["targetOrders"] = account_list[instruction.accounts[12]] 
	pool_info["baseVault"] = account_list[instruction.accounts[10]]
	pool_info["quoteVault"] = account_list[instruction.accounts[11]]
	pool_info["withdrawQueue"] = Pubkey.from_string("11111111111111111111111111111111")
	pool_info["lpVault"] = Pubkey.from_string("11111111111111111111111111111111")
	pool_info["marketVersion"] = 4
	pool_info["marketProgramId"] = Pubkey.from_string("srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX")
	pool_info["marketId"] = account_list[instruction.accounts[16]]
	pool_info["marketAuthority"] = get_market_authority(pool_info["marketProgramId"], pool_info["marketId"])
	
	serum_market_id_info = cli.get_account_info(pool_info["marketId"])
	serum_info = SERUM_MARKET_LAYOUT.parse(serum_market_id_info.value.data)
	pool_info["marketBaseVault"] = Pubkey.from_bytes(serum_info.baseVault)
	pool_info["marketQuoteVault"] = Pubkey.from_bytes(serum_info.quoteVault)
	pool_info["marketBids"] = Pubkey.from_bytes(serum_info.bids)
	pool_info["marketAsks"] = Pubkey.from_bytes(serum_info.asks)
	pool_info["marketEventQueue"] = Pubkey.from_bytes(serum_info.eventQueue)
	
	pool_info["lookupTableAccount"] = None #################################
	pool_info["openTime"] = get_ido_open_time(tx_info)[1] ########################################
	
	return pool_info

def get_ido_transaction_for_mint(token, solana_client):
	if is_raydium_listed_token(token, solana_client):
		print("[INF] Token Đã Được List IDO =======|")
		return find_old_IDO(token, solana_client)
	else:
		print("[INF] Token Chưa Được List IDO =====|".format(token))		
		sig =  asyncio.run(listen_for_new_IDO(token, WS_RPC_ENDPOINT))
		return solana_client.get_transaction(sig, max_supported_transaction_version=0).value
		
def fetch_LP_info_for_token(token, client):
	tx = get_ido_transaction_for_mint(token, client)
	lp_info = fetch_pool_info_from_ido_transaction(tx, client)	
	return lp_info
	
def main():
	parser = ArgumentParser()
	parser.add_argument("-t",type=str)
	args = parser.parse_args()
	
	#try:
	solana_api_client = Client(API_RPC_ENDPOINT)
	token = Pubkey.from_string(args.t)
	lp_info = fetch_LP_info_for_token(token, solana_api_client)
	#for k in lp_info.keys():
	#	if k == "openTime":
	#		print("{}:				{}".format(k,datetime.datetime.fromtimestamp(lp_info[k])))
	#	else:
	#		print("{}:				{}".format(k,lp_info[k]))
	
	print("Mở Bát Lúc: {}".format(datetime.datetime.fromtimestamp(lp_info["openTime"])))
	bought = False
	while True:
		duration = lp_info["openTime"] - time()
		if duration > 0.1:
			print("{} | Sẽ Mở Bán Trong Vòng: {} giây\r".format(datetime.datetime.now(), duration),end="")
		elif -0.1 < duration and duration < 0.1:
			print("\nGỬI YÊU CẦU MUA---------------{}".format(datetime.datetime.now()))
			bought = True
			sleep(1)
		else:
			if bought:
				print("Mua Thành Công.")
			else:
				print("Vào Muộn Rồi, Nghỉ Chơi Kèo Này: {}".format(datetime.datetime.now())) 
	#except:
	#	print("Địa Chỉ Token:{} Không Đúng\nVui Lòng Kiểm Tra Lại!")
			return

if __name__ == "__main__":
    main()
