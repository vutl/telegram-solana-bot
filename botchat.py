from telethon.sync import TelegramClient
from telethon import events
from telethon import Button
from constants import api_id, api_hash, bot_token

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

button_functions = {
    "createtoken": "• Create SPL Token: 0.1 SOL",
    "createopenbook": "• Openbook Market Id: 0.6 SOL",
    "createlpr": "• Create LP on Raydium: 0.6 SOL",
    "burn": "• Burn LP: 0.15 SOL",
    "locklp": "• Lock LP: 0.25 SOL",
    "fastremovelp": "• Fast Remove LP: 0.5 SOL"
}

# Tin nhan
start_message = """
The Fastest SPL Token Creator on Solana - SolMint Token Tools
Website | Telegram | Twitter
• Creat SPL token : 0.1 SOL
. Openbook Market Id: 0.6 SOL
. Creat LP on Raydium : 0,6 SOL
• Burn Lp: 0.15 SOL
• Lock LP: 0.25 SOL
• Fast Remove LP: 0.5 SOL
Main Wallet
Address: n/a
Balance: n/a
www.solmint.dev
SOLMINT | Release your project in 30 seconds
We have every tool you need to build a successful solana project!
"""

# Buttons
buttons = [
    [Button.inline("Connect Wallet", b'connectwallet'), Button.inline("Create Token", b'createtoken')],
    [Button.inline("Create OpenBook", b'createopenbook'), Button.inline("Create LP", b'createlpr')],
    [Button.inline("Burn", b'burn'), Button.inline("Remove LP", b'removelp')]
]

# Send tin nhan chao mung
async def send_start_message(event):
    await event.respond(start_message, buttons=buttons)

# Handle buttons
@client.on(events.CallbackQuery)
async def handle_button(event):
    button = event.data.decode('utf-8')
    if button in button_functions:
        # response_message = f"You selected: {button_functions[button]}"
        response_message = f"Please connect or create a new wallet to use the features. Use the /wallet command to do it"
        await event.edit(response_message, buttons=buttons)
    else:
        await event.edit('Invalid selection', buttons=buttons)

@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    sender_username = await event.get_sender()
    
    message_text = event.raw_text
    
    reply_message = f"Hello {sender_username.username}, you said: {message_text}"
    
    await event.reply(reply_message)

client.add_event_handler(send_start_message, events.NewMessage)
client.run_until_disconnected()