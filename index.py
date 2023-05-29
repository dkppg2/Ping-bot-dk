
import os
import subprocess
import asyncio
from pyrogram import Client, filters, types
from pymongo import MongoClient

api_id = "11834008"
api_hash = "469c11d445ed952818017329db22483f"
bot_token = "6185330461:AAFOMtt2bZqsaoI6es41NEGAgx8zH93wo0w"
bot_username = "DK_MAIN_MASTER_BOT"
app = Client("ping_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Connect to MongoDB Atlas
mongo_client = MongoClient("YOUR_MONGODB_CONNECTION_STRING")  # Replace with your MongoDB connection string
db = mongo_client["ping_bot_db"]  # Specify the name of your MongoDB database
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

    website = {"name": website_name, "url": website_url, "status": "off"}
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

# Define a command handler for /start command
@app.on_message(filters.command("start"))
async def start_ping(client, message):
    await message.reply_text("Pinging websites from the database.")

    websites = websites_collection.find()
    for website in websites:
        website_name = website["name"]
        website_url = website["url"]
        try:
            ping_output = await asyncio.create_subprocess_shell(f"ping -c 4 {website_url}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await ping_output.communicate()
            ping_output = stdout.decode()

            result = f"Ping result for {website_name}:\n\n{ping_output}"
            await message.reply_text(result)

            websites_collection.update_one({"name": website_name}, {"$set": {"status": "on"}})
        except subprocess.SubprocessError as e:
            error = f"Error pinging {website_name}:\n\n{e.stderr.decode()}"
            await message.reply_text(error)

            websites_collection.update_one({"name": website_name}, {"$set": {"status": "off"}})

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

# Define a command handler for /list command
@app.on_message(filters.command("list"))
async def list_websites(client, message):
    websites = websites_collection.find()
    buttons = []
    for website in websites:
        website_name = website["name"]
        website_status = website["status"]
        button_text = f"{website_name}"
        callback_data = f"status_{website_name}"  # Unique callback data for each website
        buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
        buttons.append(types.InlineKeyboardButton(text=website_status, callback_data=callback_data))

    markup = types.InlineKeyboardMarkup([buttons])
    await message.reply_text("Select a website to ping:", reply_markup=markup)

# Define a callback handler for the inline markup buttons
@app.on_callback_query()
async def handle_callback(client, callback_query):
    callback_data = callback_query.data
    if callback_data.startswith("status_"):
        website_name = callback_data.split("_")[1]
        website = websites_collection.find_one({"name": website_name})
        if website:
            website_url = website["url"]
            try:
                ping_output = await asyncio.create_subprocess_shell(f"ping -c 4 {website_url}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = await ping_output.communicate()
                ping_output = stdout.decode()

                result = f"Ping result for {website_name}:\n\n{ping_output}"
                await callback_query.message.reply_text(result)

                websites_collection.update_one({"name": website_name}, {"$set": {"status": "on"}})
            except subprocess.SubprocessError as e:
                error = f"Error pinging {website_name}:\n\n{e.stderr.decode()}"
                await callback_query.message.reply_text(error)

                websites_collection.update_one({"name": website_name}, {"$set": {"status": "off"}})
        else:
            await callback_query.message.reply_text(f"Website '{website_name}' not found. Bot username: {bot_username}")

# Start the bot
app.run()
