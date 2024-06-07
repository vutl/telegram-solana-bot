from create_token import make_swap_instruction, execute_tx, get_token_account,  fetch_pool_keys, sell_get_token_account, get_payer
from birdeye import getSymbol
from new_pools_list import check
from constants import LAMPORTS_PER_SOL
from solana.rpc.commitment import Commitment
from configparser import ConfigParser
from time import sleep, time
from argparse import ArgumentParser
import os ,sys, asyncio, time
import struct
from enum import IntEnum
from construct import Bytes, Flag, Int32ul, Int64ul, BytesInteger, Sequence, Array
from construct import Struct as cStruct
import base58
from spl.token.instructions import close_account, CloseAccountParams
from spl.token.client import Token
from spl.token.core import _TokenCore
from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from constants import solana_client


def buy_swap_price(tx, client, baseDec):
    data = None
    while data == None:
        data = client.get_transaction(tx, commitment=Commitment("confirmed"), max_supported_transaction_version=0).value.transaction.meta.inner_instructions[-1].instructions
    #data = client.get_transaction(tx, commitment=Commitment("confirmed"), max_supported_transaction_version=0).value
    #print(data.transaction.meta.inner_instructions[0].instructions)
    SOL = data[0].data
    Token = data[1].data
    DATA_LAYOUT = cStruct(
        'None' / Bytes(1),
        'Amount' / Int64ul
    )
    
    sol_amount = DATA_LAYOUT.parse(base58.b58decode(SOL)).Amount * (10**-9)      
    token_amount = DATA_LAYOUT.parse(base58.b58decode(Token)).Amount * (10**-baseDec)
    price = sol_amount / token_amount
    return price, sol_amount, token_amount


def sell_swap_price(tx, client, baseDec):
    data = None
    while data == None:
        data = client.get_transaction(tx, commitment=Commitment("confirmed"), max_supported_transaction_version=0).value.transaction.meta.inner_instructions[-1].instructions
    #data = client.get_transaction(tx, commitment=Commitment("confirmed"), max_supported_transaction_version=0).value
    #print(data.transaction.meta.inner_instructions[0].instructions)
    SOL = data[1].data
    Token = data[0].data
    DATA_LAYOUT = cStruct(
        'None' / Bytes(1),
        'Amount' / Int64ul
    )
    
    sol_amount = DATA_LAYOUT.parse(base58.b58decode(SOL)).Amount * (10**-9)      
    token_amount = DATA_LAYOUT.parse(base58.b58decode(Token)).Amount * (10**-baseDec)
    price = sol_amount / token_amount
    return price, sol_amount, token_amount

def buy(solana_client, TOKEN_TO_SWAP_BUY, payer, amount, pool_keys):

    config = ConfigParser()
    config.read('config.ini')
    GAS_PRICE =  config.getint("FEE", "computeUnitPriceMicroLamports")
    GAS_LIMIT =  config.getint("FEE", "computeUnitLimitRaydium")

    EARLY_BUY =  config.getfloat("INVESTMENT", "WHEN_TO_BUY")
    LATE_BUY = config.getfloat("INVESTMENT", "WHEN_TO_STOP")

    pair_or_mint  = Pubkey.from_string(TOKEN_TO_SWAP_BUY)
    
    #pool_keys = fetch_pool_keys(TOKEN_TO_SWAP_BUY, solana_client)
    print("[INF]Kèo Này Mở Bát Lúc: {}".format(datetime.datetime.fromtimestamp(pool_keys["pool_open_time"])))

    if pool_keys == "failed":
        return "failed"
    
    if str(pool_keys['base_mint']) != "So11111111111111111111111111111111111111112":
        mint = pool_keys['base_mint']
    else:
        mint = pool_keys['quote_mint']

        
    """
    Calculate amount
    """
    amount_in = int(amount * LAMPORTS_PER_SOL)
    # slippage = 0.1
    # lamports_amm = amount * LAMPORTS_PER_SOL
    # amount_in =  int(lamports_amm - (lamports_amm * (slippage/100)))

    txnBool = True
    while txnBool:
        try:
            #"""Get swap token program id"""
            print("[BUY] KHỞI TẠO LỆNH BUY SWAP         | {}".format(datetime.datetime.now()))
            accountProgramId = solana_client.get_account_info_json_parsed(mint)
            TOKEN_PROGRAM_ID = accountProgramId.value.owner

            """
            Set Mint Token accounts addresses
            """
            #print("2. Get Mint Token accounts addresses...")
            swap_associated_token_address, swap_token_account_Instructions  = get_token_account(solana_client, payer.pubkey(), mint)


            """
            Create Wrap Sol Instructions
            """
            #print("3. Create Wrap Sol Instructions...")
            balance_needed = Token.get_min_balance_rent_for_exempt_for_account(solana_client)
            WSOL_token_account, create_wrapped_native_tx, payer, Wsol_account_keyPair, opts, = _TokenCore._create_wrapped_native_account_args(TOKEN_PROGRAM_ID, payer.pubkey(), payer,amount_in,
                                                                False, balance_needed, Commitment("confirmed"))
            #wrap_txn = solana_client.send_transaction(wrap_tx, payer, Wsol_account_keyPair, opts=opts)
            #print(wrap_txn)
            """
            Create Swap Instructions
            """
            #print("4. Create Swap Instructions...")
            #swap_tx = Transaction(fee_payer=payer.pubkey(), instructions=[set_compute_unit_limit(GAS_LIMIT), set_compute_unit_price(GAS_PRICE)])
            instructions_swap = make_swap_instruction(  amount_in, 
                                                        WSOL_token_account,
                                                        swap_associated_token_address,
                                                        pool_keys, 
                                                        mint, 
                                                        solana_client,
                                                        payer
                                                    )


            #print("5. Create Close Account Instructions...")
            params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(), program_id=TOKEN_PROGRAM_ID)
            closeAcc =(close_account(params))


            #print("6. Add instructions to transaction...")
            swap_tx = Transaction(fee_payer=payer.pubkey())
            swap_tx.add(set_compute_unit_limit(GAS_LIMIT)) #my default limit
            swap_tx.add(set_compute_unit_price(GAS_PRICE))
            swap_tx.add(create_wrapped_native_tx)

            if swap_token_account_Instructions != None:
                swap_tx.add(swap_token_account_Instructions)
            swap_tx.add(instructions_swap)
            swap_tx.add(closeAcc)


            while True:
                duration = pool_keys["pool_open_time"] - time.time()
                if duration >= EARLY_BUY:
                    print("\r[INF] {}    | Mở Bát Trong Vòng: {} giây".format(datetime.datetime.now(), duration),end="")
                elif EARLY_BUY > duration and duration > -LATE_BUY:
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                    txid_string_sig = asyncio.run(execute_tx(swap_tx, payer, Wsol_account_keyPair, None))
                    txnBool = False
                    return txid_string_sig
                else:
                    print("[INF] QUÁ TRỄ!!! HỦY LỆNH    |")
                    return "failed"
        except:
            txnBool = False
            #print(txnBool)
            if txid_string_sig != "failed":
                return txid_string_sig, pool_keys["base_decimals"]
            else:
                return "failed"


def sell(solana_client, TOKEN_TO_SWAP_SELL, payer, pool_keys, bought_price):

    config = ConfigParser()
    config.read('config.ini')
    GAS_PRICE =  config.getint("INVESTMENT", "computeUnitPriceMicroLamports")
    GAS_LIMIT =  config.getint("INVESTMENT", "computeUnitLimitRaydium")

    take_profit_price_level = config.getfloat("TAKE_PROFIT","PRICE_LEVEL")
    stop_loss_price_level = config.getfloat("STOP_LOSS","PRICE_LEVEL")
    HOLD_TIME = config.getfloat("INVESTMENT", "WHEN_TO_SELL")

    mint1 = Pubkey.from_string(TOKEN_TO_SWAP_SELL)
    sol = Pubkey.from_string("So11111111111111111111111111111111111111112")

    """Get swap token program id"""
    #print("\n[INF] BẮT ĐẦU QUÁ TRÌNH BÁN")

    """Get Pool Keys"""
    """print("2. Get Pool Keys...")"""
    #pool_keys = fetch_pool_keys(str(mint1))
    if pool_keys == "failed":
        return "failed"

    if str(pool_keys['base_mint']) != "So11111111111111111111111111111111111111112":
        mint = pool_keys['base_mint']
    else:
        mint = pool_keys['quote_mint']

    TOKEN_PROGRAM_ID = solana_client.get_account_info_json_parsed(mint).value.owner

    txnBool = True
    while txnBool:
        """Get Token Balance from wallet"""
        print("[INF] KIỂM TRA SỐ DƯ TOKEN...")

        balanceBool = True
        while balanceBool:
            try:
                tokenPk = mint

                accountProgramId = solana_client.get_account_info(tokenPk)
                programid_of_token = accountProgramId.value.owner

                accounts = solana_client.get_token_accounts_by_owner_json_parsed(payer.pubkey(),TokenAccountOpts(program_id=programid_of_token)).value
                amount_in = 0
                #print(accounts)
                for account in accounts:
                    mint_in_acc = account.account.data.parsed['info']['mint']
                    if mint_in_acc == str(mint):
                        #print(account)
                        amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
                        print("\n[INF] Token Balance: {}".format(amount_in))
                        break
                if int(amount_in) > 0:
                    balanceBool = False
                else:
                    print("\rSố Dư Token Chưa Được Cập Nhật... Thử Lại...",end="")
                    time.sleep(1)
            except:
                print("\r[ERR] No Balance, Retrying...",end="")

        """Get token accounts"""
        print("\n[INF] Tìm TOKEN ACCOUNT Để SWAP")
        swap_token_account = sell_get_token_account(solana_client, payer.pubkey(), mint)
        WSOL_token_account, WSOL_token_account_Instructions = get_token_account(solana_client,payer.pubkey(), sol)
        
        if swap_token_account == None:
            print("[ERR] Không tìm thấy Token Account")
            return "failed"

        else:
            """Make swap instructions"""
            print("[SEL] KHỞI TẠO LỆNH SWAP SELL")
            instructions_swap = make_swap_instruction(  amount_in, 
                                                        swap_token_account,
                                                        WSOL_token_account,
                                                        pool_keys, 
                                                        mint, 
                                                        solana_client,
                                                        payer
                                                    )

            """Close wsol account"""
            #print("6.  Create Instructions to Close WSOL account...")
            params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(), program_id=TOKEN_PROGRAM_ID)
            closeAcc =(close_account(params))

            """Create transaction and add instructions"""
            #print("7. Create transaction and add instructions to Close WSOL account...")
            swap_tx = Transaction(fee_payer=payer.pubkey())
            signers = [payer]

            swap_tx.add(set_compute_unit_limit(GAS_LIMIT)) #my default limit
            swap_tx.add(set_compute_unit_price(GAS_PRICE))

            if WSOL_token_account_Instructions != None:
                swap_tx.add(WSOL_token_account_Instructions)
            swap_tx.add(instructions_swap)
            swap_tx.add(closeAcc)

            sell_wait = True
            start_sell = time.time()
            while sell_wait:
                spot_price = check_pool_price(pool_keys, solana_client)
                print("\r[INF] THỜI GIAN GIỮ: {} giây ==|== GIÁ TOKEN: {} SOL".format(time.time()-start_sell, spot_price), end='')
                if spot_price >= take_profit_price_level * bought_price:
                    print("\n[INF] Chạm TakeProfit")
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                    txn = asyncio.run(execute_tx(swap_tx, payer, None, signers))
                    sell_wait = False
                    txnBool = False
                    return txn
                elif spot_price <= stop_loss_price_level * bought_price:
                    print("\n[INF] Chạm StopLoss")
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                    txn = asyncio.run(execute_tx(swap_tx, payer, None, signers))
                    sell_wait = False
                    txnBool = False
                    return txn
                else:
                    if time.time()-start_sell > HOLD_TIME:
                        print("\n[INF] Quá Thời Gian Giữ")
                        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                        txn = asyncio.run(execute_tx(swap_tx, payer, None, signers))
                        sell_wait = False
                        txnBool = False
                        return txn

def check_pool_price(pool_keys, solana_client):
    token_amount_in_vault = solana_client.get_token_account_balance(pool_keys["base_vault"]).value.ui_amount
    sol_amount_in_vault = solana_client.get_token_account_balance(pool_keys["quote_vault"]).value.ui_amount 
    return sol_amount_in_vault/token_amount_in_vault


def main():
    config = ConfigParser()
    config.read('config.ini')
    secret_Key = config.get("WALLET", "private_key")

    token_to_swap = config.get("SNIPE_INFO", "token")
    amount = config.getfloat("SNIPE_INFO", "amount")
    payer = get_payer(secret_Key)

    """1. Get Pool infomation from mint"""
    print("||===[SNIPE-TOKEN]===--->|{}|".format(token_to_swap))
    pool_keys = fetch_pool_keys(token_to_swap, solana_client)
    
    """2. Snipe Buy Token"""
    txid_string_sig = buy(solana_client, token_to_swap, payer, amount, pool_keys)
    
    """3. Check Bought Price"""
    if txid_string_sig != "failed":
        bought_price, sol_amount, token_amount = buy_swap_price(txid_string_sig, solana_client, pool_keys["base_decimals"])
        print("==========================================================")
        print("[BUY] GIÁ MUA: {} SOL | {} SOL = {} Token".format(bought_price, sol_amount, token_amount))
        print("==========================================================")
        """4. Dump Token"""

        sell_txid_string_sig = sell(solana_client, token_to_swap, payer, pool_keys, bought_price)
        if sell_txid_string_sig != "failed":
            sell_price, sol_amount, token_amount = sell_swap_price(sell_txid_string_sig, solana_client, pool_keys["base_decimals"])
            print("==========================================================")
            print("[SEL] GIÁ BÁN: {} SOL | {} SOL = {} Token".format(sell_price, sol_amount, token_amount))
            print("==========================================================")
        #sell_wait = True
        #start_sell = time()
        #while sell_wait:
        #    spot_price = check_pool_price(pool_keys, solana_client)
        #    print("\r[INF] THỜI GIAN GIỮ: {} giây ==|== GIÁ TOKEN: {} SOL".format(time()-start_sell,spot_price), end='')
        #    if spot_price >= take_profit_price_level * bought_price:
        #        txid_string_sig = sell(solana_client, token_to_swap, payer, pool_keys)
        #        sell_price, sol_amount, token_amount = sell_swap_price(txid_string_sig, solana_client, pool_keys["base_decimals"])
        #        print("\n==========================================================")
        #        print("[SEL] TAKE PROFIT: {} SOL | {} SOL = {} Token".format(sell_price, sol_amount, token_amount))
        #        print("==========================================================")
        #        sell_wait = False
        #    elif spot_price <= stop_loss_price_level * bought_price:
        #        txid_string_sig = sell(solana_client, token_to_swap, payer, pool_keys)
        #        sell_price, sol_amount, token_amount = sell_swap_price(txid_string_sig, solana_client, pool_keys["base_decimals"])
        #        print("\n==========================================================")
        #        print("[SEL] STOP_LOSS: {} SOL | {} SOL = {} Token".format(sell_price, sol_amount, token_amount))
        #        print("==========================================================")
        #        sell_wait = False
        #    else:
        #        if time()-start_sell > HOLD_TIME:
        #            txid_string_sig = sell(solana_client, token_to_swap, payer, pool_keys)
        #            sell_price, sol_amount, token_amount = sell_swap_price(txid_string_sig, solana_client, pool_keys["base_decimals"])
        #            print("\n==========================================================")
        #            print("[SEL] QUÁ THỜI GIAN GIỮ, BÁN: {} SOL | {} SOL = {} Token".format(sell_price, sol_amount, token_amount))
        #            print("==========================================================")
        #            sell_wait = False
    sleep(3600)
    return
    
if __name__ == "__main__":
    main()