"""Player state, inventory, and stat screens."""

from collections import Counter
import random

from .data import SELLABLE_LOOT
from .pacing import say
from .terminal_colors import Fore, Style
from .ui import MenuOption, choose_menu, divider, money_text, stat_meter


def create_player():
    """Create a normal starting character.

    The player starts like a regular adventurer: no gold, no spells, basic
    health, and enough mana to matter after learning magic.
    """
    return {
        "name": "Adventurer",
        "money": 0,
        "health": 100,
        "healthMax": 100,
        "mana": 50,
        "manaMax": 50,
        "armor": 0,
        "weaponDamage": 0,
        "extraDamage": 0,
        "frogMode": False,
        "frogPower": 0,
        "frogEnergy": 25,
        "frogEnergyMax": 25,
        "backpack": [],
        "spells": [],
        "frogAttacks": [],
    }


def add_spell(player, spell_name):
    """Teach a spell once; duplicate spell entries make menus confusing."""
    if spell_name not in player["spells"]:
        player["spells"].append(spell_name)


def add_frog_attack(player, attack_name):
    """Teach the magical frog an attack once."""
    if attack_name not in player["frogAttacks"]:
        player["frogAttacks"].append(attack_name)


def activate_frog_partner(player):
    """Turn the chocolate frog into the player's battle companion."""
    player["frogMode"] = True
    player.setdefault("frogPower", 0)
    player.setdefault("frogEnergyMax", 25)
    player.setdefault("frogEnergy", player["frogEnergyMax"])
    player.setdefault("frogAttacks", [])
    if "Magical Chocolate Frog" not in player["backpack"]:
        player["backpack"].append("Magical Chocolate Frog")
    add_frog_attack(player, "Tongue Slap")


def print_stats(player):
    """Show the current player state in a compact, readable format."""
    divider("Player Stats")
    print(f"Money: {money_text(player['money'])}")
    print(
        f"Health: {Fore.RED}{stat_meter(player['health'], player['healthMax'])} "
        f"{player['health']}/{player['healthMax']}{Style.RESET_ALL}"
    )
    print(
        f"Mana: {Fore.BLUE}{stat_meter(player['mana'], player['manaMax'])} "
        f"{player['mana']}/{player['manaMax']}{Style.RESET_ALL}"
    )
    print(f"Armor: {Fore.LIGHTCYAN_EX}{player['armor']}{Style.RESET_ALL}")
    print(f"Weapon Damage: {Fore.LIGHTYELLOW_EX}+{player.get('weaponDamage', 0)}{Style.RESET_ALL}")
    print(f"Spell Damage: {Fore.LIGHTMAGENTA_EX}+{player['extraDamage']}{Style.RESET_ALL}")
    if player.get("frogMode"):
        print(
            f"Frog Energy: {Fore.LIGHTGREEN_EX}"
            f"{stat_meter(player.get('frogEnergy', 0), player.get('frogEnergyMax', 25))} "
            f"{player.get('frogEnergy', 0)}/{player.get('frogEnergyMax', 25)}"
            f"{Style.RESET_ALL}"
        )
        print(f"Frog Power: {Fore.LIGHTGREEN_EX}+{player.get('frogPower', 0)}{Style.RESET_ALL}")

    spells = ", ".join(player["spells"]) if player["spells"] else "None"
    print(f"Spells: {Fore.MAGENTA}{spells}{Style.RESET_ALL}")
    if player.get("frogMode"):
        frog_attacks = ", ".join(player.get("frogAttacks", [])) or "None"
        print(f"Frog Attacks: {Fore.LIGHTGREEN_EX}{frog_attacks}{Style.RESET_ALL}")

    if player["backpack"]:
        item_counts = Counter(player["backpack"])
        items = [
            f"{item} x{count}" if count > 1 else item
            for item, count in sorted(item_counts.items())
        ]
        print(f"Items: {Fore.LIGHTGREEN_EX}{', '.join(items)}{Style.RESET_ALL}\n")
    else:
        print(f"Items: {Fore.LIGHTGREEN_EX}None{Style.RESET_ALL}\n")


def sell_scraps(player):
    """Automatically sell monster junk when the player reaches a shop."""
    sold_anything = False
    for item in player["backpack"][:]:
        if item in SELLABLE_LOOT:
            worth = random.randint(5, 10)
            player["backpack"].remove(item)
            player["money"] += worth
            sold_anything = True
            say(f"\nYou sold a(n) {item} for ${worth}.", "quick")
    return sold_anything


def offer_potions(player):
    """Let the player drink one potion after dangerous scenes."""
    while True:
        max_health = player["healthMax"]
        big_count = player["backpack"].count("Big Health Potion")
        small_count = player["backpack"].count("Small Health Potion")

        if player["health"] >= max_health:
            if big_count or small_count:
                say("\nYour health is full, so you save your potions.", "quick")
            return False

        if not big_count and not small_count:
            say("\nNo health potions available.", "quick")
            return False

        subtitle = (
            f"Health: {Fore.RED}{stat_meter(player['health'], max_health)} "
            f"{player['health']}/{max_health}{Style.RESET_ALL}"
        )
        choice = choose_menu(
            "Potion Menu",
            [
                MenuOption(
                    "1",
                    "Drink Big Health Potion",
                    "big",
                    "restore to full",
                    aliases=("big", "big potion", "full"),
                    enabled=big_count > 0,
                    status=f"x{big_count}" if big_count else "none",
                ),
                MenuOption(
                    "2",
                    "Drink Small Health Potion",
                    "small",
                    "+15 health",
                    aliases=("small", "small potion"),
                    enabled=small_count > 0,
                    status=f"x{small_count}" if small_count else "none",
                ),
                MenuOption(
                    "3",
                    "Save potions",
                    "exit",
                    aliases=("exit", "leave", "back", "no", "n", "q"),
                ),
            ],
            prompt="Potion choice: ",
            subtitle=subtitle,
        )

        if choice == "big":
            player["health"] = max_health
            player["backpack"].remove("Big Health Potion")
            say(f"\nYour health is restored to {player['health']}.")
            break
        if choice == "small":
            player["health"] = min(max_health, player["health"] + 15)
            player["backpack"].remove("Small Health Potion")
            say(f"\nYour health is now {player['health']}.")
            break
        if choice == "exit":
            say("\nYou save your potions for later.", "quick")
            return False

    print_stats(player)
    return True
