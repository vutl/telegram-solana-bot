"Detect  New Pools Created on Solana Raydium DEX"

import asyncio
import websockets
import json
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
import pandas as pd
from tabulate import tabulate

wallet_address = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
seen_signatures = set()
solana_client = Client("https://mainnet.helius-rpc.com/?api-key=6dcb92e3-5222-4d11-9dc4-dbee6df8f373")

def get_decimals(transaction, pubkey):
	try:
		logs = transaction.transaction.meta.pre_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubkey:
			return log.ui_token_amount.decimals

	try:
		logs = transaction.transaction.meta.post_token_balances
	except AttributeError:
		logs = [""]
	for log in logs:
		if log.mint == pubkey:
			return log.ui_token_amount.decimals
	return None


def getTokens(str_signature):
    signature = Signature.from_string(str_signature)
    transaction = solana_client.get_transaction(signature, encoding="jsonParsed",
                                                max_supported_transaction_version=0).value
    instruction_list = transaction.transaction.transaction.message.instructions

    for instructions in instruction_list:
        if instructions.program_id == Pubkey.from_string(wallet_address):
            print("============NEW POOL DETECTED====================")
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
            data = {'Index': ['Id', 'baseMint', 'quoteMint', 'IpMint', 'baseDecimals', 'quoteDecimals', 'IpDecimals', 'version', 'program_id', 'authority', 'openOrders', 'targetOrders', 'baseVault', 'quoteVault', 'withdrawQueue', 'IpVault', 'marketVersion', 'marketProgramId', 'marketId'],
                    'Info': [index, index0, index1, index2, index3, index4, index5, index6, index7, index8, index9, index10, index11, index12, index13, index14, index15, index16, index17]}

            df = pd.DataFrame(data)
            table = tabulate(df, headers='keys', tablefmt='fancy_grid')
            print(table)


#Set up WebSocket connection, chay getTokens khi pool moi duoc phat hien
async def run():
    uri = "wss://mainnet.helius-rpc.com/?api-key=6dcb92e3-5222-4d11-9dc4-dbee6df8f373"
    async with websockets.connect(uri) as websocket:
        # gui subscription request
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": [wallet_address]},
                {"commitment": "finalized"}
            ]
        }))

        first_resp = await websocket.recv()
        response_dict = json.loads(first_resp)
        if 'result' in response_dict:
            print("Subscription successful. Subscription ID: ", response_dict['result'])

        async for response in websocket:

            response_dict = json.loads(response)

            if response_dict['params']['result']['value']['err'] == None:
                signature = response_dict['params']['result']['value']['signature']

                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    log_messages_set = set(response_dict['params']['result']['value']['logs'])

                    search = "initialize2"
                    if any(search in message for message in log_messages_set):
                        print(f"True, https://solscan.io/tx/{signature}")
                        getTokens(signature)
            else:
                pass


async def main():
    await run()

#loop
asyncio.run(main())