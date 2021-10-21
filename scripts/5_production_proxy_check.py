from brownie import network, BadgerRegistry, Controller, SettV3, web3
from config import REGISTRY
from helpers.constants import AddressZero
from rich.console import Console

console = Console()

ADMIN_SLOT = int(0xB53127684A568B3173AE13B9F8A6016E243E63B6E8EE1178D6A717850B5D6103)

STRATEGIES = {
    "native.renCrv": "0xe66dB6Eb807e6DAE8BD48793E9ad0140a2DEE22A",
    "native.sbtcCrv": "0x2f278515425c8eE754300e158116930B8EcCBBE1",
    "native.tbtcCrv": "0x9e0742EE7BECde52A5494310f09aad639AA4790B",
    "native.hbtcCrv": "0x7354D5119bD42a77E7162c8Afa8A1D18d5Da9cF8",
    "native.pbtcCrv": "0x3f98F3a21B125414e4740316bd6Ef14718764a22",
    "native.obtcCrv": "0x50Dd8A61Bdd11Cf5539DAA83Bc8E0F581eD8110a",
    "native.bbtcCrv": "0xf92660E0fdAfE945aa13616428c9fB4BE19f4d34",
    "native.tricrypto2": "0xf3202Aa2783F3DEE24a35853C6471db065B05D37",
    "native.cvxCrv": "0xf6D442Aead5960b283281A794B3e7d3605601247",
    "native.cvx": "0xc67129cf19BB00d60CC5CF62398fcA3A4Dc02a14",
}


def main():
    """
    Checks that the proxyAdmin of all conracts added to the BadgerRegistry match
    the proxyAdminTimelock address on the same registry. How to run:

    1. Add all keys for the network's registry to the 'keys' array below.

    2. Add all authors' addresses with vaults added to the registry into the 'authors' array below.

    3. Add all all keys for the proxyAdmins for the network's registry paired to their owners' keys.

    4. Run the script and review the console output.
    """

    console.print("You are using the", network.show_active(), "network")

    # Get production registry
    registry = BadgerRegistry.at(REGISTRY)

    # Get proxyAdminTimelock
    proxyAdmin = registry.get("proxyAdminTimelock")
    assert proxyAdmin != AddressZero
    console.print("[cyan]proxyAdminTimelock:[/cyan]", proxyAdmin)

    # NOTE: Add all existing keys from your network's registry. For example:
    keys = [
        "governance",
        "guardian",
        "keeper",
        "controller",
        "badgerTree",
        "devGovernance",
        "paymentsGovernance",
        "governanceTimelock",
        "proxyAdminDev",
        "rewardsLogger",
        "keeperAccessControl",
        "proxyAdminDfdBadger",
        "dfdBadgerSharedGovernance",
    ]

    # NOTE: Add all authors from your network's registry. For example:
    authors = ["0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"]

    # NOTE: Add the keys to all proxyAdmins from your network's registry paired to their owner
    proxyAdminOwners = [
        ["proxyAdminTimelock", "governanceTimelock"],
        ["proxyAdminDev", "devGovernance"],
        ["proxyAdminDfdBadger", "dfdBadgerSharedGovernance"],
    ]

    check_by_keys(registry, proxyAdmin, keys)
    check_vaults_and_strategies(registry, proxyAdmin, authors)
    check_proxy_admin_owners(proxyAdminOwners, registry)


def check_by_keys(registry, proxyAdmin, keys):
    console.print("[blue]Checking proxyAdmins by key...[/blue]")
    # Check the proxyAdmin of the different proxy contracts
    for key in keys:
        proxy = registry.get(key)
        if proxy == AddressZero:
            console.print(key, ":[red] key doesn't exist on the registry![/red]")
            continue
        check_proxy_admin(proxy, proxyAdmin, key)


def check_vaults_and_strategies(registry, proxyAdmin, authors):
    console.print("[blue]Checking proxyAdmins from vaults and strategies...[/blue]")

    vaultStatus = [0, 1, 2]

    vaults = []
    strategies = list(STRATEGIES.values())
    stratNames = list(STRATEGIES.keys())

    # get vaults by author
    # for author in authors:
    #     vaults += registry.getVaults("v1", author)
    #     vaults += registry.getVaults("v2", author)

    # Get promoted vaults
    # for status in vaultStatus:
    #     vaults += registry.getFilteredProductionVaults("v1", status)
    #     vaults += registry.getFilteredProductionVaults("v2", status)

    # Get strategies from vaults and check vaults' proxyAdmins
    # for vault in vaults:
    #     try:
    #         vaultContract = SettV3.at(vault)
    #         # get Controller
    #         controller = Controller.at(vaultContract.controller())
    #         strategies.append(controller.strategies(vaultContract.token()))
    #         stratNames.append(vaultContract.name().replace("Badger Sett ", "Strategy "))
    #         # Check vault proxyAdmin

    #         check_proxy_admin(vault, proxyAdmin, vaultContract.name())
    #     except Exception as error:
    #         print("Something went wrong")
    #         print(error)

    for strat in strategies:
        try:
            # Check strategies' proxyAdmin
            print(strat)
            check_proxy_admin(strat, proxyAdmin, stratNames[strategies.index(strat)])
        except Exception as error:
            print("Something went wrong")
            print(error)


def check_proxy_admin(proxy, proxyAdmin, key):
    # Get proxyAdmin address form the proxy's ADMIN_SLOT
    val = web3.eth.getStorageAt(proxy, ADMIN_SLOT).hex()
    address = "0x" + val[26:66]

    # Check differnt possible scenarios
    if address == AddressZero:
        console.print(key, ":[red] admin not found on slot (GnosisSafeProxy?)[/red]")
    elif address != proxyAdmin:
        console.print(
            key, ":[red] admin is different to proxyAdminTimelock[/red] - ", address
        )
    else:
        assert address == proxyAdmin
        console.print(key, ":[green] admin matches proxyAdminTimelock![/green]")


def check_proxy_admin_owners(proxyAdminOwners, registry):
    console.print("[blue]Checking proxyAdmins' owners...[/blue]")

    for adminOwnerPair in proxyAdminOwners:
        proxyAdmin = registry.get(adminOwnerPair[0])
        owner = registry.get(adminOwnerPair[1])
        # Get proxyAdmin's owner address from slot 0
        val = web3.eth.getStorageAt(proxyAdmin, 0).hex()
        address = "0x" + val[26:66]

        # Check differnt possible scenarios
        if address == AddressZero:
            console.print(adminOwnerPair[0], ":[red] no address found at slot 0![/red]")
        elif address != owner:
            console.print(
                adminOwnerPair[0],
                ":[red] owner is different to[/red]",
                adminOwnerPair[1],
                "-",
                address,
            )
        else:
            assert address == owner
            console.print(
                adminOwnerPair[0],
                ":[green] owner matches[/green]",
                adminOwnerPair[1],
            )
