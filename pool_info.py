"Detect  New Pools Created on Solana Raydium DEX"

import solana
import solders
import asyncio
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Finalized, Confirmed
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.types import TokenAccountOpts
import json
import os
import datetime
import re
from solders.pubkey import Pubkey
from solders.signature import Signature
from time import sleep, time
from argparse import ArgumentParser
from configparser import ConfigParser
import struct
from enum import IntEnum
from construct import Bytes, Flag, Int8ul, Int64ul, BytesInteger, Sequence, Array
from construct import Struct as cStruct
import requests

from constants import wallet_address, solana_client, uri, SERUM_MARKET_LAYOUT, RAY_AUTHORITY_V4, API_RAYDIUM_LIQUIDITY_POOL


seen_signatures = set()

def get_decimals(transaction, pubic_key):
	try:
		logs = transaction.transaction.meta.pre_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubic_key:
			return log.ui_token_amount.decimals

	try:
		logs = transaction.transaction.meta.post_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubic_key:
			return log.ui_token_amount.decimals
	return None


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

def get_ido_open_time(transaction):
	try:
		logs = transaction.transaction.meta.log_messages
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

def getTokens(str_signature):
    signature = Signature.from_string(str_signature)
    transaction = solana_client.get_transaction(signature, encoding="jsonParsed",
                                                max_supported_transaction_version=0).value
    instruction_list = transaction.transaction.transaction.message.instructions
    # pool_info ={}
    for instructions in instruction_list:
        if instructions.program_id == Pubkey.from_string(wallet_address):
            # print("============NEW POOL DETECTED====================")
            index = instructions.accounts[4]
            index0 = instructions.accounts[8]
            index1 = instructions.accounts[9]
            index2 = instructions.accounts[7]
            index3 = get_decimals(transaction, index0)
            index4 = get_decimals(transaction, index1)
            index5 = get_decimals(transaction, index0)
            index6 = 4
            index7 = Pubkey.from_string('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
            index8 = instructions.accounts[5]
            index9 = instructions.accounts[6]
            index10 = instructions.accounts[12]
            index11 = instructions.accounts[10]
            index12 = instructions.accounts[11]
            index13 = Pubkey.from_string("11111111111111111111111111111111")
            index14 = Pubkey.from_string("11111111111111111111111111111111")
            index15 = 4
            index16 = Pubkey.from_string("srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX")
            index17 = instructions.accounts[16]
            index18 = get_market_authority(index16, index17)
            
            serum_market_id_info = solana_client.get_account_info(index17)
            serum_info = SERUM_MARKET_LAYOUT.parse(serum_market_id_info.value.data)
            index19 = Pubkey.from_bytes(serum_info.baseVault)
            index20 = Pubkey.from_bytes(serum_info.quoteVault)
            index21 = Pubkey.from_bytes(serum_info.bids)
            index22 = Pubkey.from_bytes(serum_info.asks)
            index23 = Pubkey.from_bytes(serum_info.eventQueue)
            index24 = get_ido_open_time(transaction)[1]
            
            # Dinh dang object
            pool_data = {
                 "Id": str(index),
                "baseMint": str(index0),
                "quoteMint": str(index1),
                "IpMint": str(index2),
                "baseDecimals": index3,
                "quoteDecimals": index4,
                "IpDecimals": index5,
                "version": index6,
                "program_id": str(index7),
                "authority": str(index8),
                "openOrders": str(index9),
                "targetOrders": str(index10),
                "baseVault": str(index11),
                "quoteVault": str(index12),
                "withdrawQueue": str(index13),
                "IpVault": str(index14),
                "marketVersion": index15,
                "marketProgramId": str(index16),
                "marketId": str(index17),
                "marketAuthority": str(index18),
                "marketBaseVault": str(index19),
                "marketQuoteVault": str(index20),
                "marketBids": str(index21),
                "marketAsks": str(index22),
                "marketEventQueue": str(index23),
				"openTime": index24,
            }
            
            # Tao thu muc neu ko co
            active_pool_folder = 'active_pool'
            if not os.path.exists(active_pool_folder):
                os.makedirs(active_pool_folder)

            # save vao file basemint.json
            json_file_path = os.path.join(active_pool_folder, f"{pool_data["baseMint"]}.json")
            with open(json_file_path, 'w') as json_file:
                json.dump(pool_data, json_file, indent=4)
				
            return pool_data

#Set up WebSocket connection, chay getTokens khi pool moi duoc phat hien
async def run():
    async with connect(uri) as ws:
        # gui subscription request
        await ws.logs_subscribe(RpcTransactionLogsFilterMentions(Pubkey.from_string(wallet_address)), Finalized)

        resp = await ws.recv()
        print("\rSubscription successful | {}".format(datetime.datetime.now()),end="")
        while True:     
            resp = await ws.recv()
            for tx in resp:
                if tx.result.value.err == None:
                    signature = str(tx.result.value.signature)
                    logs = tx.result.value.logs
                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        log_messages_set = set(tx.result.value.logs)
                        search = "initialize2"
                        if any(search in message for message in log_messages_set):
                            print("Time: {}".format(datetime.datetime.now()))
                            print(f"Transaction link:  https://solscan.io/tx/{signature}")
                            pool_data = getTokens(signature)
                            # In ra pool data
                            for key, value in pool_data.items():
                                print(f"{key}: {value}")
                
                else: pass

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()