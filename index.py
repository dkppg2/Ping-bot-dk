import asyncio
import base64
import os
import subprocess
import asyncio
from pyrogram import Client, filters, types
from pymongo import MongoClient

api_id = "11834008"
api_hash = "469c11d445ed952818017329db22483f"
bot_token = "6292528961:AAFGutULjLy0ygV_w10Pn4mZ-OWCLcSe0l0"
bot_username = "DK_MAIN_MASTER_BOT"
app = Client("DK_MAIN_MASTER_BOT", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Connect to MongoDB Atlas
mongo_client = MongoClient("mongodb+srv://dkbotztg:dkbotztg@cluster0.82bybvo.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["ping_bot_dbz"]  # Specify the name of your MongoDB database
websites_collection = db["websites"]  # Collection to store websites

# Define a command handler to add websites
@app.on_message(filters.command("add_site"))
async def add_site(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 3:
        await message.reply_text("Invalid command. Please use /add_site <website_name> <website_url>")
        return

    website_name = command_parts[1]
    website_url = command_parts[2]

    website = {"name": website_name, "url": website_url, "status": "🔴 OFF"}
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
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Hello {message.from_user.mention},\n\nI Am Master Bot\n\nUse Me To UP @DKBOTZ Bot")
# Define a command handler for /start command
@app.on_message(filters.command("check"))
async def check_pingss(client, message):
    await message.reply_text("Pinging websites from the database.")

    websites = websites_collection.find()
    for website in websites:
        website_name = website["name"]
        website_url = website["url"]
        try:
            ping_output = await asyncio.create_subprocess_shell(f"ping -c 4 {website_url}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await ping_output.communicate()
            ping_output = stdout.decode()

            result = f"Ping result for {website_name}: 🟢 ON\n\n{ping_output}"
            await message.reply_text(result)

            websites_collection.update_one({"name": website_name}, {"$set": {"status": "🟢 ON"}})
        except subprocess.SubprocessError as e:
            error = f"Error pinging {website_name}: 🔴 OFF\n\n{e.stderr.decode()}"
            await message.reply_text(error)

            websites_collection.update_one({"name": website_name}, {"$set": {"status": "🔴 OFF"}})

# Define a command handler for /remove_site command
@app.on_message(filters.command("remove_site"))
async def remove_site(client, message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.reply_text("Invalid command. Please use /remove_site <website_name>")
        return

    website_name = command_parts[1]
    result = websites_collection.delete_one({"name": website_name})

    if result.deleted_count > 0:
        await message.reply_text(f"Removed {website_name} from the ping list.")
    else:
        await message.reply_text(f"Website '{website_name}' not found in the ping list.")

import asyncio
import base64

# Define a command handler for /list command
@app.on_message(filters.command("list"))
async def list_websites(client, message):
    websites = websites_collection.find()
    buttons = []
    row = []
    for website in websites:
        website_name = website["name"]
        website_status = website["status"]
        website_url = website["url"]
        button_text = f"{website_name}"
        status = f"{website_status}"
        callback_data = f"status_{base64.b64encode(website_url.encode()).decode()}_{website_name}"  # Unique callback data for each website
        row.append(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
        row.append(types.InlineKeyboardButton(text=status, callback_data=callback_data))
        if len(row) == 2:  # Adjust the number of buttons per row here
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)

    markup = types.InlineKeyboardMarkup(buttons)
    await message.reply_text("Select a website to ping:", reply_markup=markup)


# Define a callback handler for the inline markup buttons
@app.on_callback_query()
async def handle_callback(client, callback_query):
    callback_data = callback_query.data
    if callback_data.startswith("status_"):
        _, website_url_b64, website_name = callback_data.split("_")
        website_url = base64.b64decode(website_url_b64.encode()).decode()
        
        # Check website status
        is_website_up = await check_website_status(website_url)
        
        if is_website_up:
            await callback_query.message.reply_text(f"The website '{website_name}' is up.")
            websites_collection.update_one({"name": website_name}, {"$set": {"status": "🟢 ON"}})
        else:
            await callback_query.message.reply_text(f"The website '{website_name}' is down. Rechecking in 1 minute...")
            await asyncio.sleep(60)  # Wait for 1 minute
            is_website_up = await check_website_status(website_url)
            
            if is_website_up:
                await callback_query.message.reply_text(f"The website '{website_name}' is up now.")
                websites_collection.update_one({"name": website_name}, {"$set": {"status": "🟢 ON"}})
            else:
                await callback_query.message.reply_text(f"The website '{website_name}' is still down.")
                websites_collection.update_one({"name": website_name}, {"$set": {"status": "🔴 OFF"}})


async def check_website_status(website_url):
    try:
        ping_output = await asyncio.create_subprocess_shell(f"ping -c 4 {website_url}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await ping_output.communicate()
        ping_output = stdout.decode()

        return True
    except subprocess.SubprocessError:
        return False

# Start the bot
app.run()
