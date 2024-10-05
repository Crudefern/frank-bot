import discord
import json
import subprocess
from io import StringIO
from discord.ext import commands
from cleaninty.ctr.simpledevice import SimpleCtrDevice
from cleaninty.ctr.soap.manager import CtrSoapManager
from cleaninty.ctr.soap import helpers
from cleaninty.nintendowifi.soapenvelopebase import SoapCodeError
from .abstractors.cleaninty_abstractor import cleaninty_abstractor
from .abstractors.db_abstractor import mySQL


class cleaninty_stuff(
    commands.Cog
):  # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(
        self, bot
    ):  # this is a special method that is called when the cog is loaded
        self.bot = bot

    @discord.slash_command(
        description="does a soap (it actually doesn't right now, do not use)"
    )
    async def doasoap(
        self,
        ctx: discord.ApplicationContext,
        jsonfile: discord.Option(discord.Attachment),
    ):
        try:
            await ctx.defer(ephemeral=True)
        except discord.errors.NotFound:
            return

        resultStr = "```"

        myDB = mySQL()

        # <json stuff>
        try:
            soap_json = await jsonfile.read()
            soap_json = soap_json.decode("utf-8")
            json.loads(soap_json)  # Validate the json, output useless
        except Exception:
            await ctx.respond(ephemeral=True, content="Failed to load json")
            return
        # </json stuff>

        try:
            dev = SimpleCtrDevice(json_string=soap_json)
            soapMan = CtrSoapManager(dev, False)
            helpers.CtrSoapCheckRegister(soapMan)
            cleaninty = cleaninty_abstractor()
        except Exception as e:
            await ctx.respond(
                ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```"
            )
            return

        soap_json = dev.serialize_json()
        json_object = json.loads(soap_json)
        json_region = json_object["region"]

        if json_region == "USA":
            region_change = "JPN"
            country_change = "JP"
            language_change = "ja"
        else:
            region_change = "USA"
            country_change = "US"
            language_change = "en"

        resultStr += "Attempting eShopRegionChange...\n"
        try:
            soap_json, resultStr = cleaninty.eshop_region_change(
                json_string=soap_json,
                region=region_change,
                country=country_change,
                language=language_change,
                result_string=resultStr,
            )

        except SoapCodeError as err:
            if not err.soaperrorcode == 602:
                ctx.respond(ephemeral=True, content=f"uh oh...\n\n{err}")
                return
            donor_json_name, donor_json = myDB.get_donor_json_ready_for_transfer()
            soap_json, donor_json, resultStr = cleaninty.do_system_transfer(
                source_json=soap_json, donor_json=donor_json, result_string=resultStr
            )
            myDB.update_donor(donor_json_name, donor_json)
            resultStr += f"`{donor_json_name}` is now on cooldown\nDone!"

            helpers.CtrSoapCheckRegister(soapMan)
            soap_json = clean_json(soap_json)

            resultStr += "```"
            await ctx.respond(
                ephemeral=True,
                content=resultStr,
                file=discord.File(fp=StringIO(soap_json), filename=jsonfile.filename),
            )

        else:
            resultStr += (
                "\neShopRegionChange successful, attempting account deletion...\n"
            )
            soap_json, resultStr = cleaninty.delete_eshop_account(
                json_string=soap_json, result_string=resultStr
            )

        helpers.CtrSoapCheckRegister(soapMan)
        soap_json = clean_json(soap_json)

        resultStr += "```"
        await ctx.respond(
            ephemeral=True,
            content=resultStr,
            file=discord.File(fp=StringIO(soap_json), filename=jsonfile.filename),
        )
        # do stuff with soapman

    @discord.slash_command(description="check soap donor availability")
    async def soapcheck(self, ctx: discord.ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)
        except discord.errors.NotFound:
            return

        availability = subprocess.run(
            ["/usr/bin/bash", "./scripts/soapcheck.sh"], capture_output=True, text=True
        )
        await ctx.respond(ephemeral=True, content=f"```\n{availability.stdout}\n```")

    @discord.slash_command(
        description="uploads a donor soap json to be used for future soaps"
    )
    async def uploaddonorsoapjson(
        self,
        ctx: discord.ApplicationContext,
        donor_json_file: discord.Option(discord.Attachment),
    ):
        try:
            await ctx.defer(ephemeral=True)
        except discord.errors.NotFound:
            return

        if not donor_json_file.filename[-5:] == ".json":
            await ctx.respond(ephemeral=True, content="not a .json!")
            return

        try:
            donor_json = await donor_json_file.read()
            donor_json = donor_json.decode("utf-8")
            json.loads(donor_json)  # Validate the json, output useless
        except Exception:
            await ctx.respond(ephemeral=True, content="Failed to load json")
            return

        if donorcheck(donor_json):
            await ctx.respond(
                ephemeral=True,
                content="not a valid donor .json!\nif you believe this to be a mistake contact crudefern",
            )
            return

        donor_json = clean_json(donor_json)

        mySQL_DB = mySQL()
        mySQL_DB.write_donor(donor_json.filename, donor_json)

        await ctx.respond(
            ephemeral=True,
            content=f"`{donor_json.filename}` has been uploaded to the donor database\nwant to remove it? contact crudefern",
        )


def clean_json(json_string):
    json_object = json.loads(json_string)
    del json_object["titles"]
    return json.dumps(json_string, indent=2)


def donorcheck(input_json):
    """Checks for a valid donor .json as input"""
    try:
        input_json_obj = json.loads(input_json)
    except json.decoder.JSONDecodeError:
        return 1

    if len(input_json_obj["otp"]) != 344:
        return 1
    if len(input_json_obj["msed"]) != 428:
        return 1
    if len(input_json_obj["region"]) != 3:
        return 1
    return 0


def setup(bot):
    bot.add_cog(cleaninty_stuff(bot))
