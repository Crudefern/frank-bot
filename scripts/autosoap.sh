#!/usr/bin/env bash

# check_catch_counter(): Runs a command and only outputs errors (if there are any), then gives a status update and optionally halts if an error was detected.
# Takes three parameters. $1 (string): Command to be executed. $2 (string): Description of command's purpose. $3 (bool): Whether or not to halt on failure.
rm -rf *Zone.Identifier

check_catch_counter() {
    local exit_on_fail
    exit_on_fail=${3:-1} # Always halt on errors unless manually specified
    local error
    error=$($1 2>&1 >/dev/null)

    if [[ -n "$error" ]]; then
        echo "$2 failed, causing the following error:"
        echo "$error"
        if [[ "$exit_on_fail" -eq "1" ]]; then
            echo "Halting execution due to the above error."
            exit 2
        else
            echo "The above error has been marked as non-fatal. Continuing operation."
            return 1
        fi
    else
        echo "$2 succeeded."
        return 0
    fi
}
latestexefs=$(ls ./Tempfiles/*.exefs)
latestexefs=${latestexefs:2}
latestjson=${latestexefs:0:-6}.json
dd if="$latestexefs" of="./Tempfiles/otp.bin" bs=1 skip=3072 count=256 status=none
dd if="$latestexefs" of="./Tempfiles/secinfo.bin" bs=1 skip=1024 count=273 status=none
check_catch_counter "cleaninty ctr GenJson --otp ./Tempfiles/otp.bin --secureinfo ./Tempfiles/secinfo.bin --region JPN --country jp --out $latestjson" "Compiling a json from $latestexefs" "1"
check_catch_counter "cleaninty ctr CheckReg --console $latestjson" "Checking $latestjson's eShop data" "1"
jsonregion=$(grep -oP '(?<="region": ")[A-Z]{3}(?=",)' <"$latestjson")
jsoncountry=$(grep -oP '(?<="country": ")[A-Z]{2}(?=",)' <"$latestjson")
jsonlanguage=$(grep -oP '(?<="language": ")[a-z]{2}(?=",)' <"$latestjson")
echo "Current JSON's region: $jsonregion"
rm -f ./Tempfiles/otp.bin ./Tempfiles/secinfo.bin

if [[ "$jsonregion" == "USA" ]]; then
    regionchange=JPN
else
    regionchange=USA
fi

if [[ "$regionchange" == USA ]]; then
    countrychange=US
    languagechange=en
else
    countrychange=JP
    languagechange=ja
fi

echo "Processing..."

if cleaninty ctr EShopRegionChange --console "$latestjson" --region "$regionchange" --country "$countrychange" --language "$languagechange" | grep -q "Complete!"; then
    echo "SOAP Transfer complete!"
    echo "This console can perform a System Transfer immediately."
    check_catch_counter "cleaninty ctr EShopDelete --console $latestjson" "Deleting $latestjson's eShop account" "1"
    exit 0
else
    printf "\n\n\nRegion change failed. A system transfer is required.\n"
    if ! cd ../Donors; then
        echo "Donors folder not found. Please obtain the lamb sauce and files from donor consoles, then try again."
        exit 1
    fi

    autodonorchoice="none"
    for donor in *.json; do
        if cleaninty ctr LastTransfer --console "$donor" | grep -q "Ready for transfer!"; then
            if cleaninty ctr CheckReg --console "$donor" | grep -q "$jsonregion"; then
                echo "$donor is off cooldown and has been selected."
                autodonorchoice="$donor"
                break
            else
                echo "$donor is off cooldown, but is the wrong region. Changing automatically..."
                if check_catch_counter "cleaninty ctr EShopRegionChange --console $donor --region $jsonregion --country $jsoncountry --language $jsonlanguage" "Changing $donor's eShop region" "0"; then
                    echo "Region change to $jsonregion successful. $donor has been selected."
                    autodonorchoice="$donor"
                    break
                else
                    echo "Moving to next donor..."
                    print "\n\n"
                    continue
                fi
            fi
        else
            echo "$donor is on cooldown. Continuing..."
            continue
        fi
    done
    if [[ "$autodonorchoice" != "none" ]]; then
        cd ../scripts/Tempfiles || exit 1
        check_catch_counter "cleaninty ctr SysTransfer --source $latestjson --target ../../Donors/$autodonorchoice" "Transferring from $latestjson to $autodonorchoice" "1"
        echo "SOAP Transfer complete! System Transfer cooldown now active."
        cooldownexpiredate=$(date -d "+ 7 days" -u +"%a, %d %b %Y %T UTC")
        echo "This console can do its next System Transfer at $cooldownexpiredate."
        exit 0
    else
        echo "All donors are currently on cooldown. Please find the lamb sauce and try again later."
        exit 2
    fi
fi
