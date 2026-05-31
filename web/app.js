(() => {
  "use strict";

  const SAVE_STORAGE_KEY = "adventureGame.webSaves.v1";
  const CLOUD_STORAGE_KEY = "adventureGame.cloudSession.v1";
  const SAVE_SUFFIX = ".tasave";
  const SAVE_FORMAT_VERSION = 1;
  const DEFAULT_API_URL = "https://lordfunion.dev/adventure-api";
  const BASIC_DAMAGE = 5;
  const STATUS_DAMAGE = 3;
  const FINISHED_SCENE = "finished";
  const SCENE_ORDER = [
    "intro",
    "wizard",
    "locked_door",
    "first_goblin",
    "village",
    "forest",
    "twin_doors",
    "witch",
  ];
  const SCENE_TITLES = {
    intro: "Chocolate Frog",
    wizard: "Rumblerod",
    locked_door: "Locked Door",
    first_goblin: "First Goblin",
    village: "Village",
    forest: "Forest Trail",
    twin_doors: "Twin Doors",
    witch: "Witch",
    [FINISHED_SCENE]: "Finished Game",
  };

  const SPELLS = {
    Fireball: {
      damage: 10,
      manaCost: 5,
      effects: { burn: 3 },
      description: "Deals 10 damage and sets the target burning.",
    },
    "Arcane Blast": {
      damage: 0,
      manaCost: 15,
      effects: { stun: 2 },
      description: "Stuns an enemy for 2 turns.",
    },
    Thunderstorm: {
      damage: 20,
      manaCost: 20,
      description: "Deals 20 damage.",
    },
    "Restoration Incantation": {
      healing: 10,
      manaCost: 7,
      description: "Heals 10 health in battle.",
    },
    "Lockio Reducto": {
      description: "Unlocks sealed doors.",
    },
  };

  const MONSTERS = {
    goblin: {
      health: 20,
      damage: 5,
      attacks: ["punch", "screech", "headbutt"],
    },
    troll: {
      health: 30,
      damage: 7,
      attacks: ["club", "slam", "bite"],
    },
    skeleton: {
      health: 15,
      damage: 12,
      attacks: ["bone club", "bone scare", "bone headbutt"],
    },
    werewolf: {
      health: 40,
      damage: 15,
      attacks: ["claw", "bite", "howl"],
    },
    ogre: {
      health: 50,
      damage: 25,
      attacks: ["big club", "super smash", "stomp"],
    },
    witch: {
      health: 35,
      damage: 10,
      attacks: ["poison", "curse", "hex"],
    },
    vampire: {
      health: 45,
      damage: 17,
      attacks: ["transform into bat", "fangs", "suck blood"],
    },
  };

  const LOOT_DROPS = [
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Small Health Potion",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
  ];

  const SELLABLE_LOOT = new Set([
    "Suspicious Gold Nugget",
    "Metal Scraps of Mystery",
    "Pointy Monster Tooth",
    "Rotten Flesh",
    "Mystery Goop",
    "Strange Liquid",
    "Gnarled Toenail",
  ]);

  class GameOver extends Error {}

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function randomChoice(values) {
    return values[Math.floor(Math.random() * values.length)];
  }

  function normalizeChoice(value) {
    return value.trim().toLowerCase().split(/\s+/).filter(Boolean).join(" ");
  }

  function cleanInput(value) {
    return value.trim().split(/\s+/).filter(Boolean).join(" ");
  }

  function statMeter(current, maximum, width = 16) {
    if (maximum <= 0) {
      return `[${"-".repeat(width)}]`;
    }
    const capped = Math.max(0, Math.min(current, maximum));
    const filled = Math.round((width * capped) / maximum);
    return `[${"#".repeat(filled)}${"-".repeat(width - filled)}]`;
  }

  function sanitizeSlotName(value) {
    const cleaned = value.replace(/[^A-Za-z0-9_. -]+/g, "").trim().replace(/^[. ]+|[. ]+$/g, "");
    return cleaned || "adventure-save";
  }

  function stripSaveSuffix(value) {
    return value.endsWith(SAVE_SUFFIX) ? value.slice(0, -SAVE_SUFFIX.length) : value;
  }

  function defaultSaveStem(prefix = "adventure") {
    const now = new Date();
    const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "_");
    return `${prefix}_${stamp}`;
  }

  function pathFromPlayerInput(value, fallbackStem = null) {
    const cleaned = value.trim();
    if (!cleaned) {
      return fallbackStem || defaultSaveStem();
    }
    const lastPart = cleaned.split(/[\\/]/).pop() || cleaned;
    return stripSaveSuffix(sanitizeSlotName(lastPart));
  }

  function formatSavedAt(value) {
    return value || "unknown time";
  }

  function safeJsonParse(value, fallback) {
    try {
      return JSON.parse(value);
    } catch {
      return fallback;
    }
  }

  class Terminal {
    constructor(root, output) {
      this.root = root;
      this.output = output;
      this.activePrompt = null;
    }

    scrollToBottom() {
      this.root.scrollTop = this.root.scrollHeight;
    }

    appendLine(parts = "") {
      const line = document.createElement("div");
      line.className = "terminal-line";
      this.appendParts(line, parts);
      this.output.append(line);
      this.scrollToBottom();
      return line;
    }

    appendLogo() {
      const wrapper = document.createElement("div");
      wrapper.className = "terminal-logo";

      const image = document.createElement("img");
      image.src = "assets/logo.png";
      image.alt = "Adventure Game";
      image.width = 1254;
      image.height = 1254;
      image.decoding = "async";

      wrapper.append(image);
      this.output.append(wrapper);
      this.scrollToBottom();
      return wrapper;
    }

    appendClickableLine(parts, submitValue, disabled = false) {
      const line = this.appendLine(parts);
      if (disabled) {
        line.classList.add("terminal-choice-disabled");
        line.setAttribute("aria-disabled", "true");
        return line;
      }

      line.classList.add("terminal-choice");
      line.setAttribute("role", "button");
      line.setAttribute("tabindex", "0");
      line.addEventListener("click", () => this.submitActivePrompt(submitValue));
      line.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this.submitActivePrompt(submitValue);
        }
      });
      return line;
    }

    appendParts(parent, parts) {
      if (!Array.isArray(parts)) {
        parent.append(document.createTextNode(String(parts)));
        return;
      }

      for (const part of parts) {
        if (typeof part === "string") {
          parent.append(document.createTextNode(part));
          continue;
        }
        const span = document.createElement("span");
        span.textContent = part.text;
        if (part.className) {
          span.className = part.className;
        }
        parent.append(span);
      }
    }

    appendPromptClickChoices(parent, choices) {
      if (!choices || !choices.length) {
        return;
      }

      const choicesWrap = document.createElement("span");
      choicesWrap.className = "terminal-inline-choices";
      for (const choice of choices) {
        const button = document.createElement("span");
        button.className = "terminal-inline-choice";
        button.textContent = choice.label;
        button.setAttribute("role", "button");
        button.setAttribute("tabindex", "0");
        button.addEventListener("click", () => this.submitActivePrompt(choice.value));
        button.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.submitActivePrompt(choice.value);
          }
        });
        choicesWrap.append(document.createTextNode(" ["));
        choicesWrap.append(button);
        choicesWrap.append(document.createTextNode("]"));
      }
      choicesWrap.append(document.createTextNode(" "));
      parent.append(choicesWrap);
    }

    ask(prompt, options = {}) {
      return new Promise((resolve) => {
        const wrapper = document.createElement("div");
        wrapper.className = "terminal-input-line";

        const promptSpan = document.createElement("span");
        promptSpan.textContent = prompt;
        wrapper.append(promptSpan);
        this.appendPromptClickChoices(wrapper, options.clickChoices);

        const form = document.createElement("form");
        form.className = "terminal-input-form";

        const input = document.createElement("input");
        input.className = "terminal-input";
        input.type = options.password ? "password" : "text";
        input.autocomplete = "off";
        input.autocapitalize = "none";
        input.spellcheck = false;
        form.append(input);
        wrapper.append(form);

        this.output.append(wrapper);
        this.scrollToBottom();
        input.focus();
        this.activePrompt = { input, form };

        form.addEventListener("submit", (event) => {
          event.preventDefault();
          const raw = input.value;
          this.activePrompt = null;
          const finalLine = document.createElement("div");
          finalLine.className = "terminal-line";
          finalLine.append(document.createTextNode(prompt));
          finalLine.append(document.createTextNode(options.password && raw ? "********" : raw));
          wrapper.replaceWith(finalLine);
          this.scrollToBottom();
          resolve(cleanInput(raw));
        });
      });
    }

    submitActivePrompt(value) {
      if (!this.activePrompt) {
        return;
      }
      this.activePrompt.input.value = value;
      this.activePrompt.form.requestSubmit();
    }

    clear() {
      this.output.replaceChildren();
      this.activePrompt = null;
      this.scrollToBottom();
    }
  }

  class AdventureGame {
    constructor(terminal) {
      this.terminal = terminal;
    }

    async start() {
      this.terminal.appendLogo();
      let mode = "menu";

      while (true) {
        try {
          if (mode === "restart") {
            await this.runStory(this.newState());
          } else {
            await this.mainMenu();
          }
          return;
        } catch (error) {
          if (!(error instanceof GameOver)) {
            this.say(`\nUnexpected web-port error: ${error.message || error}`, "quick");
            throw error;
          }

          const choice = await this.restartMenu();
          if (choice === "restart") {
            this.terminal.clear();
            this.terminal.appendLogo();
            mode = "restart";
            continue;
          }
          if (choice === "main") {
            this.terminal.clear();
            this.terminal.appendLogo();
            mode = "menu";
            continue;
          }
          return;
        }
      }
    }

    say(message) {
      this.terminal.appendLine(message);
    }

    sayParts(parts) {
      this.terminal.appendLine(parts);
    }

    sayClickableParts(parts, submitValue, disabled = false) {
      this.terminal.appendClickableLine(parts, submitValue, disabled);
    }

    async ask(prompt, options = {}) {
      return this.terminal.ask(prompt, options);
    }

    divider(title) {
      this.say(`\n=== ${title} ===`);
    }

    moneyParts(amount) {
      return [{ text: `$${amount}`, className: "yellow" }];
    }

    createPlayer() {
      return {
        money: 0,
        health: 100,
        healthMax: 100,
        mana: 50,
        manaMax: 50,
        armor: 0,
        extraDamage: 0,
        backpack: [],
        spells: [],
      };
    }

    addSpell(player, spellName) {
      if (!player.spells.includes(spellName)) {
        player.spells.push(spellName);
      }
    }

    createShopStock() {
      return {
        "Arcane Blast": true,
        Thunderstorm: true,
        "Restoration Incantation": true,
        "Glorious Helmet": true,
        "Mage Boots": true,
      };
    }

    newState() {
      return {
        player: this.createPlayer(),
        shop_stock: this.createShopStock(),
        next_scene: SCENE_ORDER[0],
      };
    }

    sceneTitle(sceneId) {
      return SCENE_TITLES[sceneId] || sceneId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
    }

    nextScene(sceneId) {
      const index = SCENE_ORDER.indexOf(sceneId);
      return index + 1 >= SCENE_ORDER.length ? FINISHED_SCENE : SCENE_ORDER[index + 1];
    }

    printStats(player) {
      this.divider("Player Stats");
      this.sayParts(["Money: ", ...this.moneyParts(player.money)]);
      this.sayParts([
        "Health: ",
        { text: `${statMeter(player.health, player.healthMax)} ${player.health}/${player.healthMax}`, className: "red" },
      ]);
      this.sayParts([
        "Mana: ",
        { text: `${statMeter(player.mana, player.manaMax)} ${player.mana}/${player.manaMax}`, className: "blue" },
      ]);
      this.sayParts(["Armor: ", { text: String(player.armor), className: "cyan" }]);
      this.sayParts(["Spell Damage: ", { text: `+${player.extraDamage}`, className: "magenta" }]);

      const spells = player.spells.length ? player.spells.join(", ") : "None";
      this.sayParts(["Spells: ", { text: spells, className: "magenta" }]);

      if (player.backpack.length) {
        const counts = new Map();
        for (const item of player.backpack) {
          counts.set(item, (counts.get(item) || 0) + 1);
        }
        const items = [...counts.entries()]
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([item, count]) => (count > 1 ? `${item} x${count}` : item));
        this.sayParts(["Items: ", { text: `${items.join(", ")}\n`, className: "green" }]);
      } else {
        this.sayParts(["Items: ", { text: "None\n", className: "green" }]);
      }
    }

    optionInputs(option) {
      const inputs = [option.key, option.label, ...(option.aliases || [])];
      return new Set(inputs.filter(Boolean).map(normalizeChoice));
    }

    async chooseMenu(title, options, config = {}) {
      const prompt = config.prompt || "Choose: ";
      const invalid = config.invalid || "\nPlease choose one of the listed options.";

      while (true) {
        this.divider(title);
        if (config.subtitle) {
          Array.isArray(config.subtitle) ? this.sayParts(config.subtitle) : this.say(config.subtitle);
        }

        for (const option of options) {
          const parts = [`${option.key}. ${option.label}`];
          if (option.detail) {
            parts.push(" - ");
            if (Array.isArray(option.detail)) {
              parts.push(...option.detail);
            } else {
              parts.push(option.detail);
            }
          }
          if (option.status) {
            parts.push(` (${option.status})`);
          }
          this.sayClickableParts(parts, option.key, option.enabled === false);
        }

        const choice = normalizeChoice(await this.ask(prompt));
        for (const option of options) {
          if (this.optionInputs(option).has(choice)) {
            if (option.enabled !== false) {
              return option.value;
            }
            this.say(`\n${option.label} is not available right now.`);
            break;
          }
        }
        if (!options.some((option) => this.optionInputs(option).has(choice))) {
          this.say(invalid);
        }
      }
    }

    async askChoice(prompt, choices, invalid) {
      const normalizedChoices = Object.entries(choices).map(([value, aliases]) => [
        value,
        new Set(aliases.map(normalizeChoice)),
      ]);
      const clickChoices = Object.entries(choices).map(([value]) => ({
        label: value,
        value,
      }));

      while (true) {
        const choice = normalizeChoice(await this.ask(prompt, { clickChoices }));
        for (const [value, aliases] of normalizedChoices) {
          if (aliases.has(choice)) {
            return value;
          }
        }
        this.say(invalid);
      }
    }

    yesNo(prompt) {
      return this.askChoice(prompt, {
        yes: ["yes", "y", "1"],
        no: ["no", "n", "2"],
      }, "\nPlease answer yes or no.");
    }

    fightOrRun(prompt = "\nDo you fight or run? ") {
      return this.askChoice(prompt, {
        fight: ["fight", "f", "1"],
        run: ["run", "r", "2"],
      }, "\nPlease choose fight or run.");
    }

    chooseLeftOrRight(prompt) {
      return this.askChoice(prompt, {
        left: ["left", "l", "1"],
        right: ["right", "r", "2"],
      }, "\nPlease choose left or right.");
    }

    restartMenu() {
      return this.chooseMenu("Game Over", [
        { key: "1", label: "Restart", value: "restart", aliases: ["restart", "r", "new game", "new"] },
        { key: "2", label: "Main Menu", value: "main", aliases: ["main", "menu", "m"] },
        { key: "3", label: "Quit", value: "quit", aliases: ["quit", "q", "exit"] },
      ], {
        prompt: "Game over choice: ",
      });
    }

    normalizeState(rawState) {
      if (!rawState || typeof rawState !== "object") {
        throw new Error("The save does not contain game state.");
      }
      const rawPlayer = rawState.player;
      if (!rawPlayer || typeof rawPlayer !== "object") {
        throw new Error("The save does not contain a valid player.");
      }

      const player = this.createPlayer();
      for (const key of ["money", "health", "healthMax", "mana", "manaMax", "armor", "extraDamage"]) {
        const value = rawPlayer[key] ?? player[key];
        if (!Number.isInteger(value)) {
          throw new Error(`Save field '${key}' is not a valid number.`);
        }
        player[key] = value;
      }

      for (const key of ["backpack", "spells"]) {
        const value = rawPlayer[key] ?? [];
        if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
          throw new Error(`Save field '${key}' is not a valid list.`);
        }
        player[key] = [...value];
      }

      const shopStock = this.createShopStock();
      const rawStock = rawState.shop_stock || {};
      if (typeof rawStock !== "object" || Array.isArray(rawStock)) {
        throw new Error("The save does not contain valid shop stock.");
      }
      for (const itemName of Object.keys(shopStock)) {
        const value = rawStock[itemName] ?? shopStock[itemName];
        if (typeof value !== "boolean") {
          throw new Error(`Save field '${itemName}' is not valid shop stock.`);
        }
        shopStock[itemName] = value;
      }

      const nextScene = rawState.next_scene;
      if (!SCENE_ORDER.includes(nextScene) && nextScene !== FINISHED_SCENE) {
        throw new Error("The save points to an unknown story checkpoint.");
      }

      return { player, shop_stock: shopStock, next_scene: nextScene };
    }

    loadStateFromPayload(payload) {
      if (!payload || typeof payload !== "object") {
        throw new Error("The save payload is not valid.");
      }
      if (payload.game !== "Adventure Game") {
        throw new Error("This save belongs to a different game.");
      }
      return this.normalizeState(payload.state);
    }

    makeSavePayload(state) {
      return {
        game: "Adventure Game",
        format_version: SAVE_FORMAT_VERSION,
        saved_at: new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"),
        state: clone(state),
      };
    }

    makeSaveText(state) {
      return JSON.stringify(this.makeSavePayload(state));
    }

    readSaveSlots() {
      const parsed = safeJsonParse(localStorage.getItem(SAVE_STORAGE_KEY), {});
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    }

    writeSaveSlots(slots) {
      localStorage.setItem(SAVE_STORAGE_KEY, JSON.stringify(slots));
    }

    writeSaveText(saveText, stem) {
      const payload = this.loadStateFromPayload(JSON.parse(saveText));
      const slots = this.readSaveSlots();
      const safeStem = sanitizeSlotName(stem);
      slots[safeStem] = {
        save_data: saveText,
        saved_at: payload.saved_at,
        updated_at: Date.now(),
      };
      this.writeSaveSlots(slots);
      return `saves/${safeStem}${SAVE_SUFFIX}`;
    }

    loadSaveText(stem) {
      const slots = this.readSaveSlots();
      const slot = slots[sanitizeSlotName(stem)];
      if (!slot || typeof slot.save_data !== "string") {
        throw new Error(`No browser save exists at saves/${sanitizeSlotName(stem)}${SAVE_SUFFIX}.`);
      }
      return slot.save_data;
    }

    listSaveFiles() {
      const slots = this.readSaveSlots();
      return Object.entries(slots)
        .filter(([, slot]) => slot && typeof slot.save_data === "string")
        .sort(([, left], [, right]) => (right.updated_at || 0) - (left.updated_at || 0))
        .map(([stem, slot]) => ({ stem, name: `${stem}${SAVE_SUFFIX}`, slot }));
    }

    saveDetail(stem, slot) {
      try {
        const payload = JSON.parse(slot.save_data);
        const state = this.loadStateFromPayload(payload);
        return `${this.sceneTitle(state.next_scene)}, $${state.player.money}, saved ${formatSavedAt(payload.saved_at)}`;
      } catch {
        return "unreadable or tampered";
      }
    }

    async saveStateInteractive(state) {
      const suggestedStem = defaultSaveStem();
      const typedPath = await this.ask(`\nSave name or path [${suggestedStem}${SAVE_SUFFIX}]: `);
      const stem = typedPath ? pathFromPlayerInput(typedPath) : suggestedStem;
      const saveText = this.makeSaveText(state);

      try {
        const finalPath = this.writeSaveText(saveText, stem);
        this.say(`\nSaved encrypted checkpoint to ${finalPath}.`);
      } catch (error) {
        this.say(`\nSave failed: ${error.message || error}`);
        return;
      }

      if (this.isSignedIn()) {
        try {
          await this.uploadSave(stem, saveText);
          this.say(`\nSynced cloud save slot '${stem}'.`);
        } catch (error) {
          this.say(`\nCloud sync failed: ${error.message || error}`);
        }
      }
    }

    async loadStateInteractive() {
      while (true) {
        const saveFiles = this.listSaveFiles();
        const options = [];
        saveFiles.slice(0, 9).forEach((saveFile, index) => {
          options.push({
            key: String(index + 1),
            label: saveFile.name,
            value: saveFile.stem,
            detail: this.saveDetail(saveFile.stem, saveFile.slot),
            aliases: [saveFile.stem, saveFile.name],
          });
        });

        const customKey = String(options.length + 1);
        options.push({
          key: customKey,
          label: "Load other file",
          value: "custom",
          detail: "type a .tasave path",
          aliases: ["custom", "other", "file", "path"],
        });
        options.push({
          key: String(options.length + 1),
          label: "Back",
          value: "back",
          aliases: ["back", "cancel", "q", "quit"],
        });

        const choice = await this.chooseMenu("Load Game", options, {
          prompt: "Load choice: ",
          subtitle: "Encrypted save files end in .tasave.",
        });

        if (choice === "back") {
          return null;
        }

        let stem = choice;
        if (choice === "custom") {
          const typedPath = await this.ask("\nSave file path: ");
          if (!typedPath) {
            this.say("\nNo file selected.");
            continue;
          }
          stem = pathFromPlayerInput(typedPath);
        }

        try {
          const saveText = this.loadSaveText(stem);
          const state = this.loadStateFromPayload(JSON.parse(saveText));
          this.say(`\nLoaded save from saves/${sanitizeSlotName(stem)}${SAVE_SUFFIX}.`);
          return state;
        } catch (error) {
          this.say(`\nLoad failed: ${error.message || error}`);
        }
      }
    }

    async autosaveState(state) {
      const saveText = this.makeSaveText(state);
      try {
        this.writeSaveText(saveText, "autosave");
      } catch {
        return [false, false];
      }

      let cloudSynced = false;
      if (this.isSignedIn()) {
        try {
          await this.uploadSave("autosave", saveText, 2000);
          cloudSynced = true;
        } catch {
          cloudSynced = false;
        }
      }
      return [true, cloudSynced];
    }

    loadCloudSettings() {
      const parsed = safeJsonParse(localStorage.getItem(CLOUD_STORAGE_KEY), {});
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    }

    saveCloudSettings(settings) {
      localStorage.setItem(CLOUD_STORAGE_KEY, JSON.stringify(settings));
    }

    normalizeApiUrl(apiUrl) {
      let cleaned = apiUrl.trim().split(/\s+/).join(" ");
      if (!cleaned) {
        throw new Error("Cloud save API URL cannot be empty.");
      }
      if (!cleaned.includes("://")) {
        cleaned = `https://${cleaned}`;
      }
      const parsed = new URL(cleaned);
      if (!["http:", "https:"].includes(parsed.protocol) || !parsed.host) {
        throw new Error("Cloud save API URL must look like https://example.com/adventure-api.");
      }
      return cleaned.replace(/\/+$/, "");
    }

    currentApiUrl() {
      return DEFAULT_API_URL;
    }

    currentUsername() {
      return (this.loadCloudSettings().username || "").trim();
    }

    isSignedIn() {
      const settings = this.loadCloudSettings();
      return Boolean(settings.token && settings.username);
    }

    signOut() {
      const settings = this.loadCloudSettings();
      delete settings.token;
      delete settings.username;
      this.saveCloudSettings(settings);
    }

    normalizeSlotName(value) {
      return sanitizeSlotName(value).slice(0, 64).trim() || "autosave";
    }

    endpoint(apiUrl, action) {
      const url = new URL(apiUrl);
      if (!url.pathname.endsWith(".php")) {
        url.pathname = `${url.pathname.replace(/\/+$/, "")}/index.php`;
      }
      url.searchParams.set("action", action);
      return url.toString();
    }

    async requestCloud(action, data = {}, token = null, timeout = 6000) {
      const apiUrl = this.normalizeApiUrl(this.currentApiUrl());
      const payload = { ...data, action };
      const headers = {
        "Content-Type": "application/json",
        Accept: "application/json",
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
        payload.token = token;
      }

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), timeout);
      try {
        const response = await fetch(this.endpoint(apiUrl, action), {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        const body = await response.text();
        let result;
        try {
          result = JSON.parse(body);
        } catch {
          throw new Error("Cloud save server returned a response the game could not read.");
        }
        if (!response.ok || !result.ok) {
          throw new Error(result.error || result.message || `Cloud save server returned HTTP ${response.status}.`);
        }
        return result;
      } catch (error) {
        if (error.name === "AbortError") {
          throw new Error("Cloud save server is unavailable. Local saves still work.");
        }
        throw new Error(error.message || "Cloud save server is unavailable. Local saves still work.");
      } finally {
        window.clearTimeout(timeoutId);
      }
    }

    sessionToken() {
      const token = (this.loadCloudSettings().token || "").trim();
      if (!token) {
        throw new Error("You are not signed in to cloud saves.");
      }
      return token;
    }

    saveSession(username, token) {
      this.saveCloudSettings({ ...this.loadCloudSettings(), username, token });
    }

    async register(username, password) {
      const response = await this.requestCloud("register", { username, password });
      this.saveSession(response.username, response.token);
      return response;
    }

    async login(username, password) {
      const response = await this.requestCloud("login", { username, password });
      this.saveSession(response.username, response.token);
      return response;
    }

    async listSaves() {
      const response = await this.requestCloud("list", {}, this.sessionToken());
      return response.saves || [];
    }

    async uploadSave(slotName, saveText, timeout = 6000) {
      return this.requestCloud(
        "upload",
        { slot_name: this.normalizeSlotName(slotName), save_data: saveText },
        this.sessionToken(),
        timeout,
      );
    }

    async downloadSave(slotName) {
      const response = await this.requestCloud(
        "download",
        { slot_name: this.normalizeSlotName(slotName) },
        this.sessionToken(),
      );
      if (typeof response.save_data !== "string" || !response.save_data) {
        throw new Error("Cloud save server did not return save data.");
      }
      return response;
    }

    cloudStatus() {
      let apiPart;
      try {
        apiPart = `API: ${this.currentApiUrl()}`;
      } catch (error) {
        apiPart = `API URL problem: ${error.message || error}`;
      }

      const accountPart = this.isSignedIn() ? `Signed in: ${this.currentUsername()}` : "Not signed in";
      return `${apiPart} | ${accountPart}`;
    }

    async cloudRegister() {
      const username = await this.ask("\nChoose cloud username: ");
      if (!username) {
        this.say("\nNo username entered.");
        return;
      }
      const password = await this.ask("Choose cloud password: ", { password: true });
      const confirm = await this.ask("Confirm cloud password: ", { password: true });
      if (password !== confirm) {
        this.say("\nPasswords did not match.");
        return;
      }

      try {
        await this.register(username, password);
        this.say(`\nSigned in to cloud saves as ${this.currentUsername()}.`);
      } catch (error) {
        this.say(`\nCloud registration failed: ${error.message || error}`);
      }
    }

    async cloudLogin() {
      const username = await this.ask("\nCloud username: ");
      if (!username) {
        this.say("\nNo username entered.");
        return;
      }
      const password = await this.ask("Cloud password: ", { password: true });
      try {
        await this.login(username, password);
        this.say(`\nSigned in to cloud saves as ${this.currentUsername()}.`);
      } catch (error) {
        this.say(`\nCloud sign-in failed: ${error.message || error}`);
      }
    }

    async cloudUploadCurrent(state) {
      if (state === null) {
        this.say("\nStart or load a game before uploading a cloud save.");
        return;
      }
      if (!this.isSignedIn()) {
        this.say("\nSign in before uploading cloud saves.");
        return;
      }

      const typedSlot = await this.ask("\nCloud save slot [autosave]: ");
      const slotName = this.normalizeSlotName(typedSlot || "autosave");
      const saveText = this.makeSaveText(state);
      try {
        await this.uploadSave(slotName, saveText);
        this.say(`\nUploaded cloud save slot '${slotName}'.`);
      } catch (error) {
        this.say(`\nCloud upload failed: ${error.message || error}`);
      }
    }

    async cloudLoadInteractive() {
      if (!this.isSignedIn()) {
        this.say("\nSign in before loading cloud saves.");
        return null;
      }

      let cloudSlots;
      try {
        cloudSlots = await this.listSaves();
      } catch (error) {
        this.say(`\nCloud saves are unavailable: ${error.message || error}`);
        return null;
      }

      const options = [];
      cloudSlots.slice(0, 9).forEach((cloudSlot, index) => {
        const slotName = cloudSlot.slot_name || "";
        if (!slotName) {
          return;
        }
        options.push({
          key: String(index + 1),
          label: slotName,
          value: slotName,
          detail: `updated ${cloudSlot.updated_at || "unknown time"}`,
          aliases: [slotName],
        });
      });

      if (!options.length) {
        this.say("\nNo cloud saves found for this account.");
        return null;
      }

      options.push({
        key: String(options.length + 1),
        label: "Back",
        value: "back",
        aliases: ["back", "cancel", "q", "quit"],
      });

      const slotName = await this.chooseMenu("Load Cloud Save", options, {
        prompt: "Cloud save choice: ",
        subtitle: "Downloaded cloud saves are also copied into saves/ for offline loading.",
      });
      if (slotName === "back") {
        return null;
      }

      try {
        const response = await this.downloadSave(slotName);
        const state = this.loadStateFromPayload(JSON.parse(response.save_data));
        const localStem = `cloud_${this.normalizeSlotName(slotName)}`;
        this.writeSaveText(response.save_data, localStem);
        this.say(`\nDownloaded cloud save to saves/${localStem}${SAVE_SUFFIX}.`);
        this.say(`\nLoaded cloud save slot '${slotName}'.`);
        return state;
      } catch (error) {
        this.say(`\nCloud load failed: ${error.message || error}`);
        return null;
      }
    }

    async cloudMenu(currentState = null) {
      while (true) {
        let options = [];
        if (this.isSignedIn()) {
          let nextKey = 1;
          if (currentState !== null) {
            options.push({
              key: String(nextKey),
              label: "Upload Current Save",
              value: "upload",
              aliases: ["upload", "sync", "save"],
            });
            nextKey += 1;
          }
          options = options.concat([
            {
              key: String(nextKey),
              label: "Load Cloud Save",
              value: "load",
              aliases: ["load", "download"],
            },
            {
              key: String(nextKey + 1),
              label: "Sign Out",
              value: "logout",
              aliases: ["logout", "sign out"],
            },
            {
              key: String(nextKey + 2),
              label: "Back",
              value: "back",
              aliases: ["back", "cancel", "q", "quit"],
            },
          ]);
        } else {
          options = [
            { key: "1", label: "Create Account", value: "register", aliases: ["register", "create"] },
            { key: "2", label: "Sign In", value: "login", aliases: ["login", "sign in"] },
            { key: "3", label: "Back", value: "back", aliases: ["back", "cancel", "q", "quit"] },
          ];
        }

        const choice = await this.chooseMenu("Cloud Saves", options, {
          prompt: "Cloud choice: ",
          subtitle: this.cloudStatus(),
        });

        if (choice === "register") {
          await this.cloudRegister();
        } else if (choice === "login") {
          await this.cloudLogin();
        } else if (choice === "upload") {
          await this.cloudUploadCurrent(currentState);
        } else if (choice === "load") {
          const loadedState = await this.cloudLoadInteractive();
          if (loadedState !== null) {
            return loadedState;
          }
        } else if (choice === "logout") {
          this.signOut();
          this.say("\nSigned out of cloud saves on this device.");
        } else if (choice === "back") {
          return null;
        }
      }
    }

    async checkpointMenu(state) {
      while (true) {
        let subtitle = `Next: ${this.sceneTitle(state.next_scene)} | Autosave: saves/autosave.tasave`;
        if (this.isSignedIn()) {
          subtitle += ` | Cloud: ${this.currentUsername()}`;
        }

        const choice = await this.chooseMenu("Checkpoint", [
          { key: "1", label: "Continue", value: "continue", aliases: ["continue", "c", "next"] },
          { key: "2", label: "Save Game", value: "save", aliases: ["save", "s"] },
          { key: "3", label: "Load Game", value: "load", aliases: ["load", "l"] },
          { key: "4", label: "Cloud Saves", value: "cloud", aliases: ["cloud", "online", "sync"] },
          { key: "5", label: "Player Stats", value: "stats", aliases: ["stats", "status"] },
          { key: "6", label: "Quit", value: "quit", aliases: ["quit", "q", "exit"] },
        ], {
          prompt: "Checkpoint choice: ",
          subtitle,
        });

        if (choice === "continue") {
          return state;
        }
        if (choice === "save") {
          await this.saveStateInteractive(state);
        } else if (choice === "load") {
          const loadedState = await this.loadStateInteractive();
          if (loadedState !== null) {
            return loadedState;
          }
        } else if (choice === "cloud") {
          const loadedState = await this.cloudMenu(state);
          if (loadedState !== null) {
            return loadedState;
          }
        } else if (choice === "stats") {
          this.printStats(state.player);
        } else if (choice === "quit") {
          this.say("\nProgress is saved in saves/autosave.tasave if autosave succeeded.");
          return null;
        }
      }
    }

    async mainMenu() {
      while (true) {
        const choice = await this.chooseMenu("Adventure Game", [
          { key: "1", label: "New Game", value: "new", aliases: ["new", "start"] },
          { key: "2", label: "Load Game", value: "load", aliases: ["load", "continue"] },
          { key: "3", label: "Cloud Saves", value: "cloud", aliases: ["cloud", "online", "sync"] },
          { key: "4", label: "Quit", value: "quit", aliases: ["quit", "q", "exit"] },
        ], { prompt: "Main menu choice: " });

        if (choice === "new") {
          await this.runStory(this.newState());
          return;
        }
        if (choice === "load") {
          const state = await this.loadStateInteractive();
          if (state !== null) {
            await this.runStory(state);
            return;
          }
        }
        if (choice === "cloud") {
          const state = await this.cloudMenu();
          if (state !== null) {
            await this.runStory(state);
            return;
          }
        }
        if (choice === "quit") {
          return;
        }
      }
    }

    async runStory(state) {
      while (true) {
        const sceneId = state.next_scene;
        if (sceneId === FINISHED_SCENE) {
          this.finishGame(state.player);
          return;
        }

        await this.runScene(sceneId, state.player, state.shop_stock);

        if (sceneId === "wizard" && !state.player.backpack.includes("Magic Wand")) {
          this.say("\nWithout a magic wand, your adventure ends here. Better luck next time!");
          return;
        }

        state.next_scene = this.nextScene(sceneId);
        if (state.next_scene === FINISHED_SCENE) {
          this.finishGame(state.player);
          return;
        }

        const [autosaved, cloudSynced] = await this.autosaveState(state);
        if (autosaved) {
          let message = "\nCheckpoint autosaved locally.";
          if (cloudSynced) {
            message += " Cloud synced.";
          }
          this.say(message);
        }

        state = await this.checkpointMenu(state);
        if (state === null) {
          return;
        }
      }
    }

    async runScene(sceneId, player, shopStock) {
      if (sceneId === "intro") {
        await this.introScene(player);
      } else if (sceneId === "wizard") {
        await this.wizardScene(player);
        this.printStats(player);
      } else if (sceneId === "locked_door") {
        await this.lockedDoorScene(player);
      } else if (sceneId === "first_goblin") {
        await this.firstGoblinScene(player);
      } else if (sceneId === "village") {
        await this.villageScene(player, shopStock);
      } else if (sceneId === "forest") {
        await this.forestScene(player, shopStock);
      } else if (sceneId === "twin_doors") {
        await this.twinDoorsScene(player);
      } else if (sceneId === "witch") {
        await this.witchScene(player);
      } else {
        throw new Error("Unknown story checkpoint.");
      }
    }

    finishGame(player) {
      this.say("\nYou make it through the corridor alive. The road ahead is finally quiet.");
      this.say("\nAdventure Game is still currently being developed by Thunderstruck7 and Lord Funion. Check back later for more.");
      this.sayParts(["\nTHE END\nYou finished with ", ...this.moneyParts(player.money), "."]);
    }

    async introScene(player) {
      this.say("\nYou are out on a casual stroll when a magical chocolate frog hops around your feet.");

      const choice = await this.yesNo("\nDo you pick it up? (yes/no): ");
      if (choice === "yes") {
        this.say("\nYou pick up the frog and store it in your backpack.");
      } else {
        this.say("\nYou start to walk away. RIBBIT.");
        this.say("The frog hops into your backpack anyway.");
      }

      player.backpack.push("Magical Chocolate Frog");
      this.printStats(player);
    }

    async wizardScene(player) {
      this.say("\nYou bump into an old man with a long white beard.");
      this.say('"Was that the croak of a chocolate frog?" he asks.');

      const choice = await this.yesNo("\nWhat do you say? (yes/no): ");
      if (choice === "no") {
        this.say("\nHis old hearing must be failing him. He wanders off.");
        return;
      }

      this.say('\nHe smiles. "I am Rumblerod The Great, the only remaining wizard in the North."');
      const trade = await this.yesNo("\nTrade the frog for his spare magic wand? (yes/no): ");
      if (trade === "no") {
        this.say("\nRumblerod shrugs and continues down the path.");
        return;
      }

      const frogIndex = player.backpack.indexOf("Magical Chocolate Frog");
      if (frogIndex >= 0) {
        player.backpack.splice(frogIndex, 1);
      }
      player.backpack.push("Magic Wand");
      this.addSpell(player, "Lockio Reducto");
      this.say("\nYou receive a Magic Wand.");
      this.say('Rumblerod says, "Lockio Reducto can unlock any door."');
    }

    async lockedDoorScene(player) {
      this.say("\nYou continue your journey and come to a fork in the path.");
      const pathChoice = await this.chooseLeftOrRight("\nDo you go left or right? ");
      if (pathChoice === "right") {
        this.say("\nYou notice a locked door on the left and decide not to miss it.");
      }

      const amount = randomInt(20, 30);
      const choice = await this.yesNo("\nYou find a locked door. Use the wand and say the words? (yes/no): ");
      if (choice === "no") {
        this.say("\nA goblin sneaks up behind you and stabs you.");
        this.gameOver(player);
      }

      player.money += amount;
      this.say(`\nYou say Lockio Reducto. The door opens and you find $${amount}.`);
      this.printStats(player);
    }

    async firstGoblinScene(player) {
      this.say("\nYou turn to exit, but a goblin blocks your path.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe goblin is faster than you.");
        this.gameOver(player);
      }

      const attack = await this.chooseMenu("Quick Fight", [
        { key: "1", label: "Uppercut", value: "uppercut", aliases: ["uppercut", "punch"] },
        { key: "2", label: "Kick", value: "kick", aliases: ["kick"] },
        { key: "3", label: "Dirt Throw", value: "dirt", aliases: ["dirt", "throw dirt"] },
      ], { prompt: "Move: " });

      this.addSpell(player, "Fireball");
      if (attack === "dirt") {
        this.say("\nThe dirt blinds the goblin long enough for you to knock it out.");
      } else {
        this.say(`\nYour ${attack} knocks out the goblin.`);
      }
      this.say("It drops a page from a spell book.");
      this.say("You learned Fireball.");
      this.printStats(player);
    }

    async villageScene(player, shopStock) {
      this.say("\nYou see a village nearby.");
      this.say("A troll is attacking the villagers.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe troll catches you before you can escape.");
        this.gameOver(player);
      }
      await this.spellFight("troll", player);

      this.say('\nA villager says, "Thank you for saving our village."');
      this.say('"Take this Big Health Potion. It will restore your health."');
      player.backpack.push("Big Health Potion");
      this.printStats(player);
      await this.offerPotions(player);

      const enterStore = await this.yesNo("\nYou see Harold Sellsalot's General Store. Go inside? (yes/no): ");
      if (enterStore === "no") {
        this.say("\nA skeleton archer outside the village shoots you.");
        this.gameOver(player);
      }

      this.say("\nHarold welcomes you into the store.");
      await this.runShop(player, shopStock);

      this.say("\nYou leave the store and encounter a skeleton.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe skeleton catches you near the village gate.");
        this.gameOver(player);
      }
      await this.spellFight("skeleton", player);
      await this.offerPotions(player);
    }

    async forestScene(player, shopStock) {
      this.say("\nYou follow a forest trail.");
      this.say("A werewolf howls at you from the trees.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe werewolf catches you in the brush.");
        this.gameOver(player);
      }
      await this.spellFight("werewolf", player);
      await this.offerPotions(player);

      this.say("\nFarther down the trail, a goblin jumps into the path.");
      if (await this.fightOrRun() === "run") {
        this.say("\nThe goblin is faster than you.");
        this.gameOver(player);
      }
      await this.spellFight("goblin", player);
      await this.offerPotions(player);

      this.say("\nAt the forest edge, Miss Costalot waves you over to her traveling cart.");
      await this.runShop(player, shopStock, true);
    }

    async twinDoorsScene(player) {
      this.say("\nYou find two locked doors at the end of the road.");
      const door = await this.chooseLeftOrRight("\nDo you use the wand on the left or the right door? ");
      this.say("\nYou say Lockio Reducto and the door opens.");

      if (door === "left") {
        this.say("\nThe left door leads to a dead end guarded by an ogre.");
        if (await this.fightOrRun() === "fight") {
          await this.spellFight("ogre", player);
          await this.offerPotions(player);
          this.say("\nAfter defeating the ogre, you realize this path leads nowhere.");
        } else {
          this.say("\nYou escape back to the corridor.");
        }
        this.say("The right door is now your only option.");
      }

      this.say("\nYou go through the right door and find a chest.");
      this.say("Before you can open it, an ogre attacks.");
      if (await this.fightOrRun() === "run") {
        this.say("\nYou slide between the ogre's legs and escape.");
        return;
      }

      await this.spellFight("ogre", player);
      const amount = randomInt(15, 25);
      player.money += amount;
      this.say(`\nYou find $${amount} in the chest.`);
      this.printStats(player);
      await this.offerPotions(player);
    }

    async witchScene(player) {
      this.say("\nYou continue down the corridor.");
      if (await this.fightOrRun("\nYou see a witch. Do you fight or run? ") === "run") {
        this.say("\nYou run into the ogre's dad, who is very angry with you.");
        this.gameOver(player);
      }

      await this.spellFight("witch", player);
      await this.offerPotions(player);
    }

    sellScraps(player) {
      let soldAnything = false;
      for (const item of [...player.backpack]) {
        if (SELLABLE_LOOT.has(item)) {
          const worth = randomInt(5, 10);
          player.backpack.splice(player.backpack.indexOf(item), 1);
          player.money += worth;
          soldAnything = true;
          this.say(`\nYou sold a(n) ${item} for $${worth}.`);
        }
      }
      return soldAnything;
    }

    async offerPotions(player) {
      while (true) {
        const maxHealth = player.healthMax;
        const bigCount = player.backpack.filter((item) => item === "Big Health Potion").length;
        const smallCount = player.backpack.filter((item) => item === "Small Health Potion").length;

        if (player.health >= maxHealth) {
          if (bigCount || smallCount) {
            this.say("\nYour health is full, so you save your potions.");
          }
          return false;
        }

        if (!bigCount && !smallCount) {
          this.say("\nNo health potions available.");
          return false;
        }

        const subtitle = [
          "Health: ",
          { text: `${statMeter(player.health, maxHealth)} ${player.health}/${maxHealth}`, className: "red" },
        ];
        const choice = await this.chooseMenu("Potion Menu", [
          {
            key: "1",
            label: "Drink Big Health Potion",
            value: "big",
            detail: "restore to full",
            aliases: ["big", "big potion", "full"],
            enabled: bigCount > 0,
            status: bigCount ? `x${bigCount}` : "none",
          },
          {
            key: "2",
            label: "Drink Small Health Potion",
            value: "small",
            detail: "+15 health",
            aliases: ["small", "small potion"],
            enabled: smallCount > 0,
            status: smallCount ? `x${smallCount}` : "none",
          },
          {
            key: "3",
            label: "Save potions",
            value: "exit",
            aliases: ["exit", "leave", "back", "no", "n", "q"],
          },
        ], {
          prompt: "Potion choice: ",
          subtitle,
        });

        if (choice === "big") {
          player.health = maxHealth;
          player.backpack.splice(player.backpack.indexOf("Big Health Potion"), 1);
          this.say(`\nYour health is restored to ${player.health}.`);
          break;
        }
        if (choice === "small") {
          player.health = Math.min(maxHealth, player.health + 15);
          player.backpack.splice(player.backpack.indexOf("Small Health Potion"), 1);
          this.say(`\nYour health is now ${player.health}.`);
          break;
        }
        if (choice === "exit") {
          this.say("\nYou save your potions for later.");
          return false;
        }
      }

      this.printStats(player);
      return true;
    }

    spellDetail(player, spell) {
      const manaCost = spell.manaCost || 0;
      const parts = [];
      if (Object.prototype.hasOwnProperty.call(spell, "damage")) {
        const damage = spell.damage + (player.extraDamage || 0);
        parts.push(damage ? `${damage} damage` : "control");
      }
      if (Object.prototype.hasOwnProperty.call(spell, "healing")) {
        parts.push(`heal ${spell.healing}`);
      }
      if (spell.effects?.burn) {
        parts.push("burn");
      }
      if (spell.effects?.stun) {
        parts.push(`stun ${spell.effects.stun} turns`);
      }
      parts.push(`${manaCost} mana`);
      return parts.join(", ");
    }

    async chooseCombatAction(monsterName, monsterHealth, monsterMaxHealth, player) {
      const subtitle = [
        "You: ",
        { text: statMeter(player.health, player.healthMax), className: "red" },
        ` ${player.health}/${player.healthMax} | Mana: `,
        { text: `${player.mana}/${player.manaMax}`, className: "blue" },
        ` | ${monsterName[0].toUpperCase()}${monsterName.slice(1)}: `,
        { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
      ];

      const options = [{
        key: "1",
        label: "Basic Attack",
        value: "basic",
        detail: `free, ${BASIC_DAMAGE} damage`,
        aliases: ["basic", "attack", "hit", "punch"],
      }];

      let nextKey = 2;
      for (const spellName of player.spells) {
        const spell = SPELLS[spellName] || {};
        if (!Object.prototype.hasOwnProperty.call(spell, "damage") && !Object.prototype.hasOwnProperty.call(spell, "healing")) {
          continue;
        }

        const manaCost = spell.manaCost || 0;
        let enabled = player.mana >= manaCost;
        let status = "";
        if (!enabled) {
          status = `need ${manaCost - player.mana} mana`;
        } else if (Object.prototype.hasOwnProperty.call(spell, "healing") && player.health >= player.healthMax) {
          enabled = false;
          status = "health full";
        }

        options.push({
          key: String(nextKey),
          label: spellName,
          value: spellName,
          detail: this.spellDetail(player, spell),
          aliases: [spellName],
          enabled,
          status,
        });
        nextKey += 1;
      }

      return this.chooseMenu("Combat", options, {
        prompt: "Action: ",
        subtitle,
        invalid: "Choose an action by number or name.",
      });
    }

    monsterAttack(monsterName, monster, player) {
      const attack = randomChoice(monster.attacks);
      const damage = Math.max(0, monster.damage - (player.armor || 0));
      this.say(`The ${monsterName} attacks with ${attack}!`);
      player.health -= damage;
      if (damage) {
        this.sayParts([
          `You take ${damage} damage. Health: `,
          { text: `${player.health}/${player.healthMax}`, className: "red" },
        ]);
      } else {
        this.say("Your armor absorbs the hit.");
      }

      if (monsterName === "witch" && attack === "poison") {
        this.say("The poison slips past your armor.");
        return 3;
      }
      return 0;
    }

    async spellFight(monsterName, player) {
      const monster = MONSTERS[monsterName];
      let monsterHealth = monster.health;
      const monsterMaxHealth = monster.health;
      let burnTurns = 0;
      let stunTurns = 0;
      let poisonTicks = 0;

      this.say(`\nA fight starts between you and the ${monsterName}!`);
      this.sayParts([`The ${monsterName} has `, { text: String(monsterHealth), className: "red" }, " health."]);
      this.sayParts(["It does ", { text: String(monster.damage), className: "cyan" }, " damage."]);

      while (monsterHealth > 0 && player.health > 0) {
        if (poisonTicks > 0) {
          player.health -= STATUS_DAMAGE;
          poisonTicks -= 1;
          this.say(`The poison burns you for ${STATUS_DAMAGE} damage. Health: ${player.health}/${player.healthMax}`);
          if (player.health <= 0) {
            this.gameOver(player);
          }
        }

        if (burnTurns > 0) {
          monsterHealth -= STATUS_DAMAGE;
          burnTurns -= 1;
          this.say(`The ${monsterName} burns for ${STATUS_DAMAGE} damage. Health: ${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`);
          if (monsterHealth <= 0) {
            this.winFight(monsterName, player);
            return;
          }
        }

        const action = await this.chooseCombatAction(monsterName, monsterHealth, monsterMaxHealth, player);

        if (action === "basic") {
          monsterHealth -= BASIC_DAMAGE;
          this.say(`You strike for ${BASIC_DAMAGE} damage.`);
        } else {
          const spellName = action;
          const spell = SPELLS[spellName];
          const manaCost = spell.manaCost || 0;
          player.mana -= manaCost;
          this.say(`You cast ${spellName}.`);

          if (Object.prototype.hasOwnProperty.call(spell, "damage")) {
            const damage = spell.damage + (player.extraDamage || 0);
            monsterHealth -= damage;
            if (damage) {
              this.say(`You deal ${damage} damage.`);
            }

            const effects = spell.effects || {};
            if (Object.prototype.hasOwnProperty.call(effects, "burn")) {
              burnTurns = Math.max(burnTurns, effects.burn);
              this.say(`The target burns for ${burnTurns} turns.`);
            }
            if (Object.prototype.hasOwnProperty.call(effects, "stun")) {
              stunTurns = Math.max(stunTurns, effects.stun);
              this.say(`The ${monsterName} is stunned for ${stunTurns} turns.`);
            }
          } else {
            const healAmount = Math.max(0, Math.min(player.healthMax - player.health, spell.healing));
            player.health += healAmount;
            this.say(`You heal ${healAmount} health.`);
          }
        }

        if (monsterHealth <= 0) {
          this.winFight(monsterName, player);
          return;
        }

        if (stunTurns > 0) {
          stunTurns -= 1;
          this.say(`The ${monsterName} is stunned and skips its turn.`);
        } else {
          poisonTicks = Math.max(poisonTicks, this.monsterAttack(monsterName, monster, player));
        }

        if (player.health <= 0) {
          this.gameOver(player);
        }

        this.sayParts([
          `The ${monsterName} has `,
          { text: `${Math.max(monsterHealth, 0)}/${monsterMaxHealth}`, className: "red" },
          " health remaining.",
        ]);
      }
    }

    winFight(monsterName, player) {
      this.say(`The ${monsterName} has been defeated!`);
      player.money += 10;
      const drop = randomChoice(LOOT_DROPS);
      player.backpack.push(drop);
      player.mana = player.manaMax;
      this.say(`You gained $10 and found a ${drop}.`);
      this.printStats(player);
    }

    gameOver(player) {
      this.say("You have been defeated!");
      this.sayParts(["GAME OVER\nYou had ", ...this.moneyParts(player.money), "."]);
      throw new GameOver();
    }

    buySpell(player, stock, spellName, price) {
      if (!stock[spellName]) {
        this.say("\nThat spell is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough money.");
        return;
      }

      player.money -= price;
      this.addSpell(player, spellName);
      stock[spellName] = false;
      this.say(`\nYou learned ${spellName}.`);
      this.say(`You have $${player.money} left.`);
    }

    buyItem(player, itemName, price) {
      if (player.money < price) {
        this.say("\nYou don't have enough money.");
        return;
      }

      player.money -= price;
      player.backpack.push(itemName);
      this.say(`\nYou bought a ${itemName}.`);
      this.say(`You have $${player.money} left.`);
    }

    async buyMana(player) {
      while (true) {
        const amountText = normalizeChoice(await this.ask("\nMana to buy ($1 each, 'all' for max, or 'back'): "));
        let amount;
        if (["back", "b", "cancel", "leave", "q"].includes(amountText)) {
          this.say("\nYou decide not to buy mana.");
          return;
        }
        if (["all", "max"].includes(amountText)) {
          if (player.money <= 0) {
            this.say("\nYou don't have enough money.");
            return;
          }
          amount = player.money;
        } else if (/^\d+$/.test(amountText)) {
          amount = Number.parseInt(amountText, 10);
        } else {
          this.say("\nPlease enter a number, 'all', or 'back'.");
          continue;
        }

        if (amount <= 0) {
          this.say("\nPlease enter a positive number.");
          continue;
        }
        if (player.money < amount) {
          this.say("\nYou don't have enough money.");
          return;
        }

        player.money -= amount;
        player.mana += amount;
        player.manaMax += amount;
        this.say(`\nYou bought ${amount} mana.`);
        this.say(`You have $${player.money} left.`);
        return;
      }
    }

    priceStatus(player, price, unavailable = false, unavailableLabel = "owned") {
      if (unavailable) {
        return unavailableLabel;
      }
      if (player.money < price) {
        return `need $${price - player.money} more`;
      }
      return "";
    }

    buyEquipment(player, stock, itemName, price, statName, amount) {
      if (!stock[itemName]) {
        this.say("\nThat equipment is out of stock.");
        return;
      }
      if (player.money < price) {
        this.say("\nYou don't have enough money.");
        return;
      }

      player.money -= price;
      player[statName] += amount;
      player.backpack.push(itemName);
      stock[itemName] = false;
      this.say(`\nYou bought ${itemName}.`);
      this.say(`You have $${player.money} left.`);
    }

    async runShop(player, stock, advanced = false) {
      this.sellScraps(player);

      while (true) {
        const options = [
          {
            key: "1",
            label: "Arcane Blast",
            value: "arcane",
            detail: [...this.moneyParts(20), ` - ${SPELLS["Arcane Blast"].description}`],
            aliases: ["arcane", "arcane blast", "spell 1"],
            enabled: stock["Arcane Blast"],
            status: this.priceStatus(player, 20, !stock["Arcane Blast"], "learned"),
          },
          {
            key: "2",
            label: "Small Health Potion",
            value: "small_potion",
            detail: [...this.moneyParts(15), " - heals 15 health"],
            aliases: ["small", "small potion", "health potion", "potion"],
            status: this.priceStatus(player, 15),
          },
          {
            key: "3",
            label: "Thunderstorm",
            value: "thunderstorm",
            detail: [...this.moneyParts(40), ` - ${SPELLS.Thunderstorm.description}`],
            aliases: ["thunder", "thunderstorm", "spell 3"],
            enabled: stock.Thunderstorm,
            status: this.priceStatus(player, 40, !stock.Thunderstorm, "learned"),
          },
          {
            key: "4",
            label: "Restoration Incantation",
            value: "restoration",
            detail: [...this.moneyParts(30), ` - ${SPELLS["Restoration Incantation"].description}`],
            aliases: ["restore", "restoration", "heal spell", "spell 4"],
            enabled: stock["Restoration Incantation"],
            status: this.priceStatus(player, 30, !stock["Restoration Incantation"], "learned"),
          },
          {
            key: "5",
            label: "Add Mana",
            value: "mana",
            detail: [...this.moneyParts(1), " = +1 max mana"],
            aliases: ["mana", "add mana", "buy mana"],
            status: player.money ? "spend any amount" : "no money",
          },
        ];

        if (advanced) {
          options.push(
            {
              key: "6",
              label: "Big Health Potion",
              value: "big_potion",
              detail: [...this.moneyParts(40), " - restores full health"],
              aliases: ["big", "big potion", "full potion"],
              status: this.priceStatus(player, 40),
            },
            {
              key: "7",
              label: "Glorious Helmet",
              value: "helmet",
              detail: [...this.moneyParts(50), " - +5 armor"],
              aliases: ["helmet", "armor"],
              enabled: stock["Glorious Helmet"],
              status: this.priceStatus(player, 50, !stock["Glorious Helmet"], "owned"),
            },
            {
              key: "8",
              label: "Mage Boots",
              value: "boots",
              detail: [...this.moneyParts(35), " - +3 spell damage"],
              aliases: ["boots", "mage boots", "damage"],
              enabled: stock["Mage Boots"],
              status: this.priceStatus(player, 35, !stock["Mage Boots"], "owned"),
            },
            {
              key: "9",
              label: "Leave store",
              value: "leave",
              aliases: ["leave", "exit", "back", "q"],
            },
          );
        } else {
          options.push({
            key: "6",
            label: "Leave store",
            value: "leave",
            aliases: ["leave", "exit", "back", "q"],
          });
        }

        const subtitle = [
          "Gold: ",
          ...this.moneyParts(player.money),
          ` | Health: ${statMeter(player.health, player.healthMax)} ${player.health}/${player.healthMax} | Mana: ${statMeter(player.mana, player.manaMax)} ${player.mana}/${player.manaMax}`,
        ];

        const choice = await this.chooseMenu("Shop Menu", options, {
          prompt: "Shop choice: ",
          subtitle,
        });

        if (choice === "arcane") {
          this.buySpell(player, stock, "Arcane Blast", 20);
        } else if (choice === "small_potion") {
          this.buyItem(player, "Small Health Potion", 15);
        } else if (choice === "thunderstorm") {
          this.buySpell(player, stock, "Thunderstorm", 40);
        } else if (choice === "restoration") {
          this.buySpell(player, stock, "Restoration Incantation", 30);
        } else if (choice === "mana") {
          await this.buyMana(player);
        } else if (choice === "big_potion") {
          this.buyItem(player, "Big Health Potion", 40);
        } else if (choice === "helmet") {
          this.buyEquipment(player, stock, "Glorious Helmet", 50, "armor", 5);
        } else if (choice === "boots") {
          this.buyEquipment(player, stock, "Mage Boots", 35, "extraDamage", 3);
        } else if (choice === "leave") {
          this.say("\nYou leave the store.");
          this.printStats(player);
          return;
        }
      }
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    const terminal = new Terminal(
      document.getElementById("terminal"),
      document.getElementById("terminal-output"),
    );
    const game = new AdventureGame(terminal);
    game.start();
  });
})();
