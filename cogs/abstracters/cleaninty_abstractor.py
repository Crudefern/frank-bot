from cleaninty.ctr.simpledevice import SimpleCtrDevice
from cleaninty.ctr.soap.manager import CtrSoapManager
from cleaninty.ctr.soap import helpers, ias
from cleaninty.nintendowifi.soapenvelopebase import SoapCodeError
from cleaninty.ctr.ninja import NinjaManager, NinjaException
import datetime


class cleaninty_abstractor:
    def eshop_region_change(
        self, json_string, region, country, language, result_string
    ):
        result_string += "Initializing console...\n"
        device = SimpleCtrDevice(json_string=json_string)
        soap_device = CtrSoapManager(device, False)

        result_string += "Checking registry...\n"
        helpers.CtrSoapCheckRegister(soap_device)

        json_string = device.serialize_json()

        if region == soap_device.region and soap_device.account_status != "U":
            result_string += "Console already in the desired region.\n"
            return device.serialize_json(), result_string

        device.reboot()

        if soap_device.account_status != "U":
            result_string += "Initializing console session...\n"
            helpers.CtrSoapUseSystemApps(soap_device, helpers.SysApps.ESHOP)
            helpers.CtrSoapSessionConnect(soap_device)

            result_string += "Unregister...\n"
            _run_unregister(device, soap_device)

            json_string = device.serialize_json()

            device.reboot()

        soap_device.region_change(region, country, language)

        result_string += "Initializing console session...\n"
        helpers.CtrSoapUseSystemApps(soap_device, helpers.SysApps.ESHOP)
        try:
            helpers.CtrSoapSessionConnect(soap_device)
        except SoapCodeError as e:
            if e.soaperrorcode == 602:
                print("We got soap error 602.")
                print("Region could not be changed.")
                print("Any existing eshop account was deleted in the process.")
                print("This console has titles attached to it on a different region.")
                print("System transfer to another console is needed to remove them.")
                print("System transfer without NNID transfer is enough.")
                print("NNID-only transfers do not work to fix.")
                result_string += "soap error 602...\n"
                helpers.CtrSoapCheckRegister(soap_device)
                return device.serialize_json(), result_string
            raise

        helpers.CtrSoapCheckRegister(soap_device)

        return device.serialize_json(), result_string

    def delete_eshop_account(self, json_string, result_string):
        result_string += "Initializing console...\n"
        device = SimpleCtrDevice(json_string=json_string)
        soap_device = CtrSoapManager(device, False)

        result_string += "Checking registry...\n"
        helpers.CtrSoapCheckRegister(soap_device)

        result_string += "Saving updated session...\n"
        json_string = device.serialize_json()

        if soap_device.account_status == "U":
            result_string += "Console already does not have EShop account.\n"
            return device.serialize_json(), result_string

        device.reboot()

        result_string += "Initializing console session...\n"
        helpers.CtrSoapUseSystemApps(soap_device, helpers.SysApps.ESHOP)
        helpers.CtrSoapSessionConnect(soap_device)

        result_string += "Saving updated session...\n"
        json_string = device.serialize_json()

        result_string += f"Unregister...\n{_run_unregister(device, soap_device)}\n"

        result_string += "Saving updated session...\n"
        return device.serialize_json(), result_string

    def get_last_moved_time(self, json_string):
        device = SimpleCtrDevice(json_string=json_string)
        soap_device = CtrSoapManager(device, False)
        helpers.CtrSoapCheckRegister(soap_device)

        json_string = device.serialize_json()
        acct_attributes = ias.GetAccountAttributesByProfile(soap_device, "MOVE_ACCT")

        for i in acct_attributes.accountattributes:
            if i[0] == "MoveAccountLastMovedDate":
                return (int(i[1]) if i[1] else 0) / 1000


def _run_unregister(device, soap_device, result_string):
    try:
        ias.Unregister(soap_device, ias.GetChallenge(soap_device).challenge)
        soap_device.unregister_account()
        virtual = False
    except SoapCodeError as e:
        if e.soaperrorcode != 434:
            raise
        virtual = True

    if virtual:
        result_string += "Virtual account link! Attempt detach by error..."
        device.reboot()

        result_string += "Initializing console session..."
        helpers.CtrSoapUseSystemApps(soap_device, helpers.SysApps.SYSTRANSFER)
        helpers.CtrSoapSessionConnect(soap_device)

        device_ninja = NinjaManager(soap_device, False)
        try:
            device_ninja.open_without_nna()
        except NinjaException as e:
            if e.errorcode != 3136:
                raise

        device.reboot()

        helpers.CtrSoapUseSystemApps(soap_device, helpers.SysApps.ESHOP)

        helpers.CtrSoapCheckRegister(soap_device)

        if soap_device.account_status != "U":
            result_string += "Unregister..."
            ias.Unregister(soap_device, ias.GetChallenge(soap_device).challenge)
            soap_device.unregister_account()
        else:
            result_string += "Unregistered!"
        return result_string
