import spl.token.instructions as spl_token
from spl.token.client import Token
from spl.token.instructions import mint_to, MintToParams, set_authority, SetAuthorityParams, AuthorityType, Instruction, burn, BurnParams, CloseAccountParams, close_account, create_associated_token_account, get_associated_token_address
from spl.token._layouts import MINT_LAYOUT

from solana.rpc.api import Client, RPCException
from solana.rpc.commitment import Commitment
from solana.transaction import Transaction, AccountMeta
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts

import solders.system_program as sp
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price

from pool_info import getTokens
from layouts import SWAP_LAYOUT, POOL_INFO_LAYOUT
from constants import SYSTEM_PROGRAM_ID, SYSTEM_RENT_ID, TOKEN_PROGRAM_ID, TOKEN_METADATA_PROGRAM_ID, RAY_V4, SERUM_PROGRAM_ID, solana_client
from configparser import ConfigParser
from time import sleep, time
import base58
import asyncio
import datetime
import json
import requests
import os
import sys
from construct import Bytes
from borsh_construct import CStruct, String, U8, U16, U64, Vec, Option, Bool, Enum


programid_of_token = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
payer = Keypair.from_bytes(base58.b58decode("4uofue5s3U4Hr7k31vVrFAPcYYrKWKdX3reyFeX8a56q7ChAC2X1Rwe1uQVhg1AGA99iEsmg2BwV5ULxaQMQM59h"))

config = ConfigParser()
# using sys and os because sometimes this shitty config reader does not read from curr directory
config.read('config.ini')

# RPC settings 
RPC_HTTPS_URL = config.get("RPC_URL", "rpc_url")

ctx1 = Client(RPC_HTTPS_URL, commitment=Commitment("confirmed"), timeout=30,blockhash_cache=True)

secret_Key = config.get("WALLET", "private_key")
    
GAS_LIMIT = config.getint("FEE", "computeUnitLimitRaydium")
GAS_PRICE = config.getint("FEE", "computeUnitPriceMicroLamports")


def get_payer(pubkey):
    payer = Keypair.from_bytes(base58.b58decode(pubkey))
    return payer


async def execute_tx(swap_tx, payer, Wsol_account_keyPair, signers):    
    solana_client = AsyncClient(RPC_HTTPS_URL, commitment=Commitment("confirmed"), timeout=30, blockhash_cache=False)
        
    try:
        #start_time = time.time()
        retry_send_tx = 0
        txnBool = True
        while txnBool:
            try:
                #print("7. Execute Transaction...")
                start_time = time()
                if Wsol_account_keyPair != None:
                    txn = await solana_client.send_transaction(swap_tx, payer, Wsol_account_keyPair)
                else:
                    txn = await solana_client.send_transaction(swap_tx, *signers)

                txid_string_sig = txn.value
                node_proc_time = time()
                print("\n[TXT] RPC NODE ĐÃ NHẬN LỆNH        | {}\n..... Chờ Mạng Lưới Xác Nhận".format(datetime.datetime.now()))
                
                checkTxn = True
                while checkTxn:
                    try:
                        status = await solana_client.get_transaction(txid_string_sig,"json")
                        # FeesUsed = (status.value.transaction.meta.fee) / 1000000000
                        if status.value.transaction.meta.err == None:
                            # print(f"[TXN] Transaction Fees: {FeesUsed:.10f} SOL")
                            finish_time = time()
                            execution_time = time() - start_time
                            print("[INF] THÀNH CÔNG                    | {} |\n[INF] TX : {}".format(datetime.datetime.now(),txn.value))
                            print(f"Transaction link (for devnet):  https://solscan.io/tx/{txn.value}")
                            print(f"Or link:  https://explorer.solana.com/tx/{txn.value}?cluster=devnet")
                            print("[INF] Thời Gian Node Nhận Lệnh    : {} giây".format(node_proc_time - start_time))
                            print("[INF] Thời Gian Mạng Lưới Xác Thực: {} giây".format(finish_time - node_proc_time))
                            print("[INF] Tổng Thời Gian Thực Thi     : {} giây".format(finish_time - start_time))

                            txnBool = False
                            checkTxn = False
                            #sendWebhook(f"e|TXN Success",f"[Raydium] TXN Execution time: {execution_time}")
                            return txid_string_sig
                        
                        else:
                            print("[INF] THẤT BẠI")
                            execution_time = time() - start_time
                            print(f"Thời Gian: {execution_time} giây")
                            checkTxn = False

                    except Exception as e:
                        # sendWebhook(f"e|TXN ERROR {token_symbol}",f"[Raydium]: {e}")
                        # print(f"Sleeping... {e}\nRetrying...")
                        pass

            except RPCException as e:
                retry_send_tx += 1
                print("\r[ERR] NODE BÁO LỖI {}...Thử Lại {}...".format(e, retry_send_tx), end="")
                #print(swap_tx.instructions)
                #print(swap_tx.recent_blockhash)
                #print(swap_tx.fee_payer)
                #print(swap_tx.signatures)
                #print(swap_tx.compile_message())
                #time.sleep(1)
                #txnBool = False
                #return "failed"
                #print(f"\rError: [{e.args[0].message}]...\nRetrying...")
                #sendWebhook(f"e|TXN ERROR {token_symbol}",f"[Raydium]: {e.args[0].data.logs}")

            except Exception as e:
                #sendWebhook(f"e|TXN Exception ERROR {token_symbol}",f"[Raydium]: {e.args[0].message}")
                print(f"\nError: [{e}]...\nEnd...")
                txnBool = False
                return "failed"
    except Exception as e:
        print(e)
        print("Main Swap error Raydium... retrying...")


# structure of the instruction
instruction_structure = CStruct(
    "instructionDiscriminator" / U8,
    "createMetadataAccountArgsV3" / CStruct(
        "data" / CStruct(
            "name" / String,
            "symbol" / String,
            "uri" / String,            
            "sellerFeeBasisPoints" / U16,
            "creators" / Option(Vec(CStruct(
                "address" / Bytes(32),
                "verified" / Bool,
                "share" / U8
            ))),
            "collection" / Option(CStruct(
                "verified" / Bool,
                "key" / String
            )),
            "uses" / Option(CStruct(
                "useMethod" / Enum(
                    "Burn",
                    "Multiple",
                    "Single",
                    enum_name="UseMethod"
                ),
                "remaining" / U64,
                "total" / U64
            ))
        ),
        "isMutable" / Bool,
        "collectionDetails" / Option(String) # fixme: string is not correct, insert correct type
    )
)

def metadata_account_instruction(token_name, symbol, uri, token, payer):
    metadata_pda = Pubkey.find_program_address([b"metadata", bytes(TOKEN_METADATA_PROGRAM_ID), bytes(token)], TOKEN_METADATA_PROGRAM_ID)[0]
    
    accounts = [
        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=True), # metadata
        AccountMeta(pubkey=token, is_signer=False, is_writable=False), # mint
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=False), # mint authority
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True), # payer
        AccountMeta(pubkey=payer.pubkey(), is_signer=False, is_writable=False), # update authority
        AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False), # system program
        AccountMeta(pubkey=SYSTEM_RENT_ID, is_signer=False, is_writable=False) # rent
    ]
    
    data = {
            "instructionDiscriminator": 33,
            "createMetadataAccountArgsV3": {
                "data": {
                    "name": token_name,
                    "symbol": symbol,
                    "uri": uri,
                    "sellerFeeBasisPoints": 0,
                    "creators": [
                        {
                            "address": bytes(payer.pubkey()),
                            "verified": True,
                            "share": 100
                        }
                    ],
                    "collection": None,
                    "uses": None
                },
                "isMutable": False,
                "collectionDetails": None
            }
        }
    return Instruction(TOKEN_METADATA_PROGRAM_ID, instruction_structure.build(data), accounts)


def create_mint(solana_client, payer, mint_authority, decimals, program_id, GAS_PRICE, GAS_LIMIT):
    balance_needed = Token.get_min_balance_rent_for_exempt_for_mint(solana_client)
    mint_keypair = Keypair()
    txn = Transaction(fee_payer=payer.pubkey()).add(set_compute_unit_price(GAS_PRICE)).add(set_compute_unit_limit(GAS_LIMIT))
    txn.add(
            sp.create_account(
                sp.CreateAccountParams(
                    from_pubkey=payer.pubkey(),
                    to_pubkey=mint_keypair.pubkey(),
                    lamports=balance_needed,
                    space=MINT_LAYOUT.sizeof(),
                    owner=program_id,
                )
            )
        )
    txn.add(
            spl_token.initialize_mint(
                spl_token.InitializeMintParams(
                    program_id=program_id,
                    mint=mint_keypair.pubkey(),
                    decimals=decimals,
                    mint_authority=mint_authority,
                )
            )
        )
    return mint_keypair, txn



def mint_to_account_instructions(amount, dest, mint, mint_authority, payer):
    params = MintToParams(amount=amount, dest=dest, mint=mint, mint_authority=mint_authority, program_id=TOKEN_PROGRAM_ID)
    return mint_to(params)


def name_token_instructions(token_name, symbol, uri, token, payer):
    metadata_account_Instructions = metadata_account_instruction(token_name, symbol, uri, token, payer)
    return  metadata_account_Instructions


def revoke_mint_authority_instructions(mint, current_mint_authority):
    params = SetAuthorityParams(account=mint, authority=AuthorityType.MINT_TOKENS, current_authority=current_mint_authority, program_id=TOKEN_PROGRAM_ID)
    return set_authority(params)


def create_and_mint_to_account(solana_api_client, mint_amount, mint_decimals, payer, GAS_PRICE, LIMIT, token_name, symbol, uri):
    #Create mint:
    print("CREATE MINT")
    signers = [payer]

    mint, tx = create_mint(solana_api_client, payer, payer.pubkey(), mint_decimals, TOKEN_PROGRAM_ID, GAS_PRICE, LIMIT)
    print("----- {}".format(mint.pubkey()))

    #Mint to Account
    #Create Associated Token Account Instuction
    associated_token_address, associated_token_account_Instructions = get_token_account(solana_api_client, payer.pubkey(), mint.pubkey())
    print("MOTHER WALLET: {}".format(payer.pubkey()))
    print("Associated Token Account: {}".format(associated_token_address))

    #Mint to account
    mint_to_account_Instructions = mint_to_account_instructions(mint_amount, associated_token_address, mint.pubkey(), payer.pubkey(), payer)
    if associated_token_account_Instructions != None:
        tx.add(associated_token_account_Instructions)
    tx.add(mint_to_account_Instructions)

    print("CREATE NAME AND LOGO")
    tx.add(name_token_instructions(token_name, symbol, uri, mint.pubkey(), payer))

    print("REVOKE MINT AUTHORITY")
    tx.add(revoke_mint_authority_instructions(mint.pubkey(), payer.pubkey()))

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(execute_tx(tx, payer, mint, signers))

    return tx

def burn_and_close(account, amount, mint, owner):
	burn_params = BurnParams(account=account, amount=amount, mint=mint, owner=owner.pubkey(), program_id=programid_of_token, signers=[])
	burn_ins = burn(burn_params)
	
	close_params = CloseAccountParams(account=account, dest=owner.pubkey(), owner=owner.pubkey(), program_id=programid_of_token, signers=[])
	close_ins = close_account(close_params)
	
	tx = Transaction(fee_payer=owner.pubkey()).add(burn_ins).add(close_ins)
	signers = [owner]
	return tx, signers


async def delete_account(account, payer):
	print(account)
	token_account = account.pubkey
	amount = int(account.account.data.parsed['info']['tokenAmount']['amount'])
	mint_in_account = Pubkey.from_string(account.account.data.parsed['info']['mint'])
	tx, signers = burn_and_close(token_account, amount, mint_in_account, payer)
	await execute_tx(tx, payer, None, signers)
	return


async def clean(solana_client):
	token_accounts = solana_client.get_token_accounts_by_owner_json_parsed(payer.pubkey(),TokenAccountOpts(program_id=programid_of_token)).value
	#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
	await asyncio.gather(*(delete_account(account, payer) for account in token_accounts))


def make_simulate_pool_info_instruction(accounts, mint, ctx):
        keys = [
            AccountMeta(pubkey=accounts["amm_id"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["authority"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["open_orders"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["base_vault"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["quote_vault"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["lp_mint"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["market_id"], is_signer=False, is_writable=False),    
            AccountMeta(pubkey=accounts['event_queue'], is_signer=False, is_writable=False),    
        ]
        data = POOL_INFO_LAYOUT.build(
            dict(
                instruction=12,
                simulate_type=0
            )
        )
        return Instruction(RAY_V4, data, keys)


def make_swap_instruction(amount_in: int, token_account_in: Pubkey.from_string, token_account_out: Pubkey.from_string,
                              accounts: dict, mint, ctx, owner) -> Instruction:
        
        tokenPk = mint
        accountProgramId = ctx.get_account_info_json_parsed(tokenPk)
        TOKEN_PROGRAM_ID = accountProgramId.value.owner
        
        keys = [
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["amm_id"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["authority"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=accounts["open_orders"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["target_orders"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["base_vault"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["quote_vault"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=SERUM_PROGRAM_ID, is_signer=False, is_writable=False), 
            AccountMeta(pubkey=accounts["market_id"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["bids"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["asks"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["event_queue"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["market_base_vault"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["market_quote_vault"], is_signer=False, is_writable=True),
            AccountMeta(pubkey=accounts["market_authority"], is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),  #UserSourceTokenAccount 
            AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True), #UserDestTokenAccount 
            AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False) #UserOwner 
        ]

        data = SWAP_LAYOUT.build(
            dict(
                instruction=9,
                amount_in=int(amount_in),
                min_amount_out=0
            )
        )
        return Instruction(RAY_V4, data, keys)


def get_token_account(ctx, 
                      owner: Pubkey.from_string, 
                      mint: Pubkey.from_string):
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey, None
    except:
        swap_associated_token_address = get_associated_token_address(owner, mint)
        swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
        return swap_associated_token_address, swap_token_account_Instructions


def sell_get_token_account(ctx, 
                      owner: Pubkey.from_string, 
                      mint: Pubkey.from_string):
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey
    except:
        print("Mint Token Not found")
        return None

def fetch_pool_keys(mint):
	amm_info = getTokens(Pubkey.from_string(mint))
	return {
                    'amm_id': amm_info['id'],
                    'authority': amm_info['authority'],
                    'base_mint': amm_info['baseMint'],
                    'base_decimals': amm_info['baseDecimals'],
                    'quote_mint': amm_info['quoteMint'],
                    'quote_decimals': amm_info['quoteDecimals'],
                    'lp_mint': amm_info['lpMint'],
                    'open_orders': amm_info['openOrders'],
                    'target_orders': amm_info['targetOrders'],
                    'base_vault': amm_info['baseVault'],
                    'quote_vault': amm_info['quoteVault'],
                    'market_id': amm_info['marketId'],
                    'market_base_vault': amm_info['marketBaseVault'],
                    'market_quote_vault': amm_info['marketQuoteVault'],
                    'market_authority': amm_info['marketAuthority'],
                    'bids': amm_info['marketBids'],
                    'asks': amm_info['marketAsks'],
                    'event_queue': amm_info['marketEventQueue'],
                    'pool_open_time' : amm_info['openTime']
            }



def main():
    mint_decimals = config.getint("MINT", "decimals")
    mint_amount = config.getint("MINT", "amount")
    
    token_name = config.get("METADATA","token_name")
    symbol = config.get("METADATA","symbol")
    URI = config.get("METADATA","uri")
        
    payer = get_payer(secret_Key)
    
    print("||===[MINT TOKEN Ver:1.0.0]===||")
    tx = create_and_mint_to_account(solana_client, mint_amount, mint_decimals, payer, GAS_PRICE, GAS_LIMIT, token_name, symbol, URI)

    sleep(3600)
    return
    
if __name__ == "__main__":
    main()