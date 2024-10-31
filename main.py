import datetime
import discord
import os
from cleaninty.ctr.simpledevice import SimpleCtrDevice
from cleaninty.ctr.soap.manager import CtrSoapManager
from cleaninty.ctr.soap import helpers, ias
from dotenv import load_dotenv
from cogs.abstractors.db_abstractor import the_db


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


@bot.slash_command(description="get FATFS return code info")
async def fatfserr(
    ctx: discord.ApplicationContext,
    input: discord.Option(int, description="the value"),
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


@bot.slash_command(description="gets the time nintendo thinks it is")
async def nintendotime(ctx: discord.ApplicationContext):
    try:
        await ctx.defer(ephemeral=True)
    except discord.errors.NotFound:
        return

    db = the_db()
    device = SimpleCtrDevice(json_string=db.get_donor_json_ready_for_transfer()[1])
    soap_device = CtrSoapManager(device, False)
    helpers.CtrSoapCheckRegister(soap_device)

    utc_0 = datetime.datetime.fromtimestamp(0, datetime.UTC)

    acct_attributes = ias.GetAccountAttributesByProfile(soap_device, "MOVE_ACCT")
    server_time = (
        utc_0 + datetime.timedelta(milliseconds=acct_attributes.timestamp)
    ).timestamp()
    await ctx.respond(
        ephemeral=True, content=f"<t:{int(server_time)}:T><t:{int(server_time)}:D>"
    )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} successfully!")
    print(
        discord.utils.oauth_url(
            bot.user.id, permissions=discord.Permissions(permissions=2147518464)
        )
    )
    await bot.change_presence(activity=discord.Game(name="I HAS ...MANY THINGS"))


@bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    await ctx.respond(
        ephemeral=True,
        content="an error has occurred, please do not attempt to run the command you just ran again",
    )
    raise error


bot.load_extension("cogs.soupman")
bot.load_extension("cogs.soap_stuff")

bot.run(os.getenv("DISCORD_TOKEN"))

print("\nexiting")
