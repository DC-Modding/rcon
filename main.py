import os
import discord
from discord.ext import commands
from mcrcon import MCRcon
import sqlite3
import statics

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="-", intents=intents)

db_path = os.path.abspath(__file__)
db_path = os.path.join(os.path.dirname(db_path), 'servers.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS servers
             (name TEXT, ip TEXT, port INTEGER, password TEXT)''')
conn.commit()

def check_user(ctx):
    return ctx.user.id in statics.authorized_users

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    await bot.tree.sync()

async def get_server_names(interaction: discord.Interaction, current: str):
    c.execute("SELECT name FROM servers")
    servers = c.fetchall()
    return [discord.app_commands.Choice(name=server[0], value=server[0]) for server in servers if
            current.lower() in server[0].lower()]

async def get_server_names_with_all(interaction: discord.Interaction, current: str):
    c.execute("SELECT name FROM servers")
    servers = c.fetchall()
    choices = [discord.app_commands.Choice(name=server[0], value=server[0]) for server in servers if
               current.lower() in server[0].lower()]
    if current.lower() in "all":
        choices.append(discord.app_commands.Choice(name="all", value="all"))
    return choices

@bot.tree.command(name="add", description="Add a server to the list")
async def add_server(ctx: discord.Interaction, server_name: str, ip: str, port: int, password: str):
    if not check_user(ctx):
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    c.execute("SELECT * FROM servers WHERE name=?", (server_name,))
    if c.fetchone():
        await ctx.response.send_message(f'Server with the name `{server_name}` already exists.')
    else:
        c.execute("INSERT INTO servers (name, ip, port, password) VALUES (?, ?, ?, ?)",
                  (server_name, ip, port, password))
        conn.commit()
        await ctx.response.send_message(f'Server `{server_name}` added.')

@bot.tree.command(name="edit", description="Edit an existing server")
@discord.app_commands.autocomplete(server_name=get_server_names)
async def edit_server(ctx: discord.Interaction, server_name: str, new_ip: str = None, new_port: int = None,
                      new_password: str = None):
    if not check_user(ctx):
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    c.execute("SELECT * FROM servers WHERE name=?", (server_name,))
    if c.fetchone():
        if new_ip:
            c.execute("UPDATE servers SET ip=? WHERE name=?", (new_ip, server_name))
        if new_port:
            c.execute("UPDATE servers SET port=? WHERE name=?", (new_port, server_name))
        if new_password:
            c.execute("UPDATE servers SET password=? WHERE name=?", (new_password, server_name))
        conn.commit()
        await ctx.response.send_message(f'Server `{server_name}` updated.')
    else:
        await ctx.response.send_message(f'Server with the name `{server_name}` not found.')

@bot.tree.command(name="delete", description="Delete a server from the list")
@discord.app_commands.autocomplete(server_name=get_server_names)
async def delete_server(ctx: discord.Interaction, server_name: str):
    if not check_user(ctx):
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    c.execute("SELECT * FROM servers WHERE name=?", (server_name,))
    if c.fetchone():
        c.execute("DELETE FROM servers WHERE name=?", (server_name,))
        conn.commit()
        await ctx.response.send_message(f'Server `{server_name}` deleted.')
    else:
        await ctx.response.send_message(f'Server with the name `{server_name}` not found.')

@bot.tree.command(name="list", description="List all servers")
async def list_servers(ctx: discord.Interaction):
    if not check_user(ctx):
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    c.execute("SELECT * FROM servers")
    servers = c.fetchall()
    if servers:
        await ctx.response.send_message("Fetching server list...")
        for server in servers:
            embed = discord.Embed(title=f"Server: {server[0]}", color=discord.Color.blue())
            embed.add_field(name="IP", value=server[1], inline=True)
            embed.add_field(name="Port", value=str(server[2]), inline=True)
            embed.add_field(name="Password", value=server[3], inline=True)
            await ctx.followup.send(embed=embed)
    else:
        await ctx.response.send_message("No servers found.")

@bot.tree.command(name="rcon", description="Send an RCON command")
@discord.app_commands.autocomplete(server_name=get_server_names_with_all)
async def rcon_command(ctx: discord.Interaction, server_name: str, *, command: str):
    if not check_user(ctx):
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await ctx.response.defer()  # Defer the response to avoid timeout
    if server_name.lower() == "all":
        c.execute("SELECT name, ip, port, password FROM servers")
        servers = c.fetchall()
        if servers:
            responses = []
            for server in servers:
                name, ip, port, password = server
                try:
                    with MCRcon(ip, password, port) as mcr:
                        response = mcr.command(command)
                        responses.append(f'{name} - {response}')
                except Exception as e:
                    responses.append(f'{name} - Error: {e}')
            response_message = '\n\n'.join(responses)
            await ctx.followup.send(f'Responses:\n{response_message}')
        else:
            await ctx.followup.send('No servers found.')
    else:
        c.execute("SELECT ip, port, password FROM servers WHERE name=?", (server_name,))
        server = c.fetchone()
        if server:
            ip, port, password = server
            try:
                with MCRcon(ip, password, port) as mcr:
                    response = mcr.command(command)
                    await ctx.followup.send(f'Response: {response}')
            except Exception as e:
                await ctx.followup.send(f'Error: {e}')
        else:
            await ctx.followup.send('Server not found.')

bot.run(statics.bot_token)
