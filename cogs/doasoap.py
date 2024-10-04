import discord
import json
import subprocess
import os
from discord.ext import commands
from cleaninty.ctr.simpledevice import SimpleCtrDevice
from cleaninty.ctr.soap.manager import CtrSoapManager
from cleaninty.ctr.soap import helpers
from pyctr.type.exefs import ExeFSReader
from io import BytesIO, StringIO
from cleaninty.nintendowifi.soapenvelopebase import SoapCodeError
from .cleaninty_abstracter import eshop_region_change, delete_eshop_account


class doaSOAP(
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

        # <json stuff>
        try:
            jsonStr = await jsonfile.read()
            jsonStr = jsonStr.decode("utf-8")
            json.loads(jsonStr)  # Validate the json, output useless
        except Exception:
            await ctx.respond(ephemeral=True, content="Failed to load json")
            return
        # </json stuff>

        try:
            dev = SimpleCtrDevice(json_string=jsonStr)
            soapMan = CtrSoapManager(dev, False)
            helpers.CtrSoapCheckRegister(soapMan)
        except Exception as e:
            await ctx.respond(
                ephemeral=True, content=f"Cleaninty error:\n```\n{e}\n```"
            )
            return
        jsonStr = dev.serialize_json()
        json_object = json.loads(jsonStr)
        json_region = json_object["region"]

        # if json_region == "USA":
        if False:
            region_change = "JPN"
            country_change = "JP"
            language_change = "ja"
        else:
            region_change = "USA"
            country_change = "US"
            language_change = "en"

        resultStr += "Attempting eShopRegionChange...\n"
        try:
            jsonStr, resultStr = eshop_region_change(
                json_string=jsonStr,
                region=region_change,
                country=country_change,
                language=language_change,
                result_string=resultStr,
            )
        except SoapCodeError:
            pass
        else:
            resultStr += (
                "\neShopRegionChange successful, attempting account deletion...\n"
            )
            helpers.CtrSoapCheckRegister(soapMan)
            resultStr += f"region: {soapMan.region}\ncountry: {soapMan.country}\nlanguage: {soapMan.language}\n"
            jsonStr, resultStr = delete_eshop_account(
                json_string=jsonStr, result_string=resultStr
            )
        resultStr += "```"
        await ctx.respond(ephemeral=True, content=resultStr)
        # do stuff with soapman


def setup(bot):
    bot.add_cog(doaSOAP(bot))
