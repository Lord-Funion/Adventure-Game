"""Turn-based spell combat."""

import random

from .data import LOOT_DROPS, MONSTERS, SPELLS
from .pacing import say
from .player import print_stats
from .terminal_colors import Fore, Style
from .ui import MenuOption, choose_menu, stat_meter


BASIC_DAMAGE = 5
STATUS_DAMAGE = 3


class GameOver(Exception):
    """Raised when the player dies so the story runner can show restart options."""


def _monster_attack(monster_name, monster, player):
    """Resolve one enemy turn and return poison duration if applied."""
    attack = random.choice(monster["attacks"])
    damage = max(0, monster["damage"] - player.get("armor", 0))

    say(f"The {monster_name} attacks with {attack}!", "quick")
    player["health"] -= damage
    if damage:
        say(
            f"You take {damage} damage. Health: "
            f"{Fore.RED}{player['health']}/{player['healthMax']}{Style.RESET_ALL}"
        )
    else:
        say("Your armor absorbs the hit.", "quick")

    if monster_name == "witch" and attack == "poison":
        say("The poison slips past your armor.", "quick")
        return 3
    return 0


def _spell_detail(player, spell):
    """Build a concise combat menu description for one spell."""
    mana_cost = spell.get("manaCost", 0)
    parts = []

    if "damage" in spell:
        damage = spell["damage"] + player.get("extraDamage", 0)
        parts.append(f"{damage} damage" if damage else "control")
    if "healing" in spell:
        parts.append(f"heal {spell['healing']}")
    if spell.get("effects", {}).get("burn"):
        parts.append("burn")
    if spell.get("effects", {}).get("stun"):
        parts.append(f"stun {spell['effects']['stun']} turns")
    parts.append(f"{mana_cost} mana")

    return ", ".join(parts)


def _choose_combat_action(monster_name, monster_health, monster_max_health, player):
    """Show the combat menu and return either 'basic' or a spell name."""
    subtitle = (
        f"You: {Fore.RED}{stat_meter(player['health'], player['healthMax'])} "
        f"{player['health']}/{player['healthMax']}{Style.RESET_ALL} | "
        f"Mana: {Fore.BLUE}{player['mana']}/{player['manaMax']}{Style.RESET_ALL} | "
        f"{monster_name.title()}: {Fore.RED}"
        f"{max(monster_health, 0)}/{monster_max_health}{Style.RESET_ALL}"
    )
    options = [
        MenuOption(
            "1",
            "Basic Attack",
            "basic",
            f"free, {BASIC_DAMAGE} damage",
            aliases=("basic", "attack", "hit", "punch"),
        )
    ]

    next_key = 2
    for spell_name in player["spells"]:
        spell = SPELLS.get(spell_name, {})
        if "damage" not in spell and "healing" not in spell:
            continue

        mana_cost = spell.get("manaCost", 0)
        enabled = player["mana"] >= mana_cost
        status = ""
        if not enabled:
            status = f"need {mana_cost - player['mana']} mana"
        elif "healing" in spell and player["health"] >= player["healthMax"]:
            enabled = False
            status = "health full"

        options.append(
            MenuOption(
                str(next_key),
                spell_name,
                spell_name,
                _spell_detail(player, spell),
                aliases=(spell_name,),
                enabled=enabled,
                status=status,
            )
        )
        next_key += 1

    return choose_menu(
        "Combat",
        options,
        prompt="Action: ",
        subtitle=subtitle,
        invalid="Choose an action by number or name.",
    )


def spell_fight(monster_name, player):
    """Run combat until the player or monster is defeated."""
    monster = MONSTERS[monster_name]
    monster_health = monster["health"]
    monster_max_health = monster["health"]
    burn_turns = 0
    stun_turns = 0
    poison_ticks = 0

    say(f"\nA fight starts between you and the {monster_name}!", "beat")
    say(f"The {monster_name} has {Fore.RED}{monster_health}{Style.RESET_ALL} health.", "quick")
    say(f"It does {Fore.LIGHTCYAN_EX}{monster['damage']}{Style.RESET_ALL} damage.", "quick")

    while monster_health > 0 and player["health"] > 0:
        if poison_ticks > 0:
            player["health"] -= STATUS_DAMAGE
            poison_ticks -= 1
            say(
                f"The poison burns you for {STATUS_DAMAGE} damage. "
                f"Health: {player['health']}/{player['healthMax']}"
            )
            if player["health"] <= 0:
                game_over(player)

        if burn_turns > 0:
            monster_health -= STATUS_DAMAGE
            burn_turns -= 1
            say(
                f"The {monster_name} burns for {STATUS_DAMAGE} damage. "
                f"Health: {max(monster_health, 0)}/{monster_max_health}",
                "quick",
            )
            if monster_health <= 0:
                win_fight(monster_name, player)
                return

        action = _choose_combat_action(monster_name, monster_health, monster_max_health, player)

        if action == "basic":
            monster_health -= BASIC_DAMAGE
            say(f"You strike for {BASIC_DAMAGE} damage.", "quick")
        else:
            spell_name = action
            spell = SPELLS[spell_name]
            mana_cost = spell.get("manaCost", 0)
            player["mana"] -= mana_cost
            say(f"You cast {spell_name}.", "quick")

            if "damage" in spell:
                damage = spell["damage"] + player.get("extraDamage", 0)
                monster_health -= damage
                if damage:
                    say(f"You deal {damage} damage.")

                effects = spell.get("effects", {})
                if "burn" in effects:
                    burn_turns = max(burn_turns, effects["burn"])
                    say(f"The target burns for {burn_turns} turns.", "quick")
                if "stun" in effects:
                    stun_turns = max(stun_turns, effects["stun"])
                    say(f"The {monster_name} is stunned for {stun_turns} turns.", "quick")
            else:
                heal_amount = min(
                    player["healthMax"] - player["health"],
                    spell["healing"],
                )
                heal_amount = max(0, heal_amount)
                player["health"] += heal_amount
                say(f"You heal {heal_amount} health.", "quick")

        if monster_health <= 0:
            win_fight(monster_name, player)
            return

        if stun_turns > 0:
            stun_turns -= 1
            say(f"The {monster_name} is stunned and skips its turn.", "quick")
        else:
            poison_ticks = max(poison_ticks, _monster_attack(monster_name, monster, player))

        if player["health"] <= 0:
            game_over(player)

        say(
            f"The {monster_name} has "
            f"{Fore.RED}{max(monster_health, 0)}/{monster_max_health}{Style.RESET_ALL} "
            "health remaining.",
            "quick",
        )


def win_fight(monster_name, player):
    """Give the player rewards and reset mana after a victory."""
    say(f"The {monster_name} has been defeated!", "beat")
    player["money"] += 10
    drop = random.choice(LOOT_DROPS)
    player["backpack"].append(drop)
    player["mana"] = player["manaMax"]
    say(f"You gained ${10} and found a {drop}.")
    print_stats(player)


def game_over(player):
    """Stop the program when the player dies."""
    say("You have been defeated!", "beat")
    print(f"GAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.")
    raise GameOver()
