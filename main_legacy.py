# main.py
import time
import random
from colorama import Fore, Style
from fight import spellFight, potions
from collections import Counter

# Player state stored in a dictionary - tracks all player progress
player = {
    "money": 1000,  # Starting currency for purchasing items/spells
    "health": 100,  # Player's health points (0 = game over)
    "backpack": [],  # Inventory for items like potions
    "spells": [],  # Collection of learned spells
    "mana": 300,  # Current mana points for casting spells
    "manaMax": 300,  # Maximum mana points - resets after each combat
    "armor": 0,
    "extraDamage": 0,
}

# Spell database - defines all available spells and their properties
spells = {
    "Fireball": {
        "damage": 10,
        "manaCost": 5,
        "effects": {
            "burn": 3  # Causes ongoing burn damage for 3 points
        },
        "description": "A basic fire spell that deals 10 damage."
    },
    "Arcane Blast": {
        "damage": 0,
        "manaCost": 15,
        "effects": {
            "stun": 2  # Stuns the target for 2 turns
        },
        "description": "A powerful blinding light spell than stuns."
    },
    "Thunderstorm": {
        "damage": 20,
        "manaCost": 20,
        "description": "A devastating spell that deals 20 damage."
    },
    "Restoration Incantation": {
        "healing": 10,
        "manaCost": 7,
        "description": "Heals 10 health in battle."
    },
    "Lockio Reducto": {
        "description": "Unlocks any door."
    }
}

lootable_drops = ['Suspicious Gold Nugget', 'Metal Scraps of Mystery', 'Pointy Monster Tooth',
                  'Rotten Flesh', 'Mystery Goop', 'Strange Liquid',
                  'Gnarled Toenail']


def sell_scraps(player):
    # Work on a copy of the backpack so we can safely remove items
    for item in player['backpack'][:]:
        if item in lootable_drops:  # only sell known loot
            scrapsWorth = random.randint(5, 10)
            player['backpack'].remove(item)
            player['money'] += scrapsWorth
            print(f"\nYou sold a(n) {item} for ${scrapsWorth}.")
            time.sleep(1.5)


def PPS(player):
    """
    Print Player Stats - displays current player status with colored formatting
    """
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


# Monster definitions and their properties
monsters = ["goblin", "troll", "skeleton", "werewolf", "ogre", "witch", "vampire"]
monsterDamage = [5, 7, 12, 15, 25, 10, 17]  # Damage each monster deals

# Attack options for each monster type
goblinAttacks = ["punch", "screech", "headbutt"]
trollAttacks = ["club", "slam", "bite"]
skeletonAttacks = ["bone club", "bone scare", "bone headbutt"]
werewolfAttacks = ["claw", "bite", "howl"]
ogreAttacks = ["big club", "super smash", "stomp"]
witchAttacks = ["poison", "curse", "hex"]
vampireAttacks = ["transform into bat", "fangs", "suck blood"]
dragonAttacks = ["fire breath", "roar", "tail whip"]

# Randomly select attack for each monster
goblinAttack = random.choice(goblinAttacks)
trollAttack = random.choice(trollAttacks)
skeletonAttack = random.choice(skeletonAttacks)
werewolfAttack = random.choice(werewolfAttacks)
ogreAttack = random.choice(ogreAttacks)
witchAttack = random.choice(witchAttacks)
vampireAttack = random.choice(vampireAttacks)
dragonAttack = random.choice(dragonAttacks)

# Shop inventory tracking
stillBuying = True
stock1 = True  # Arcane Blast availability
stock2 = True  # Big Health Potion availability
stock3 = True  # Thunderstorm availability
stock4 = True  # Restoration Incantation availability
stock5 = True  # Glorious Helmet availability
stock6 = True  # Mage Boots availability

# === GAME START ===
while True:
    if player['health'] <= 0:
        print("\nYou have been defeated!")
        time.sleep(1.5)
        print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.")
        exit()

    print("\nYou are just out on casual stroll when a mysterious magical chocolate frog hops around you.")
    time.sleep(1.5)

    while True:
        choice = input("\nDo you pick it up? (yes/no): ")

        if choice.lower() == 'yes':
            print("\nYou wonder if the frog is edible although you would never eat it because it is still alive. Then you pick up the frog and store it in your backpack.")
            time.sleep(1.5)
            break
        elif choice.lower() == 'no':
            print("\nYou think you might be going crazy and blink a few times but the frog is still there hopping around.")
            time.sleep(1.5)
            print("\nYou decide picking it up could be dangerous and start to walk away. RIBBIT. The frog hops into your backpack. It seems like you have no choice but to keep it.")
            time.sleep(1.5)
            break
        else:
            print("\nPlease answer with 'yes' or 'no'.")
            time.sleep(1.5)

    # Add frog to inventory
    player["backpack"].append('Magical Chocolate Frog')

    PPS(player)

    # === WIZARD ENCOUNTER ===
    print("\nYou continue walking. OOOF! You bump into an older man with a long white beard. Hello my name is...wait, was that the croak of a chocolate frog that I heard?")
    time.sleep(1.5)

    while True:
        choice = input("\nWhat do you say? (yes/no): ")

        if choice.lower() == 'yes':
            print("\nReally? Well then I'm going to tell you a secret. I am Rumblerod The Great. The only remaining wizard in the North.")
            time.sleep(1.5)
            while True:
                choice = input("\nIf you give me that magical chocolate frog then I'll trade you this spare magic wand. Have we got a deal? (yes/no): ")

                if choice.lower() == 'yes':
                    print("\nThank you! Here, take this magic wand. These chocolate frogs are very rare.")
                    time.sleep(1.5)
                    print("Oh and by the way, if you say 'lockio reducto' you can unlock any door.")
                    time.sleep(1.5)
                    player["backpack"][0] = "Magic Wand"
                    player["spells"].append("Lockio Reducto")
                    break
                elif choice.lower() == 'no':
                    print("\nOh well, maybe next time.")
                    time.sleep(1.5)
                    break
                else:
                    print("\nPlease answer with 'yes' or 'no'.")
                    time.sleep(1.5)
            break
        elif choice.lower() == 'no':
            print("\nOh sorry. My old hearing must be failing me. It was nice to meet you.")
            time.sleep(1.5)
            break
        else:
            print("\nPlease answer with 'yes' or 'no'.")
            time.sleep(1.5)

    PPS(player)

    # === MAIN ADVENTURE PATH ===
    if "Magic Wand" in player["backpack"]:
        print("\nYou continue your journey and you come to a fork in the path.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you go left or right? ")

            if choice.lower() == "left":
                break
            elif choice.lower() == "right":
                print("\nYou start going right, but you notice a locked door on the left. You think it would be a shame to miss it.")
                time.sleep(1.5)
                print("\nYou decide to go left.")
                time.sleep(1.5)
                break
            else:
                print("\nPlease choose 'left' or 'right'.")
                time.sleep(1.5)

        # === LEFT PATH - Locked Door ===
        amountGiven = random.randint(20, 30)

        while True:
            choice = input("\nYou go left and you find a locked door. You remember what the old man told you, do you use the wand and say the words? (yes/no): ")

            if choice.lower() == "yes":
                print(f"\nYou say lockio reducto and the door unlocks. You find {amountGiven} dollars in an open chest.")
                time.sleep(1.5)
                player["money"] += amountGiven
                PPS(player)
                break
            elif choice.lower() == "no":
                print("\nA goblin sneaks up behind you and stabs you.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                exit()
            else:
                print("\nPlease answer with 'yes' or 'no'.")
                time.sleep(1.5)

        # === FIRST COMBAT ENCOUNTER - Goblin ===
        print("\nYou turn to exit, but there is a goblin blocking your path.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you fight or run? ")

            if choice.lower() == "run":
                print("\nThe goblin is faster than you and you get eaten.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                exit()
            elif choice.lower() == "fight":
                while True:
                    choice = input("\nDo you want to use:\n1. Uppercut\n2. Kick\n3. Dirt Throw\nChoose a number: ")
                    if choice in ["1", "2", "3"]:
                        print("\nYour attack is very effective and the goblin is knocked out.")
                        time.sleep(1.5)
                        print("\nThe goblin drops a page from a spell book.")
                        time.sleep(1.5)
                        print("\nYou continue on your journey down the path.")
                        time.sleep(1.5)
                        player["spells"].append("Fireball")
                        print("\nYou learned the spell fireball! It does 10 damage.")
                        time.sleep(1.5)
                        PPS(player)
                        break
                    else:
                        print("\nPlease choose 1, 2, or 3.")
                        time.sleep(1.5)
                break
            else:
                print("\nPlease choose 'fight' or 'run'.")
                time.sleep(1.5)

        # === VILLAGE ENCOUNTER - Troll Combat ===
        print("\nYou see a village nearby.")
        time.sleep(1.5)
        print("\nYou get closer and you see a troll that is attacking the villagers.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you fight or run? ")

            if choice.lower() == "run":
                print("\nThe troll is faster than you and you get eaten.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                exit()
            elif choice.lower() == "fight":
                spellFight(1, monsterDamage[1], trollAttack, player, monsters, spells)
                break
            else:
                print("\nPlease choose 'fight' or 'run'.")
                time.sleep(1.5)

        # === VILLAGE REWARD ===
        print("\nYou continue into the village when a man approaches you.")
        time.sleep(1.5)
        print('\n"Thank you for saving our village", he says.')
        time.sleep(1.5)
        print('\n"Take this Big Health Potion, it will restore your health to full."')
        time.sleep(1.5)
        player["backpack"].append('Big Health Potion')
        print("\nYou put the Big Health Potion in your backpack.")
        time.sleep(1.5)
        PPS(player)

        # Option to use Big Health Potion immediately
        potions(player)

        # === GENERAL STORE ENCOUNTER ===
        print("\nYou see a building with a sign that says 'Harold Sellsalot's General Store'.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you go inside? (yes/no): ")

            if choice.lower() == "no":
                print("\nA skeleton archer on the outside of the village shoots you with an arrow.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had ${player['money']} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                exit()
            elif choice.lower() == "yes":
                print("\nYou go inside and see the same man from before.")
                time.sleep(1.5)
                print('\n"Welcome to my store", he says.')
                time.sleep(1.5)
                print('\n"I am Harold Sellsalot, are you interested in purchasing any of my goods?"')
                time.sleep(1.5)
                break
            else:
                print("\nPlease answer with 'yes' or 'no'.")
                time.sleep(1.5)

        # Shopping loop
        while stillBuying:
            sell_scraps(player)
            print("\n=== Shop Menu ===")
            choice = input(
                f"You have {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.\n"
                "Would you like to buy:\n"
                f"1. {Fore.MAGENTA}Arcane Blast{Style.RESET_ALL} - $20 - Stuns for 2 turns\n"
                f"2. {Fore.GREEN}Small Health Potion{Style.RESET_ALL} - $15 - Heals 15 health\n"
                f"3. {Fore.MAGENTA}Thunderstorm{Style.RESET_ALL} - $40 - Does 20 Damage\n"
                f"4. {Fore.GREEN}Restoration Incantation{Style.RESET_ALL} - $30 - Heals 10 Health in battle\n"
                f"5. {Fore.LIGHTBLUE_EX}Add Mana - $1 = +1 Mana{Style.RESET_ALL}\n"
                "6. leave\nChoose a number: "
            )
            if choice == "1":
                if player["money"] >= 20 and stock1:
                    player["money"] -= 20
                    player["spells"].append("Arcane Blast")
                    print("\nYou have learned the spell Arcane Blast!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock1 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "2":
                if player["money"] >= 15:
                    player["money"] -= 15
                    player["backpack"].append("Small Health Potion")
                    print("\nYou bought a Health Potion!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                else:
                    print("\nYou don't have enough money.")
                    time.sleep(1.5)

            elif choice == "3":
                if player["money"] >= 40 and stock3:
                    player["money"] -= 40
                    player["spells"].append("Thunderstorm")
                    print("\nYou have learned the spell Thunderstorm!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock3 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "4":
                if player["money"] >= 30 and stock4:
                    player["money"] -= 30
                    player["spells"].append("Restoration Incantation")
                    print("\nYou have learned the spell Restoration Incantation!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock4 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "5":
                while True:
                    choice = input("\nHow much mana do you want to buy? ")
                    if choice.isdigit():
                        choice = int(choice)
                        if choice <= 0:
                            print("\nPlease enter a positive number.")
                            time.sleep(1.5)
                            continue
                        if player["money"] >= choice:
                            player["money"] -= choice
                            player["mana"] += choice
                            player["manaMax"] += choice
                            print(f"\nYou bought {choice} mana.")
                            time.sleep(1.5)
                            print(f"You have ${player['money']} left.")
                            time.sleep(1.5)
                            break
                        else:
                            print("\nYou don't have enough money.")
                            time.sleep(1.5)
                            break
                    else:
                        print("\nInvalid input. Please enter a number.")
                        time.sleep(1.5)
                        continue

            elif choice == "6":
                stillBuying = False
                print("\nYou leave the store.")
                time.sleep(1.5)
                break

            else:
                print("\nInvalid choice.")
                time.sleep(1.5)

        # === COMBAT - Skeleton ===
        print("\nYou leave the store and continue to the exit, but you encounter a skeleton on your way out.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you fight or run? ")
            if choice.lower() == "run":
                print("\nThe skeleton is faster than you and you get eaten.")
                time.sleep(1.5)
                PPS(player)
                exit()
            elif choice.lower() == "fight":
                spellFight(2, monsterDamage[2], skeletonAttack, player, monsters, spells)
                break
            else:
                print("\nPlease choose 'fight' or 'run'.")
                time.sleep(1.5)

        potions(player)
        print("\nYou follow a forest trail up ahead.")
        time.sleep(1.5)
        print("\nYou begin down the trail, when a werewolf howls at you.")
        time.sleep(1.5)

        while True:
            choice = input("\nDo you fight or run? ")
            if choice.lower() == "run":
                print("\nThe werewolf is faster than you and you get eaten.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                time.sleep(1.5)
                exit()
            elif choice.lower() == "fight":
                spellFight(3, monsterDamage[3], werewolfAttack, player, monsters, spells)
                break
            else:
                print("\nPlease choose 'fight' or 'run'.")
                time.sleep(1.5)

        PPS(player)
        potions(player)

        print("\nYou continue through the forest and you come across a goblin.")
        time.sleep(1.5)
        while True:
            choice = input("\nDo you fight or run? ")
            if choice.lower() == "run":
                print("\nThe goblin is faster than you and you get eaten.")
                time.sleep(1.5)
                print(f"\nGAME OVER\nYou had {Fore.YELLOW}${player['money']}{Style.RESET_ALL} and a {player['backpack'][0]} and the spell {player['spells'][0]} in your backpack.")
                time.sleep(1.5)
                exit()
            elif choice.lower() == "fight":
                spellFight(0, monsterDamage[0], goblinAttack, player, monsters, spells)
                break
        PPS(player)
        potions(player)

        print("\nWhen you come to the end of the forest you see a traveling merchant and decide to check out her goods.")
        time.sleep(1.5)
        print("She introduces herself as Miss Costalot and she has a few things for sale.")
        time.sleep(1.5)
        stillBuying = True

        while stillBuying:
            sell_scraps(player)
            print("\n=== Shop Menu ===")
            choice = input(
                f"You have {Fore.YELLOW}${player['money']}{Style.RESET_ALL}.\n"
                "Would you like to buy:\n"
                f"1. {Fore.MAGENTA}Arcane Blast{Style.RESET_ALL} - $20 - Stuns for 2 turns\n"
                f"2. {Fore.GREEN}Small Health Potion{Style.RESET_ALL} - $15 - Heals 15 health\n"
                f"3. {Fore.MAGENTA}Thunderstorm{Style.RESET_ALL} - $40 - Does 20 Damage\n"
                f"4. {Fore.GREEN}Restoration Incantation{Style.RESET_ALL} - $30 - Heals 10 Health in battle\n"
                f"5. {Fore.LIGHTBLUE_EX}Add Mana - $1 = +1 Mana{Style.RESET_ALL}\n"
                f"6. {Fore.LIGHTGREEN_EX}Big Health Potion{Style.RESET_ALL} - $40 - Heals to full health\n"
                f"7. {Fore.LIGHTCYAN_EX}Glorius Helmet{Style.RESET_ALL} - $50 - Adds 5 armor\n"
                f"8. {Fore.LIGHTCYAN_EX}Mage Boots{Style.RESET_ALL} - $35 - Increases your spell damage by 3\n"
                "9. leave\nChoose a number: "
            )

            if choice == "1":
                if player["money"] >= 20 and stock1:
                    player["money"] -= 20
                    player["spells"].append("Arcane Blast")
                    print("\nYou have learned the spell Arcane Blast!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock1 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "2":
                if player["money"] >= 15:
                    player["money"] -= 15
                    player["backpack"].append("Small Health Potion")
                    print("\nYou bought a Health Potion!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                else:
                    print("\nYou don't have enough money.")
                    time.sleep(1.5)

            elif choice == "3":
                if player["money"] >= 40 and stock3:
                    player["money"] -= 40
                    player["spells"].append("Thunderstorm")
                    print("\nYou have learned the spell Thunderstorm!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock3 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "4":
                if player["money"] >= 30 and stock4:
                    player["money"] -= 30
                    player["spells"].append("Restoration Incantation")
                    print("\nYou have learned the spell Restoration Incantation!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock4 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "5":
                while True:
                    choice = input("\nHow much mana do you want to buy? ")
                    if choice.isdigit():
                        choice = int(choice)
                        if choice <= 0:
                            print("\nPlease enter a positive number.")
                            time.sleep(1.5)
                            continue
                        if player["money"] >= choice:
                            player["money"] -= choice
                            player["mana"] += choice
                            player["manaMax"] += choice
                            print(f"\nYou bought {choice} mana.")
                            time.sleep(1.5)
                            print(f"You have ${player['money']} left.")
                            time.sleep(1.5)
                            break
                        else:
                            print("\nYou don't have enough money.")
                            time.sleep(1.5)
                            break
                    else:
                        print("\nInvalid input. Please enter a number.")
                        time.sleep(1.5)
                        continue

            elif choice == "6":
                if player["money"] >= 40:
                    player["money"] -= 40
                    player["backpack"].append("Big Health Potion")
                    print("\nYou bought a Big Health Potion!")
                    time.sleep(1.5)
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "7":
                if player["money"] >= 50 and stock5:
                    player["money"] -= 50
                    player["armor"] += 5
                    print("\nYou bought a Glorious Helmet!")
                    time.sleep(1.5)
                    player["backpack"].append("Glorious Helmet")
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock5 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)

            elif choice == "8":
                if player["money"] >= 35 and stock6:
                    player["money"] -= 35
                    player["extraDamage"] += 3
                    print("\nYou bought a pair of Mage Boots!")
                    time.sleep(1.5)
                    player["backpack"].append("Mage Boots")
                    print(f"You have ${player['money']} left.")
                    time.sleep(1.5)
                    stock6 = False
                else:
                    print("\nYou don't have enough money or it is out of stock.")
                    time.sleep(1.5)
            elif choice == "9":
                stillBuying = False
                print("\nYou leave the store.")
                time.sleep(1.5)
                break
            else:
                print("\nInvalid choice.")
                time.sleep(1.5)

        print("\nYou go on your way and see 2 doors. You test them and they are both locked.")
        time.sleep(1.5)
        while True:
            choice = input("\nDo you use the wand on the left or the right door? ")
            if choice.lower() != "left" and choice.lower() != "right":
                print("\nPlease choose 'left' or 'right'.")
                time.sleep(1.5)
            else:
                break

        print("\nYou say lockio reducto and the door unlocks.")
        time.sleep(1.5)

        if choice.lower() == "left":
            print("\nYou go through the left door and immediately hit a dead end with an ogre blocking your way!")
            time.sleep(1.5)
            while True:
                choice = input("\nDo you fight or run? ")
                if choice.lower() == "run":
                    print("\nYou turn back and escape to the corridor. The right door is now your only option.")
                    time.sleep(1.5)
                    choice = "right"  # Force convergence to right path
                    break
                elif choice.lower() == "fight":
                    spellFight(4, monsterDamage[4], ogreAttack, player, monsters, spells)
                    potions(player)
                    print("\nAfter defeating the ogre, you realize this path leads nowhere.")
                    time.sleep(1.5)
                    print("\nYou return to the corridor and take the right door instead.")
                    time.sleep(1.5)
                    choice = "right"  # Force convergence to right path
                    break
                else:
                    print("\nPlease choose 'fight' or 'run'.")
                    time.sleep(1.5)
                    continue

        if choice == "right":  # Now handles both original right choice and converged left path
            print("\nYou go through the right door and you see a chest.")
            time.sleep(1.5)
            print("\nBefore you can open it, an ogre comes out and attacks you.")
            time.sleep(1.5)
            while True:
                choice = input("\nDo you fight or run? ")
                if choice.lower() == "run":
                    print("\nYou slide in between the ogre's legs and successfully escape.")
                    time.sleep(1.5)
                    break
                elif choice.lower() == "fight":
                    spellFight(4, monsterDamage[4], ogreAttack, player, monsters, spells)
                    amountGiven = random.randint(15, 25)
                    print(f"\nYou find {amountGiven} dollars in the chest.")
                    time.sleep(1.5)
                    player["money"] += amountGiven
                    break
                else:
                    print("\nPlease choose 'fight' or 'run'.")
                    time.sleep(1.5)
                    continue

        PPS(player)
        potions(player)

        print("\nYou continue down the corridor.")
        time.sleep(1.5)

        while True:
            choice = input("\nYou see a witch, do you fight or run? ")
            if choice.lower() == "run":
                print("\nYou turn and run as fast as you can.")
                time.sleep(1.5)
                print("\nYou run into the ogre's dad, and he is very angry with you.")
                time.sleep(1.5)
                print("\nHe eats you and you lose.")
                time.sleep(1.5)
                PPS(player)
                exit()
            elif choice.lower() == "fight":
                spellFight(5, monsterDamage[5], witchAttack, player, monsters, spells)
                break
            else:
                print("\nPlease choose 'fight' or 'run'.")
                time.sleep(1.5)

        potions(player)
        break

    # === ALTERNATE PATH ===
    if "Magic Wand" not in player["backpack"]:  # Remember to add 'Gnome Depot' as a shop
        print("\nWithout a magic wand, your adventure ends here. Better luck next time!")
        exit()
