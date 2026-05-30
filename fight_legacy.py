import time
import random
from colorama import Fore, Style
from collections import Counter

drops = ['Suspicious Gold Nugget', 'Metal Scraps of Mystery', 'Pointy Monster Tooth',
         'Rotten Flesh', 'Small Health Potion', 'Mystery Goop', 'Strange Liquid',
         'Gnarled Toenail']

def potions(player):
    """Handle potion drinking logic"""
    while True:
        max_health = player.get("healthMax", 100)
        big_count = player["backpack"].count("Big Health Potion")
        small_count = player["backpack"].count("Small Health Potion")

        if not big_count and not small_count:
            print("\nYou don't have any health potions left.")
            time.sleep(1.5)
            return

        print("\n=== Potion Menu ===")
        time.sleep(1.5)
        print(f"Big Health Potions: {big_count}")
        time.sleep(1.5)
        print(f"Small Health Potions: {small_count}")
        time.sleep(1.5)
        print(f"Your current health: {Fore.RED}{player['health']}{Style.RESET_ALL}")
        time.sleep(1.5)
        print("1. Drink Big Health Potion (restores to full)")
        time.sleep(1.5)
        print("2. Drink Small Health Potion (+15 health)")
        time.sleep(1.5)
        print("3. Exit")
        time.sleep(1.5)

        choice = input("Choose an option: ").strip()

        if choice == "1" and big_count:
            player["health"] = max_health
            player["backpack"].remove("Big Health Potion")
            print(f"\nYou drank a Big Health Potion. Health restored to {Fore.RED}{max_health}{Style.RESET_ALL}.")
            time.sleep(1.5)
            break
        elif choice == "2" and small_count:
            player["health"] = min(max_health, player["health"] + 15)
            player["backpack"].remove("Small Health Potion")
            print(f"\nYou drank a Small Health Potion. Health is now {Fore.RED}{player['health']}{Style.RESET_ALL}.")
            time.sleep(1.5)
            break
        elif choice == "3":
            print("\nYou chose not to drink a potion.")
            time.sleep(1.5)
            break
        else:
            print("\nInvalid choice or no potions of that type.")
            time.sleep(1.5)

    PPS(player)

def PPS(player):
    """Print Player Stats with colored formatting"""
    print("\n=== Player Stats ===")
    time.sleep(1.5)
    print(f"Money: {Fore.LIGHTYELLOW_EX}${player['money']}{Style.RESET_ALL}")
    time.sleep(1.5)
    print(f"Spells: {Fore.MAGENTA}{', '.join(player['spells']) if player['spells'] else 'None'}{Style.RESET_ALL}")
    time.sleep(1.5)

    if player['backpack']:
        item_counts = Counter(player['backpack'])
        formatted_items = [
            f"{item} x{count}" if count > 1 else item
            for item, count in item_counts.items()
        ]
        print(f"Items: {Fore.LIGHTGREEN_EX}{', '.join(formatted_items)}{Style.RESET_ALL}")
    else:
        print(f"Items: {Fore.LIGHTGREEN_EX}None{Style.RESET_ALL}")
    time.sleep(1.5)

    print(f"Health: {Fore.RED}{player['health']}{Style.RESET_ALL}")
    time.sleep(1.5)
    print(f"Mana: {Fore.BLUE}{player['mana']}{Style.RESET_ALL}\n")
    time.sleep(1.5)

def spellFight(monster, monsterDamage, monsterAttack, player, monsters, spells):
    """Handle spell-based combat encounters with fixed logic"""
    monster_health_table = [20, 30, 15, 40, 50, 35, 45]
    monster_health = monster_health_table[monster]
    monster_name = monsters[monster]
    burn_active = False
    stun_turns = 0
    poison_ticks = 0

    # Combat introduction
    print(f"\nA fight has started between you and the {monster_name}!")
    time.sleep(1.5)
    print(f"The {monster_name} has {Fore.RED}{monster_health}{Style.RESET_ALL} health.")
    time.sleep(1.5)
    print(f"The {monster_name} does {Fore.LIGHTCYAN_EX}{monsterDamage}{Style.RESET_ALL} damage.")
    time.sleep(2)

    while monster_health > 0 and player["health"] > 0:
        # Apply poison damage at the start of player's turn
        if poison_ticks > 0:
            player["health"] -= 3
            poison_ticks -= 1
            print(f"\nThe poison burns you for 3 damage! Health: {Fore.RED}{player['health']}{Style.RESET_ALL}")
            time.sleep(1.5)
            if player["health"] <= 0:
                print("\nYou have been defeated by poison!")
                time.sleep(1.5)
                print(f"GAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.")
                time.sleep(1.5)
                exit()

        # Player's turn
        print(f"\nYour Mana: {Fore.BLUE}{player['mana']}{Style.RESET_ALL}")
        time.sleep(1.5)
        print("Available spells:", ", ".join(player["spells"]))
        time.sleep(1.5)
        choice = input("Which spell do you want to use? ").strip()
        known_spell = next((spell_name for spell_name in player["spells"] if spell_name.lower() == choice.lower()), None)

        if known_spell is None:
            print("\nYou don't know that spell.")
            time.sleep(1)
            continue

        choice = known_spell
        spell = spells.get(choice, {})
        if "damage" not in spell and "healing" not in spell:
            print("\nYou can't use that spell in combat.")
            time.sleep(1)
            continue

        mana_cost = spell.get("manaCost", 0)

        # Handle low mana
        if player["mana"] < mana_cost:
            print(f"\nNot enough mana! You need {mana_cost} but have {player['mana']}.")
            time.sleep(1)
            print("Using basic attack (5 damage).")
            time.sleep(1.5)
            monster_health -= 5
        else:
            player["mana"] -= mana_cost
            print(f"\nYou cast {choice} at the {monster_name}.")
            time.sleep(1.5)

            # Apply burn damage if active
            if burn_active:
                monster_health -= 3
                print("The burn deals 3 extra damage!")
                time.sleep(1.5)

            # Handle spell effects
            if "damage" in spell:
                damage = spell["damage"] + player.get("extraDamage", 0)
                monster_health -= damage
                print(f"You deal {damage} damage!")
                time.sleep(1.5)

                if "effects" in spell:
                    if "burn" in spell["effects"]:
                        burn_active = True
                        print("The target is now burning!")
                        time.sleep(1.5)
                    if "stun" in spell["effects"]:
                        stun_turns = spell["effects"]["stun"]
                        print(f"The {monster_name} is stunned for {stun_turns} turns!")
                        time.sleep(1.5)

            elif "healing" in spell:
                max_health = player.get("healthMax", 100)
                heal_amount = min(max_health - player["health"], spell["healing"])
                heal_amount = max(0, heal_amount)
                player["health"] += heal_amount
                print(f"You heal {heal_amount} health.")
                time.sleep(1.5)

        # Check monster status
        if monster_health <= 0:
            print(f"\nThe {monster_name} has been defeated!")
            time.sleep(1.5)
            player["money"] += 10
            drop = random.choice(drops)
            player["backpack"].append(drop)
            print(f"You gained {Fore.LIGHTYELLOW_EX}10{Style.RESET_ALL} dollars and found a {drop}.")
            time.sleep(1.5)
            break

        # Monster's turn (if alive and not stunned)
        if stun_turns > 0:
            stun_turns -= 1
            print(f"\nThe {monster_name} is stunned and skips its turn!")
            time.sleep(1.5)
        else:
            if monster_name.lower() == "witch":
                attack_type = random.choice(["poison", "curse", "hex"])
                print(f"\nThe witch uses {attack_type}!")
                time.sleep(1.5)
                damage = max(0, monsterDamage - player.get("armor", 0))
                player["health"] -= damage
                print(f"You take {damage} damage. Health: {Fore.RED}{player['health']}{Style.RESET_ALL}")
                time.sleep(1.5)
                if attack_type == "poison":
                    print("\nThe witch casts a vile poison on you!")
                    time.sleep(1.5)
                    print("Your armor is ineffective against the poison.")
                    time.sleep(1.5)
                    poison_ticks = 3
            else:
                damage = max(0, monsterDamage - player.get("armor", 0))
                player["health"] -= damage
                print(f"\nThe {monster_name} attacks with {monsterAttack}!")
                time.sleep(1.5)
                print(f"You take {damage} damage. Health: {Fore.RED}{player['health']}{Style.RESET_ALL}")
                time.sleep(1.5)

        # Check player status
        if player["health"] <= 0:
            print("\nYou have been defeated!")
            time.sleep(1.5)
            print(f"GAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.")
            time.sleep(1.5)
            exit()

        # Display remaining health
        if monster_health > 0:
            print(f"\nThe {monster_name} has {Fore.RED}{monster_health}{Style.RESET_ALL} health remaining.")
            time.sleep(2)

    # Reset mana after combat
    player["mana"] = player["manaMax"]
    PPS(player)
