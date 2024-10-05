import os
import subprocess
from dotenv import load_dotenv
import discord
from pyctr.type.exefs import ExeFSReader
from io import BytesIO

bot = discord.Bot()
load_dotenv()

fatfserrlist = (
    "FR_OK    /* (0) Succeeded */",
    "FR_DISK_ERR    /* (1) A hard error occurred in the low level disk I/O layer */",
    "FR_INT_ERR    /* (2) Assertion failed */",
    "FR_NOT_READY    /* (3) The physical drive cannot work */",
    "FR_NO_FILE    /* (4) Could not find the file */",
    "FR_NO_PATH    /* (5) Could not find the path */",
    "FR_INVALID_NAME    /* (6) The path name format is invalid */",
    "FR_DENIED    /* (7) Access denied due to prohibited access or directory full */",
    "FR_EXIST    /* (8) Access denied due to prohibited access */",
    "FR_INVALID_OBJECT    /* (9) The file/directory object is invalid */",
    "FR_WRITE_PROTECTED    /* (10) The physical drive is write protected */",
    "FR_INVALID_DRIVE    /* (11) The logical drive number is invalid */",
    "FR_NOT_ENABLED    /* (12) The volume has no work area */",
    "FR_NO_FILESYSTEM    /* (13) There is no valid FAT volume */",
    "FR_MKFS_ABORTED    /* (14) The f_mkfs() aborted due to any problem */",
    "FR_TIMEOUT    /* (15) Could not get a grant to access the volume within defined period */",
    "FR_LOCKED    /* (16) The operation is rejected according to the file sharing policy */",
    "FR_NOT_ENOUGH_CORE    /* (17) LFN working buffer could not be allocated */",
    "FR_TOO_MANY_OPEN_FILES    /* (18) Number of open files > FF_FS_LOCK */",
)


@bot.slash_command(description="does a soap but (should) actually work")
async def doasoap_functional(
    ctx: discord.ApplicationContext, file: discord.Option(discord.Attachment)
):
    try:
        await ctx.defer(ephemeral=True)
    except discord.errors.NotFound:
        return

    try:
        exeFS = ExeFSReader(BytesIO(await file.read()))
        if not "secinfo" and "otp" in exeFS.entries:
            await ctx.respond(ephemeral=True, content="Invalid essential")
            return
    except Exception:
        await ctx.respond(ephemeral=True, content="Invalid essential")
        return

    local_file = open(f"./scripts/Tempfiles/{file.filename}", mode="wb")
    local_file.write(await file.read())
    local_file.close()

    script = subprocess.run(
        ["/usr/bin/bash", "./scripts/autosoap.sh"],
        capture_output=True,
        text=True,
    )
    await ctx.respond(
        ephemeral=True, content=f"script stdout: ```\n{script.stdout}\n```"
    )
    if script.stderr != "":
        await ctx.respond(
            ephemeral=True,
            content=f"script stderr (something borked): ```\n{script.stderr}\n```",
        )


@bot.slash_command(description="check system health")
async def healthcheck(ctx: discord.ApplicationContext):
    try:
        await ctx.defer(ephemeral=True)
    except discord.errors.NotFound:
        return

    availability = subprocess.run(
        ["/usr/bin/bash", "./scripts/healthcheck.sh"], capture_output=True, text=True
    )
    await ctx.respond(ephemeral=True, content=f"```\n{availability.stdout}\n```")


@bot.slash_command(description="get FATFS return code info")
async def fatfserr(
    ctx: discord.ApplicationContext,
    input: discord.Option(name="input", required=True, description="the value"),
):
    try:
        await ctx.defer(ephemeral=True)
    except discord.errors.NotFound:
        return
    try:
        await ctx.respond(
            ephemeral=True, content=f"`{fatfserrlist[int(input.lstrip('-'))]}`"
        )
    except (IndexError, ValueError):
        await ctx.respond(ephemeral=True, content="invalid or unknown value")


@bot.event
async def on_ready():
    """Starts bot"""
    print(f"We have logged in as {bot.user}")
    print(
        discord.utils.oauth_url(
            bot.user.id, permissions=discord.Permissions(permissions=2147518464)
        )
    )
    await bot.change_presence(activity=discord.Game(name="I HAS ...MANY THINGS"))


bot.load_extension("cogs.soupman")
bot.load_extension("cogs.soap_stuff")

bot.run(os.getenv("DISCORD_TOKEN"))
