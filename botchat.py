from telethon.sync import TelegramClient
from telethon import events

api_id = '29398688'
api_hash = '2eb07147c2fd51961182419fb7c19ead'
bot_token = '7079490697:AAENOdhLs7PbvbugoLnANNvJthlzaw8beOc'

# Tao bot instance
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

#Khi co tnhan moi, function o duoi se dc called
@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    # Extract username ng gui tnhan
    sender_username = await event.get_sender()
    
    # Extract tnhan
    message_text = event.raw_text
    
    reply_message = f"Hello {sender_username.username}, you said: {message_text}"
    
    # Send tnhan
    await event.reply(reply_message)

client.run_until_disconnected()