#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace fs = std::filesystem;

constexpr int BASIC_DAMAGE = 5;
constexpr int STATUS_DAMAGE = 3;
constexpr const char* FINISHED_SCENE = "finished";
constexpr const char* SAVE_PATH = "saves/cpp_autosave.cppsave";

struct GameOver : std::exception {};

struct Spell {
    bool has_damage = false;
    int damage = 0;
    bool has_healing = false;
    int healing = 0;
    int mana_cost = 0;
    int burn = 0;
    int stun = 0;
    std::string description;
};

struct Monster {
    int health = 0;
    int damage = 0;
    std::vector<std::string> attacks;
};

struct Player {
    int money = 0;
    int health = 100;
    int health_max = 100;
    int mana = 50;
    int mana_max = 50;
    int armor = 0;
    int extra_damage = 0;
    std::vector<std::string> backpack;
    std::vector<std::string> spells;
};

struct State {
    Player player;
    std::unordered_map<std::string, bool> shop_stock;
    std::string next_scene = "intro";
};

struct MenuOption {
    std::string key;
    std::string label;
    std::string value;
    std::string detail;
    std::vector<std::string> aliases;
    bool enabled = true;
    std::string status;

    MenuOption(
        std::string key_value,
        std::string label_value,
        std::string option_value,
        std::string detail_value = "",
        std::vector<std::string> alias_values = {},
        bool enabled_value = true,
        std::string status_value = ""
    )
        : key(std::move(key_value)),
          label(std::move(label_value)),
          value(std::move(option_value)),
          detail(std::move(detail_value)),
          aliases(std::move(alias_values)),
          enabled(enabled_value),
          status(std::move(status_value)) {}
};

std::mt19937& rng() {
    static std::mt19937 engine(std::random_device{}());
    return engine;
}

int random_int(int min, int max) {
    std::uniform_int_distribution<int> dist(min, max);
    return dist(rng());
}

template <typename T>
const T& random_choice(const std::vector<T>& values) {
    std::uniform_int_distribution<std::size_t> dist(0, values.size() - 1);
    return values[dist(rng())];
}

std::string trim(const std::string& value) {
    std::size_t first = 0;
    while (first < value.size() && std::isspace(static_cast<unsigned char>(value[first]))) {
        ++first;
    }
    std::size_t last = value.size();
    while (last > first && std::isspace(static_cast<unsigned char>(value[last - 1]))) {
        --last;
    }
    return value.substr(first, last - first);
}

std::string normalize_choice(const std::string& value) {
    std::string lowered;
    bool in_space = false;
    for (char ch : trim(value)) {
        if (std::isspace(static_cast<unsigned char>(ch))) {
            if (!in_space && !lowered.empty()) {
                lowered.push_back(' ');
            }
            in_space = true;
        } else {
            lowered.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
            in_space = false;
        }
    }
    return trim(lowered);
}

std::string ask(const std::string& prompt) {
    std::cout << prompt;
    std::string value;
    if (!std::getline(std::cin, value)) {
        throw std::runtime_error("Input stream closed.");
    }
    return trim(value);
}

void say(const std::string& message) {
    std::cout << message << "\n";
}

void divider(const std::string& title) {
    std::cout << "\n=== " << title << " ===\n";
}

std::string stat_meter(int current, int maximum, int width = 16) {
    if (maximum <= 0) {
        return "[" + std::string(width, '-') + "]";
    }
    int capped = std::max(0, std::min(current, maximum));
    int filled = static_cast<int>((width * capped + maximum / 2) / maximum);
    return "[" + std::string(filled, '#') + std::string(width - filled, '-') + "]";
}

const std::vector<std::string>& scene_order() {
    static const std::vector<std::string> order = {
        "intro",
        "wizard",
        "locked_door",
        "first_goblin",
        "village",
        "forest",
        "twin_doors",
        "witch",
    };
    return order;
}

const std::unordered_map<std::string, std::string>& scene_titles() {
    static const std::unordered_map<std::string, std::string> titles = {
        {"intro", "Chocolate Frog"},
        {"wizard", "Rumblerod"},
        {"locked_door", "Locked Door"},
        {"first_goblin", "First Goblin"},
        {"village", "Village"},
        {"forest", "Forest Trail"},
        {"twin_doors", "Twin Doors"},
        {"witch", "Witch"},
        {FINISHED_SCENE, "Finished Game"},
    };
    return titles;
}

const std::unordered_map<std::string, Spell>& spells() {
    static const std::unordered_map<std::string, Spell> data = {
        {"Fireball", {true, 10, false, 0, 5, 3, 0, "Deals 10 damage and sets the target burning."}},
        {"Arcane Blast", {true, 0, false, 0, 15, 0, 2, "Stuns an enemy for 2 turns."}},
        {"Thunderstorm", {true, 20, false, 0, 20, 0, 0, "Deals 20 damage."}},
        {"Restoration Incantation", {false, 0, true, 10, 7, 0, 0, "Heals 10 health in battle."}},
        {"Lockio Reducto", {false, 0, false, 0, 0, 0, 0, "Unlocks sealed doors."}},
    };
    return data;
}

const std::unordered_map<std::string, Monster>& monsters() {
    static const std::unordered_map<std::string, Monster> data = {
        {"goblin", {20, 5, {"punch", "screech", "headbutt"}}},
        {"troll", {30, 7, {"club", "slam", "bite"}}},
        {"skeleton", {15, 12, {"bone club", "bone scare", "bone headbutt"}}},
        {"werewolf", {40, 15, {"claw", "bite", "howl"}}},
        {"ogre", {50, 25, {"big club", "super smash", "stomp"}}},
        {"witch", {35, 10, {"poison", "curse", "hex"}}},
        {"vampire", {45, 17, {"transform into bat", "fangs", "suck blood"}}},
    };
    return data;
}

const std::vector<std::string>& loot_drops() {
    static const std::vector<std::string> drops = {
        "Suspicious Gold Nugget",
        "Metal Scraps of Mystery",
        "Pointy Monster Tooth",
        "Rotten Flesh",
        "Small Health Potion",
        "Mystery Goop",
        "Strange Liquid",
        "Gnarled Toenail",
    };
    return drops;
}

bool is_sellable_loot(const std::string& item) {
    static const std::vector<std::string> sellable = {
        "Suspicious Gold Nugget",
        "Metal Scraps of Mystery",
        "Pointy Monster Tooth",
        "Rotten Flesh",
        "Mystery Goop",
        "Strange Liquid",
        "Gnarled Toenail",
    };
    return std::find(sellable.begin(), sellable.end(), item) != sellable.end();
}

std::unordered_map<std::string, bool> create_shop_stock() {
    return {
        {"Arcane Blast", true},
        {"Thunderstorm", true},
        {"Restoration Incantation", true},
        {"Glorious Helmet", true},
        {"Mage Boots", true},
    };
}

State new_state() {
    State state;
    state.shop_stock = create_shop_stock();
    state.next_scene = scene_order().front();
    return state;
}

std::string scene_title(const std::string& scene_id) {
    auto found = scene_titles().find(scene_id);
    if (found != scene_titles().end()) {
        return found->second;
    }
    std::string title = scene_id;
    std::replace(title.begin(), title.end(), '_', ' ');
    bool capitalize = true;
    for (char& ch : title) {
        if (capitalize) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        capitalize = ch == ' ';
    }
    return title;
}

std::string next_scene(const std::string& scene_id) {
    const auto& order = scene_order();
    auto found = std::find(order.begin(), order.end(), scene_id);
    if (found == order.end() || std::next(found) == order.end()) {
        return FINISHED_SCENE;
    }
    return *std::next(found);
}

bool has_item(const Player& player, const std::string& item) {
    return std::find(player.backpack.begin(), player.backpack.end(), item) != player.backpack.end();
}

void remove_item(Player& player, const std::string& item) {
    auto found = std::find(player.backpack.begin(), player.backpack.end(), item);
    if (found != player.backpack.end()) {
        player.backpack.erase(found);
    }
}

void add_spell(Player& player, const std::string& spell_name) {
    if (std::find(player.spells.begin(), player.spells.end(), spell_name) == player.spells.end()) {
        player.spells.push_back(spell_name);
    }
}

int count_item(const Player& player, const std::string& item) {
    return static_cast<int>(std::count(player.backpack.begin(), player.backpack.end(), item));
}

void print_stats(const Player& player) {
    divider("Player Stats");
    std::cout << "Money: $" << player.money << "\n";
    std::cout << "Health: " << stat_meter(player.health, player.health_max) << " "
              << player.health << "/" << player.health_max << "\n";
    std::cout << "Mana: " << stat_meter(player.mana, player.mana_max) << " "
              << player.mana << "/" << player.mana_max << "\n";
    std::cout << "Armor: " << player.armor << "\n";
    std::cout << "Spell Damage: +" << player.extra_damage << "\n";

    std::cout << "Spells: ";
    if (player.spells.empty()) {
        std::cout << "None\n";
    } else {
        for (std::size_t i = 0; i < player.spells.size(); ++i) {
            if (i) {
                std::cout << ", ";
            }
            std::cout << player.spells[i];
        }
        std::cout << "\n";
    }

    std::cout << "Items: ";
    if (player.backpack.empty()) {
        std::cout << "None\n\n";
        return;
    }

    std::map<std::string, int> counts;
    for (const std::string& item : player.backpack) {
        counts[item] += 1;
    }
    bool first = true;
    for (const auto& [item, count] : counts) {
        if (!first) {
            std::cout << ", ";
        }
        first = false;
        std::cout << item;
        if (count > 1) {
            std::cout << " x" << count;
        }
    }
    std::cout << "\n\n";
}

std::vector<std::string> option_inputs(const MenuOption& option) {
    std::vector<std::string> inputs = {option.key, option.label};
    inputs.insert(inputs.end(), option.aliases.begin(), option.aliases.end());
    for (std::string& input : inputs) {
        input = normalize_choice(input);
    }
    return inputs;
}

std::string choose_menu(
    const std::string& title,
    const std::vector<MenuOption>& options,
    const std::string& prompt = "Choose: ",
    const std::string& subtitle = "",
    const std::string& invalid = "\nPlease choose one of the listed options."
) {
    while (true) {
        divider(title);
        if (!subtitle.empty()) {
            std::cout << subtitle << "\n";
        }

        for (const MenuOption& option : options) {
            std::cout << option.key << ". " << option.label;
            if (!option.detail.empty()) {
                std::cout << " - " << option.detail;
            }
            if (!option.status.empty()) {
                std::cout << " (" << option.status << ")";
            }
            if (!option.enabled) {
                std::cout << " [unavailable]";
            }
            std::cout << "\n";
        }

        std::string choice = normalize_choice(ask(prompt));
        bool matched_disabled = false;
        for (const MenuOption& option : options) {
            std::vector<std::string> inputs = option_inputs(option);
            if (std::find(inputs.begin(), inputs.end(), choice) != inputs.end()) {
                if (option.enabled) {
                    return option.value;
                }
                matched_disabled = true;
                say("\n" + option.label + " is not available right now.");
                break;
            }
        }
        if (!matched_disabled) {
            say(invalid);
        }
    }
}

std::string ask_choice(
    const std::string& prompt,
    const std::unordered_map<std::string, std::vector<std::string>>& choices,
    const std::string& invalid
) {
    while (true) {
        std::string choice = normalize_choice(ask(prompt));
        for (const auto& [value, aliases] : choices) {
            for (const std::string& alias : aliases) {
                if (choice == normalize_choice(alias)) {
                    return value;
                }
            }
        }
        say(invalid);
    }
}

std::string yes_no(const std::string& prompt) {
    return ask_choice(prompt, {{"yes", {"yes", "y", "1"}}, {"no", {"no", "n", "2"}}}, "\nPlease answer yes or no.");
}

std::string fight_or_run(const std::string& prompt = "\nDo you fight or run? ") {
    return ask_choice(prompt, {{"fight", {"fight", "f", "1"}}, {"run", {"run", "r", "2"}}}, "\nPlease choose fight or run.");
}

std::string choose_left_or_right(const std::string& prompt) {
    return ask_choice(prompt, {{"left", {"left", "l", "1"}}, {"right", {"right", "r", "2"}}}, "\nPlease choose left or right.");
}

void game_over(const Player& player) {
    say("You have been defeated!");
    std::cout << "GAME OVER\nYou had $" << player.money << ".\n";
    throw GameOver();
}

std::string spell_detail(const Player& player, const Spell& spell) {
    std::vector<std::string> parts;
    if (spell.has_damage) {
        int damage = spell.damage + player.extra_damage;
        parts.push_back(damage ? std::to_string(damage) + " damage" : "control");
    }
    if (spell.has_healing) {
        parts.push_back("heal " + std::to_string(spell.healing));
    }
    if (spell.burn) {
        parts.push_back("burn");
    }
    if (spell.stun) {
        parts.push_back("stun " + std::to_string(spell.stun) + " turns");
    }
    parts.push_back(std::to_string(spell.mana_cost) + " mana");

    std::ostringstream out;
    for (std::size_t i = 0; i < parts.size(); ++i) {
        if (i) {
            out << ", ";
        }
        out << parts[i];
    }
    return out.str();
}

std::string choose_combat_action(const std::string& monster_name, int monster_health, int monster_max_health, const Player& player) {
    std::ostringstream subtitle;
    subtitle << "You: " << stat_meter(player.health, player.health_max) << " "
             << player.health << "/" << player.health_max
             << " | Mana: " << player.mana << "/" << player.mana_max
             << " | " << scene_title(monster_name) << ": "
             << std::max(monster_health, 0) << "/" << monster_max_health;

    std::vector<MenuOption> options = {
        {"1", "Basic Attack", "basic", "free, " + std::to_string(BASIC_DAMAGE) + " damage", {"basic", "attack", "hit", "punch"}},
    };

    int next_key = 2;
    for (const std::string& spell_name : player.spells) {
        auto spell_found = spells().find(spell_name);
        if (spell_found == spells().end()) {
            continue;
        }
        const Spell& spell = spell_found->second;
        if (!spell.has_damage && !spell.has_healing) {
            continue;
        }

        bool enabled = player.mana >= spell.mana_cost;
        std::string status;
        if (!enabled) {
            status = "need " + std::to_string(spell.mana_cost - player.mana) + " mana";
        } else if (spell.has_healing && player.health >= player.health_max) {
            enabled = false;
            status = "health full";
        }

        options.push_back({
            std::to_string(next_key++),
            spell_name,
            spell_name,
            spell_detail(player, spell),
            {spell_name},
            enabled,
            status,
        });
    }

    return choose_menu("Combat", options, "Action: ", subtitle.str(), "Choose an action by number or name.");
}

int monster_attack(const std::string& monster_name, const Monster& monster, Player& player) {
    const std::string& attack = random_choice(monster.attacks);
    int damage = std::max(0, monster.damage - player.armor);
    say("The " + monster_name + " attacks with " + attack + "!");
    player.health -= damage;
    if (damage) {
        say("You take " + std::to_string(damage) + " damage. Health: " +
            std::to_string(player.health) + "/" + std::to_string(player.health_max));
    } else {
        say("Your armor absorbs the hit.");
    }

    if (monster_name == "witch" && attack == "poison") {
        say("The poison slips past your armor.");
        return 3;
    }
    return 0;
}

void win_fight(const std::string& monster_name, Player& player) {
    say("The " + monster_name + " has been defeated!");
    player.money += 10;
    std::string drop = random_choice(loot_drops());
    player.backpack.push_back(drop);
    player.mana = player.mana_max;
    say("You gained $10 and found a " + drop + ".");
    print_stats(player);
}

void spell_fight(const std::string& monster_name, Player& player) {
    const Monster& monster = monsters().at(monster_name);
    int monster_health = monster.health;
    int monster_max_health = monster.health;
    int burn_turns = 0;
    int stun_turns = 0;
    int poison_ticks = 0;

    say("\nA fight starts between you and the " + monster_name + "!");
    say("The " + monster_name + " has " + std::to_string(monster_health) + " health.");
    say("It does " + std::to_string(monster.damage) + " damage.");

    while (monster_health > 0 && player.health > 0) {
        if (poison_ticks > 0) {
            player.health -= STATUS_DAMAGE;
            poison_ticks -= 1;
            say("The poison burns you for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                std::to_string(player.health) + "/" + std::to_string(player.health_max));
            if (player.health <= 0) {
                game_over(player);
            }
        }

        if (burn_turns > 0) {
            monster_health -= STATUS_DAMAGE;
            burn_turns -= 1;
            say("The " + monster_name + " burns for " + std::to_string(STATUS_DAMAGE) + " damage. Health: " +
                std::to_string(std::max(monster_health, 0)) + "/" + std::to_string(monster_max_health));
            if (monster_health <= 0) {
                win_fight(monster_name, player);
                return;
            }
        }

        std::string action = choose_combat_action(monster_name, monster_health, monster_max_health, player);
        if (action == "basic") {
            monster_health -= BASIC_DAMAGE;
            say("You strike for " + std::to_string(BASIC_DAMAGE) + " damage.");
        } else {
            const Spell& spell = spells().at(action);
            player.mana -= spell.mana_cost;
            say("You cast " + action + ".");

            if (spell.has_damage) {
                int damage = spell.damage + player.extra_damage;
                monster_health -= damage;
                if (damage) {
                    say("You deal " + std::to_string(damage) + " damage.");
                }
                if (spell.burn) {
                    burn_turns = std::max(burn_turns, spell.burn);
                    say("The target burns for " + std::to_string(burn_turns) + " turns.");
                }
                if (spell.stun) {
                    stun_turns = std::max(stun_turns, spell.stun);
                    say("The " + monster_name + " is stunned for " + std::to_string(stun_turns) + " turns.");
                }
            } else {
                int heal_amount = std::max(0, std::min(player.health_max - player.health, spell.healing));
                player.health += heal_amount;
                say("You heal " + std::to_string(heal_amount) + " health.");
            }
        }

        if (monster_health <= 0) {
            win_fight(monster_name, player);
            return;
        }

        if (stun_turns > 0) {
            stun_turns -= 1;
            say("The " + monster_name + " is stunned and skips its turn.");
        } else {
            poison_ticks = std::max(poison_ticks, monster_attack(monster_name, monster, player));
        }

        if (player.health <= 0) {
            game_over(player);
        }

        say("The " + monster_name + " has " + std::to_string(std::max(monster_health, 0)) + "/" +
            std::to_string(monster_max_health) + " health remaining.");
    }
}

bool sell_scraps(Player& player) {
    bool sold_anything = false;
    std::vector<std::string> remaining;
    for (const std::string& item : player.backpack) {
        if (is_sellable_loot(item)) {
            int worth = random_int(5, 10);
            player.money += worth;
            sold_anything = true;
            say("\nYou sold a(n) " + item + " for $" + std::to_string(worth) + ".");
        } else {
            remaining.push_back(item);
        }
    }
    player.backpack = remaining;
    return sold_anything;
}

bool offer_potions(Player& player) {
    while (true) {
        int big_count = count_item(player, "Big Health Potion");
        int small_count = count_item(player, "Small Health Potion");

        if (player.health >= player.health_max) {
            if (big_count || small_count) {
                say("\nYour health is full, so you save your potions.");
            }
            return false;
        }

        if (!big_count && !small_count) {
            say("\nNo health potions available.");
            return false;
        }

        std::ostringstream subtitle;
        subtitle << "Health: " << stat_meter(player.health, player.health_max) << " "
                 << player.health << "/" << player.health_max;
        std::string choice = choose_menu("Potion Menu", {
            {"1", "Drink Big Health Potion", "big", "restore to full", {"big", "big potion", "full"}, big_count > 0, big_count ? "x" + std::to_string(big_count) : "none"},
            {"2", "Drink Small Health Potion", "small", "+15 health", {"small", "small potion"}, small_count > 0, small_count ? "x" + std::to_string(small_count) : "none"},
            {"3", "Save potions", "exit", "", {"exit", "leave", "back", "no", "n", "q"}},
        }, "Potion choice: ", subtitle.str());

        if (choice == "big") {
            player.health = player.health_max;
            remove_item(player, "Big Health Potion");
            say("\nYour health is restored to " + std::to_string(player.health) + ".");
            break;
        }
        if (choice == "small") {
            player.health = std::min(player.health_max, player.health + 15);
            remove_item(player, "Small Health Potion");
            say("\nYour health is now " + std::to_string(player.health) + ".");
            break;
        }
        if (choice == "exit") {
            say("\nYou save your potions for later.");
            return false;
        }
    }

    print_stats(player);
    return true;
}

std::string price_status(const Player& player, int price, bool unavailable = false, const std::string& unavailable_label = "owned") {
    if (unavailable) {
        return unavailable_label;
    }
    if (player.money < price) {
        return "need $" + std::to_string(price - player.money) + " more";
    }
    return "";
}

void buy_spell(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& spell_name, int price) {
    if (!stock[spell_name]) {
        say("\nThat spell is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough money.");
        return;
    }
    player.money -= price;
    add_spell(player, spell_name);
    stock[spell_name] = false;
    say("\nYou learned " + spell_name + ".");
    say("You have $" + std::to_string(player.money) + " left.");
}

void buy_item(Player& player, const std::string& item_name, int price) {
    if (player.money < price) {
        say("\nYou don't have enough money.");
        return;
    }
    player.money -= price;
    player.backpack.push_back(item_name);
    say("\nYou bought a " + item_name + ".");
    say("You have $" + std::to_string(player.money) + " left.");
}

void buy_equipment(Player& player, std::unordered_map<std::string, bool>& stock, const std::string& item_name, int price, const std::string& stat_name, int amount) {
    if (!stock[item_name]) {
        say("\nThat equipment is out of stock.");
        return;
    }
    if (player.money < price) {
        say("\nYou don't have enough money.");
        return;
    }
    player.money -= price;
    if (stat_name == "armor") {
        player.armor += amount;
    } else if (stat_name == "extraDamage") {
        player.extra_damage += amount;
    }
    player.backpack.push_back(item_name);
    stock[item_name] = false;
    say("\nYou bought " + item_name + ".");
    say("You have $" + std::to_string(player.money) + " left.");
}

void buy_mana(Player& player) {
    while (true) {
        std::string amount_text = normalize_choice(ask("\nMana to buy ($1 each, 'all' for max, or 'back'): "));
        int amount = 0;
        if (amount_text == "back" || amount_text == "b" || amount_text == "cancel" || amount_text == "leave" || amount_text == "q") {
            say("\nYou decide not to buy mana.");
            return;
        }
        if (amount_text == "all" || amount_text == "max") {
            if (player.money <= 0) {
                say("\nYou don't have enough money.");
                return;
            }
            amount = player.money;
        } else {
            try {
                std::size_t parsed = 0;
                amount = std::stoi(amount_text, &parsed);
                if (parsed != amount_text.size()) {
                    throw std::invalid_argument("bad number");
                }
            } catch (const std::exception&) {
                say("\nPlease enter a number, 'all', or 'back'.");
                continue;
            }
        }

        if (amount <= 0) {
            say("\nPlease enter a positive number.");
            continue;
        }
        if (player.money < amount) {
            say("\nYou don't have enough money.");
            return;
        }
        player.money -= amount;
        player.mana += amount;
        player.mana_max += amount;
        say("\nYou bought " + std::to_string(amount) + " mana.");
        say("You have $" + std::to_string(player.money) + " left.");
        return;
    }
}

void run_shop(Player& player, std::unordered_map<std::string, bool>& stock, bool advanced = false) {
    sell_scraps(player);

    while (true) {
        std::vector<MenuOption> options = {
            {"1", "Arcane Blast", "arcane", "$20 - " + spells().at("Arcane Blast").description, {"arcane", "arcane blast", "spell 1"}, stock["Arcane Blast"], price_status(player, 20, !stock["Arcane Blast"], "learned")},
            {"2", "Small Health Potion", "small_potion", "$15 - heals 15 health", {"small", "small potion", "health potion", "potion"}, true, price_status(player, 15)},
            {"3", "Thunderstorm", "thunderstorm", "$40 - " + spells().at("Thunderstorm").description, {"thunder", "thunderstorm", "spell 3"}, stock["Thunderstorm"], price_status(player, 40, !stock["Thunderstorm"], "learned")},
            {"4", "Restoration Incantation", "restoration", "$30 - " + spells().at("Restoration Incantation").description, {"restore", "restoration", "heal spell", "spell 4"}, stock["Restoration Incantation"], price_status(player, 30, !stock["Restoration Incantation"], "learned")},
            {"5", "Add Mana", "mana", "$1 = +1 max mana", {"mana", "add mana", "buy mana"}, true, player.money ? "spend any amount" : "no money"},
        };

        if (advanced) {
            options.push_back({"6", "Big Health Potion", "big_potion", "$40 - restores full health", {"big", "big potion", "full potion"}, true, price_status(player, 40)});
            options.push_back({"7", "Glorious Helmet", "helmet", "$50 - +5 armor", {"helmet", "armor"}, stock["Glorious Helmet"], price_status(player, 50, !stock["Glorious Helmet"], "owned")});
            options.push_back({"8", "Mage Boots", "boots", "$35 - +3 spell damage", {"boots", "mage boots", "damage"}, stock["Mage Boots"], price_status(player, 35, !stock["Mage Boots"], "owned")});
            options.push_back({"9", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
        } else {
            options.push_back({"6", "Leave store", "leave", "", {"leave", "exit", "back", "q"}});
        }

        std::ostringstream subtitle;
        subtitle << "Gold: $" << player.money
                 << " | Health: " << stat_meter(player.health, player.health_max) << " " << player.health << "/" << player.health_max
                 << " | Mana: " << stat_meter(player.mana, player.mana_max) << " " << player.mana << "/" << player.mana_max;
        std::string choice = choose_menu("Shop Menu", options, "Shop choice: ", subtitle.str());

        if (choice == "arcane") {
            buy_spell(player, stock, "Arcane Blast", 20);
        } else if (choice == "small_potion") {
            buy_item(player, "Small Health Potion", 15);
        } else if (choice == "thunderstorm") {
            buy_spell(player, stock, "Thunderstorm", 40);
        } else if (choice == "restoration") {
            buy_spell(player, stock, "Restoration Incantation", 30);
        } else if (choice == "mana") {
            buy_mana(player);
        } else if (choice == "big_potion") {
            buy_item(player, "Big Health Potion", 40);
        } else if (choice == "helmet") {
            buy_equipment(player, stock, "Glorious Helmet", 50, "armor", 5);
        } else if (choice == "boots") {
            buy_equipment(player, stock, "Mage Boots", 35, "extraDamage", 3);
        } else if (choice == "leave") {
            say("\nYou leave the store.");
            print_stats(player);
            return;
        }
    }
}

void write_vector(std::ofstream& out, const std::vector<std::string>& values) {
    out << values.size() << "\n";
    for (const std::string& value : values) {
        out << value << "\n";
    }
}

std::vector<std::string> read_vector(std::ifstream& in) {
    std::string line;
    std::getline(in, line);
    int count = std::stoi(line);
    std::vector<std::string> values;
    for (int i = 0; i < count; ++i) {
        std::getline(in, line);
        values.push_back(line);
    }
    return values;
}

void save_state(const State& state, const std::string& path = SAVE_PATH) {
    fs::create_directories(fs::path(path).parent_path());
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Could not write save file.");
    }
    const Player& p = state.player;
    out << "AdventureGameCppSaveV1\n";
    out << state.next_scene << "\n";
    out << p.money << "\n" << p.health << "\n" << p.health_max << "\n" << p.mana << "\n"
        << p.mana_max << "\n" << p.armor << "\n" << p.extra_damage << "\n";
    write_vector(out, p.backpack);
    write_vector(out, p.spells);
    out << state.shop_stock.size() << "\n";
    for (const auto& [item, stocked] : state.shop_stock) {
        out << item << "\n" << (stocked ? 1 : 0) << "\n";
    }
}

State load_state(const std::string& path = SAVE_PATH) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("No C++ autosave found.");
    }
    std::string line;
    std::getline(in, line);
    if (line != "AdventureGameCppSaveV1") {
        throw std::runtime_error("Save file is not a C++ port save.");
    }

    State state;
    state.shop_stock = create_shop_stock();
    std::getline(in, state.next_scene);
    Player& p = state.player;
    std::getline(in, line); p.money = std::stoi(line);
    std::getline(in, line); p.health = std::stoi(line);
    std::getline(in, line); p.health_max = std::stoi(line);
    std::getline(in, line); p.mana = std::stoi(line);
    std::getline(in, line); p.mana_max = std::stoi(line);
    std::getline(in, line); p.armor = std::stoi(line);
    std::getline(in, line); p.extra_damage = std::stoi(line);
    p.backpack = read_vector(in);
    p.spells = read_vector(in);

    std::getline(in, line);
    int stock_count = std::stoi(line);
    for (int i = 0; i < stock_count; ++i) {
        std::string item;
        std::string stocked;
        std::getline(in, item);
        std::getline(in, stocked);
        state.shop_stock[item] = stocked == "1";
    }
    return state;
}

bool autosave_state(const State& state) {
    try {
        save_state(state);
    } catch (const std::exception&) {
        return false;
    }
    return true;
}

State load_state_interactive() {
    while (true) {
        std::string choice = choose_menu("Load Game", {
            {"1", "Load C++ Autosave", "autosave", SAVE_PATH, {"load", "autosave", "continue"}},
            {"2", "Back", "back", "", {"back", "cancel"}},
        }, "Load choice: ", "C++ port saves are stored separately from Python/web saves.");

        if (choice == "back") {
            throw std::runtime_error("back");
        }
        try {
            State state = load_state();
            say("\nLoaded C++ autosave.");
            return state;
        } catch (const std::exception& exc) {
            say(std::string("\nLoad failed: ") + exc.what());
        }
    }
}

void intro_scene(Player& player) {
    say("\nYou are out on a casual stroll when a magical chocolate frog hops around your feet.");
    std::string choice = yes_no("\nDo you pick it up? (yes/no): ");
    if (choice == "yes") {
        say("\nYou pick up the frog and store it in your backpack.");
    } else {
        say("\nYou start to walk away. RIBBIT.");
        say("The frog hops into your backpack anyway.");
    }
    player.backpack.push_back("Magical Chocolate Frog");
    print_stats(player);
}

void wizard_scene(Player& player) {
    say("\nYou bump into an old man with a long white beard.");
    say("\"Was that the croak of a chocolate frog?\" he asks.");
    if (yes_no("\nWhat do you say? (yes/no): ") == "no") {
        say("\nHis old hearing must be failing him. He wanders off.");
        return;
    }

    say("\nHe smiles. \"I am Rumblerod The Great, the only remaining wizard in the North.\"");
    if (yes_no("\nTrade the frog for his spare magic wand? (yes/no): ") == "no") {
        say("\nRumblerod shrugs and continues down the path.");
        return;
    }

    remove_item(player, "Magical Chocolate Frog");
    player.backpack.push_back("Magic Wand");
    add_spell(player, "Lockio Reducto");
    say("\nYou receive a Magic Wand.");
    say("Rumblerod says, \"Lockio Reducto can unlock any door.\"");
}

void locked_door_scene(Player& player) {
    say("\nYou continue your journey and come to a fork in the path.");
    if (choose_left_or_right("\nDo you go left or right? ") == "right") {
        say("\nYou notice a locked door on the left and decide not to miss it.");
    }

    int amount = random_int(20, 30);
    if (yes_no("\nYou find a locked door. Use the wand and say the words? (yes/no): ") == "no") {
        say("\nA goblin sneaks up behind you and stabs you.");
        game_over(player);
    }

    player.money += amount;
    say("\nYou say Lockio Reducto. The door opens and you find $" + std::to_string(amount) + ".");
    print_stats(player);
}

void first_goblin_scene(Player& player) {
    say("\nYou turn to exit, but a goblin blocks your path.");
    if (fight_or_run() == "run") {
        say("\nThe goblin is faster than you.");
        game_over(player);
    }

    std::string attack = choose_menu("Quick Fight", {
        {"1", "Uppercut", "uppercut", "", {"uppercut", "punch"}},
        {"2", "Kick", "kick", "", {"kick"}},
        {"3", "Dirt Throw", "dirt", "", {"dirt", "throw dirt"}},
    }, "Move: ");

    add_spell(player, "Fireball");
    if (attack == "dirt") {
        say("\nThe dirt blinds the goblin long enough for you to knock it out.");
    } else {
        say("\nYour " + attack + " knocks out the goblin.");
    }
    say("It drops a page from a spell book.");
    say("You learned Fireball.");
    print_stats(player);
}

void village_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nYou see a village nearby.");
    say("A troll is attacking the villagers.");
    if (fight_or_run() == "run") {
        say("\nThe troll catches you before you can escape.");
        game_over(player);
    }
    spell_fight("troll", player);

    say("\nA villager says, \"Thank you for saving our village.\"");
    say("\"Take this Big Health Potion. It will restore your health.\"");
    player.backpack.push_back("Big Health Potion");
    print_stats(player);
    offer_potions(player);

    if (yes_no("\nYou see Harold Sellsalot's General Store. Go inside? (yes/no): ") == "no") {
        say("\nA skeleton archer outside the village shoots you.");
        game_over(player);
    }

    say("\nHarold welcomes you into the store.");
    run_shop(player, shop_stock);

    say("\nYou leave the store and encounter a skeleton.");
    if (fight_or_run() == "run") {
        say("\nThe skeleton catches you near the village gate.");
        game_over(player);
    }
    spell_fight("skeleton", player);
    offer_potions(player);
}

void forest_scene(Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    say("\nYou follow a forest trail.");
    say("A werewolf howls at you from the trees.");
    if (fight_or_run() == "run") {
        say("\nThe werewolf catches you in the brush.");
        game_over(player);
    }
    spell_fight("werewolf", player);
    offer_potions(player);

    say("\nFarther down the trail, a goblin jumps into the path.");
    if (fight_or_run() == "run") {
        say("\nThe goblin is faster than you.");
        game_over(player);
    }
    spell_fight("goblin", player);
    offer_potions(player);

    say("\nAt the forest edge, Miss Costalot waves you over to her traveling cart.");
    run_shop(player, shop_stock, true);
}

void twin_doors_scene(Player& player) {
    say("\nYou find two locked doors at the end of the road.");
    std::string door = choose_left_or_right("\nDo you use the wand on the left or the right door? ");
    say("\nYou say Lockio Reducto and the door opens.");

    if (door == "left") {
        say("\nThe left door leads to a dead end guarded by an ogre.");
        if (fight_or_run() == "fight") {
            spell_fight("ogre", player);
            offer_potions(player);
            say("\nAfter defeating the ogre, you realize this path leads nowhere.");
        } else {
            say("\nYou escape back to the corridor.");
        }
        say("The right door is now your only option.");
    }

    say("\nYou go through the right door and find a chest.");
    say("Before you can open it, an ogre attacks.");
    if (fight_or_run() == "run") {
        say("\nYou slide between the ogre's legs and escape.");
        return;
    }

    spell_fight("ogre", player);
    int amount = random_int(15, 25);
    player.money += amount;
    say("\nYou find $" + std::to_string(amount) + " in the chest.");
    print_stats(player);
    offer_potions(player);
}

void witch_scene(Player& player) {
    say("\nYou continue down the corridor.");
    if (fight_or_run("\nYou see a witch. Do you fight or run? ") == "run") {
        say("\nYou run into the ogre's dad, who is very angry with you.");
        game_over(player);
    }
    spell_fight("witch", player);
    offer_potions(player);
}

void run_scene(const std::string& scene_id, Player& player, std::unordered_map<std::string, bool>& shop_stock) {
    if (scene_id == "intro") {
        intro_scene(player);
    } else if (scene_id == "wizard") {
        wizard_scene(player);
        print_stats(player);
    } else if (scene_id == "locked_door") {
        locked_door_scene(player);
    } else if (scene_id == "first_goblin") {
        first_goblin_scene(player);
    } else if (scene_id == "village") {
        village_scene(player, shop_stock);
    } else if (scene_id == "forest") {
        forest_scene(player, shop_stock);
    } else if (scene_id == "twin_doors") {
        twin_doors_scene(player);
    } else if (scene_id == "witch") {
        witch_scene(player);
    } else {
        throw std::runtime_error("Unknown story checkpoint.");
    }
}

void finish_game(const Player& player) {
    say("\nYou make it through the corridor alive. The road ahead is finally quiet.");
    say("\nAdventure Game is still currently being developed by Thunderstruck7 and Lord Funion. Check back later for more.");
    std::cout << "\nTHE END\nYou finished with $" << player.money << ".\n";
}

bool checkpoint_menu(State& state) {
    while (true) {
        std::string subtitle = "Next: " + scene_title(state.next_scene) + " | Autosave: " + SAVE_PATH;
        std::string choice = choose_menu("Checkpoint", {
            {"1", "Continue", "continue", "", {"continue", "c", "next"}},
            {"2", "Save Game", "save", "", {"save", "s"}},
            {"3", "Load Game", "load", "", {"load", "l"}},
            {"4", "Cloud Saves", "cloud", "", {"cloud", "online", "sync"}},
            {"5", "Player Stats", "stats", "", {"stats", "status"}},
        }, "Checkpoint choice: ", subtitle);

        if (choice == "continue") {
            return true;
        }
        if (choice == "save") {
            try {
                save_state(state);
                say("\nSaved C++ checkpoint to " + std::string(SAVE_PATH) + ".");
            } catch (const std::exception& exc) {
                say(std::string("\nSave failed: ") + exc.what());
            }
        } else if (choice == "load") {
            try {
                state = load_state();
                say("\nLoaded C++ autosave.");
                return true;
            } catch (const std::exception& exc) {
                say(std::string("\nLoad failed: ") + exc.what());
            }
        } else if (choice == "cloud") {
            say("\nCloud saves are not available in the C++ port.");
        } else if (choice == "stats") {
            print_stats(state.player);
        }
    }
}

void run_story(State state) {
    while (true) {
        std::string scene_id = state.next_scene;
        if (scene_id == FINISHED_SCENE) {
            finish_game(state.player);
            return;
        }

        run_scene(scene_id, state.player, state.shop_stock);

        if (scene_id == "wizard" && !has_item(state.player, "Magic Wand")) {
            say("\nWithout a magic wand, your adventure ends here. Better luck next time!");
            return;
        }

        state.next_scene = next_scene(scene_id);
        if (state.next_scene == FINISHED_SCENE) {
            finish_game(state.player);
            return;
        }

        if (autosave_state(state)) {
            say("\nCheckpoint autosaved locally.");
        }

        checkpoint_menu(state);
    }
}

std::string restart_menu() {
    return choose_menu("Game Over", {
        {"1", "Restart", "restart", "", {"restart", "r", "new game", "new"}},
        {"2", "Main Menu", "main", "", {"main", "menu", "m"}},
    }, "Game over choice: ");
}

State main_menu_state() {
    while (true) {
        std::string choice = choose_menu("Adventure Game", {
            {"1", "New Game", "new", "", {"new", "start"}},
            {"2", "Load Game", "load", "", {"load", "continue"}},
            {"3", "Cloud Saves", "cloud", "", {"cloud", "online", "sync"}},
        }, "Main menu choice: ");

        if (choice == "new") {
            return new_state();
        }
        if (choice == "load") {
            try {
                return load_state_interactive();
            } catch (const std::runtime_error& exc) {
                if (std::string(exc.what()) == "back") {
                    continue;
                }
                throw;
            }
        }
        if (choice == "cloud") {
            say("\nCloud saves are not available in the C++ port.");
        }
    }
}

void show_logo() {
    std::cout
        << "    ___       __                 __\n"
        << "   /   | ____/ /   _____  ____  / /___  __________\n"
        << "  / /| |/ __  / | / / _ \\/ __ \\/ __/ / / / ___/ _ \\\n"
        << " / ___ / /_/ /| |/ /  __/ / / / /_/ /_/ / /  /  __/\n"
        << "/_/  |_\\__,_/ |___/\\___/_/ /_/\\__/\\__,_/_/   \\___/\n"
        << "          ______\n"
        << "         / ____/___ _____ ___  ___\n"
        << "        / / __/ __ `/ __ `__ \\/ _ \\\n"
        << "       / /_/ / /_/ / / / / / /  __/\n"
        << "       \\____/\\__,_/_/ /_/ /_/\\___/\n\n";
}

void run_game() {
    show_logo();
    std::string mode = "menu";
    while (true) {
        try {
            if (mode == "restart") {
                run_story(new_state());
            } else {
                run_story(main_menu_state());
            }
            return;
        } catch (const GameOver&) {
            std::string choice = restart_menu();
            if (choice == "restart") {
                show_logo();
                mode = "restart";
            } else if (choice == "main") {
                show_logo();
                mode = "menu";
            }
        }
    }
}

int main() {
    try {
        run_game();
    } catch (const std::exception& exc) {
        std::cerr << "\nAdventure Game C++ port error: " << exc.what() << "\n";
        return 1;
    }
    return 0;
}
