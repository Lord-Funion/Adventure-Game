"""Shop menus and purchase behavior."""

from .data import SPELLS
from .pacing import ask, say
from .player import add_spell, print_stats, sell_scraps
from .ui import MenuOption, choose_menu, money_text, normalize_choice, stat_meter


def _buy_spell(player, stock, spell_name, price):
    """Buy a one-time spell if it is affordable and still stocked."""
    if not stock.get(spell_name, True):
        say("\nThat spell is out of stock.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    add_spell(player, spell_name)
    stock[spell_name] = False
    say(f"\nYou learned {spell_name}.")
    say(f"You have ${player['money']} left.", "quick")


def _buy_item(player, item_name, price):
    """Buy a normal inventory item."""
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    player["backpack"].append(item_name)
    say(f"\nYou bought a {item_name}.")
    say(f"You have ${player['money']} left.", "quick")


def _buy_mana(player):
    """Let the player permanently increase maximum mana."""
    while True:
        amount_text = normalize_choice(
            ask("\nMana to buy ($1 each, 'all' for max, or 'back'): ")
        )
        if amount_text in {"back", "b", "cancel", "leave", "q"}:
            say("\nYou decide not to buy mana.", "quick")
            return
        if amount_text in {"all", "max"}:
            if player["money"] <= 0:
                say("\nYou don't have enough money.", "quick")
                return
            amount = player["money"]
        elif amount_text.isdigit():
            amount = int(amount_text)
        else:
            say("\nPlease enter a number, 'all', or 'back'.", "quick")
            continue

        if amount <= 0:
            say("\nPlease enter a positive number.", "quick")
            continue
        if player["money"] < amount:
            say("\nYou don't have enough money.", "quick")
            return

        player["money"] -= amount
        player["mana"] += amount
        player["manaMax"] += amount
        say(f"\nYou bought {amount} mana.")
        say(f"You have ${player['money']} left.", "quick")
        return


def _price_status(player, price, unavailable=False, unavailable_label="owned"):
    """Summarize affordability and one-time stock state for menu rows."""
    if unavailable:
        return unavailable_label
    if player["money"] < price:
        return f"need ${price - player['money']} more"
    return ""


def _buy_equipment(player, stock, item_name, price, stat_name, amount):
    """Buy one-time equipment and apply its permanent stat bonus."""
    if not stock.get(item_name, True):
        say("\nThat equipment is out of stock.", "quick")
        return
    if player["money"] < price:
        say("\nYou don't have enough money.", "quick")
        return

    player["money"] -= price
    player[stat_name] += amount
    player["backpack"].append(item_name)
    stock[item_name] = False
    say(f"\nYou bought {item_name}.")
    say(f"You have ${player['money']} left.", "quick")


def run_shop(player, stock, advanced=False):
    """Run Harold's or Miss Costalot's shop menu."""
    sell_scraps(player)

    while True:
        options = [
            MenuOption(
                "1",
                "Arcane Blast",
                "arcane",
                f"{money_text(20)} - {SPELLS['Arcane Blast']['description']}",
                aliases=("arcane", "arcane blast", "spell 1"),
                enabled=stock.get("Arcane Blast", True),
                status=_price_status(
                    player,
                    20,
                    not stock.get("Arcane Blast", True),
                    "learned",
                ),
            ),
            MenuOption(
                "2",
                "Small Health Potion",
                "small_potion",
                f"{money_text(15)} - heals 15 health",
                aliases=("small", "small potion", "health potion", "potion"),
                status=_price_status(player, 15),
            ),
            MenuOption(
                "3",
                "Thunderstorm",
                "thunderstorm",
                f"{money_text(40)} - {SPELLS['Thunderstorm']['description']}",
                aliases=("thunder", "thunderstorm", "spell 3"),
                enabled=stock.get("Thunderstorm", True),
                status=_price_status(
                    player,
                    40,
                    not stock.get("Thunderstorm", True),
                    "learned",
                ),
            ),
            MenuOption(
                "4",
                "Restoration Incantation",
                "restoration",
                f"{money_text(30)} - {SPELLS['Restoration Incantation']['description']}",
                aliases=("restore", "restoration", "heal spell", "spell 4"),
                enabled=stock.get("Restoration Incantation", True),
                status=_price_status(
                    player,
                    30,
                    not stock.get("Restoration Incantation", True),
                    "learned",
                ),
            ),
            MenuOption(
                "5",
                "Add Mana",
                "mana",
                f"{money_text(1)} = +1 max mana",
                aliases=("mana", "add mana", "buy mana"),
                status="spend any amount" if player["money"] else "no money",
            ),
        ]
        if advanced:
            options.extend(
                [
                    MenuOption(
                        "6",
                        "Big Health Potion",
                        "big_potion",
                        f"{money_text(40)} - restores full health",
                        aliases=("big", "big potion", "full potion"),
                        status=_price_status(player, 40),
                    ),
                    MenuOption(
                        "7",
                        "Glorious Helmet",
                        "helmet",
                        f"{money_text(50)} - +5 armor",
                        aliases=("helmet", "armor"),
                        enabled=stock.get("Glorious Helmet", True),
                        status=_price_status(
                            player,
                            50,
                            not stock.get("Glorious Helmet", True),
                            "owned",
                        ),
                    ),
                    MenuOption(
                        "8",
                        "Mage Boots",
                        "boots",
                        f"{money_text(35)} - +3 spell damage",
                        aliases=("boots", "mage boots", "damage"),
                        enabled=stock.get("Mage Boots", True),
                        status=_price_status(
                            player,
                            35,
                            not stock.get("Mage Boots", True),
                            "owned",
                        ),
                    ),
                    MenuOption(
                        "9",
                        "Leave store",
                        "leave",
                        aliases=("leave", "exit", "back", "q"),
                    ),
                ]
            )
        else:
            options.append(
                MenuOption(
                    "6",
                    "Leave store",
                    "leave",
                    aliases=("leave", "exit", "back", "q"),
                )
            )

        subtitle = (
            f"Gold: {money_text(player['money'])} | "
            f"Health: {stat_meter(player['health'], player['healthMax'])} "
            f"{player['health']}/{player['healthMax']} | "
            f"Mana: {stat_meter(player['mana'], player['manaMax'])} "
            f"{player['mana']}/{player['manaMax']}"
        )
        choice = choose_menu("Shop Menu", options, prompt="Shop choice: ", subtitle=subtitle)

        if choice == "arcane":
            _buy_spell(player, stock, "Arcane Blast", 20)
        elif choice == "small_potion":
            _buy_item(player, "Small Health Potion", 15)
        elif choice == "thunderstorm":
            _buy_spell(player, stock, "Thunderstorm", 40)
        elif choice == "restoration":
            _buy_spell(player, stock, "Restoration Incantation", 30)
        elif choice == "mana":
            _buy_mana(player)
        elif choice == "big_potion":
            _buy_item(player, "Big Health Potion", 40)
        elif choice == "helmet":
            _buy_equipment(player, stock, "Glorious Helmet", 50, "armor", 5)
        elif choice == "boots":
            _buy_equipment(player, stock, "Mage Boots", 35, "extraDamage", 3)
        elif choice == "leave":
            say("\nYou leave the store.", "quick")
            print_stats(player)
            return
