import os
import subprocess
import asyncio
from fastapi import FastAPI, Request
from pyrogram import Client, filters
from pymongo import MongoClient

# Initialize your bot using API credentials
api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"
bot_token = "6185330461:AAFOMtt2bZqsaoI6es41NEGAgx8zH93wo0w"
bot_username = "YOUR_BOT_USERNAME"
app = Client("ping_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Create a FastAPI instance
api = FastAPI()

# Connect to MongoDB Atlas
mongo_client = MongoClient("YOUR_MONGODB_CONNECTION_STRING")  # Replace with your MongoDB connection string
db = mongo_client["ping_bot_db"]  # Specify the name of your MongoDB database
websites_collection = db["websites"]  # Collection to store websites

# Define a route to handle Telegram webhook
@api.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await app.process_updates(data)
    return {"ok": True}

# Define a command handler to add websites
@app.on_message(filters.command("add_site"))
async def add_site(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 3:
        await message.reply_text("Invalid command. Please use /add_site <website_name> <website_url>")
        return

    website_name = command_parts[1]
    website_url = command_parts[2]

    website = {"name": website_name, "url": website_url}
    websites_collection.insert_one(website)

    await message.reply_text(f"Added {website_name} to the ping list. Bot username: {bot_username}")

# Define a command handler to ping a specific website
@app.on_message(filters.command("ping"))
async def ping_website(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.reply_text("Invalid command. Please use /ping <website_name>")
        return

    website_name = command_parts[1]

    website = websites_collection.find_one({"name": website_name})
    if website:
        website_url = website["url"]
        try:
            ping_output = await asyncio.create_subprocess_shell(f"ping -c 4 {website_url}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await ping_output.communicate()
            ping_output = stdout.decode()

            result = f"Ping result for {website_name}:\n\n{ping_output}"
            await message.reply_text(result)
        except subprocess.SubprocessError as e:
            error = f"Error pinging {website_name}:\n\n{e.stderr.decode()}"
            await message.reply_text(error)
    else:
        await message.reply_text(f"Website '{website_name}' not found. Bot username: {bot_username}")

# Start the bot
app.run_app(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
