#!/usr/bin/env node
"use strict";
var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};

// node_modules/commander/lib/error.js
var require_error = __commonJS({
  "node_modules/commander/lib/error.js"(exports2) {
    var CommanderError = class extends Error {
      /**
       * Constructs the CommanderError class
       * @param {number} exitCode suggested exit code which could be used with process.exit
       * @param {string} code an id string representing the error
       * @param {string} message human-readable description of the error
       * @constructor
       */
      constructor(exitCode, code, message) {
        super(message);
        Error.captureStackTrace(this, this.constructor);
        this.name = this.constructor.name;
        this.code = code;
        this.exitCode = exitCode;
        this.nestedError = void 0;
      }
    };
    var InvalidArgumentError = class extends CommanderError {
      /**
       * Constructs the InvalidArgumentError class
       * @param {string} [message] explanation of why argument is invalid
       * @constructor
       */
      constructor(message) {
        super(1, "commander.invalidArgument", message);
        Error.captureStackTrace(this, this.constructor);
        this.name = this.constructor.name;
      }
    };
    exports2.CommanderError = CommanderError;
    exports2.InvalidArgumentError = InvalidArgumentError;
  }
});

// node_modules/commander/lib/argument.js
var require_argument = __commonJS({
  "node_modules/commander/lib/argument.js"(exports2) {
    var { InvalidArgumentError } = require_error();
    var Argument = class {
      /**
       * Initialize a new command argument with the given name and description.
       * The default is that the argument is required, and you can explicitly
       * indicate this with <> around the name. Put [] around the name for an optional argument.
       *
       * @param {string} name
       * @param {string} [description]
       */
      constructor(name, description) {
        this.description = description || "";
        this.variadic = false;
        this.parseArg = void 0;
        this.defaultValue = void 0;
        this.defaultValueDescription = void 0;
        this.argChoices = void 0;
        switch (name[0]) {
          case "<":
            this.required = true;
            this._name = name.slice(1, -1);
            break;
          case "[":
            this.required = false;
            this._name = name.slice(1, -1);
            break;
          default:
            this.required = true;
            this._name = name;
            break;
        }
        if (this._name.length > 3 && this._name.slice(-3) === "...") {
          this.variadic = true;
          this._name = this._name.slice(0, -3);
        }
      }
      /**
       * Return argument name.
       *
       * @return {string}
       */
      name() {
        return this._name;
      }
      /**
       * @api private
       */
      _concatValue(value, previous) {
        if (previous === this.defaultValue || !Array.isArray(previous)) {
          return [value];
        }
        return previous.concat(value);
      }
      /**
       * Set the default value, and optionally supply the description to be displayed in the help.
       *
       * @param {*} value
       * @param {string} [description]
       * @return {Argument}
       */
      default(value, description) {
        this.defaultValue = value;
        this.defaultValueDescription = description;
        return this;
      }
      /**
       * Set the custom handler for processing CLI command arguments into argument values.
       *
       * @param {Function} [fn]
       * @return {Argument}
       */
      argParser(fn) {
        this.parseArg = fn;
        return this;
      }
      /**
       * Only allow argument value to be one of choices.
       *
       * @param {string[]} values
       * @return {Argument}
       */
      choices(values) {
        this.argChoices = values.slice();
        this.parseArg = (arg, previous) => {
          if (!this.argChoices.includes(arg)) {
            throw new InvalidArgumentError(`Allowed choices are ${this.argChoices.join(", ")}.`);
          }
          if (this.variadic) {
            return this._concatValue(arg, previous);
          }
          return arg;
        };
        return this;
      }
      /**
       * Make argument required.
       */
      argRequired() {
        this.required = true;
        return this;
      }
      /**
       * Make argument optional.
       */
      argOptional() {
        this.required = false;
        return this;
      }
    };
    function humanReadableArgName(arg) {
      const nameOutput = arg.name() + (arg.variadic === true ? "..." : "");
      return arg.required ? "<" + nameOutput + ">" : "[" + nameOutput + "]";
    }
    exports2.Argument = Argument;
    exports2.humanReadableArgName = humanReadableArgName;
  }
});

// node_modules/commander/lib/help.js
var require_help = __commonJS({
  "node_modules/commander/lib/help.js"(exports2) {
    var { humanReadableArgName } = require_argument();
    var Help = class {
      constructor() {
        this.helpWidth = void 0;
        this.sortSubcommands = false;
        this.sortOptions = false;
        this.showGlobalOptions = false;
      }
      /**
       * Get an array of the visible subcommands. Includes a placeholder for the implicit help command, if there is one.
       *
       * @param {Command} cmd
       * @returns {Command[]}
       */
      visibleCommands(cmd) {
        const visibleCommands = cmd.commands.filter((cmd2) => !cmd2._hidden);
        if (cmd._hasImplicitHelpCommand()) {
          const [, helpName, helpArgs] = cmd._helpCommandnameAndArgs.match(/([^ ]+) *(.*)/);
          const helpCommand = cmd.createCommand(helpName).helpOption(false);
          helpCommand.description(cmd._helpCommandDescription);
          if (helpArgs) helpCommand.arguments(helpArgs);
          visibleCommands.push(helpCommand);
        }
        if (this.sortSubcommands) {
          visibleCommands.sort((a, b) => {
            return a.name().localeCompare(b.name());
          });
        }
        return visibleCommands;
      }
      /**
       * Compare options for sort.
       *
       * @param {Option} a
       * @param {Option} b
       * @returns number
       */
      compareOptions(a, b) {
        const getSortKey = (option) => {
          return option.short ? option.short.replace(/^-/, "") : option.long.replace(/^--/, "");
        };
        return getSortKey(a).localeCompare(getSortKey(b));
      }
      /**
       * Get an array of the visible options. Includes a placeholder for the implicit help option, if there is one.
       *
       * @param {Command} cmd
       * @returns {Option[]}
       */
      visibleOptions(cmd) {
        const visibleOptions = cmd.options.filter((option) => !option.hidden);
        const showShortHelpFlag = cmd._hasHelpOption && cmd._helpShortFlag && !cmd._findOption(cmd._helpShortFlag);
        const showLongHelpFlag = cmd._hasHelpOption && !cmd._findOption(cmd._helpLongFlag);
        if (showShortHelpFlag || showLongHelpFlag) {
          let helpOption;
          if (!showShortHelpFlag) {
            helpOption = cmd.createOption(cmd._helpLongFlag, cmd._helpDescription);
          } else if (!showLongHelpFlag) {
            helpOption = cmd.createOption(cmd._helpShortFlag, cmd._helpDescription);
          } else {
            helpOption = cmd.createOption(cmd._helpFlags, cmd._helpDescription);
          }
          visibleOptions.push(helpOption);
        }
        if (this.sortOptions) {
          visibleOptions.sort(this.compareOptions);
        }
        return visibleOptions;
      }
      /**
       * Get an array of the visible global options. (Not including help.)
       *
       * @param {Command} cmd
       * @returns {Option[]}
       */
      visibleGlobalOptions(cmd) {
        if (!this.showGlobalOptions) return [];
        const globalOptions = [];
        for (let ancestorCmd = cmd.parent; ancestorCmd; ancestorCmd = ancestorCmd.parent) {
          const visibleOptions = ancestorCmd.options.filter((option) => !option.hidden);
          globalOptions.push(...visibleOptions);
        }
        if (this.sortOptions) {
          globalOptions.sort(this.compareOptions);
        }
        return globalOptions;
      }
      /**
       * Get an array of the arguments if any have a description.
       *
       * @param {Command} cmd
       * @returns {Argument[]}
       */
      visibleArguments(cmd) {
        if (cmd._argsDescription) {
          cmd.registeredArguments.forEach((argument) => {
            argument.description = argument.description || cmd._argsDescription[argument.name()] || "";
          });
        }
        if (cmd.registeredArguments.find((argument) => argument.description)) {
          return cmd.registeredArguments;
        }
        return [];
      }
      /**
       * Get the command term to show in the list of subcommands.
       *
       * @param {Command} cmd
       * @returns {string}
       */
      subcommandTerm(cmd) {
        const args = cmd.registeredArguments.map((arg) => humanReadableArgName(arg)).join(" ");
        return cmd._name + (cmd._aliases[0] ? "|" + cmd._aliases[0] : "") + (cmd.options.length ? " [options]" : "") + // simplistic check for non-help option
        (args ? " " + args : "");
      }
      /**
       * Get the option term to show in the list of options.
       *
       * @param {Option} option
       * @returns {string}
       */
      optionTerm(option) {
        return option.flags;
      }
      /**
       * Get the argument term to show in the list of arguments.
       *
       * @param {Argument} argument
       * @returns {string}
       */
      argumentTerm(argument) {
        return argument.name();
      }
      /**
       * Get the longest command term length.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {number}
       */
      longestSubcommandTermLength(cmd, helper) {
        return helper.visibleCommands(cmd).reduce((max, command) => {
          return Math.max(max, helper.subcommandTerm(command).length);
        }, 0);
      }
      /**
       * Get the longest option term length.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {number}
       */
      longestOptionTermLength(cmd, helper) {
        return helper.visibleOptions(cmd).reduce((max, option) => {
          return Math.max(max, helper.optionTerm(option).length);
        }, 0);
      }
      /**
       * Get the longest global option term length.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {number}
       */
      longestGlobalOptionTermLength(cmd, helper) {
        return helper.visibleGlobalOptions(cmd).reduce((max, option) => {
          return Math.max(max, helper.optionTerm(option).length);
        }, 0);
      }
      /**
       * Get the longest argument term length.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {number}
       */
      longestArgumentTermLength(cmd, helper) {
        return helper.visibleArguments(cmd).reduce((max, argument) => {
          return Math.max(max, helper.argumentTerm(argument).length);
        }, 0);
      }
      /**
       * Get the command usage to be displayed at the top of the built-in help.
       *
       * @param {Command} cmd
       * @returns {string}
       */
      commandUsage(cmd) {
        let cmdName = cmd._name;
        if (cmd._aliases[0]) {
          cmdName = cmdName + "|" + cmd._aliases[0];
        }
        let ancestorCmdNames = "";
        for (let ancestorCmd = cmd.parent; ancestorCmd; ancestorCmd = ancestorCmd.parent) {
          ancestorCmdNames = ancestorCmd.name() + " " + ancestorCmdNames;
        }
        return ancestorCmdNames + cmdName + " " + cmd.usage();
      }
      /**
       * Get the description for the command.
       *
       * @param {Command} cmd
       * @returns {string}
       */
      commandDescription(cmd) {
        return cmd.description();
      }
      /**
       * Get the subcommand summary to show in the list of subcommands.
       * (Fallback to description for backwards compatibility.)
       *
       * @param {Command} cmd
       * @returns {string}
       */
      subcommandDescription(cmd) {
        return cmd.summary() || cmd.description();
      }
      /**
       * Get the option description to show in the list of options.
       *
       * @param {Option} option
       * @return {string}
       */
      optionDescription(option) {
        const extraInfo = [];
        if (option.argChoices) {
          extraInfo.push(
            // use stringify to match the display of the default value
            `choices: ${option.argChoices.map((choice) => JSON.stringify(choice)).join(", ")}`
          );
        }
        if (option.defaultValue !== void 0) {
          const showDefault = option.required || option.optional || option.isBoolean() && typeof option.defaultValue === "boolean";
          if (showDefault) {
            extraInfo.push(`default: ${option.defaultValueDescription || JSON.stringify(option.defaultValue)}`);
          }
        }
        if (option.presetArg !== void 0 && option.optional) {
          extraInfo.push(`preset: ${JSON.stringify(option.presetArg)}`);
        }
        if (option.envVar !== void 0) {
          extraInfo.push(`env: ${option.envVar}`);
        }
        if (extraInfo.length > 0) {
          return `${option.description} (${extraInfo.join(", ")})`;
        }
        return option.description;
      }
      /**
       * Get the argument description to show in the list of arguments.
       *
       * @param {Argument} argument
       * @return {string}
       */
      argumentDescription(argument) {
        const extraInfo = [];
        if (argument.argChoices) {
          extraInfo.push(
            // use stringify to match the display of the default value
            `choices: ${argument.argChoices.map((choice) => JSON.stringify(choice)).join(", ")}`
          );
        }
        if (argument.defaultValue !== void 0) {
          extraInfo.push(`default: ${argument.defaultValueDescription || JSON.stringify(argument.defaultValue)}`);
        }
        if (extraInfo.length > 0) {
          const extraDescripton = `(${extraInfo.join(", ")})`;
          if (argument.description) {
            return `${argument.description} ${extraDescripton}`;
          }
          return extraDescripton;
        }
        return argument.description;
      }
      /**
       * Generate the built-in help text.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {string}
       */
      formatHelp(cmd, helper) {
        const termWidth = helper.padWidth(cmd, helper);
        const helpWidth = helper.helpWidth || 80;
        const itemIndentWidth = 2;
        const itemSeparatorWidth = 2;
        function formatItem(term, description) {
          if (description) {
            const fullText = `${term.padEnd(termWidth + itemSeparatorWidth)}${description}`;
            return helper.wrap(fullText, helpWidth - itemIndentWidth, termWidth + itemSeparatorWidth);
          }
          return term;
        }
        function formatList(textArray) {
          return textArray.join("\n").replace(/^/gm, " ".repeat(itemIndentWidth));
        }
        let output = [`Usage: ${helper.commandUsage(cmd)}`, ""];
        const commandDescription = helper.commandDescription(cmd);
        if (commandDescription.length > 0) {
          output = output.concat([helper.wrap(commandDescription, helpWidth, 0), ""]);
        }
        const argumentList = helper.visibleArguments(cmd).map((argument) => {
          return formatItem(helper.argumentTerm(argument), helper.argumentDescription(argument));
        });
        if (argumentList.length > 0) {
          output = output.concat(["Arguments:", formatList(argumentList), ""]);
        }
        const optionList = helper.visibleOptions(cmd).map((option) => {
          return formatItem(helper.optionTerm(option), helper.optionDescription(option));
        });
        if (optionList.length > 0) {
          output = output.concat(["Options:", formatList(optionList), ""]);
        }
        if (this.showGlobalOptions) {
          const globalOptionList = helper.visibleGlobalOptions(cmd).map((option) => {
            return formatItem(helper.optionTerm(option), helper.optionDescription(option));
          });
          if (globalOptionList.length > 0) {
            output = output.concat(["Global Options:", formatList(globalOptionList), ""]);
          }
        }
        const commandList = helper.visibleCommands(cmd).map((cmd2) => {
          return formatItem(helper.subcommandTerm(cmd2), helper.subcommandDescription(cmd2));
        });
        if (commandList.length > 0) {
          output = output.concat(["Commands:", formatList(commandList), ""]);
        }
        return output.join("\n");
      }
      /**
       * Calculate the pad width from the maximum term length.
       *
       * @param {Command} cmd
       * @param {Help} helper
       * @returns {number}
       */
      padWidth(cmd, helper) {
        return Math.max(
          helper.longestOptionTermLength(cmd, helper),
          helper.longestGlobalOptionTermLength(cmd, helper),
          helper.longestSubcommandTermLength(cmd, helper),
          helper.longestArgumentTermLength(cmd, helper)
        );
      }
      /**
       * Wrap the given string to width characters per line, with lines after the first indented.
       * Do not wrap if insufficient room for wrapping (minColumnWidth), or string is manually formatted.
       *
       * @param {string} str
       * @param {number} width
       * @param {number} indent
       * @param {number} [minColumnWidth=40]
       * @return {string}
       *
       */
      wrap(str, width, indent, minColumnWidth = 40) {
        const indents = " \\f\\t\\v\xA0\u1680\u2000-\u200A\u202F\u205F\u3000\uFEFF";
        const manualIndent = new RegExp(`[\\n][${indents}]+`);
        if (str.match(manualIndent)) return str;
        const columnWidth = width - indent;
        if (columnWidth < minColumnWidth) return str;
        const leadingStr = str.slice(0, indent);
        const columnText = str.slice(indent).replace("\r\n", "\n");
        const indentString = " ".repeat(indent);
        const zeroWidthSpace = "\u200B";
        const breaks = `\\s${zeroWidthSpace}`;
        const regex = new RegExp(`
|.{1,${columnWidth - 1}}([${breaks}]|$)|[^${breaks}]+?([${breaks}]|$)`, "g");
        const lines = columnText.match(regex) || [];
        return leadingStr + lines.map((line, i) => {
          if (line === "\n") return "";
          return (i > 0 ? indentString : "") + line.trimEnd();
        }).join("\n");
      }
    };
    exports2.Help = Help;
  }
});

// node_modules/commander/lib/option.js
var require_option = __commonJS({
  "node_modules/commander/lib/option.js"(exports2) {
    var { InvalidArgumentError } = require_error();
    var Option = class {
      /**
       * Initialize a new `Option` with the given `flags` and `description`.
       *
       * @param {string} flags
       * @param {string} [description]
       */
      constructor(flags, description) {
        this.flags = flags;
        this.description = description || "";
        this.required = flags.includes("<");
        this.optional = flags.includes("[");
        this.variadic = /\w\.\.\.[>\]]$/.test(flags);
        this.mandatory = false;
        const optionFlags = splitOptionFlags(flags);
        this.short = optionFlags.shortFlag;
        this.long = optionFlags.longFlag;
        this.negate = false;
        if (this.long) {
          this.negate = this.long.startsWith("--no-");
        }
        this.defaultValue = void 0;
        this.defaultValueDescription = void 0;
        this.presetArg = void 0;
        this.envVar = void 0;
        this.parseArg = void 0;
        this.hidden = false;
        this.argChoices = void 0;
        this.conflictsWith = [];
        this.implied = void 0;
      }
      /**
       * Set the default value, and optionally supply the description to be displayed in the help.
       *
       * @param {*} value
       * @param {string} [description]
       * @return {Option}
       */
      default(value, description) {
        this.defaultValue = value;
        this.defaultValueDescription = description;
        return this;
      }
      /**
       * Preset to use when option used without option-argument, especially optional but also boolean and negated.
       * The custom processing (parseArg) is called.
       *
       * @example
       * new Option('--color').default('GREYSCALE').preset('RGB');
       * new Option('--donate [amount]').preset('20').argParser(parseFloat);
       *
       * @param {*} arg
       * @return {Option}
       */
      preset(arg) {
        this.presetArg = arg;
        return this;
      }
      /**
       * Add option name(s) that conflict with this option.
       * An error will be displayed if conflicting options are found during parsing.
       *
       * @example
       * new Option('--rgb').conflicts('cmyk');
       * new Option('--js').conflicts(['ts', 'jsx']);
       *
       * @param {string | string[]} names
       * @return {Option}
       */
      conflicts(names) {
        this.conflictsWith = this.conflictsWith.concat(names);
        return this;
      }
      /**
       * Specify implied option values for when this option is set and the implied options are not.
       *
       * The custom processing (parseArg) is not called on the implied values.
       *
       * @example
       * program
       *   .addOption(new Option('--log', 'write logging information to file'))
       *   .addOption(new Option('--trace', 'log extra details').implies({ log: 'trace.txt' }));
       *
       * @param {Object} impliedOptionValues
       * @return {Option}
       */
      implies(impliedOptionValues) {
        let newImplied = impliedOptionValues;
        if (typeof impliedOptionValues === "string") {
          newImplied = { [impliedOptionValues]: true };
        }
        this.implied = Object.assign(this.implied || {}, newImplied);
        return this;
      }
      /**
       * Set environment variable to check for option value.
       *
       * An environment variable is only used if when processed the current option value is
       * undefined, or the source of the current value is 'default' or 'config' or 'env'.
       *
       * @param {string} name
       * @return {Option}
       */
      env(name) {
        this.envVar = name;
        return this;
      }
      /**
       * Set the custom handler for processing CLI option arguments into option values.
       *
       * @param {Function} [fn]
       * @return {Option}
       */
      argParser(fn) {
        this.parseArg = fn;
        return this;
      }
      /**
       * Whether the option is mandatory and must have a value after parsing.
       *
       * @param {boolean} [mandatory=true]
       * @return {Option}
       */
      makeOptionMandatory(mandatory = true) {
        this.mandatory = !!mandatory;
        return this;
      }
      /**
       * Hide option in help.
       *
       * @param {boolean} [hide=true]
       * @return {Option}
       */
      hideHelp(hide = true) {
        this.hidden = !!hide;
        return this;
      }
      /**
       * @api private
       */
      _concatValue(value, previous) {
        if (previous === this.defaultValue || !Array.isArray(previous)) {
          return [value];
        }
        return previous.concat(value);
      }
      /**
       * Only allow option value to be one of choices.
       *
       * @param {string[]} values
       * @return {Option}
       */
      choices(values) {
        this.argChoices = values.slice();
        this.parseArg = (arg, previous) => {
          if (!this.argChoices.includes(arg)) {
            throw new InvalidArgumentError(`Allowed choices are ${this.argChoices.join(", ")}.`);
          }
          if (this.variadic) {
            return this._concatValue(arg, previous);
          }
          return arg;
        };
        return this;
      }
      /**
       * Return option name.
       *
       * @return {string}
       */
      name() {
        if (this.long) {
          return this.long.replace(/^--/, "");
        }
        return this.short.replace(/^-/, "");
      }
      /**
       * Return option name, in a camelcase format that can be used
       * as a object attribute key.
       *
       * @return {string}
       * @api private
       */
      attributeName() {
        return camelcase(this.name().replace(/^no-/, ""));
      }
      /**
       * Check if `arg` matches the short or long flag.
       *
       * @param {string} arg
       * @return {boolean}
       * @api private
       */
      is(arg) {
        return this.short === arg || this.long === arg;
      }
      /**
       * Return whether a boolean option.
       *
       * Options are one of boolean, negated, required argument, or optional argument.
       *
       * @return {boolean}
       * @api private
       */
      isBoolean() {
        return !this.required && !this.optional && !this.negate;
      }
    };
    var DualOptions = class {
      /**
       * @param {Option[]} options
       */
      constructor(options) {
        this.positiveOptions = /* @__PURE__ */ new Map();
        this.negativeOptions = /* @__PURE__ */ new Map();
        this.dualOptions = /* @__PURE__ */ new Set();
        options.forEach((option) => {
          if (option.negate) {
            this.negativeOptions.set(option.attributeName(), option);
          } else {
            this.positiveOptions.set(option.attributeName(), option);
          }
        });
        this.negativeOptions.forEach((value, key) => {
          if (this.positiveOptions.has(key)) {
            this.dualOptions.add(key);
          }
        });
      }
      /**
       * Did the value come from the option, and not from possible matching dual option?
       *
       * @param {*} value
       * @param {Option} option
       * @returns {boolean}
       */
      valueFromOption(value, option) {
        const optionKey = option.attributeName();
        if (!this.dualOptions.has(optionKey)) return true;
        const preset = this.negativeOptions.get(optionKey).presetArg;
        const negativeValue = preset !== void 0 ? preset : false;
        return option.negate === (negativeValue === value);
      }
    };
    function camelcase(str) {
      return str.split("-").reduce((str2, word) => {
        return str2 + word[0].toUpperCase() + word.slice(1);
      });
    }
    function splitOptionFlags(flags) {
      let shortFlag;
      let longFlag;
      const flagParts = flags.split(/[ |,]+/);
      if (flagParts.length > 1 && !/^[[<]/.test(flagParts[1])) shortFlag = flagParts.shift();
      longFlag = flagParts.shift();
      if (!shortFlag && /^-[^-]$/.test(longFlag)) {
        shortFlag = longFlag;
        longFlag = void 0;
      }
      return { shortFlag, longFlag };
    }
    exports2.Option = Option;
    exports2.splitOptionFlags = splitOptionFlags;
    exports2.DualOptions = DualOptions;
  }
});

// node_modules/commander/lib/suggestSimilar.js
var require_suggestSimilar = __commonJS({
  "node_modules/commander/lib/suggestSimilar.js"(exports2) {
    var maxDistance = 3;
    function editDistance(a, b) {
      if (Math.abs(a.length - b.length) > maxDistance) return Math.max(a.length, b.length);
      const d = [];
      for (let i = 0; i <= a.length; i++) {
        d[i] = [i];
      }
      for (let j = 0; j <= b.length; j++) {
        d[0][j] = j;
      }
      for (let j = 1; j <= b.length; j++) {
        for (let i = 1; i <= a.length; i++) {
          let cost = 1;
          if (a[i - 1] === b[j - 1]) {
            cost = 0;
          } else {
            cost = 1;
          }
          d[i][j] = Math.min(
            d[i - 1][j] + 1,
            // deletion
            d[i][j - 1] + 1,
            // insertion
            d[i - 1][j - 1] + cost
            // substitution
          );
          if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
            d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
          }
        }
      }
      return d[a.length][b.length];
    }
    function suggestSimilar(word, candidates) {
      if (!candidates || candidates.length === 0) return "";
      candidates = Array.from(new Set(candidates));
      const searchingOptions = word.startsWith("--");
      if (searchingOptions) {
        word = word.slice(2);
        candidates = candidates.map((candidate) => candidate.slice(2));
      }
      let similar = [];
      let bestDistance = maxDistance;
      const minSimilarity = 0.4;
      candidates.forEach((candidate) => {
        if (candidate.length <= 1) return;
        const distance = editDistance(word, candidate);
        const length = Math.max(word.length, candidate.length);
        const similarity = (length - distance) / length;
        if (similarity > minSimilarity) {
          if (distance < bestDistance) {
            bestDistance = distance;
            similar = [candidate];
          } else if (distance === bestDistance) {
            similar.push(candidate);
          }
        }
      });
      similar.sort((a, b) => a.localeCompare(b));
      if (searchingOptions) {
        similar = similar.map((candidate) => `--${candidate}`);
      }
      if (similar.length > 1) {
        return `
(Did you mean one of ${similar.join(", ")}?)`;
      }
      if (similar.length === 1) {
        return `
(Did you mean ${similar[0]}?)`;
      }
      return "";
    }
    exports2.suggestSimilar = suggestSimilar;
  }
});

// node_modules/commander/lib/command.js
var require_command = __commonJS({
  "node_modules/commander/lib/command.js"(exports2) {
    var EventEmitter = require("events").EventEmitter;
    var childProcess = require("child_process");
    var path2 = require("path");
    var fs2 = require("fs");
    var process2 = require("process");
    var { Argument, humanReadableArgName } = require_argument();
    var { CommanderError } = require_error();
    var { Help } = require_help();
    var { Option, splitOptionFlags, DualOptions } = require_option();
    var { suggestSimilar } = require_suggestSimilar();
    var Command = class _Command extends EventEmitter {
      /**
       * Initialize a new `Command`.
       *
       * @param {string} [name]
       */
      constructor(name) {
        super();
        this.commands = [];
        this.options = [];
        this.parent = null;
        this._allowUnknownOption = false;
        this._allowExcessArguments = true;
        this.registeredArguments = [];
        this._args = this.registeredArguments;
        this.args = [];
        this.rawArgs = [];
        this.processedArgs = [];
        this._scriptPath = null;
        this._name = name || "";
        this._optionValues = {};
        this._optionValueSources = {};
        this._storeOptionsAsProperties = false;
        this._actionHandler = null;
        this._executableHandler = false;
        this._executableFile = null;
        this._executableDir = null;
        this._defaultCommandName = null;
        this._exitCallback = null;
        this._aliases = [];
        this._combineFlagAndOptionalValue = true;
        this._description = "";
        this._summary = "";
        this._argsDescription = void 0;
        this._enablePositionalOptions = false;
        this._passThroughOptions = false;
        this._lifeCycleHooks = {};
        this._showHelpAfterError = false;
        this._showSuggestionAfterError = true;
        this._outputConfiguration = {
          writeOut: (str) => process2.stdout.write(str),
          writeErr: (str) => process2.stderr.write(str),
          getOutHelpWidth: () => process2.stdout.isTTY ? process2.stdout.columns : void 0,
          getErrHelpWidth: () => process2.stderr.isTTY ? process2.stderr.columns : void 0,
          outputError: (str, write) => write(str)
        };
        this._hidden = false;
        this._hasHelpOption = true;
        this._helpFlags = "-h, --help";
        this._helpDescription = "display help for command";
        this._helpShortFlag = "-h";
        this._helpLongFlag = "--help";
        this._addImplicitHelpCommand = void 0;
        this._helpCommandName = "help";
        this._helpCommandnameAndArgs = "help [command]";
        this._helpCommandDescription = "display help for command";
        this._helpConfiguration = {};
      }
      /**
       * Copy settings that are useful to have in common across root command and subcommands.
       *
       * (Used internally when adding a command using `.command()` so subcommands inherit parent settings.)
       *
       * @param {Command} sourceCommand
       * @return {Command} `this` command for chaining
       */
      copyInheritedSettings(sourceCommand) {
        this._outputConfiguration = sourceCommand._outputConfiguration;
        this._hasHelpOption = sourceCommand._hasHelpOption;
        this._helpFlags = sourceCommand._helpFlags;
        this._helpDescription = sourceCommand._helpDescription;
        this._helpShortFlag = sourceCommand._helpShortFlag;
        this._helpLongFlag = sourceCommand._helpLongFlag;
        this._helpCommandName = sourceCommand._helpCommandName;
        this._helpCommandnameAndArgs = sourceCommand._helpCommandnameAndArgs;
        this._helpCommandDescription = sourceCommand._helpCommandDescription;
        this._helpConfiguration = sourceCommand._helpConfiguration;
        this._exitCallback = sourceCommand._exitCallback;
        this._storeOptionsAsProperties = sourceCommand._storeOptionsAsProperties;
        this._combineFlagAndOptionalValue = sourceCommand._combineFlagAndOptionalValue;
        this._allowExcessArguments = sourceCommand._allowExcessArguments;
        this._enablePositionalOptions = sourceCommand._enablePositionalOptions;
        this._showHelpAfterError = sourceCommand._showHelpAfterError;
        this._showSuggestionAfterError = sourceCommand._showSuggestionAfterError;
        return this;
      }
      /**
       * @returns {Command[]}
       * @api private
       */
      _getCommandAndAncestors() {
        const result = [];
        for (let command = this; command; command = command.parent) {
          result.push(command);
        }
        return result;
      }
      /**
       * Define a command.
       *
       * There are two styles of command: pay attention to where to put the description.
       *
       * @example
       * // Command implemented using action handler (description is supplied separately to `.command`)
       * program
       *   .command('clone <source> [destination]')
       *   .description('clone a repository into a newly created directory')
       *   .action((source, destination) => {
       *     console.log('clone command called');
       *   });
       *
       * // Command implemented using separate executable file (description is second parameter to `.command`)
       * program
       *   .command('start <service>', 'start named service')
       *   .command('stop [service]', 'stop named service, or all if no name supplied');
       *
       * @param {string} nameAndArgs - command name and arguments, args are `<required>` or `[optional]` and last may also be `variadic...`
       * @param {Object|string} [actionOptsOrExecDesc] - configuration options (for action), or description (for executable)
       * @param {Object} [execOpts] - configuration options (for executable)
       * @return {Command} returns new command for action handler, or `this` for executable command
       */
      command(nameAndArgs, actionOptsOrExecDesc, execOpts) {
        let desc = actionOptsOrExecDesc;
        let opts = execOpts;
        if (typeof desc === "object" && desc !== null) {
          opts = desc;
          desc = null;
        }
        opts = opts || {};
        const [, name, args] = nameAndArgs.match(/([^ ]+) *(.*)/);
        const cmd = this.createCommand(name);
        if (desc) {
          cmd.description(desc);
          cmd._executableHandler = true;
        }
        if (opts.isDefault) this._defaultCommandName = cmd._name;
        cmd._hidden = !!(opts.noHelp || opts.hidden);
        cmd._executableFile = opts.executableFile || null;
        if (args) cmd.arguments(args);
        this.commands.push(cmd);
        cmd.parent = this;
        cmd.copyInheritedSettings(this);
        if (desc) return this;
        return cmd;
      }
      /**
       * Factory routine to create a new unattached command.
       *
       * See .command() for creating an attached subcommand, which uses this routine to
       * create the command. You can override createCommand to customise subcommands.
       *
       * @param {string} [name]
       * @return {Command} new command
       */
      createCommand(name) {
        return new _Command(name);
      }
      /**
       * You can customise the help with a subclass of Help by overriding createHelp,
       * or by overriding Help properties using configureHelp().
       *
       * @return {Help}
       */
      createHelp() {
        return Object.assign(new Help(), this.configureHelp());
      }
      /**
       * You can customise the help by overriding Help properties using configureHelp(),
       * or with a subclass of Help by overriding createHelp().
       *
       * @param {Object} [configuration] - configuration options
       * @return {Command|Object} `this` command for chaining, or stored configuration
       */
      configureHelp(configuration) {
        if (configuration === void 0) return this._helpConfiguration;
        this._helpConfiguration = configuration;
        return this;
      }
      /**
       * The default output goes to stdout and stderr. You can customise this for special
       * applications. You can also customise the display of errors by overriding outputError.
       *
       * The configuration properties are all functions:
       *
       *     // functions to change where being written, stdout and stderr
       *     writeOut(str)
       *     writeErr(str)
       *     // matching functions to specify width for wrapping help
       *     getOutHelpWidth()
       *     getErrHelpWidth()
       *     // functions based on what is being written out
       *     outputError(str, write) // used for displaying errors, and not used for displaying help
       *
       * @param {Object} [configuration] - configuration options
       * @return {Command|Object} `this` command for chaining, or stored configuration
       */
      configureOutput(configuration) {
        if (configuration === void 0) return this._outputConfiguration;
        Object.assign(this._outputConfiguration, configuration);
        return this;
      }
      /**
       * Display the help or a custom message after an error occurs.
       *
       * @param {boolean|string} [displayHelp]
       * @return {Command} `this` command for chaining
       */
      showHelpAfterError(displayHelp = true) {
        if (typeof displayHelp !== "string") displayHelp = !!displayHelp;
        this._showHelpAfterError = displayHelp;
        return this;
      }
      /**
       * Display suggestion of similar commands for unknown commands, or options for unknown options.
       *
       * @param {boolean} [displaySuggestion]
       * @return {Command} `this` command for chaining
       */
      showSuggestionAfterError(displaySuggestion = true) {
        this._showSuggestionAfterError = !!displaySuggestion;
        return this;
      }
      /**
       * Add a prepared subcommand.
       *
       * See .command() for creating an attached subcommand which inherits settings from its parent.
       *
       * @param {Command} cmd - new subcommand
       * @param {Object} [opts] - configuration options
       * @return {Command} `this` command for chaining
       */
      addCommand(cmd, opts) {
        if (!cmd._name) {
          throw new Error(`Command passed to .addCommand() must have a name
- specify the name in Command constructor or using .name()`);
        }
        opts = opts || {};
        if (opts.isDefault) this._defaultCommandName = cmd._name;
        if (opts.noHelp || opts.hidden) cmd._hidden = true;
        this.commands.push(cmd);
        cmd.parent = this;
        return this;
      }
      /**
       * Factory routine to create a new unattached argument.
       *
       * See .argument() for creating an attached argument, which uses this routine to
       * create the argument. You can override createArgument to return a custom argument.
       *
       * @param {string} name
       * @param {string} [description]
       * @return {Argument} new argument
       */
      createArgument(name, description) {
        return new Argument(name, description);
      }
      /**
       * Define argument syntax for command.
       *
       * The default is that the argument is required, and you can explicitly
       * indicate this with <> around the name. Put [] around the name for an optional argument.
       *
       * @example
       * program.argument('<input-file>');
       * program.argument('[output-file]');
       *
       * @param {string} name
       * @param {string} [description]
       * @param {Function|*} [fn] - custom argument processing function
       * @param {*} [defaultValue]
       * @return {Command} `this` command for chaining
       */
      argument(name, description, fn, defaultValue) {
        const argument = this.createArgument(name, description);
        if (typeof fn === "function") {
          argument.default(defaultValue).argParser(fn);
        } else {
          argument.default(fn);
        }
        this.addArgument(argument);
        return this;
      }
      /**
       * Define argument syntax for command, adding multiple at once (without descriptions).
       *
       * See also .argument().
       *
       * @example
       * program.arguments('<cmd> [env]');
       *
       * @param {string} names
       * @return {Command} `this` command for chaining
       */
      arguments(names) {
        names.trim().split(/ +/).forEach((detail) => {
          this.argument(detail);
        });
        return this;
      }
      /**
       * Define argument syntax for command, adding a prepared argument.
       *
       * @param {Argument} argument
       * @return {Command} `this` command for chaining
       */
      addArgument(argument) {
        const previousArgument = this.registeredArguments.slice(-1)[0];
        if (previousArgument && previousArgument.variadic) {
          throw new Error(`only the last argument can be variadic '${previousArgument.name()}'`);
        }
        if (argument.required && argument.defaultValue !== void 0 && argument.parseArg === void 0) {
          throw new Error(`a default value for a required argument is never used: '${argument.name()}'`);
        }
        this.registeredArguments.push(argument);
        return this;
      }
      /**
       * Override default decision whether to add implicit help command.
       *
       *    addHelpCommand() // force on
       *    addHelpCommand(false); // force off
       *    addHelpCommand('help [cmd]', 'display help for [cmd]'); // force on with custom details
       *
       * @return {Command} `this` command for chaining
       */
      addHelpCommand(enableOrNameAndArgs, description) {
        if (enableOrNameAndArgs === false) {
          this._addImplicitHelpCommand = false;
        } else {
          this._addImplicitHelpCommand = true;
          if (typeof enableOrNameAndArgs === "string") {
            this._helpCommandName = enableOrNameAndArgs.split(" ")[0];
            this._helpCommandnameAndArgs = enableOrNameAndArgs;
          }
          this._helpCommandDescription = description || this._helpCommandDescription;
        }
        return this;
      }
      /**
       * @return {boolean}
       * @api private
       */
      _hasImplicitHelpCommand() {
        if (this._addImplicitHelpCommand === void 0) {
          return this.commands.length && !this._actionHandler && !this._findCommand("help");
        }
        return this._addImplicitHelpCommand;
      }
      /**
       * Add hook for life cycle event.
       *
       * @param {string} event
       * @param {Function} listener
       * @return {Command} `this` command for chaining
       */
      hook(event, listener) {
        const allowedValues = ["preSubcommand", "preAction", "postAction"];
        if (!allowedValues.includes(event)) {
          throw new Error(`Unexpected value for event passed to hook : '${event}'.
Expecting one of '${allowedValues.join("', '")}'`);
        }
        if (this._lifeCycleHooks[event]) {
          this._lifeCycleHooks[event].push(listener);
        } else {
          this._lifeCycleHooks[event] = [listener];
        }
        return this;
      }
      /**
       * Register callback to use as replacement for calling process.exit.
       *
       * @param {Function} [fn] optional callback which will be passed a CommanderError, defaults to throwing
       * @return {Command} `this` command for chaining
       */
      exitOverride(fn) {
        if (fn) {
          this._exitCallback = fn;
        } else {
          this._exitCallback = (err) => {
            if (err.code !== "commander.executeSubCommandAsync") {
              throw err;
            } else {
            }
          };
        }
        return this;
      }
      /**
       * Call process.exit, and _exitCallback if defined.
       *
       * @param {number} exitCode exit code for using with process.exit
       * @param {string} code an id string representing the error
       * @param {string} message human-readable description of the error
       * @return never
       * @api private
       */
      _exit(exitCode, code, message) {
        if (this._exitCallback) {
          this._exitCallback(new CommanderError(exitCode, code, message));
        }
        process2.exit(exitCode);
      }
      /**
       * Register callback `fn` for the command.
       *
       * @example
       * program
       *   .command('serve')
       *   .description('start service')
       *   .action(function() {
       *      // do work here
       *   });
       *
       * @param {Function} fn
       * @return {Command} `this` command for chaining
       */
      action(fn) {
        const listener = (args) => {
          const expectedArgsCount = this.registeredArguments.length;
          const actionArgs = args.slice(0, expectedArgsCount);
          if (this._storeOptionsAsProperties) {
            actionArgs[expectedArgsCount] = this;
          } else {
            actionArgs[expectedArgsCount] = this.opts();
          }
          actionArgs.push(this);
          return fn.apply(this, actionArgs);
        };
        this._actionHandler = listener;
        return this;
      }
      /**
       * Factory routine to create a new unattached option.
       *
       * See .option() for creating an attached option, which uses this routine to
       * create the option. You can override createOption to return a custom option.
       *
       * @param {string} flags
       * @param {string} [description]
       * @return {Option} new option
       */
      createOption(flags, description) {
        return new Option(flags, description);
      }
      /**
       * Wrap parseArgs to catch 'commander.invalidArgument'.
       *
       * @param {Option | Argument} target
       * @param {string} value
       * @param {*} previous
       * @param {string} invalidArgumentMessage
       * @api private
       */
      _callParseArg(target, value, previous, invalidArgumentMessage) {
        try {
          return target.parseArg(value, previous);
        } catch (err) {
          if (err.code === "commander.invalidArgument") {
            const message = `${invalidArgumentMessage} ${err.message}`;
            this.error(message, { exitCode: err.exitCode, code: err.code });
          }
          throw err;
        }
      }
      /**
       * Add an option.
       *
       * @param {Option} option
       * @return {Command} `this` command for chaining
       */
      addOption(option) {
        const oname = option.name();
        const name = option.attributeName();
        if (option.negate) {
          const positiveLongFlag = option.long.replace(/^--no-/, "--");
          if (!this._findOption(positiveLongFlag)) {
            this.setOptionValueWithSource(name, option.defaultValue === void 0 ? true : option.defaultValue, "default");
          }
        } else if (option.defaultValue !== void 0) {
          this.setOptionValueWithSource(name, option.defaultValue, "default");
        }
        this.options.push(option);
        const handleOptionValue = (val, invalidValueMessage, valueSource) => {
          if (val == null && option.presetArg !== void 0) {
            val = option.presetArg;
          }
          const oldValue = this.getOptionValue(name);
          if (val !== null && option.parseArg) {
            val = this._callParseArg(option, val, oldValue, invalidValueMessage);
          } else if (val !== null && option.variadic) {
            val = option._concatValue(val, oldValue);
          }
          if (val == null) {
            if (option.negate) {
              val = false;
            } else if (option.isBoolean() || option.optional) {
              val = true;
            } else {
              val = "";
            }
          }
          this.setOptionValueWithSource(name, val, valueSource);
        };
        this.on("option:" + oname, (val) => {
          const invalidValueMessage = `error: option '${option.flags}' argument '${val}' is invalid.`;
          handleOptionValue(val, invalidValueMessage, "cli");
        });
        if (option.envVar) {
          this.on("optionEnv:" + oname, (val) => {
            const invalidValueMessage = `error: option '${option.flags}' value '${val}' from env '${option.envVar}' is invalid.`;
            handleOptionValue(val, invalidValueMessage, "env");
          });
        }
        return this;
      }
      /**
       * Internal implementation shared by .option() and .requiredOption()
       *
       * @api private
       */
      _optionEx(config, flags, description, fn, defaultValue) {
        if (typeof flags === "object" && flags instanceof Option) {
          throw new Error("To add an Option object use addOption() instead of option() or requiredOption()");
        }
        const option = this.createOption(flags, description);
        option.makeOptionMandatory(!!config.mandatory);
        if (typeof fn === "function") {
          option.default(defaultValue).argParser(fn);
        } else if (fn instanceof RegExp) {
          const regex = fn;
          fn = (val, def) => {
            const m = regex.exec(val);
            return m ? m[0] : def;
          };
          option.default(defaultValue).argParser(fn);
        } else {
          option.default(fn);
        }
        return this.addOption(option);
      }
      /**
       * Define option with `flags`, `description`, and optional argument parsing function or `defaultValue` or both.
       *
       * The `flags` string contains the short and/or long flags, separated by comma, a pipe or space. A required
       * option-argument is indicated by `<>` and an optional option-argument by `[]`.
       *
       * See the README for more details, and see also addOption() and requiredOption().
       *
       * @example
       * program
       *     .option('-p, --pepper', 'add pepper')
       *     .option('-p, --pizza-type <TYPE>', 'type of pizza') // required option-argument
       *     .option('-c, --cheese [CHEESE]', 'add extra cheese', 'mozzarella') // optional option-argument with default
       *     .option('-t, --tip <VALUE>', 'add tip to purchase cost', parseFloat) // custom parse function
       *
       * @param {string} flags
       * @param {string} [description]
       * @param {Function|*} [parseArg] - custom option processing function or default value
       * @param {*} [defaultValue]
       * @return {Command} `this` command for chaining
       */
      option(flags, description, parseArg, defaultValue) {
        return this._optionEx({}, flags, description, parseArg, defaultValue);
      }
      /**
      * Add a required option which must have a value after parsing. This usually means
      * the option must be specified on the command line. (Otherwise the same as .option().)
      *
      * The `flags` string contains the short and/or long flags, separated by comma, a pipe or space.
      *
      * @param {string} flags
      * @param {string} [description]
      * @param {Function|*} [parseArg] - custom option processing function or default value
      * @param {*} [defaultValue]
      * @return {Command} `this` command for chaining
      */
      requiredOption(flags, description, parseArg, defaultValue) {
        return this._optionEx({ mandatory: true }, flags, description, parseArg, defaultValue);
      }
      /**
       * Alter parsing of short flags with optional values.
       *
       * @example
       * // for `.option('-f,--flag [value]'):
       * program.combineFlagAndOptionalValue(true);  // `-f80` is treated like `--flag=80`, this is the default behaviour
       * program.combineFlagAndOptionalValue(false) // `-fb` is treated like `-f -b`
       *
       * @param {Boolean} [combine=true] - if `true` or omitted, an optional value can be specified directly after the flag.
       */
      combineFlagAndOptionalValue(combine = true) {
        this._combineFlagAndOptionalValue = !!combine;
        return this;
      }
      /**
       * Allow unknown options on the command line.
       *
       * @param {Boolean} [allowUnknown=true] - if `true` or omitted, no error will be thrown
       * for unknown options.
       */
      allowUnknownOption(allowUnknown = true) {
        this._allowUnknownOption = !!allowUnknown;
        return this;
      }
      /**
       * Allow excess command-arguments on the command line. Pass false to make excess arguments an error.
       *
       * @param {Boolean} [allowExcess=true] - if `true` or omitted, no error will be thrown
       * for excess arguments.
       */
      allowExcessArguments(allowExcess = true) {
        this._allowExcessArguments = !!allowExcess;
        return this;
      }
      /**
       * Enable positional options. Positional means global options are specified before subcommands which lets
       * subcommands reuse the same option names, and also enables subcommands to turn on passThroughOptions.
       * The default behaviour is non-positional and global options may appear anywhere on the command line.
       *
       * @param {Boolean} [positional=true]
       */
      enablePositionalOptions(positional = true) {
        this._enablePositionalOptions = !!positional;
        return this;
      }
      /**
       * Pass through options that come after command-arguments rather than treat them as command-options,
       * so actual command-options come before command-arguments. Turning this on for a subcommand requires
       * positional options to have been enabled on the program (parent commands).
       * The default behaviour is non-positional and options may appear before or after command-arguments.
       *
       * @param {Boolean} [passThrough=true]
       * for unknown options.
       */
      passThroughOptions(passThrough = true) {
        this._passThroughOptions = !!passThrough;
        if (!!this.parent && passThrough && !this.parent._enablePositionalOptions) {
          throw new Error("passThroughOptions can not be used without turning on enablePositionalOptions for parent command(s)");
        }
        return this;
      }
      /**
        * Whether to store option values as properties on command object,
        * or store separately (specify false). In both cases the option values can be accessed using .opts().
        *
        * @param {boolean} [storeAsProperties=true]
        * @return {Command} `this` command for chaining
        */
      storeOptionsAsProperties(storeAsProperties = true) {
        if (this.options.length) {
          throw new Error("call .storeOptionsAsProperties() before adding options");
        }
        this._storeOptionsAsProperties = !!storeAsProperties;
        return this;
      }
      /**
       * Retrieve option value.
       *
       * @param {string} key
       * @return {Object} value
       */
      getOptionValue(key) {
        if (this._storeOptionsAsProperties) {
          return this[key];
        }
        return this._optionValues[key];
      }
      /**
       * Store option value.
       *
       * @param {string} key
       * @param {Object} value
       * @return {Command} `this` command for chaining
       */
      setOptionValue(key, value) {
        return this.setOptionValueWithSource(key, value, void 0);
      }
      /**
        * Store option value and where the value came from.
        *
        * @param {string} key
        * @param {Object} value
        * @param {string} source - expected values are default/config/env/cli/implied
        * @return {Command} `this` command for chaining
        */
      setOptionValueWithSource(key, value, source) {
        if (this._storeOptionsAsProperties) {
          this[key] = value;
        } else {
          this._optionValues[key] = value;
        }
        this._optionValueSources[key] = source;
        return this;
      }
      /**
        * Get source of option value.
        * Expected values are default | config | env | cli | implied
        *
        * @param {string} key
        * @return {string}
        */
      getOptionValueSource(key) {
        return this._optionValueSources[key];
      }
      /**
        * Get source of option value. See also .optsWithGlobals().
        * Expected values are default | config | env | cli | implied
        *
        * @param {string} key
        * @return {string}
        */
      getOptionValueSourceWithGlobals(key) {
        let source;
        this._getCommandAndAncestors().forEach((cmd) => {
          if (cmd.getOptionValueSource(key) !== void 0) {
            source = cmd.getOptionValueSource(key);
          }
        });
        return source;
      }
      /**
       * Get user arguments from implied or explicit arguments.
       * Side-effects: set _scriptPath if args included script. Used for default program name, and subcommand searches.
       *
       * @api private
       */
      _prepareUserArgs(argv, parseOptions) {
        if (argv !== void 0 && !Array.isArray(argv)) {
          throw new Error("first parameter to parse must be array or undefined");
        }
        parseOptions = parseOptions || {};
        if (argv === void 0) {
          argv = process2.argv;
          if (process2.versions && process2.versions.electron) {
            parseOptions.from = "electron";
          }
        }
        this.rawArgs = argv.slice();
        let userArgs;
        switch (parseOptions.from) {
          case void 0:
          case "node":
            this._scriptPath = argv[1];
            userArgs = argv.slice(2);
            break;
          case "electron":
            if (process2.defaultApp) {
              this._scriptPath = argv[1];
              userArgs = argv.slice(2);
            } else {
              userArgs = argv.slice(1);
            }
            break;
          case "user":
            userArgs = argv.slice(0);
            break;
          default:
            throw new Error(`unexpected parse option { from: '${parseOptions.from}' }`);
        }
        if (!this._name && this._scriptPath) this.nameFromFilename(this._scriptPath);
        this._name = this._name || "program";
        return userArgs;
      }
      /**
       * Parse `argv`, setting options and invoking commands when defined.
       *
       * The default expectation is that the arguments are from node and have the application as argv[0]
       * and the script being run in argv[1], with user parameters after that.
       *
       * @example
       * program.parse(process.argv);
       * program.parse(); // implicitly use process.argv and auto-detect node vs electron conventions
       * program.parse(my-args, { from: 'user' }); // just user supplied arguments, nothing special about argv[0]
       *
       * @param {string[]} [argv] - optional, defaults to process.argv
       * @param {Object} [parseOptions] - optionally specify style of options with from: node/user/electron
       * @param {string} [parseOptions.from] - where the args are from: 'node', 'user', 'electron'
       * @return {Command} `this` command for chaining
       */
      parse(argv, parseOptions) {
        const userArgs = this._prepareUserArgs(argv, parseOptions);
        this._parseCommand([], userArgs);
        return this;
      }
      /**
       * Parse `argv`, setting options and invoking commands when defined.
       *
       * Use parseAsync instead of parse if any of your action handlers are async. Returns a Promise.
       *
       * The default expectation is that the arguments are from node and have the application as argv[0]
       * and the script being run in argv[1], with user parameters after that.
       *
       * @example
       * await program.parseAsync(process.argv);
       * await program.parseAsync(); // implicitly use process.argv and auto-detect node vs electron conventions
       * await program.parseAsync(my-args, { from: 'user' }); // just user supplied arguments, nothing special about argv[0]
       *
       * @param {string[]} [argv]
       * @param {Object} [parseOptions]
       * @param {string} parseOptions.from - where the args are from: 'node', 'user', 'electron'
       * @return {Promise}
       */
      async parseAsync(argv, parseOptions) {
        const userArgs = this._prepareUserArgs(argv, parseOptions);
        await this._parseCommand([], userArgs);
        return this;
      }
      /**
       * Execute a sub-command executable.
       *
       * @api private
       */
      _executeSubCommand(subcommand, args) {
        args = args.slice();
        let launchWithNode = false;
        const sourceExt = [".js", ".ts", ".tsx", ".mjs", ".cjs"];
        function findFile(baseDir, baseName) {
          const localBin = path2.resolve(baseDir, baseName);
          if (fs2.existsSync(localBin)) return localBin;
          if (sourceExt.includes(path2.extname(baseName))) return void 0;
          const foundExt = sourceExt.find((ext) => fs2.existsSync(`${localBin}${ext}`));
          if (foundExt) return `${localBin}${foundExt}`;
          return void 0;
        }
        this._checkForMissingMandatoryOptions();
        this._checkForConflictingOptions();
        let executableFile = subcommand._executableFile || `${this._name}-${subcommand._name}`;
        let executableDir = this._executableDir || "";
        if (this._scriptPath) {
          let resolvedScriptPath;
          try {
            resolvedScriptPath = fs2.realpathSync(this._scriptPath);
          } catch (err) {
            resolvedScriptPath = this._scriptPath;
          }
          executableDir = path2.resolve(path2.dirname(resolvedScriptPath), executableDir);
        }
        if (executableDir) {
          let localFile = findFile(executableDir, executableFile);
          if (!localFile && !subcommand._executableFile && this._scriptPath) {
            const legacyName = path2.basename(this._scriptPath, path2.extname(this._scriptPath));
            if (legacyName !== this._name) {
              localFile = findFile(executableDir, `${legacyName}-${subcommand._name}`);
            }
          }
          executableFile = localFile || executableFile;
        }
        launchWithNode = sourceExt.includes(path2.extname(executableFile));
        let proc;
        if (process2.platform !== "win32") {
          if (launchWithNode) {
            args.unshift(executableFile);
            args = incrementNodeInspectorPort(process2.execArgv).concat(args);
            proc = childProcess.spawn(process2.argv[0], args, { stdio: "inherit" });
          } else {
            proc = childProcess.spawn(executableFile, args, { stdio: "inherit" });
          }
        } else {
          args.unshift(executableFile);
          args = incrementNodeInspectorPort(process2.execArgv).concat(args);
          proc = childProcess.spawn(process2.execPath, args, { stdio: "inherit" });
        }
        if (!proc.killed) {
          const signals = ["SIGUSR1", "SIGUSR2", "SIGTERM", "SIGINT", "SIGHUP"];
          signals.forEach((signal) => {
            process2.on(signal, () => {
              if (proc.killed === false && proc.exitCode === null) {
                proc.kill(signal);
              }
            });
          });
        }
        const exitCallback = this._exitCallback;
        if (!exitCallback) {
          proc.on("close", process2.exit.bind(process2));
        } else {
          proc.on("close", () => {
            exitCallback(new CommanderError(process2.exitCode || 0, "commander.executeSubCommandAsync", "(close)"));
          });
        }
        proc.on("error", (err) => {
          if (err.code === "ENOENT") {
            const executableDirMessage = executableDir ? `searched for local subcommand relative to directory '${executableDir}'` : "no directory for search for local subcommand, use .executableDir() to supply a custom directory";
            const executableMissing = `'${executableFile}' does not exist
 - if '${subcommand._name}' is not meant to be an executable command, remove description parameter from '.command()' and use '.description()' instead
 - if the default executable name is not suitable, use the executableFile option to supply a custom name or path
 - ${executableDirMessage}`;
            throw new Error(executableMissing);
          } else if (err.code === "EACCES") {
            throw new Error(`'${executableFile}' not executable`);
          }
          if (!exitCallback) {
            process2.exit(1);
          } else {
            const wrappedError = new CommanderError(1, "commander.executeSubCommandAsync", "(error)");
            wrappedError.nestedError = err;
            exitCallback(wrappedError);
          }
        });
        this.runningCommand = proc;
      }
      /**
       * @api private
       */
      _dispatchSubcommand(commandName, operands, unknown) {
        const subCommand = this._findCommand(commandName);
        if (!subCommand) this.help({ error: true });
        let promiseChain;
        promiseChain = this._chainOrCallSubCommandHook(promiseChain, subCommand, "preSubcommand");
        promiseChain = this._chainOrCall(promiseChain, () => {
          if (subCommand._executableHandler) {
            this._executeSubCommand(subCommand, operands.concat(unknown));
          } else {
            return subCommand._parseCommand(operands, unknown);
          }
        });
        return promiseChain;
      }
      /**
       * Invoke help directly if possible, or dispatch if necessary.
       * e.g. help foo
       *
       * @api private
       */
      _dispatchHelpCommand(subcommandName) {
        if (!subcommandName) {
          this.help();
        }
        const subCommand = this._findCommand(subcommandName);
        if (subCommand && !subCommand._executableHandler) {
          subCommand.help();
        }
        return this._dispatchSubcommand(subcommandName, [], [
          this._helpLongFlag || this._helpShortFlag
        ]);
      }
      /**
       * Check this.args against expected this.registeredArguments.
       *
       * @api private
       */
      _checkNumberOfArguments() {
        this.registeredArguments.forEach((arg, i) => {
          if (arg.required && this.args[i] == null) {
            this.missingArgument(arg.name());
          }
        });
        if (this.registeredArguments.length > 0 && this.registeredArguments[this.registeredArguments.length - 1].variadic) {
          return;
        }
        if (this.args.length > this.registeredArguments.length) {
          this._excessArguments(this.args);
        }
      }
      /**
       * Process this.args using this.registeredArguments and save as this.processedArgs!
       *
       * @api private
       */
      _processArguments() {
        const myParseArg = (argument, value, previous) => {
          let parsedValue = value;
          if (value !== null && argument.parseArg) {
            const invalidValueMessage = `error: command-argument value '${value}' is invalid for argument '${argument.name()}'.`;
            parsedValue = this._callParseArg(argument, value, previous, invalidValueMessage);
          }
          return parsedValue;
        };
        this._checkNumberOfArguments();
        const processedArgs = [];
        this.registeredArguments.forEach((declaredArg, index) => {
          let value = declaredArg.defaultValue;
          if (declaredArg.variadic) {
            if (index < this.args.length) {
              value = this.args.slice(index);
              if (declaredArg.parseArg) {
                value = value.reduce((processed, v) => {
                  return myParseArg(declaredArg, v, processed);
                }, declaredArg.defaultValue);
              }
            } else if (value === void 0) {
              value = [];
            }
          } else if (index < this.args.length) {
            value = this.args[index];
            if (declaredArg.parseArg) {
              value = myParseArg(declaredArg, value, declaredArg.defaultValue);
            }
          }
          processedArgs[index] = value;
        });
        this.processedArgs = processedArgs;
      }
      /**
       * Once we have a promise we chain, but call synchronously until then.
       *
       * @param {Promise|undefined} promise
       * @param {Function} fn
       * @return {Promise|undefined}
       * @api private
       */
      _chainOrCall(promise, fn) {
        if (promise && promise.then && typeof promise.then === "function") {
          return promise.then(() => fn());
        }
        return fn();
      }
      /**
       *
       * @param {Promise|undefined} promise
       * @param {string} event
       * @return {Promise|undefined}
       * @api private
       */
      _chainOrCallHooks(promise, event) {
        let result = promise;
        const hooks = [];
        this._getCommandAndAncestors().reverse().filter((cmd) => cmd._lifeCycleHooks[event] !== void 0).forEach((hookedCommand) => {
          hookedCommand._lifeCycleHooks[event].forEach((callback) => {
            hooks.push({ hookedCommand, callback });
          });
        });
        if (event === "postAction") {
          hooks.reverse();
        }
        hooks.forEach((hookDetail) => {
          result = this._chainOrCall(result, () => {
            return hookDetail.callback(hookDetail.hookedCommand, this);
          });
        });
        return result;
      }
      /**
       *
       * @param {Promise|undefined} promise
       * @param {Command} subCommand
       * @param {string} event
       * @return {Promise|undefined}
       * @api private
       */
      _chainOrCallSubCommandHook(promise, subCommand, event) {
        let result = promise;
        if (this._lifeCycleHooks[event] !== void 0) {
          this._lifeCycleHooks[event].forEach((hook) => {
            result = this._chainOrCall(result, () => {
              return hook(this, subCommand);
            });
          });
        }
        return result;
      }
      /**
       * Process arguments in context of this command.
       * Returns action result, in case it is a promise.
       *
       * @api private
       */
      _parseCommand(operands, unknown) {
        const parsed = this.parseOptions(unknown);
        this._parseOptionsEnv();
        this._parseOptionsImplied();
        operands = operands.concat(parsed.operands);
        unknown = parsed.unknown;
        this.args = operands.concat(unknown);
        if (operands && this._findCommand(operands[0])) {
          return this._dispatchSubcommand(operands[0], operands.slice(1), unknown);
        }
        if (this._hasImplicitHelpCommand() && operands[0] === this._helpCommandName) {
          return this._dispatchHelpCommand(operands[1]);
        }
        if (this._defaultCommandName) {
          outputHelpIfRequested(this, unknown);
          return this._dispatchSubcommand(this._defaultCommandName, operands, unknown);
        }
        if (this.commands.length && this.args.length === 0 && !this._actionHandler && !this._defaultCommandName) {
          this.help({ error: true });
        }
        outputHelpIfRequested(this, parsed.unknown);
        this._checkForMissingMandatoryOptions();
        this._checkForConflictingOptions();
        const checkForUnknownOptions = () => {
          if (parsed.unknown.length > 0) {
            this.unknownOption(parsed.unknown[0]);
          }
        };
        const commandEvent = `command:${this.name()}`;
        if (this._actionHandler) {
          checkForUnknownOptions();
          this._processArguments();
          let promiseChain;
          promiseChain = this._chainOrCallHooks(promiseChain, "preAction");
          promiseChain = this._chainOrCall(promiseChain, () => this._actionHandler(this.processedArgs));
          if (this.parent) {
            promiseChain = this._chainOrCall(promiseChain, () => {
              this.parent.emit(commandEvent, operands, unknown);
            });
          }
          promiseChain = this._chainOrCallHooks(promiseChain, "postAction");
          return promiseChain;
        }
        if (this.parent && this.parent.listenerCount(commandEvent)) {
          checkForUnknownOptions();
          this._processArguments();
          this.parent.emit(commandEvent, operands, unknown);
        } else if (operands.length) {
          if (this._findCommand("*")) {
            return this._dispatchSubcommand("*", operands, unknown);
          }
          if (this.listenerCount("command:*")) {
            this.emit("command:*", operands, unknown);
          } else if (this.commands.length) {
            this.unknownCommand();
          } else {
            checkForUnknownOptions();
            this._processArguments();
          }
        } else if (this.commands.length) {
          checkForUnknownOptions();
          this.help({ error: true });
        } else {
          checkForUnknownOptions();
          this._processArguments();
        }
      }
      /**
       * Find matching command.
       *
       * @api private
       */
      _findCommand(name) {
        if (!name) return void 0;
        return this.commands.find((cmd) => cmd._name === name || cmd._aliases.includes(name));
      }
      /**
       * Return an option matching `arg` if any.
       *
       * @param {string} arg
       * @return {Option}
       * @api private
       */
      _findOption(arg) {
        return this.options.find((option) => option.is(arg));
      }
      /**
       * Display an error message if a mandatory option does not have a value.
       * Called after checking for help flags in leaf subcommand.
       *
       * @api private
       */
      _checkForMissingMandatoryOptions() {
        this._getCommandAndAncestors().forEach((cmd) => {
          cmd.options.forEach((anOption) => {
            if (anOption.mandatory && cmd.getOptionValue(anOption.attributeName()) === void 0) {
              cmd.missingMandatoryOptionValue(anOption);
            }
          });
        });
      }
      /**
       * Display an error message if conflicting options are used together in this.
       *
       * @api private
       */
      _checkForConflictingLocalOptions() {
        const definedNonDefaultOptions = this.options.filter(
          (option) => {
            const optionKey = option.attributeName();
            if (this.getOptionValue(optionKey) === void 0) {
              return false;
            }
            return this.getOptionValueSource(optionKey) !== "default";
          }
        );
        const optionsWithConflicting = definedNonDefaultOptions.filter(
          (option) => option.conflictsWith.length > 0
        );
        optionsWithConflicting.forEach((option) => {
          const conflictingAndDefined = definedNonDefaultOptions.find(
            (defined) => option.conflictsWith.includes(defined.attributeName())
          );
          if (conflictingAndDefined) {
            this._conflictingOption(option, conflictingAndDefined);
          }
        });
      }
      /**
       * Display an error message if conflicting options are used together.
       * Called after checking for help flags in leaf subcommand.
       *
       * @api private
       */
      _checkForConflictingOptions() {
        this._getCommandAndAncestors().forEach((cmd) => {
          cmd._checkForConflictingLocalOptions();
        });
      }
      /**
       * Parse options from `argv` removing known options,
       * and return argv split into operands and unknown arguments.
       *
       * Examples:
       *
       *     argv => operands, unknown
       *     --known kkk op => [op], []
       *     op --known kkk => [op], []
       *     sub --unknown uuu op => [sub], [--unknown uuu op]
       *     sub -- --unknown uuu op => [sub --unknown uuu op], []
       *
       * @param {String[]} argv
       * @return {{operands: String[], unknown: String[]}}
       */
      parseOptions(argv) {
        const operands = [];
        const unknown = [];
        let dest = operands;
        const args = argv.slice();
        function maybeOption(arg) {
          return arg.length > 1 && arg[0] === "-";
        }
        let activeVariadicOption = null;
        while (args.length) {
          const arg = args.shift();
          if (arg === "--") {
            if (dest === unknown) dest.push(arg);
            dest.push(...args);
            break;
          }
          if (activeVariadicOption && !maybeOption(arg)) {
            this.emit(`option:${activeVariadicOption.name()}`, arg);
            continue;
          }
          activeVariadicOption = null;
          if (maybeOption(arg)) {
            const option = this._findOption(arg);
            if (option) {
              if (option.required) {
                const value = args.shift();
                if (value === void 0) this.optionMissingArgument(option);
                this.emit(`option:${option.name()}`, value);
              } else if (option.optional) {
                let value = null;
                if (args.length > 0 && !maybeOption(args[0])) {
                  value = args.shift();
                }
                this.emit(`option:${option.name()}`, value);
              } else {
                this.emit(`option:${option.name()}`);
              }
              activeVariadicOption = option.variadic ? option : null;
              continue;
            }
          }
          if (arg.length > 2 && arg[0] === "-" && arg[1] !== "-") {
            const option = this._findOption(`-${arg[1]}`);
            if (option) {
              if (option.required || option.optional && this._combineFlagAndOptionalValue) {
                this.emit(`option:${option.name()}`, arg.slice(2));
              } else {
                this.emit(`option:${option.name()}`);
                args.unshift(`-${arg.slice(2)}`);
              }
              continue;
            }
          }
          if (/^--[^=]+=/.test(arg)) {
            const index = arg.indexOf("=");
            const option = this._findOption(arg.slice(0, index));
            if (option && (option.required || option.optional)) {
              this.emit(`option:${option.name()}`, arg.slice(index + 1));
              continue;
            }
          }
          if (maybeOption(arg)) {
            dest = unknown;
          }
          if ((this._enablePositionalOptions || this._passThroughOptions) && operands.length === 0 && unknown.length === 0) {
            if (this._findCommand(arg)) {
              operands.push(arg);
              if (args.length > 0) unknown.push(...args);
              break;
            } else if (arg === this._helpCommandName && this._hasImplicitHelpCommand()) {
              operands.push(arg);
              if (args.length > 0) operands.push(...args);
              break;
            } else if (this._defaultCommandName) {
              unknown.push(arg);
              if (args.length > 0) unknown.push(...args);
              break;
            }
          }
          if (this._passThroughOptions) {
            dest.push(arg);
            if (args.length > 0) dest.push(...args);
            break;
          }
          dest.push(arg);
        }
        return { operands, unknown };
      }
      /**
       * Return an object containing local option values as key-value pairs.
       *
       * @return {Object}
       */
      opts() {
        if (this._storeOptionsAsProperties) {
          const result = {};
          const len = this.options.length;
          for (let i = 0; i < len; i++) {
            const key = this.options[i].attributeName();
            result[key] = key === this._versionOptionName ? this._version : this[key];
          }
          return result;
        }
        return this._optionValues;
      }
      /**
       * Return an object containing merged local and global option values as key-value pairs.
       *
       * @return {Object}
       */
      optsWithGlobals() {
        return this._getCommandAndAncestors().reduce(
          (combinedOptions, cmd) => Object.assign(combinedOptions, cmd.opts()),
          {}
        );
      }
      /**
       * Display error message and exit (or call exitOverride).
       *
       * @param {string} message
       * @param {Object} [errorOptions]
       * @param {string} [errorOptions.code] - an id string representing the error
       * @param {number} [errorOptions.exitCode] - used with process.exit
       */
      error(message, errorOptions) {
        this._outputConfiguration.outputError(`${message}
`, this._outputConfiguration.writeErr);
        if (typeof this._showHelpAfterError === "string") {
          this._outputConfiguration.writeErr(`${this._showHelpAfterError}
`);
        } else if (this._showHelpAfterError) {
          this._outputConfiguration.writeErr("\n");
          this.outputHelp({ error: true });
        }
        const config = errorOptions || {};
        const exitCode = config.exitCode || 1;
        const code = config.code || "commander.error";
        this._exit(exitCode, code, message);
      }
      /**
       * Apply any option related environment variables, if option does
       * not have a value from cli or client code.
       *
       * @api private
       */
      _parseOptionsEnv() {
        this.options.forEach((option) => {
          if (option.envVar && option.envVar in process2.env) {
            const optionKey = option.attributeName();
            if (this.getOptionValue(optionKey) === void 0 || ["default", "config", "env"].includes(this.getOptionValueSource(optionKey))) {
              if (option.required || option.optional) {
                this.emit(`optionEnv:${option.name()}`, process2.env[option.envVar]);
              } else {
                this.emit(`optionEnv:${option.name()}`);
              }
            }
          }
        });
      }
      /**
       * Apply any implied option values, if option is undefined or default value.
       *
       * @api private
       */
      _parseOptionsImplied() {
        const dualHelper = new DualOptions(this.options);
        const hasCustomOptionValue = (optionKey) => {
          return this.getOptionValue(optionKey) !== void 0 && !["default", "implied"].includes(this.getOptionValueSource(optionKey));
        };
        this.options.filter((option) => option.implied !== void 0 && hasCustomOptionValue(option.attributeName()) && dualHelper.valueFromOption(this.getOptionValue(option.attributeName()), option)).forEach((option) => {
          Object.keys(option.implied).filter((impliedKey) => !hasCustomOptionValue(impliedKey)).forEach((impliedKey) => {
            this.setOptionValueWithSource(impliedKey, option.implied[impliedKey], "implied");
          });
        });
      }
      /**
       * Argument `name` is missing.
       *
       * @param {string} name
       * @api private
       */
      missingArgument(name) {
        const message = `error: missing required argument '${name}'`;
        this.error(message, { code: "commander.missingArgument" });
      }
      /**
       * `Option` is missing an argument.
       *
       * @param {Option} option
       * @api private
       */
      optionMissingArgument(option) {
        const message = `error: option '${option.flags}' argument missing`;
        this.error(message, { code: "commander.optionMissingArgument" });
      }
      /**
       * `Option` does not have a value, and is a mandatory option.
       *
       * @param {Option} option
       * @api private
       */
      missingMandatoryOptionValue(option) {
        const message = `error: required option '${option.flags}' not specified`;
        this.error(message, { code: "commander.missingMandatoryOptionValue" });
      }
      /**
       * `Option` conflicts with another option.
       *
       * @param {Option} option
       * @param {Option} conflictingOption
       * @api private
       */
      _conflictingOption(option, conflictingOption) {
        const findBestOptionFromValue = (option2) => {
          const optionKey = option2.attributeName();
          const optionValue = this.getOptionValue(optionKey);
          const negativeOption = this.options.find((target) => target.negate && optionKey === target.attributeName());
          const positiveOption = this.options.find((target) => !target.negate && optionKey === target.attributeName());
          if (negativeOption && (negativeOption.presetArg === void 0 && optionValue === false || negativeOption.presetArg !== void 0 && optionValue === negativeOption.presetArg)) {
            return negativeOption;
          }
          return positiveOption || option2;
        };
        const getErrorMessage = (option2) => {
          const bestOption = findBestOptionFromValue(option2);
          const optionKey = bestOption.attributeName();
          const source = this.getOptionValueSource(optionKey);
          if (source === "env") {
            return `environment variable '${bestOption.envVar}'`;
          }
          return `option '${bestOption.flags}'`;
        };
        const message = `error: ${getErrorMessage(option)} cannot be used with ${getErrorMessage(conflictingOption)}`;
        this.error(message, { code: "commander.conflictingOption" });
      }
      /**
       * Unknown option `flag`.
       *
       * @param {string} flag
       * @api private
       */
      unknownOption(flag) {
        if (this._allowUnknownOption) return;
        let suggestion = "";
        if (flag.startsWith("--") && this._showSuggestionAfterError) {
          let candidateFlags = [];
          let command = this;
          do {
            const moreFlags = command.createHelp().visibleOptions(command).filter((option) => option.long).map((option) => option.long);
            candidateFlags = candidateFlags.concat(moreFlags);
            command = command.parent;
          } while (command && !command._enablePositionalOptions);
          suggestion = suggestSimilar(flag, candidateFlags);
        }
        const message = `error: unknown option '${flag}'${suggestion}`;
        this.error(message, { code: "commander.unknownOption" });
      }
      /**
       * Excess arguments, more than expected.
       *
       * @param {string[]} receivedArgs
       * @api private
       */
      _excessArguments(receivedArgs) {
        if (this._allowExcessArguments) return;
        const expected = this.registeredArguments.length;
        const s = expected === 1 ? "" : "s";
        const forSubcommand = this.parent ? ` for '${this.name()}'` : "";
        const message = `error: too many arguments${forSubcommand}. Expected ${expected} argument${s} but got ${receivedArgs.length}.`;
        this.error(message, { code: "commander.excessArguments" });
      }
      /**
       * Unknown command.
       *
       * @api private
       */
      unknownCommand() {
        const unknownName = this.args[0];
        let suggestion = "";
        if (this._showSuggestionAfterError) {
          const candidateNames = [];
          this.createHelp().visibleCommands(this).forEach((command) => {
            candidateNames.push(command.name());
            if (command.alias()) candidateNames.push(command.alias());
          });
          suggestion = suggestSimilar(unknownName, candidateNames);
        }
        const message = `error: unknown command '${unknownName}'${suggestion}`;
        this.error(message, { code: "commander.unknownCommand" });
      }
      /**
       * Get or set the program version.
       *
       * This method auto-registers the "-V, --version" option which will print the version number.
       *
       * You can optionally supply the flags and description to override the defaults.
       *
       * @param {string} [str]
       * @param {string} [flags]
       * @param {string} [description]
       * @return {this | string | undefined} `this` command for chaining, or version string if no arguments
       */
      version(str, flags, description) {
        if (str === void 0) return this._version;
        this._version = str;
        flags = flags || "-V, --version";
        description = description || "output the version number";
        const versionOption = this.createOption(flags, description);
        this._versionOptionName = versionOption.attributeName();
        this.options.push(versionOption);
        this.on("option:" + versionOption.name(), () => {
          this._outputConfiguration.writeOut(`${str}
`);
          this._exit(0, "commander.version", str);
        });
        return this;
      }
      /**
       * Set the description.
       *
       * @param {string} [str]
       * @param {Object} [argsDescription]
       * @return {string|Command}
       */
      description(str, argsDescription) {
        if (str === void 0 && argsDescription === void 0) return this._description;
        this._description = str;
        if (argsDescription) {
          this._argsDescription = argsDescription;
        }
        return this;
      }
      /**
       * Set the summary. Used when listed as subcommand of parent.
       *
       * @param {string} [str]
       * @return {string|Command}
       */
      summary(str) {
        if (str === void 0) return this._summary;
        this._summary = str;
        return this;
      }
      /**
       * Set an alias for the command.
       *
       * You may call more than once to add multiple aliases. Only the first alias is shown in the auto-generated help.
       *
       * @param {string} [alias]
       * @return {string|Command}
       */
      alias(alias) {
        if (alias === void 0) return this._aliases[0];
        let command = this;
        if (this.commands.length !== 0 && this.commands[this.commands.length - 1]._executableHandler) {
          command = this.commands[this.commands.length - 1];
        }
        if (alias === command._name) throw new Error("Command alias can't be the same as its name");
        command._aliases.push(alias);
        return this;
      }
      /**
       * Set aliases for the command.
       *
       * Only the first alias is shown in the auto-generated help.
       *
       * @param {string[]} [aliases]
       * @return {string[]|Command}
       */
      aliases(aliases) {
        if (aliases === void 0) return this._aliases;
        aliases.forEach((alias) => this.alias(alias));
        return this;
      }
      /**
       * Set / get the command usage `str`.
       *
       * @param {string} [str]
       * @return {String|Command}
       */
      usage(str) {
        if (str === void 0) {
          if (this._usage) return this._usage;
          const args = this.registeredArguments.map((arg) => {
            return humanReadableArgName(arg);
          });
          return [].concat(
            this.options.length || this._hasHelpOption ? "[options]" : [],
            this.commands.length ? "[command]" : [],
            this.registeredArguments.length ? args : []
          ).join(" ");
        }
        this._usage = str;
        return this;
      }
      /**
       * Get or set the name of the command.
       *
       * @param {string} [str]
       * @return {string|Command}
       */
      name(str) {
        if (str === void 0) return this._name;
        this._name = str;
        return this;
      }
      /**
       * Set the name of the command from script filename, such as process.argv[1],
       * or require.main.filename, or __filename.
       *
       * (Used internally and public although not documented in README.)
       *
       * @example
       * program.nameFromFilename(require.main.filename);
       *
       * @param {string} filename
       * @return {Command}
       */
      nameFromFilename(filename) {
        this._name = path2.basename(filename, path2.extname(filename));
        return this;
      }
      /**
       * Get or set the directory for searching for executable subcommands of this command.
       *
       * @example
       * program.executableDir(__dirname);
       * // or
       * program.executableDir('subcommands');
       *
       * @param {string} [path]
       * @return {string|null|Command}
       */
      executableDir(path3) {
        if (path3 === void 0) return this._executableDir;
        this._executableDir = path3;
        return this;
      }
      /**
       * Return program help documentation.
       *
       * @param {{ error: boolean }} [contextOptions] - pass {error:true} to wrap for stderr instead of stdout
       * @return {string}
       */
      helpInformation(contextOptions) {
        const helper = this.createHelp();
        if (helper.helpWidth === void 0) {
          helper.helpWidth = contextOptions && contextOptions.error ? this._outputConfiguration.getErrHelpWidth() : this._outputConfiguration.getOutHelpWidth();
        }
        return helper.formatHelp(this, helper);
      }
      /**
       * @api private
       */
      _getHelpContext(contextOptions) {
        contextOptions = contextOptions || {};
        const context = { error: !!contextOptions.error };
        let write;
        if (context.error) {
          write = (arg) => this._outputConfiguration.writeErr(arg);
        } else {
          write = (arg) => this._outputConfiguration.writeOut(arg);
        }
        context.write = contextOptions.write || write;
        context.command = this;
        return context;
      }
      /**
       * Output help information for this command.
       *
       * Outputs built-in help, and custom text added using `.addHelpText()`.
       *
       * @param {{ error: boolean } | Function} [contextOptions] - pass {error:true} to write to stderr instead of stdout
       */
      outputHelp(contextOptions) {
        let deprecatedCallback;
        if (typeof contextOptions === "function") {
          deprecatedCallback = contextOptions;
          contextOptions = void 0;
        }
        const context = this._getHelpContext(contextOptions);
        this._getCommandAndAncestors().reverse().forEach((command) => command.emit("beforeAllHelp", context));
        this.emit("beforeHelp", context);
        let helpInformation = this.helpInformation(context);
        if (deprecatedCallback) {
          helpInformation = deprecatedCallback(helpInformation);
          if (typeof helpInformation !== "string" && !Buffer.isBuffer(helpInformation)) {
            throw new Error("outputHelp callback must return a string or a Buffer");
          }
        }
        context.write(helpInformation);
        if (this._helpLongFlag) {
          this.emit(this._helpLongFlag);
        }
        this.emit("afterHelp", context);
        this._getCommandAndAncestors().forEach((command) => command.emit("afterAllHelp", context));
      }
      /**
       * You can pass in flags and a description to override the help
       * flags and help description for your command. Pass in false to
       * disable the built-in help option.
       *
       * @param {string | boolean} [flags]
       * @param {string} [description]
       * @return {Command} `this` command for chaining
       */
      helpOption(flags, description) {
        if (typeof flags === "boolean") {
          this._hasHelpOption = flags;
          return this;
        }
        this._helpFlags = flags || this._helpFlags;
        this._helpDescription = description || this._helpDescription;
        const helpFlags = splitOptionFlags(this._helpFlags);
        this._helpShortFlag = helpFlags.shortFlag;
        this._helpLongFlag = helpFlags.longFlag;
        return this;
      }
      /**
       * Output help information and exit.
       *
       * Outputs built-in help, and custom text added using `.addHelpText()`.
       *
       * @param {{ error: boolean }} [contextOptions] - pass {error:true} to write to stderr instead of stdout
       */
      help(contextOptions) {
        this.outputHelp(contextOptions);
        let exitCode = process2.exitCode || 0;
        if (exitCode === 0 && contextOptions && typeof contextOptions !== "function" && contextOptions.error) {
          exitCode = 1;
        }
        this._exit(exitCode, "commander.help", "(outputHelp)");
      }
      /**
       * Add additional text to be displayed with the built-in help.
       *
       * Position is 'before' or 'after' to affect just this command,
       * and 'beforeAll' or 'afterAll' to affect this command and all its subcommands.
       *
       * @param {string} position - before or after built-in help
       * @param {string | Function} text - string to add, or a function returning a string
       * @return {Command} `this` command for chaining
       */
      addHelpText(position, text) {
        const allowedValues = ["beforeAll", "before", "after", "afterAll"];
        if (!allowedValues.includes(position)) {
          throw new Error(`Unexpected value for position to addHelpText.
Expecting one of '${allowedValues.join("', '")}'`);
        }
        const helpEvent = `${position}Help`;
        this.on(helpEvent, (context) => {
          let helpStr;
          if (typeof text === "function") {
            helpStr = text({ error: context.error, command: context.command });
          } else {
            helpStr = text;
          }
          if (helpStr) {
            context.write(`${helpStr}
`);
          }
        });
        return this;
      }
    };
    function outputHelpIfRequested(cmd, args) {
      const helpOption = cmd._hasHelpOption && args.find((arg) => arg === cmd._helpLongFlag || arg === cmd._helpShortFlag);
      if (helpOption) {
        cmd.outputHelp();
        cmd._exit(0, "commander.helpDisplayed", "(outputHelp)");
      }
    }
    function incrementNodeInspectorPort(args) {
      return args.map((arg) => {
        if (!arg.startsWith("--inspect")) {
          return arg;
        }
        let debugOption;
        let debugHost = "127.0.0.1";
        let debugPort = "9229";
        let match;
        if ((match = arg.match(/^(--inspect(-brk)?)$/)) !== null) {
          debugOption = match[1];
        } else if ((match = arg.match(/^(--inspect(-brk|-port)?)=([^:]+)$/)) !== null) {
          debugOption = match[1];
          if (/^\d+$/.test(match[3])) {
            debugPort = match[3];
          } else {
            debugHost = match[3];
          }
        } else if ((match = arg.match(/^(--inspect(-brk|-port)?)=([^:]+):(\d+)$/)) !== null) {
          debugOption = match[1];
          debugHost = match[3];
          debugPort = match[4];
        }
        if (debugOption && debugPort !== "0") {
          return `${debugOption}=${debugHost}:${parseInt(debugPort) + 1}`;
        }
        return arg;
      });
    }
    exports2.Command = Command;
  }
});

// node_modules/commander/index.js
var require_commander = __commonJS({
  "node_modules/commander/index.js"(exports2, module2) {
    var { Argument } = require_argument();
    var { Command } = require_command();
    var { CommanderError, InvalidArgumentError } = require_error();
    var { Help } = require_help();
    var { Option } = require_option();
    exports2 = module2.exports = new Command();
    exports2.program = exports2;
    exports2.Command = Command;
    exports2.Option = Option;
    exports2.Argument = Argument;
    exports2.Help = Help;
    exports2.CommanderError = CommanderError;
    exports2.InvalidArgumentError = InvalidArgumentError;
    exports2.InvalidOptionArgumentError = InvalidArgumentError;
  }
});

// dist/models/MigrationState.js
var require_MigrationState = __commonJS({
  "dist/models/MigrationState.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.MigrationStateManager = void 0;
    var MigrationStateManager = class {
      static create(params) {
        const now = (/* @__PURE__ */ new Date()).toISOString();
        const migrationId = `migration_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        return {
          id: migrationId,
          fromModel: params.fromModel,
          toModel: params.toModel,
          projectId: params.projectId,
          status: "pending",
          startedAt: now,
          steps: this.getDefaultSteps(params.fromModel, params.toModel),
          backup: {
            id: `backup_${migrationId}`,
            path: params.backupPath,
            createdAt: now,
            size: 0,
            checksum: "",
            files: []
          },
          metadata: {
            version: "0.1.0",
            dryRun: params.dryRun || false,
            preserveHistory: true,
            userConfirmation: false,
            automaticRollback: true,
            skipValidation: false,
            customSettings: {}
          }
        };
      }
      static getDefaultSteps(fromModel, toModel) {
        const baseSteps = [
          {
            name: "validate_project",
            description: "Validate project configuration and structure",
            status: "pending",
            order: 1,
            requiredFiles: [".specify/config.json"],
            outputFiles: []
          },
          {
            name: "create_backup",
            description: "Create backup of current project state",
            status: "pending",
            order: 2,
            requiredFiles: [],
            outputFiles: []
          },
          {
            name: "update_config",
            description: `Update AI model from ${fromModel} to ${toModel}`,
            status: "pending",
            order: 3,
            requiredFiles: [".specify/config.json"],
            outputFiles: [".specify/config.json"]
          },
          {
            name: "migrate_specs",
            description: "Migrate specification files to new model format",
            status: "pending",
            order: 4,
            requiredFiles: [],
            outputFiles: []
          },
          {
            name: "update_tasks",
            description: "Update task tracking configuration",
            status: "pending",
            order: 5,
            requiredFiles: [],
            outputFiles: []
          },
          {
            name: "validate_migration",
            description: "Validate migration success and functionality",
            status: "pending",
            order: 6,
            requiredFiles: [],
            outputFiles: []
          }
        ];
        return baseSteps.map((step, index) => ({
          ...step,
          id: `step_${index + 1}_${step.name}`
        }));
      }
      static updateStep(migration, stepId, updates) {
        const steps = migration.steps.map((step) => step.id === stepId ? { ...step, ...updates } : step);
        return {
          ...migration,
          steps
        };
      }
      static startRollback(migration, reason) {
        return {
          ...migration,
          status: "rolled_back",
          rollback: {
            triggeredAt: (/* @__PURE__ */ new Date()).toISOString(),
            reason,
            success: false,
            restoredFiles: []
          }
        };
      }
      static complete(migration, success) {
        const now = (/* @__PURE__ */ new Date()).toISOString();
        const duration = migration.startedAt ? new Date(now).getTime() - new Date(migration.startedAt).getTime() : 0;
        return {
          ...migration,
          status: success ? "completed" : "failed",
          completedAt: now,
          duration
        };
      }
      static canRollback(migration) {
        return migration.status !== "rolled_back" && migration.backup.files.length > 0 && migration.metadata.automaticRollback;
      }
    };
    exports2.MigrationStateManager = MigrationStateManager;
  }
});

// dist/models/AIModelSettings.js
var require_AIModelSettings = __commonJS({
  "dist/models/AIModelSettings.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.AIModelSettingsProvider = void 0;
    var AIModelSettingsProvider = class {
      static getSettings(modelType) {
        return this.MODEL_DEFINITIONS[modelType] || null;
      }
      static getAllModels() {
        return Object.values(this.MODEL_DEFINITIONS);
      }
      static isCompatible(modelType, cliVersion) {
        const settings = this.getSettings(modelType);
        if (!settings)
          return false;
        return cliVersion >= settings.compatibility.minimumCliVersion;
      }
    };
    exports2.AIModelSettingsProvider = AIModelSettingsProvider;
    AIModelSettingsProvider.MODEL_DEFINITIONS = {
      claude: {
        modelType: "claude",
        version: "3.0",
        capabilities: {
          maxTokens: 2e5,
          supportedFormats: ["text", "json", "markdown", "code"],
          features: [
            {
              name: "code-generation",
              enabled: true,
              description: "Generate and refactor code",
              requirements: ["typescript", "javascript"]
            },
            {
              name: "spec-analysis",
              enabled: true,
              description: "Analyze and validate specifications"
            },
            {
              name: "task-tracking",
              enabled: true,
              description: "Track and update task progress"
            }
          ],
          rateLimit: {
            requestsPerMinute: 60,
            tokensPerMinute: 1e5,
            dailyLimit: 1e6
          }
        },
        configuration: {
          temperature: 0.7,
          maxOutputTokens: 4096,
          customSettings: {}
        },
        compatibility: {
          supportedVersions: ["2.1", "3.0"],
          migrationSupport: true,
          minimumCliVersion: "0.1.0"
        }
      },
      gemini: {
        modelType: "gemini",
        version: "1.5",
        capabilities: {
          maxTokens: 1e5,
          supportedFormats: ["text", "json", "markdown"],
          features: [
            {
              name: "code-generation",
              enabled: true,
              description: "Generate and refactor code"
            },
            {
              name: "spec-analysis",
              enabled: true,
              description: "Analyze specifications"
            }
          ],
          rateLimit: {
            requestsPerMinute: 30,
            tokensPerMinute: 5e4
          }
        },
        configuration: {
          temperature: 0.8,
          maxOutputTokens: 2048,
          customSettings: {}
        },
        compatibility: {
          supportedVersions: ["1.0", "1.5"],
          migrationSupport: true,
          minimumCliVersion: "0.1.0"
        }
      },
      copilot: {
        modelType: "copilot",
        version: "1.0",
        capabilities: {
          maxTokens: 8e3,
          supportedFormats: ["text", "code"],
          features: [
            {
              name: "code-generation",
              enabled: true,
              description: "AI-powered code completion and generation",
              requirements: ["github-copilot-extension"]
            },
            {
              name: "code-explanation",
              enabled: true,
              description: "Explain existing code"
            },
            {
              name: "refactoring",
              enabled: true,
              description: "Suggest code improvements"
            }
          ],
          rateLimit: {
            requestsPerMinute: 100,
            tokensPerMinute: 2e5
          }
        },
        configuration: {
          temperature: 0.6,
          maxOutputTokens: 1024,
          customSettings: {}
        },
        compatibility: {
          supportedVersions: ["1.0"],
          migrationSupport: true,
          minimumCliVersion: "0.1.0"
        }
      }
    };
  }
});

// node_modules/universalify/index.js
var require_universalify = __commonJS({
  "node_modules/universalify/index.js"(exports2) {
    "use strict";
    exports2.fromCallback = function(fn) {
      return Object.defineProperty(function(...args) {
        if (typeof args[args.length - 1] === "function") fn.apply(this, args);
        else {
          return new Promise((resolve, reject) => {
            args.push((err, res) => err != null ? reject(err) : resolve(res));
            fn.apply(this, args);
          });
        }
      }, "name", { value: fn.name });
    };
    exports2.fromPromise = function(fn) {
      return Object.defineProperty(function(...args) {
        const cb = args[args.length - 1];
        if (typeof cb !== "function") return fn.apply(this, args);
        else {
          args.pop();
          fn.apply(this, args).then((r) => cb(null, r), cb);
        }
      }, "name", { value: fn.name });
    };
  }
});

// node_modules/graceful-fs/polyfills.js
var require_polyfills = __commonJS({
  "node_modules/graceful-fs/polyfills.js"(exports2, module2) {
    var constants = require("constants");
    var origCwd = process.cwd;
    var cwd = null;
    var platform = process.env.GRACEFUL_FS_PLATFORM || process.platform;
    process.cwd = function() {
      if (!cwd)
        cwd = origCwd.call(process);
      return cwd;
    };
    try {
      process.cwd();
    } catch (er) {
    }
    if (typeof process.chdir === "function") {
      chdir = process.chdir;
      process.chdir = function(d) {
        cwd = null;
        chdir.call(process, d);
      };
      if (Object.setPrototypeOf) Object.setPrototypeOf(process.chdir, chdir);
    }
    var chdir;
    module2.exports = patch;
    function patch(fs2) {
      if (constants.hasOwnProperty("O_SYMLINK") && process.version.match(/^v0\.6\.[0-2]|^v0\.5\./)) {
        patchLchmod(fs2);
      }
      if (!fs2.lutimes) {
        patchLutimes(fs2);
      }
      fs2.chown = chownFix(fs2.chown);
      fs2.fchown = chownFix(fs2.fchown);
      fs2.lchown = chownFix(fs2.lchown);
      fs2.chmod = chmodFix(fs2.chmod);
      fs2.fchmod = chmodFix(fs2.fchmod);
      fs2.lchmod = chmodFix(fs2.lchmod);
      fs2.chownSync = chownFixSync(fs2.chownSync);
      fs2.fchownSync = chownFixSync(fs2.fchownSync);
      fs2.lchownSync = chownFixSync(fs2.lchownSync);
      fs2.chmodSync = chmodFixSync(fs2.chmodSync);
      fs2.fchmodSync = chmodFixSync(fs2.fchmodSync);
      fs2.lchmodSync = chmodFixSync(fs2.lchmodSync);
      fs2.stat = statFix(fs2.stat);
      fs2.fstat = statFix(fs2.fstat);
      fs2.lstat = statFix(fs2.lstat);
      fs2.statSync = statFixSync(fs2.statSync);
      fs2.fstatSync = statFixSync(fs2.fstatSync);
      fs2.lstatSync = statFixSync(fs2.lstatSync);
      if (fs2.chmod && !fs2.lchmod) {
        fs2.lchmod = function(path2, mode, cb) {
          if (cb) process.nextTick(cb);
        };
        fs2.lchmodSync = function() {
        };
      }
      if (fs2.chown && !fs2.lchown) {
        fs2.lchown = function(path2, uid, gid, cb) {
          if (cb) process.nextTick(cb);
        };
        fs2.lchownSync = function() {
        };
      }
      if (platform === "win32") {
        fs2.rename = typeof fs2.rename !== "function" ? fs2.rename : (function(fs$rename) {
          function rename(from, to, cb) {
            var start = Date.now();
            var backoff = 0;
            fs$rename(from, to, function CB(er) {
              if (er && (er.code === "EACCES" || er.code === "EPERM" || er.code === "EBUSY") && Date.now() - start < 6e4) {
                setTimeout(function() {
                  fs2.stat(to, function(stater, st) {
                    if (stater && stater.code === "ENOENT")
                      fs$rename(from, to, CB);
                    else
                      cb(er);
                  });
                }, backoff);
                if (backoff < 100)
                  backoff += 10;
                return;
              }
              if (cb) cb(er);
            });
          }
          if (Object.setPrototypeOf) Object.setPrototypeOf(rename, fs$rename);
          return rename;
        })(fs2.rename);
      }
      fs2.read = typeof fs2.read !== "function" ? fs2.read : (function(fs$read) {
        function read(fd, buffer, offset, length, position, callback_) {
          var callback;
          if (callback_ && typeof callback_ === "function") {
            var eagCounter = 0;
            callback = function(er, _, __) {
              if (er && er.code === "EAGAIN" && eagCounter < 10) {
                eagCounter++;
                return fs$read.call(fs2, fd, buffer, offset, length, position, callback);
              }
              callback_.apply(this, arguments);
            };
          }
          return fs$read.call(fs2, fd, buffer, offset, length, position, callback);
        }
        if (Object.setPrototypeOf) Object.setPrototypeOf(read, fs$read);
        return read;
      })(fs2.read);
      fs2.readSync = typeof fs2.readSync !== "function" ? fs2.readSync : /* @__PURE__ */ (function(fs$readSync) {
        return function(fd, buffer, offset, length, position) {
          var eagCounter = 0;
          while (true) {
            try {
              return fs$readSync.call(fs2, fd, buffer, offset, length, position);
            } catch (er) {
              if (er.code === "EAGAIN" && eagCounter < 10) {
                eagCounter++;
                continue;
              }
              throw er;
            }
          }
        };
      })(fs2.readSync);
      function patchLchmod(fs3) {
        fs3.lchmod = function(path2, mode, callback) {
          fs3.open(
            path2,
            constants.O_WRONLY | constants.O_SYMLINK,
            mode,
            function(err, fd) {
              if (err) {
                if (callback) callback(err);
                return;
              }
              fs3.fchmod(fd, mode, function(err2) {
                fs3.close(fd, function(err22) {
                  if (callback) callback(err2 || err22);
                });
              });
            }
          );
        };
        fs3.lchmodSync = function(path2, mode) {
          var fd = fs3.openSync(path2, constants.O_WRONLY | constants.O_SYMLINK, mode);
          var threw = true;
          var ret;
          try {
            ret = fs3.fchmodSync(fd, mode);
            threw = false;
          } finally {
            if (threw) {
              try {
                fs3.closeSync(fd);
              } catch (er) {
              }
            } else {
              fs3.closeSync(fd);
            }
          }
          return ret;
        };
      }
      function patchLutimes(fs3) {
        if (constants.hasOwnProperty("O_SYMLINK") && fs3.futimes) {
          fs3.lutimes = function(path2, at, mt, cb) {
            fs3.open(path2, constants.O_SYMLINK, function(er, fd) {
              if (er) {
                if (cb) cb(er);
                return;
              }
              fs3.futimes(fd, at, mt, function(er2) {
                fs3.close(fd, function(er22) {
                  if (cb) cb(er2 || er22);
                });
              });
            });
          };
          fs3.lutimesSync = function(path2, at, mt) {
            var fd = fs3.openSync(path2, constants.O_SYMLINK);
            var ret;
            var threw = true;
            try {
              ret = fs3.futimesSync(fd, at, mt);
              threw = false;
            } finally {
              if (threw) {
                try {
                  fs3.closeSync(fd);
                } catch (er) {
                }
              } else {
                fs3.closeSync(fd);
              }
            }
            return ret;
          };
        } else if (fs3.futimes) {
          fs3.lutimes = function(_a, _b, _c, cb) {
            if (cb) process.nextTick(cb);
          };
          fs3.lutimesSync = function() {
          };
        }
      }
      function chmodFix(orig) {
        if (!orig) return orig;
        return function(target, mode, cb) {
          return orig.call(fs2, target, mode, function(er) {
            if (chownErOk(er)) er = null;
            if (cb) cb.apply(this, arguments);
          });
        };
      }
      function chmodFixSync(orig) {
        if (!orig) return orig;
        return function(target, mode) {
          try {
            return orig.call(fs2, target, mode);
          } catch (er) {
            if (!chownErOk(er)) throw er;
          }
        };
      }
      function chownFix(orig) {
        if (!orig) return orig;
        return function(target, uid, gid, cb) {
          return orig.call(fs2, target, uid, gid, function(er) {
            if (chownErOk(er)) er = null;
            if (cb) cb.apply(this, arguments);
          });
        };
      }
      function chownFixSync(orig) {
        if (!orig) return orig;
        return function(target, uid, gid) {
          try {
            return orig.call(fs2, target, uid, gid);
          } catch (er) {
            if (!chownErOk(er)) throw er;
          }
        };
      }
      function statFix(orig) {
        if (!orig) return orig;
        return function(target, options, cb) {
          if (typeof options === "function") {
            cb = options;
            options = null;
          }
          function callback(er, stats) {
            if (stats) {
              if (stats.uid < 0) stats.uid += 4294967296;
              if (stats.gid < 0) stats.gid += 4294967296;
            }
            if (cb) cb.apply(this, arguments);
          }
          return options ? orig.call(fs2, target, options, callback) : orig.call(fs2, target, callback);
        };
      }
      function statFixSync(orig) {
        if (!orig) return orig;
        return function(target, options) {
          var stats = options ? orig.call(fs2, target, options) : orig.call(fs2, target);
          if (stats) {
            if (stats.uid < 0) stats.uid += 4294967296;
            if (stats.gid < 0) stats.gid += 4294967296;
          }
          return stats;
        };
      }
      function chownErOk(er) {
        if (!er)
          return true;
        if (er.code === "ENOSYS")
          return true;
        var nonroot = !process.getuid || process.getuid() !== 0;
        if (nonroot) {
          if (er.code === "EINVAL" || er.code === "EPERM")
            return true;
        }
        return false;
      }
    }
  }
});

// node_modules/graceful-fs/legacy-streams.js
var require_legacy_streams = __commonJS({
  "node_modules/graceful-fs/legacy-streams.js"(exports2, module2) {
    var Stream = require("stream").Stream;
    module2.exports = legacy;
    function legacy(fs2) {
      return {
        ReadStream,
        WriteStream
      };
      function ReadStream(path2, options) {
        if (!(this instanceof ReadStream)) return new ReadStream(path2, options);
        Stream.call(this);
        var self = this;
        this.path = path2;
        this.fd = null;
        this.readable = true;
        this.paused = false;
        this.flags = "r";
        this.mode = 438;
        this.bufferSize = 64 * 1024;
        options = options || {};
        var keys = Object.keys(options);
        for (var index = 0, length = keys.length; index < length; index++) {
          var key = keys[index];
          this[key] = options[key];
        }
        if (this.encoding) this.setEncoding(this.encoding);
        if (this.start !== void 0) {
          if ("number" !== typeof this.start) {
            throw TypeError("start must be a Number");
          }
          if (this.end === void 0) {
            this.end = Infinity;
          } else if ("number" !== typeof this.end) {
            throw TypeError("end must be a Number");
          }
          if (this.start > this.end) {
            throw new Error("start must be <= end");
          }
          this.pos = this.start;
        }
        if (this.fd !== null) {
          process.nextTick(function() {
            self._read();
          });
          return;
        }
        fs2.open(this.path, this.flags, this.mode, function(err, fd) {
          if (err) {
            self.emit("error", err);
            self.readable = false;
            return;
          }
          self.fd = fd;
          self.emit("open", fd);
          self._read();
        });
      }
      function WriteStream(path2, options) {
        if (!(this instanceof WriteStream)) return new WriteStream(path2, options);
        Stream.call(this);
        this.path = path2;
        this.fd = null;
        this.writable = true;
        this.flags = "w";
        this.encoding = "binary";
        this.mode = 438;
        this.bytesWritten = 0;
        options = options || {};
        var keys = Object.keys(options);
        for (var index = 0, length = keys.length; index < length; index++) {
          var key = keys[index];
          this[key] = options[key];
        }
        if (this.start !== void 0) {
          if ("number" !== typeof this.start) {
            throw TypeError("start must be a Number");
          }
          if (this.start < 0) {
            throw new Error("start must be >= zero");
          }
          this.pos = this.start;
        }
        this.busy = false;
        this._queue = [];
        if (this.fd === null) {
          this._open = fs2.open;
          this._queue.push([this._open, this.path, this.flags, this.mode, void 0]);
          this.flush();
        }
      }
    }
  }
});

// node_modules/graceful-fs/clone.js
var require_clone = __commonJS({
  "node_modules/graceful-fs/clone.js"(exports2, module2) {
    "use strict";
    module2.exports = clone;
    var getPrototypeOf = Object.getPrototypeOf || function(obj) {
      return obj.__proto__;
    };
    function clone(obj) {
      if (obj === null || typeof obj !== "object")
        return obj;
      if (obj instanceof Object)
        var copy = { __proto__: getPrototypeOf(obj) };
      else
        var copy = /* @__PURE__ */ Object.create(null);
      Object.getOwnPropertyNames(obj).forEach(function(key) {
        Object.defineProperty(copy, key, Object.getOwnPropertyDescriptor(obj, key));
      });
      return copy;
    }
  }
});

// node_modules/graceful-fs/graceful-fs.js
var require_graceful_fs = __commonJS({
  "node_modules/graceful-fs/graceful-fs.js"(exports2, module2) {
    var fs2 = require("fs");
    var polyfills = require_polyfills();
    var legacy = require_legacy_streams();
    var clone = require_clone();
    var util = require("util");
    var gracefulQueue;
    var previousSymbol;
    if (typeof Symbol === "function" && typeof Symbol.for === "function") {
      gracefulQueue = Symbol.for("graceful-fs.queue");
      previousSymbol = Symbol.for("graceful-fs.previous");
    } else {
      gracefulQueue = "___graceful-fs.queue";
      previousSymbol = "___graceful-fs.previous";
    }
    function noop() {
    }
    function publishQueue(context, queue2) {
      Object.defineProperty(context, gracefulQueue, {
        get: function() {
          return queue2;
        }
      });
    }
    var debug = noop;
    if (util.debuglog)
      debug = util.debuglog("gfs4");
    else if (/\bgfs4\b/i.test(process.env.NODE_DEBUG || ""))
      debug = function() {
        var m = util.format.apply(util, arguments);
        m = "GFS4: " + m.split(/\n/).join("\nGFS4: ");
        console.error(m);
      };
    if (!fs2[gracefulQueue]) {
      queue = global[gracefulQueue] || [];
      publishQueue(fs2, queue);
      fs2.close = (function(fs$close) {
        function close(fd, cb) {
          return fs$close.call(fs2, fd, function(err) {
            if (!err) {
              resetQueue();
            }
            if (typeof cb === "function")
              cb.apply(this, arguments);
          });
        }
        Object.defineProperty(close, previousSymbol, {
          value: fs$close
        });
        return close;
      })(fs2.close);
      fs2.closeSync = (function(fs$closeSync) {
        function closeSync(fd) {
          fs$closeSync.apply(fs2, arguments);
          resetQueue();
        }
        Object.defineProperty(closeSync, previousSymbol, {
          value: fs$closeSync
        });
        return closeSync;
      })(fs2.closeSync);
      if (/\bgfs4\b/i.test(process.env.NODE_DEBUG || "")) {
        process.on("exit", function() {
          debug(fs2[gracefulQueue]);
          require("assert").equal(fs2[gracefulQueue].length, 0);
        });
      }
    }
    var queue;
    if (!global[gracefulQueue]) {
      publishQueue(global, fs2[gracefulQueue]);
    }
    module2.exports = patch(clone(fs2));
    if (process.env.TEST_GRACEFUL_FS_GLOBAL_PATCH && !fs2.__patched) {
      module2.exports = patch(fs2);
      fs2.__patched = true;
    }
    function patch(fs3) {
      polyfills(fs3);
      fs3.gracefulify = patch;
      fs3.createReadStream = createReadStream;
      fs3.createWriteStream = createWriteStream;
      var fs$readFile = fs3.readFile;
      fs3.readFile = readFile;
      function readFile(path2, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$readFile(path2, options, cb);
        function go$readFile(path3, options2, cb2, startTime) {
          return fs$readFile(path3, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$readFile, [path3, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$writeFile = fs3.writeFile;
      fs3.writeFile = writeFile;
      function writeFile(path2, data, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$writeFile(path2, data, options, cb);
        function go$writeFile(path3, data2, options2, cb2, startTime) {
          return fs$writeFile(path3, data2, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$writeFile, [path3, data2, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$appendFile = fs3.appendFile;
      if (fs$appendFile)
        fs3.appendFile = appendFile;
      function appendFile(path2, data, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        return go$appendFile(path2, data, options, cb);
        function go$appendFile(path3, data2, options2, cb2, startTime) {
          return fs$appendFile(path3, data2, options2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$appendFile, [path3, data2, options2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$copyFile = fs3.copyFile;
      if (fs$copyFile)
        fs3.copyFile = copyFile;
      function copyFile(src, dest, flags, cb) {
        if (typeof flags === "function") {
          cb = flags;
          flags = 0;
        }
        return go$copyFile(src, dest, flags, cb);
        function go$copyFile(src2, dest2, flags2, cb2, startTime) {
          return fs$copyFile(src2, dest2, flags2, function(err) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$copyFile, [src2, dest2, flags2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      var fs$readdir = fs3.readdir;
      fs3.readdir = readdir;
      var noReaddirOptionVersions = /^v[0-5]\./;
      function readdir(path2, options, cb) {
        if (typeof options === "function")
          cb = options, options = null;
        var go$readdir = noReaddirOptionVersions.test(process.version) ? function go$readdir2(path3, options2, cb2, startTime) {
          return fs$readdir(path3, fs$readdirCallback(
            path3,
            options2,
            cb2,
            startTime
          ));
        } : function go$readdir2(path3, options2, cb2, startTime) {
          return fs$readdir(path3, options2, fs$readdirCallback(
            path3,
            options2,
            cb2,
            startTime
          ));
        };
        return go$readdir(path2, options, cb);
        function fs$readdirCallback(path3, options2, cb2, startTime) {
          return function(err, files) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([
                go$readdir,
                [path3, options2, cb2],
                err,
                startTime || Date.now(),
                Date.now()
              ]);
            else {
              if (files && files.sort)
                files.sort();
              if (typeof cb2 === "function")
                cb2.call(this, err, files);
            }
          };
        }
      }
      if (process.version.substr(0, 4) === "v0.8") {
        var legStreams = legacy(fs3);
        ReadStream = legStreams.ReadStream;
        WriteStream = legStreams.WriteStream;
      }
      var fs$ReadStream = fs3.ReadStream;
      if (fs$ReadStream) {
        ReadStream.prototype = Object.create(fs$ReadStream.prototype);
        ReadStream.prototype.open = ReadStream$open;
      }
      var fs$WriteStream = fs3.WriteStream;
      if (fs$WriteStream) {
        WriteStream.prototype = Object.create(fs$WriteStream.prototype);
        WriteStream.prototype.open = WriteStream$open;
      }
      Object.defineProperty(fs3, "ReadStream", {
        get: function() {
          return ReadStream;
        },
        set: function(val) {
          ReadStream = val;
        },
        enumerable: true,
        configurable: true
      });
      Object.defineProperty(fs3, "WriteStream", {
        get: function() {
          return WriteStream;
        },
        set: function(val) {
          WriteStream = val;
        },
        enumerable: true,
        configurable: true
      });
      var FileReadStream = ReadStream;
      Object.defineProperty(fs3, "FileReadStream", {
        get: function() {
          return FileReadStream;
        },
        set: function(val) {
          FileReadStream = val;
        },
        enumerable: true,
        configurable: true
      });
      var FileWriteStream = WriteStream;
      Object.defineProperty(fs3, "FileWriteStream", {
        get: function() {
          return FileWriteStream;
        },
        set: function(val) {
          FileWriteStream = val;
        },
        enumerable: true,
        configurable: true
      });
      function ReadStream(path2, options) {
        if (this instanceof ReadStream)
          return fs$ReadStream.apply(this, arguments), this;
        else
          return ReadStream.apply(Object.create(ReadStream.prototype), arguments);
      }
      function ReadStream$open() {
        var that = this;
        open(that.path, that.flags, that.mode, function(err, fd) {
          if (err) {
            if (that.autoClose)
              that.destroy();
            that.emit("error", err);
          } else {
            that.fd = fd;
            that.emit("open", fd);
            that.read();
          }
        });
      }
      function WriteStream(path2, options) {
        if (this instanceof WriteStream)
          return fs$WriteStream.apply(this, arguments), this;
        else
          return WriteStream.apply(Object.create(WriteStream.prototype), arguments);
      }
      function WriteStream$open() {
        var that = this;
        open(that.path, that.flags, that.mode, function(err, fd) {
          if (err) {
            that.destroy();
            that.emit("error", err);
          } else {
            that.fd = fd;
            that.emit("open", fd);
          }
        });
      }
      function createReadStream(path2, options) {
        return new fs3.ReadStream(path2, options);
      }
      function createWriteStream(path2, options) {
        return new fs3.WriteStream(path2, options);
      }
      var fs$open = fs3.open;
      fs3.open = open;
      function open(path2, flags, mode, cb) {
        if (typeof mode === "function")
          cb = mode, mode = null;
        return go$open(path2, flags, mode, cb);
        function go$open(path3, flags2, mode2, cb2, startTime) {
          return fs$open(path3, flags2, mode2, function(err, fd) {
            if (err && (err.code === "EMFILE" || err.code === "ENFILE"))
              enqueue([go$open, [path3, flags2, mode2, cb2], err, startTime || Date.now(), Date.now()]);
            else {
              if (typeof cb2 === "function")
                cb2.apply(this, arguments);
            }
          });
        }
      }
      return fs3;
    }
    function enqueue(elem) {
      debug("ENQUEUE", elem[0].name, elem[1]);
      fs2[gracefulQueue].push(elem);
      retry();
    }
    var retryTimer;
    function resetQueue() {
      var now = Date.now();
      for (var i = 0; i < fs2[gracefulQueue].length; ++i) {
        if (fs2[gracefulQueue][i].length > 2) {
          fs2[gracefulQueue][i][3] = now;
          fs2[gracefulQueue][i][4] = now;
        }
      }
      retry();
    }
    function retry() {
      clearTimeout(retryTimer);
      retryTimer = void 0;
      if (fs2[gracefulQueue].length === 0)
        return;
      var elem = fs2[gracefulQueue].shift();
      var fn = elem[0];
      var args = elem[1];
      var err = elem[2];
      var startTime = elem[3];
      var lastTime = elem[4];
      if (startTime === void 0) {
        debug("RETRY", fn.name, args);
        fn.apply(null, args);
      } else if (Date.now() - startTime >= 6e4) {
        debug("TIMEOUT", fn.name, args);
        var cb = args.pop();
        if (typeof cb === "function")
          cb.call(null, err);
      } else {
        var sinceAttempt = Date.now() - lastTime;
        var sinceStart = Math.max(lastTime - startTime, 1);
        var desiredDelay = Math.min(sinceStart * 1.2, 100);
        if (sinceAttempt >= desiredDelay) {
          debug("RETRY", fn.name, args);
          fn.apply(null, args.concat([startTime]));
        } else {
          fs2[gracefulQueue].push(elem);
        }
      }
      if (retryTimer === void 0) {
        retryTimer = setTimeout(retry, 0);
      }
    }
  }
});

// node_modules/fs-extra/lib/fs/index.js
var require_fs = __commonJS({
  "node_modules/fs-extra/lib/fs/index.js"(exports2) {
    "use strict";
    var u = require_universalify().fromCallback;
    var fs2 = require_graceful_fs();
    var api = [
      "access",
      "appendFile",
      "chmod",
      "chown",
      "close",
      "copyFile",
      "cp",
      "fchmod",
      "fchown",
      "fdatasync",
      "fstat",
      "fsync",
      "ftruncate",
      "futimes",
      "glob",
      "lchmod",
      "lchown",
      "lutimes",
      "link",
      "lstat",
      "mkdir",
      "mkdtemp",
      "open",
      "opendir",
      "readdir",
      "readFile",
      "readlink",
      "realpath",
      "rename",
      "rm",
      "rmdir",
      "stat",
      "statfs",
      "symlink",
      "truncate",
      "unlink",
      "utimes",
      "writeFile"
    ].filter((key) => {
      return typeof fs2[key] === "function";
    });
    Object.assign(exports2, fs2);
    api.forEach((method) => {
      exports2[method] = u(fs2[method]);
    });
    exports2.exists = function(filename, callback) {
      if (typeof callback === "function") {
        return fs2.exists(filename, callback);
      }
      return new Promise((resolve) => {
        return fs2.exists(filename, resolve);
      });
    };
    exports2.read = function(fd, buffer, offset, length, position, callback) {
      if (typeof callback === "function") {
        return fs2.read(fd, buffer, offset, length, position, callback);
      }
      return new Promise((resolve, reject) => {
        fs2.read(fd, buffer, offset, length, position, (err, bytesRead, buffer2) => {
          if (err) return reject(err);
          resolve({ bytesRead, buffer: buffer2 });
        });
      });
    };
    exports2.write = function(fd, buffer, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs2.write(fd, buffer, ...args);
      }
      return new Promise((resolve, reject) => {
        fs2.write(fd, buffer, ...args, (err, bytesWritten, buffer2) => {
          if (err) return reject(err);
          resolve({ bytesWritten, buffer: buffer2 });
        });
      });
    };
    exports2.readv = function(fd, buffers, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs2.readv(fd, buffers, ...args);
      }
      return new Promise((resolve, reject) => {
        fs2.readv(fd, buffers, ...args, (err, bytesRead, buffers2) => {
          if (err) return reject(err);
          resolve({ bytesRead, buffers: buffers2 });
        });
      });
    };
    exports2.writev = function(fd, buffers, ...args) {
      if (typeof args[args.length - 1] === "function") {
        return fs2.writev(fd, buffers, ...args);
      }
      return new Promise((resolve, reject) => {
        fs2.writev(fd, buffers, ...args, (err, bytesWritten, buffers2) => {
          if (err) return reject(err);
          resolve({ bytesWritten, buffers: buffers2 });
        });
      });
    };
    if (typeof fs2.realpath.native === "function") {
      exports2.realpath.native = u(fs2.realpath.native);
    } else {
      process.emitWarning(
        "fs.realpath.native is not a function. Is fs being monkey-patched?",
        "Warning",
        "fs-extra-WARN0003"
      );
    }
  }
});

// node_modules/fs-extra/lib/mkdirs/utils.js
var require_utils = __commonJS({
  "node_modules/fs-extra/lib/mkdirs/utils.js"(exports2, module2) {
    "use strict";
    var path2 = require("path");
    module2.exports.checkPath = function checkPath(pth) {
      if (process.platform === "win32") {
        const pathHasInvalidWinCharacters = /[<>:"|?*]/.test(pth.replace(path2.parse(pth).root, ""));
        if (pathHasInvalidWinCharacters) {
          const error = new Error(`Path contains invalid characters: ${pth}`);
          error.code = "EINVAL";
          throw error;
        }
      }
    };
  }
});

// node_modules/fs-extra/lib/mkdirs/make-dir.js
var require_make_dir = __commonJS({
  "node_modules/fs-extra/lib/mkdirs/make-dir.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var { checkPath } = require_utils();
    var getMode = (options) => {
      const defaults = { mode: 511 };
      if (typeof options === "number") return options;
      return { ...defaults, ...options }.mode;
    };
    module2.exports.makeDir = async (dir, options) => {
      checkPath(dir);
      return fs2.mkdir(dir, {
        mode: getMode(options),
        recursive: true
      });
    };
    module2.exports.makeDirSync = (dir, options) => {
      checkPath(dir);
      return fs2.mkdirSync(dir, {
        mode: getMode(options),
        recursive: true
      });
    };
  }
});

// node_modules/fs-extra/lib/mkdirs/index.js
var require_mkdirs = __commonJS({
  "node_modules/fs-extra/lib/mkdirs/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var { makeDir: _makeDir, makeDirSync } = require_make_dir();
    var makeDir = u(_makeDir);
    module2.exports = {
      mkdirs: makeDir,
      mkdirsSync: makeDirSync,
      // alias
      mkdirp: makeDir,
      mkdirpSync: makeDirSync,
      ensureDir: makeDir,
      ensureDirSync: makeDirSync
    };
  }
});

// node_modules/fs-extra/lib/path-exists/index.js
var require_path_exists = __commonJS({
  "node_modules/fs-extra/lib/path-exists/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var fs2 = require_fs();
    function pathExists(path2) {
      return fs2.access(path2).then(() => true).catch(() => false);
    }
    module2.exports = {
      pathExists: u(pathExists),
      pathExistsSync: fs2.existsSync
    };
  }
});

// node_modules/fs-extra/lib/util/utimes.js
var require_utimes = __commonJS({
  "node_modules/fs-extra/lib/util/utimes.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var u = require_universalify().fromPromise;
    async function utimesMillis(path2, atime, mtime) {
      const fd = await fs2.open(path2, "r+");
      let closeErr = null;
      try {
        await fs2.futimes(fd, atime, mtime);
      } finally {
        try {
          await fs2.close(fd);
        } catch (e) {
          closeErr = e;
        }
      }
      if (closeErr) {
        throw closeErr;
      }
    }
    function utimesMillisSync(path2, atime, mtime) {
      const fd = fs2.openSync(path2, "r+");
      fs2.futimesSync(fd, atime, mtime);
      return fs2.closeSync(fd);
    }
    module2.exports = {
      utimesMillis: u(utimesMillis),
      utimesMillisSync
    };
  }
});

// node_modules/fs-extra/lib/util/stat.js
var require_stat = __commonJS({
  "node_modules/fs-extra/lib/util/stat.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var path2 = require("path");
    var u = require_universalify().fromPromise;
    function getStats(src, dest, opts) {
      const statFunc = opts.dereference ? (file) => fs2.stat(file, { bigint: true }) : (file) => fs2.lstat(file, { bigint: true });
      return Promise.all([
        statFunc(src),
        statFunc(dest).catch((err) => {
          if (err.code === "ENOENT") return null;
          throw err;
        })
      ]).then(([srcStat, destStat]) => ({ srcStat, destStat }));
    }
    function getStatsSync(src, dest, opts) {
      let destStat;
      const statFunc = opts.dereference ? (file) => fs2.statSync(file, { bigint: true }) : (file) => fs2.lstatSync(file, { bigint: true });
      const srcStat = statFunc(src);
      try {
        destStat = statFunc(dest);
      } catch (err) {
        if (err.code === "ENOENT") return { srcStat, destStat: null };
        throw err;
      }
      return { srcStat, destStat };
    }
    async function checkPaths(src, dest, funcName, opts) {
      const { srcStat, destStat } = await getStats(src, dest, opts);
      if (destStat) {
        if (areIdentical(srcStat, destStat)) {
          const srcBaseName = path2.basename(src);
          const destBaseName = path2.basename(dest);
          if (funcName === "move" && srcBaseName !== destBaseName && srcBaseName.toLowerCase() === destBaseName.toLowerCase()) {
            return { srcStat, destStat, isChangingCase: true };
          }
          throw new Error("Source and destination must not be the same.");
        }
        if (srcStat.isDirectory() && !destStat.isDirectory()) {
          throw new Error(`Cannot overwrite non-directory '${dest}' with directory '${src}'.`);
        }
        if (!srcStat.isDirectory() && destStat.isDirectory()) {
          throw new Error(`Cannot overwrite directory '${dest}' with non-directory '${src}'.`);
        }
      }
      if (srcStat.isDirectory() && isSrcSubdir(src, dest)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return { srcStat, destStat };
    }
    function checkPathsSync(src, dest, funcName, opts) {
      const { srcStat, destStat } = getStatsSync(src, dest, opts);
      if (destStat) {
        if (areIdentical(srcStat, destStat)) {
          const srcBaseName = path2.basename(src);
          const destBaseName = path2.basename(dest);
          if (funcName === "move" && srcBaseName !== destBaseName && srcBaseName.toLowerCase() === destBaseName.toLowerCase()) {
            return { srcStat, destStat, isChangingCase: true };
          }
          throw new Error("Source and destination must not be the same.");
        }
        if (srcStat.isDirectory() && !destStat.isDirectory()) {
          throw new Error(`Cannot overwrite non-directory '${dest}' with directory '${src}'.`);
        }
        if (!srcStat.isDirectory() && destStat.isDirectory()) {
          throw new Error(`Cannot overwrite directory '${dest}' with non-directory '${src}'.`);
        }
      }
      if (srcStat.isDirectory() && isSrcSubdir(src, dest)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return { srcStat, destStat };
    }
    async function checkParentPaths(src, srcStat, dest, funcName) {
      const srcParent = path2.resolve(path2.dirname(src));
      const destParent = path2.resolve(path2.dirname(dest));
      if (destParent === srcParent || destParent === path2.parse(destParent).root) return;
      let destStat;
      try {
        destStat = await fs2.stat(destParent, { bigint: true });
      } catch (err) {
        if (err.code === "ENOENT") return;
        throw err;
      }
      if (areIdentical(srcStat, destStat)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return checkParentPaths(src, srcStat, destParent, funcName);
    }
    function checkParentPathsSync(src, srcStat, dest, funcName) {
      const srcParent = path2.resolve(path2.dirname(src));
      const destParent = path2.resolve(path2.dirname(dest));
      if (destParent === srcParent || destParent === path2.parse(destParent).root) return;
      let destStat;
      try {
        destStat = fs2.statSync(destParent, { bigint: true });
      } catch (err) {
        if (err.code === "ENOENT") return;
        throw err;
      }
      if (areIdentical(srcStat, destStat)) {
        throw new Error(errMsg(src, dest, funcName));
      }
      return checkParentPathsSync(src, srcStat, destParent, funcName);
    }
    function areIdentical(srcStat, destStat) {
      return destStat.ino !== void 0 && destStat.dev !== void 0 && destStat.ino === srcStat.ino && destStat.dev === srcStat.dev;
    }
    function isSrcSubdir(src, dest) {
      const srcArr = path2.resolve(src).split(path2.sep).filter((i) => i);
      const destArr = path2.resolve(dest).split(path2.sep).filter((i) => i);
      return srcArr.every((cur, i) => destArr[i] === cur);
    }
    function errMsg(src, dest, funcName) {
      return `Cannot ${funcName} '${src}' to a subdirectory of itself, '${dest}'.`;
    }
    module2.exports = {
      // checkPaths
      checkPaths: u(checkPaths),
      checkPathsSync,
      // checkParent
      checkParentPaths: u(checkParentPaths),
      checkParentPathsSync,
      // Misc
      isSrcSubdir,
      areIdentical
    };
  }
});

// node_modules/fs-extra/lib/copy/copy.js
var require_copy = __commonJS({
  "node_modules/fs-extra/lib/copy/copy.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var path2 = require("path");
    var { mkdirs } = require_mkdirs();
    var { pathExists } = require_path_exists();
    var { utimesMillis } = require_utimes();
    var stat = require_stat();
    async function copy(src, dest, opts = {}) {
      if (typeof opts === "function") {
        opts = { filter: opts };
      }
      opts.clobber = "clobber" in opts ? !!opts.clobber : true;
      opts.overwrite = "overwrite" in opts ? !!opts.overwrite : opts.clobber;
      if (opts.preserveTimestamps && process.arch === "ia32") {
        process.emitWarning(
          "Using the preserveTimestamps option in 32-bit node is not recommended;\n\n	see https://github.com/jprichardson/node-fs-extra/issues/269",
          "Warning",
          "fs-extra-WARN0001"
        );
      }
      const { srcStat, destStat } = await stat.checkPaths(src, dest, "copy", opts);
      await stat.checkParentPaths(src, srcStat, dest, "copy");
      const include = await runFilter(src, dest, opts);
      if (!include) return;
      const destParent = path2.dirname(dest);
      const dirExists = await pathExists(destParent);
      if (!dirExists) {
        await mkdirs(destParent);
      }
      await getStatsAndPerformCopy(destStat, src, dest, opts);
    }
    async function runFilter(src, dest, opts) {
      if (!opts.filter) return true;
      return opts.filter(src, dest);
    }
    async function getStatsAndPerformCopy(destStat, src, dest, opts) {
      const statFn = opts.dereference ? fs2.stat : fs2.lstat;
      const srcStat = await statFn(src);
      if (srcStat.isDirectory()) return onDir(srcStat, destStat, src, dest, opts);
      if (srcStat.isFile() || srcStat.isCharacterDevice() || srcStat.isBlockDevice()) return onFile(srcStat, destStat, src, dest, opts);
      if (srcStat.isSymbolicLink()) return onLink(destStat, src, dest, opts);
      if (srcStat.isSocket()) throw new Error(`Cannot copy a socket file: ${src}`);
      if (srcStat.isFIFO()) throw new Error(`Cannot copy a FIFO pipe: ${src}`);
      throw new Error(`Unknown file: ${src}`);
    }
    async function onFile(srcStat, destStat, src, dest, opts) {
      if (!destStat) return copyFile(srcStat, src, dest, opts);
      if (opts.overwrite) {
        await fs2.unlink(dest);
        return copyFile(srcStat, src, dest, opts);
      }
      if (opts.errorOnExist) {
        throw new Error(`'${dest}' already exists`);
      }
    }
    async function copyFile(srcStat, src, dest, opts) {
      await fs2.copyFile(src, dest);
      if (opts.preserveTimestamps) {
        if (fileIsNotWritable(srcStat.mode)) {
          await makeFileWritable(dest, srcStat.mode);
        }
        const updatedSrcStat = await fs2.stat(src);
        await utimesMillis(dest, updatedSrcStat.atime, updatedSrcStat.mtime);
      }
      return fs2.chmod(dest, srcStat.mode);
    }
    function fileIsNotWritable(srcMode) {
      return (srcMode & 128) === 0;
    }
    function makeFileWritable(dest, srcMode) {
      return fs2.chmod(dest, srcMode | 128);
    }
    async function onDir(srcStat, destStat, src, dest, opts) {
      if (!destStat) {
        await fs2.mkdir(dest);
      }
      const promises = [];
      for await (const item of await fs2.opendir(src)) {
        const srcItem = path2.join(src, item.name);
        const destItem = path2.join(dest, item.name);
        promises.push(
          runFilter(srcItem, destItem, opts).then((include) => {
            if (include) {
              return stat.checkPaths(srcItem, destItem, "copy", opts).then(({ destStat: destStat2 }) => {
                return getStatsAndPerformCopy(destStat2, srcItem, destItem, opts);
              });
            }
          })
        );
      }
      await Promise.all(promises);
      if (!destStat) {
        await fs2.chmod(dest, srcStat.mode);
      }
    }
    async function onLink(destStat, src, dest, opts) {
      let resolvedSrc = await fs2.readlink(src);
      if (opts.dereference) {
        resolvedSrc = path2.resolve(process.cwd(), resolvedSrc);
      }
      if (!destStat) {
        return fs2.symlink(resolvedSrc, dest);
      }
      let resolvedDest = null;
      try {
        resolvedDest = await fs2.readlink(dest);
      } catch (e) {
        if (e.code === "EINVAL" || e.code === "UNKNOWN") return fs2.symlink(resolvedSrc, dest);
        throw e;
      }
      if (opts.dereference) {
        resolvedDest = path2.resolve(process.cwd(), resolvedDest);
      }
      if (stat.isSrcSubdir(resolvedSrc, resolvedDest)) {
        throw new Error(`Cannot copy '${resolvedSrc}' to a subdirectory of itself, '${resolvedDest}'.`);
      }
      if (stat.isSrcSubdir(resolvedDest, resolvedSrc)) {
        throw new Error(`Cannot overwrite '${resolvedDest}' with '${resolvedSrc}'.`);
      }
      await fs2.unlink(dest);
      return fs2.symlink(resolvedSrc, dest);
    }
    module2.exports = copy;
  }
});

// node_modules/fs-extra/lib/copy/copy-sync.js
var require_copy_sync = __commonJS({
  "node_modules/fs-extra/lib/copy/copy-sync.js"(exports2, module2) {
    "use strict";
    var fs2 = require_graceful_fs();
    var path2 = require("path");
    var mkdirsSync = require_mkdirs().mkdirsSync;
    var utimesMillisSync = require_utimes().utimesMillisSync;
    var stat = require_stat();
    function copySync(src, dest, opts) {
      if (typeof opts === "function") {
        opts = { filter: opts };
      }
      opts = opts || {};
      opts.clobber = "clobber" in opts ? !!opts.clobber : true;
      opts.overwrite = "overwrite" in opts ? !!opts.overwrite : opts.clobber;
      if (opts.preserveTimestamps && process.arch === "ia32") {
        process.emitWarning(
          "Using the preserveTimestamps option in 32-bit node is not recommended;\n\n	see https://github.com/jprichardson/node-fs-extra/issues/269",
          "Warning",
          "fs-extra-WARN0002"
        );
      }
      const { srcStat, destStat } = stat.checkPathsSync(src, dest, "copy", opts);
      stat.checkParentPathsSync(src, srcStat, dest, "copy");
      if (opts.filter && !opts.filter(src, dest)) return;
      const destParent = path2.dirname(dest);
      if (!fs2.existsSync(destParent)) mkdirsSync(destParent);
      return getStats(destStat, src, dest, opts);
    }
    function getStats(destStat, src, dest, opts) {
      const statSync = opts.dereference ? fs2.statSync : fs2.lstatSync;
      const srcStat = statSync(src);
      if (srcStat.isDirectory()) return onDir(srcStat, destStat, src, dest, opts);
      else if (srcStat.isFile() || srcStat.isCharacterDevice() || srcStat.isBlockDevice()) return onFile(srcStat, destStat, src, dest, opts);
      else if (srcStat.isSymbolicLink()) return onLink(destStat, src, dest, opts);
      else if (srcStat.isSocket()) throw new Error(`Cannot copy a socket file: ${src}`);
      else if (srcStat.isFIFO()) throw new Error(`Cannot copy a FIFO pipe: ${src}`);
      throw new Error(`Unknown file: ${src}`);
    }
    function onFile(srcStat, destStat, src, dest, opts) {
      if (!destStat) return copyFile(srcStat, src, dest, opts);
      return mayCopyFile(srcStat, src, dest, opts);
    }
    function mayCopyFile(srcStat, src, dest, opts) {
      if (opts.overwrite) {
        fs2.unlinkSync(dest);
        return copyFile(srcStat, src, dest, opts);
      } else if (opts.errorOnExist) {
        throw new Error(`'${dest}' already exists`);
      }
    }
    function copyFile(srcStat, src, dest, opts) {
      fs2.copyFileSync(src, dest);
      if (opts.preserveTimestamps) handleTimestamps(srcStat.mode, src, dest);
      return setDestMode(dest, srcStat.mode);
    }
    function handleTimestamps(srcMode, src, dest) {
      if (fileIsNotWritable(srcMode)) makeFileWritable(dest, srcMode);
      return setDestTimestamps(src, dest);
    }
    function fileIsNotWritable(srcMode) {
      return (srcMode & 128) === 0;
    }
    function makeFileWritable(dest, srcMode) {
      return setDestMode(dest, srcMode | 128);
    }
    function setDestMode(dest, srcMode) {
      return fs2.chmodSync(dest, srcMode);
    }
    function setDestTimestamps(src, dest) {
      const updatedSrcStat = fs2.statSync(src);
      return utimesMillisSync(dest, updatedSrcStat.atime, updatedSrcStat.mtime);
    }
    function onDir(srcStat, destStat, src, dest, opts) {
      if (!destStat) return mkDirAndCopy(srcStat.mode, src, dest, opts);
      return copyDir(src, dest, opts);
    }
    function mkDirAndCopy(srcMode, src, dest, opts) {
      fs2.mkdirSync(dest);
      copyDir(src, dest, opts);
      return setDestMode(dest, srcMode);
    }
    function copyDir(src, dest, opts) {
      const dir = fs2.opendirSync(src);
      try {
        let dirent;
        while ((dirent = dir.readSync()) !== null) {
          copyDirItem(dirent.name, src, dest, opts);
        }
      } finally {
        dir.closeSync();
      }
    }
    function copyDirItem(item, src, dest, opts) {
      const srcItem = path2.join(src, item);
      const destItem = path2.join(dest, item);
      if (opts.filter && !opts.filter(srcItem, destItem)) return;
      const { destStat } = stat.checkPathsSync(srcItem, destItem, "copy", opts);
      return getStats(destStat, srcItem, destItem, opts);
    }
    function onLink(destStat, src, dest, opts) {
      let resolvedSrc = fs2.readlinkSync(src);
      if (opts.dereference) {
        resolvedSrc = path2.resolve(process.cwd(), resolvedSrc);
      }
      if (!destStat) {
        return fs2.symlinkSync(resolvedSrc, dest);
      } else {
        let resolvedDest;
        try {
          resolvedDest = fs2.readlinkSync(dest);
        } catch (err) {
          if (err.code === "EINVAL" || err.code === "UNKNOWN") return fs2.symlinkSync(resolvedSrc, dest);
          throw err;
        }
        if (opts.dereference) {
          resolvedDest = path2.resolve(process.cwd(), resolvedDest);
        }
        if (stat.isSrcSubdir(resolvedSrc, resolvedDest)) {
          throw new Error(`Cannot copy '${resolvedSrc}' to a subdirectory of itself, '${resolvedDest}'.`);
        }
        if (stat.isSrcSubdir(resolvedDest, resolvedSrc)) {
          throw new Error(`Cannot overwrite '${resolvedDest}' with '${resolvedSrc}'.`);
        }
        return copyLink(resolvedSrc, dest);
      }
    }
    function copyLink(resolvedSrc, dest) {
      fs2.unlinkSync(dest);
      return fs2.symlinkSync(resolvedSrc, dest);
    }
    module2.exports = copySync;
  }
});

// node_modules/fs-extra/lib/copy/index.js
var require_copy2 = __commonJS({
  "node_modules/fs-extra/lib/copy/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    module2.exports = {
      copy: u(require_copy()),
      copySync: require_copy_sync()
    };
  }
});

// node_modules/fs-extra/lib/remove/index.js
var require_remove = __commonJS({
  "node_modules/fs-extra/lib/remove/index.js"(exports2, module2) {
    "use strict";
    var fs2 = require_graceful_fs();
    var u = require_universalify().fromCallback;
    function remove(path2, callback) {
      fs2.rm(path2, { recursive: true, force: true }, callback);
    }
    function removeSync(path2) {
      fs2.rmSync(path2, { recursive: true, force: true });
    }
    module2.exports = {
      remove: u(remove),
      removeSync
    };
  }
});

// node_modules/fs-extra/lib/empty/index.js
var require_empty = __commonJS({
  "node_modules/fs-extra/lib/empty/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var fs2 = require_fs();
    var path2 = require("path");
    var mkdir = require_mkdirs();
    var remove = require_remove();
    var emptyDir = u(async function emptyDir2(dir) {
      let items;
      try {
        items = await fs2.readdir(dir);
      } catch {
        return mkdir.mkdirs(dir);
      }
      return Promise.all(items.map((item) => remove.remove(path2.join(dir, item))));
    });
    function emptyDirSync(dir) {
      let items;
      try {
        items = fs2.readdirSync(dir);
      } catch {
        return mkdir.mkdirsSync(dir);
      }
      items.forEach((item) => {
        item = path2.join(dir, item);
        remove.removeSync(item);
      });
    }
    module2.exports = {
      emptyDirSync,
      emptydirSync: emptyDirSync,
      emptyDir,
      emptydir: emptyDir
    };
  }
});

// node_modules/fs-extra/lib/ensure/file.js
var require_file = __commonJS({
  "node_modules/fs-extra/lib/ensure/file.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var path2 = require("path");
    var fs2 = require_fs();
    var mkdir = require_mkdirs();
    async function createFile(file) {
      let stats;
      try {
        stats = await fs2.stat(file);
      } catch {
      }
      if (stats && stats.isFile()) return;
      const dir = path2.dirname(file);
      let dirStats = null;
      try {
        dirStats = await fs2.stat(dir);
      } catch (err) {
        if (err.code === "ENOENT") {
          await mkdir.mkdirs(dir);
          await fs2.writeFile(file, "");
          return;
        } else {
          throw err;
        }
      }
      if (dirStats.isDirectory()) {
        await fs2.writeFile(file, "");
      } else {
        await fs2.readdir(dir);
      }
    }
    function createFileSync(file) {
      let stats;
      try {
        stats = fs2.statSync(file);
      } catch {
      }
      if (stats && stats.isFile()) return;
      const dir = path2.dirname(file);
      try {
        if (!fs2.statSync(dir).isDirectory()) {
          fs2.readdirSync(dir);
        }
      } catch (err) {
        if (err && err.code === "ENOENT") mkdir.mkdirsSync(dir);
        else throw err;
      }
      fs2.writeFileSync(file, "");
    }
    module2.exports = {
      createFile: u(createFile),
      createFileSync
    };
  }
});

// node_modules/fs-extra/lib/ensure/link.js
var require_link = __commonJS({
  "node_modules/fs-extra/lib/ensure/link.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var path2 = require("path");
    var fs2 = require_fs();
    var mkdir = require_mkdirs();
    var { pathExists } = require_path_exists();
    var { areIdentical } = require_stat();
    async function createLink(srcpath, dstpath) {
      let dstStat;
      try {
        dstStat = await fs2.lstat(dstpath);
      } catch {
      }
      let srcStat;
      try {
        srcStat = await fs2.lstat(srcpath);
      } catch (err) {
        err.message = err.message.replace("lstat", "ensureLink");
        throw err;
      }
      if (dstStat && areIdentical(srcStat, dstStat)) return;
      const dir = path2.dirname(dstpath);
      const dirExists = await pathExists(dir);
      if (!dirExists) {
        await mkdir.mkdirs(dir);
      }
      await fs2.link(srcpath, dstpath);
    }
    function createLinkSync(srcpath, dstpath) {
      let dstStat;
      try {
        dstStat = fs2.lstatSync(dstpath);
      } catch {
      }
      try {
        const srcStat = fs2.lstatSync(srcpath);
        if (dstStat && areIdentical(srcStat, dstStat)) return;
      } catch (err) {
        err.message = err.message.replace("lstat", "ensureLink");
        throw err;
      }
      const dir = path2.dirname(dstpath);
      const dirExists = fs2.existsSync(dir);
      if (dirExists) return fs2.linkSync(srcpath, dstpath);
      mkdir.mkdirsSync(dir);
      return fs2.linkSync(srcpath, dstpath);
    }
    module2.exports = {
      createLink: u(createLink),
      createLinkSync
    };
  }
});

// node_modules/fs-extra/lib/ensure/symlink-paths.js
var require_symlink_paths = __commonJS({
  "node_modules/fs-extra/lib/ensure/symlink-paths.js"(exports2, module2) {
    "use strict";
    var path2 = require("path");
    var fs2 = require_fs();
    var { pathExists } = require_path_exists();
    var u = require_universalify().fromPromise;
    async function symlinkPaths(srcpath, dstpath) {
      if (path2.isAbsolute(srcpath)) {
        try {
          await fs2.lstat(srcpath);
        } catch (err) {
          err.message = err.message.replace("lstat", "ensureSymlink");
          throw err;
        }
        return {
          toCwd: srcpath,
          toDst: srcpath
        };
      }
      const dstdir = path2.dirname(dstpath);
      const relativeToDst = path2.join(dstdir, srcpath);
      const exists = await pathExists(relativeToDst);
      if (exists) {
        return {
          toCwd: relativeToDst,
          toDst: srcpath
        };
      }
      try {
        await fs2.lstat(srcpath);
      } catch (err) {
        err.message = err.message.replace("lstat", "ensureSymlink");
        throw err;
      }
      return {
        toCwd: srcpath,
        toDst: path2.relative(dstdir, srcpath)
      };
    }
    function symlinkPathsSync(srcpath, dstpath) {
      if (path2.isAbsolute(srcpath)) {
        const exists2 = fs2.existsSync(srcpath);
        if (!exists2) throw new Error("absolute srcpath does not exist");
        return {
          toCwd: srcpath,
          toDst: srcpath
        };
      }
      const dstdir = path2.dirname(dstpath);
      const relativeToDst = path2.join(dstdir, srcpath);
      const exists = fs2.existsSync(relativeToDst);
      if (exists) {
        return {
          toCwd: relativeToDst,
          toDst: srcpath
        };
      }
      const srcExists = fs2.existsSync(srcpath);
      if (!srcExists) throw new Error("relative srcpath does not exist");
      return {
        toCwd: srcpath,
        toDst: path2.relative(dstdir, srcpath)
      };
    }
    module2.exports = {
      symlinkPaths: u(symlinkPaths),
      symlinkPathsSync
    };
  }
});

// node_modules/fs-extra/lib/ensure/symlink-type.js
var require_symlink_type = __commonJS({
  "node_modules/fs-extra/lib/ensure/symlink-type.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var u = require_universalify().fromPromise;
    async function symlinkType(srcpath, type) {
      if (type) return type;
      let stats;
      try {
        stats = await fs2.lstat(srcpath);
      } catch {
        return "file";
      }
      return stats && stats.isDirectory() ? "dir" : "file";
    }
    function symlinkTypeSync(srcpath, type) {
      if (type) return type;
      let stats;
      try {
        stats = fs2.lstatSync(srcpath);
      } catch {
        return "file";
      }
      return stats && stats.isDirectory() ? "dir" : "file";
    }
    module2.exports = {
      symlinkType: u(symlinkType),
      symlinkTypeSync
    };
  }
});

// node_modules/fs-extra/lib/ensure/symlink.js
var require_symlink = __commonJS({
  "node_modules/fs-extra/lib/ensure/symlink.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var path2 = require("path");
    var fs2 = require_fs();
    var { mkdirs, mkdirsSync } = require_mkdirs();
    var { symlinkPaths, symlinkPathsSync } = require_symlink_paths();
    var { symlinkType, symlinkTypeSync } = require_symlink_type();
    var { pathExists } = require_path_exists();
    var { areIdentical } = require_stat();
    async function createSymlink(srcpath, dstpath, type) {
      let stats;
      try {
        stats = await fs2.lstat(dstpath);
      } catch {
      }
      if (stats && stats.isSymbolicLink()) {
        const [srcStat, dstStat] = await Promise.all([
          fs2.stat(srcpath),
          fs2.stat(dstpath)
        ]);
        if (areIdentical(srcStat, dstStat)) return;
      }
      const relative = await symlinkPaths(srcpath, dstpath);
      srcpath = relative.toDst;
      const toType = await symlinkType(relative.toCwd, type);
      const dir = path2.dirname(dstpath);
      if (!await pathExists(dir)) {
        await mkdirs(dir);
      }
      return fs2.symlink(srcpath, dstpath, toType);
    }
    function createSymlinkSync(srcpath, dstpath, type) {
      let stats;
      try {
        stats = fs2.lstatSync(dstpath);
      } catch {
      }
      if (stats && stats.isSymbolicLink()) {
        const srcStat = fs2.statSync(srcpath);
        const dstStat = fs2.statSync(dstpath);
        if (areIdentical(srcStat, dstStat)) return;
      }
      const relative = symlinkPathsSync(srcpath, dstpath);
      srcpath = relative.toDst;
      type = symlinkTypeSync(relative.toCwd, type);
      const dir = path2.dirname(dstpath);
      const exists = fs2.existsSync(dir);
      if (exists) return fs2.symlinkSync(srcpath, dstpath, type);
      mkdirsSync(dir);
      return fs2.symlinkSync(srcpath, dstpath, type);
    }
    module2.exports = {
      createSymlink: u(createSymlink),
      createSymlinkSync
    };
  }
});

// node_modules/fs-extra/lib/ensure/index.js
var require_ensure = __commonJS({
  "node_modules/fs-extra/lib/ensure/index.js"(exports2, module2) {
    "use strict";
    var { createFile, createFileSync } = require_file();
    var { createLink, createLinkSync } = require_link();
    var { createSymlink, createSymlinkSync } = require_symlink();
    module2.exports = {
      // file
      createFile,
      createFileSync,
      ensureFile: createFile,
      ensureFileSync: createFileSync,
      // link
      createLink,
      createLinkSync,
      ensureLink: createLink,
      ensureLinkSync: createLinkSync,
      // symlink
      createSymlink,
      createSymlinkSync,
      ensureSymlink: createSymlink,
      ensureSymlinkSync: createSymlinkSync
    };
  }
});

// node_modules/jsonfile/utils.js
var require_utils2 = __commonJS({
  "node_modules/jsonfile/utils.js"(exports2, module2) {
    function stringify(obj, { EOL = "\n", finalEOL = true, replacer = null, spaces } = {}) {
      const EOF = finalEOL ? EOL : "";
      const str = JSON.stringify(obj, replacer, spaces);
      return str.replace(/\n/g, EOL) + EOF;
    }
    function stripBom(content) {
      if (Buffer.isBuffer(content)) content = content.toString("utf8");
      return content.replace(/^\uFEFF/, "");
    }
    module2.exports = { stringify, stripBom };
  }
});

// node_modules/jsonfile/index.js
var require_jsonfile = __commonJS({
  "node_modules/jsonfile/index.js"(exports2, module2) {
    var _fs;
    try {
      _fs = require_graceful_fs();
    } catch (_) {
      _fs = require("fs");
    }
    var universalify = require_universalify();
    var { stringify, stripBom } = require_utils2();
    async function _readFile(file, options = {}) {
      if (typeof options === "string") {
        options = { encoding: options };
      }
      const fs2 = options.fs || _fs;
      const shouldThrow = "throws" in options ? options.throws : true;
      let data = await universalify.fromCallback(fs2.readFile)(file, options);
      data = stripBom(data);
      let obj;
      try {
        obj = JSON.parse(data, options ? options.reviver : null);
      } catch (err) {
        if (shouldThrow) {
          err.message = `${file}: ${err.message}`;
          throw err;
        } else {
          return null;
        }
      }
      return obj;
    }
    var readFile = universalify.fromPromise(_readFile);
    function readFileSync(file, options = {}) {
      if (typeof options === "string") {
        options = { encoding: options };
      }
      const fs2 = options.fs || _fs;
      const shouldThrow = "throws" in options ? options.throws : true;
      try {
        let content = fs2.readFileSync(file, options);
        content = stripBom(content);
        return JSON.parse(content, options.reviver);
      } catch (err) {
        if (shouldThrow) {
          err.message = `${file}: ${err.message}`;
          throw err;
        } else {
          return null;
        }
      }
    }
    async function _writeFile(file, obj, options = {}) {
      const fs2 = options.fs || _fs;
      const str = stringify(obj, options);
      await universalify.fromCallback(fs2.writeFile)(file, str, options);
    }
    var writeFile = universalify.fromPromise(_writeFile);
    function writeFileSync(file, obj, options = {}) {
      const fs2 = options.fs || _fs;
      const str = stringify(obj, options);
      return fs2.writeFileSync(file, str, options);
    }
    module2.exports = {
      readFile,
      readFileSync,
      writeFile,
      writeFileSync
    };
  }
});

// node_modules/fs-extra/lib/json/jsonfile.js
var require_jsonfile2 = __commonJS({
  "node_modules/fs-extra/lib/json/jsonfile.js"(exports2, module2) {
    "use strict";
    var jsonFile = require_jsonfile();
    module2.exports = {
      // jsonfile exports
      readJson: jsonFile.readFile,
      readJsonSync: jsonFile.readFileSync,
      writeJson: jsonFile.writeFile,
      writeJsonSync: jsonFile.writeFileSync
    };
  }
});

// node_modules/fs-extra/lib/output-file/index.js
var require_output_file = __commonJS({
  "node_modules/fs-extra/lib/output-file/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var fs2 = require_fs();
    var path2 = require("path");
    var mkdir = require_mkdirs();
    var pathExists = require_path_exists().pathExists;
    async function outputFile(file, data, encoding = "utf-8") {
      const dir = path2.dirname(file);
      if (!await pathExists(dir)) {
        await mkdir.mkdirs(dir);
      }
      return fs2.writeFile(file, data, encoding);
    }
    function outputFileSync(file, ...args) {
      const dir = path2.dirname(file);
      if (!fs2.existsSync(dir)) {
        mkdir.mkdirsSync(dir);
      }
      fs2.writeFileSync(file, ...args);
    }
    module2.exports = {
      outputFile: u(outputFile),
      outputFileSync
    };
  }
});

// node_modules/fs-extra/lib/json/output-json.js
var require_output_json = __commonJS({
  "node_modules/fs-extra/lib/json/output-json.js"(exports2, module2) {
    "use strict";
    var { stringify } = require_utils2();
    var { outputFile } = require_output_file();
    async function outputJson(file, data, options = {}) {
      const str = stringify(data, options);
      await outputFile(file, str, options);
    }
    module2.exports = outputJson;
  }
});

// node_modules/fs-extra/lib/json/output-json-sync.js
var require_output_json_sync = __commonJS({
  "node_modules/fs-extra/lib/json/output-json-sync.js"(exports2, module2) {
    "use strict";
    var { stringify } = require_utils2();
    var { outputFileSync } = require_output_file();
    function outputJsonSync(file, data, options) {
      const str = stringify(data, options);
      outputFileSync(file, str, options);
    }
    module2.exports = outputJsonSync;
  }
});

// node_modules/fs-extra/lib/json/index.js
var require_json = __commonJS({
  "node_modules/fs-extra/lib/json/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    var jsonFile = require_jsonfile2();
    jsonFile.outputJson = u(require_output_json());
    jsonFile.outputJsonSync = require_output_json_sync();
    jsonFile.outputJSON = jsonFile.outputJson;
    jsonFile.outputJSONSync = jsonFile.outputJsonSync;
    jsonFile.writeJSON = jsonFile.writeJson;
    jsonFile.writeJSONSync = jsonFile.writeJsonSync;
    jsonFile.readJSON = jsonFile.readJson;
    jsonFile.readJSONSync = jsonFile.readJsonSync;
    module2.exports = jsonFile;
  }
});

// node_modules/fs-extra/lib/move/move.js
var require_move = __commonJS({
  "node_modules/fs-extra/lib/move/move.js"(exports2, module2) {
    "use strict";
    var fs2 = require_fs();
    var path2 = require("path");
    var { copy } = require_copy2();
    var { remove } = require_remove();
    var { mkdirp } = require_mkdirs();
    var { pathExists } = require_path_exists();
    var stat = require_stat();
    async function move(src, dest, opts = {}) {
      const overwrite = opts.overwrite || opts.clobber || false;
      const { srcStat, isChangingCase = false } = await stat.checkPaths(src, dest, "move", opts);
      await stat.checkParentPaths(src, srcStat, dest, "move");
      const destParent = path2.dirname(dest);
      const parsedParentPath = path2.parse(destParent);
      if (parsedParentPath.root !== destParent) {
        await mkdirp(destParent);
      }
      return doRename(src, dest, overwrite, isChangingCase);
    }
    async function doRename(src, dest, overwrite, isChangingCase) {
      if (!isChangingCase) {
        if (overwrite) {
          await remove(dest);
        } else if (await pathExists(dest)) {
          throw new Error("dest already exists.");
        }
      }
      try {
        await fs2.rename(src, dest);
      } catch (err) {
        if (err.code !== "EXDEV") {
          throw err;
        }
        await moveAcrossDevice(src, dest, overwrite);
      }
    }
    async function moveAcrossDevice(src, dest, overwrite) {
      const opts = {
        overwrite,
        errorOnExist: true,
        preserveTimestamps: true
      };
      await copy(src, dest, opts);
      return remove(src);
    }
    module2.exports = move;
  }
});

// node_modules/fs-extra/lib/move/move-sync.js
var require_move_sync = __commonJS({
  "node_modules/fs-extra/lib/move/move-sync.js"(exports2, module2) {
    "use strict";
    var fs2 = require_graceful_fs();
    var path2 = require("path");
    var copySync = require_copy2().copySync;
    var removeSync = require_remove().removeSync;
    var mkdirpSync = require_mkdirs().mkdirpSync;
    var stat = require_stat();
    function moveSync(src, dest, opts) {
      opts = opts || {};
      const overwrite = opts.overwrite || opts.clobber || false;
      const { srcStat, isChangingCase = false } = stat.checkPathsSync(src, dest, "move", opts);
      stat.checkParentPathsSync(src, srcStat, dest, "move");
      if (!isParentRoot(dest)) mkdirpSync(path2.dirname(dest));
      return doRename(src, dest, overwrite, isChangingCase);
    }
    function isParentRoot(dest) {
      const parent = path2.dirname(dest);
      const parsedPath = path2.parse(parent);
      return parsedPath.root === parent;
    }
    function doRename(src, dest, overwrite, isChangingCase) {
      if (isChangingCase) return rename(src, dest, overwrite);
      if (overwrite) {
        removeSync(dest);
        return rename(src, dest, overwrite);
      }
      if (fs2.existsSync(dest)) throw new Error("dest already exists.");
      return rename(src, dest, overwrite);
    }
    function rename(src, dest, overwrite) {
      try {
        fs2.renameSync(src, dest);
      } catch (err) {
        if (err.code !== "EXDEV") throw err;
        return moveAcrossDevice(src, dest, overwrite);
      }
    }
    function moveAcrossDevice(src, dest, overwrite) {
      const opts = {
        overwrite,
        errorOnExist: true,
        preserveTimestamps: true
      };
      copySync(src, dest, opts);
      return removeSync(src);
    }
    module2.exports = moveSync;
  }
});

// node_modules/fs-extra/lib/move/index.js
var require_move2 = __commonJS({
  "node_modules/fs-extra/lib/move/index.js"(exports2, module2) {
    "use strict";
    var u = require_universalify().fromPromise;
    module2.exports = {
      move: u(require_move()),
      moveSync: require_move_sync()
    };
  }
});

// node_modules/fs-extra/lib/index.js
var require_lib = __commonJS({
  "node_modules/fs-extra/lib/index.js"(exports2, module2) {
    "use strict";
    module2.exports = {
      // Export promiseified graceful-fs:
      ...require_fs(),
      // Export extra methods:
      ...require_copy2(),
      ...require_empty(),
      ...require_ensure(),
      ...require_json(),
      ...require_mkdirs(),
      ...require_move2(),
      ...require_output_file(),
      ...require_path_exists(),
      ...require_remove()
    };
  }
});

// dist/services/ModelSwitcher.js
var require_ModelSwitcher = __commonJS({
  "dist/services/ModelSwitcher.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ModelSwitcher = void 0;
    var MigrationState_1 = require_MigrationState();
    var AIModelSettings_1 = require_AIModelSettings();
    var path2 = __importStar2(require("path"));
    var fs2 = __importStar2(require_lib());
    var ModelSwitcher = class {
      constructor(configManager, backupDirectory = "./.specify/backups") {
        this.configManager = configManager;
        this.backupDirectory = backupDirectory;
      }
      async switchModel(projectConfig, options) {
        const warnings = [];
        try {
          if (projectConfig.aiModel === options.targetModel) {
            return {
              success: false,
              migrationId: "",
              errorMessage: `Project is already using ${options.targetModel}`,
              warnings
            };
          }
          const targetSettings = AIModelSettings_1.AIModelSettingsProvider.getSettings(options.targetModel);
          if (!targetSettings) {
            return {
              success: false,
              migrationId: "",
              errorMessage: `Unknown target model: ${options.targetModel}`,
              warnings
            };
          }
          if (targetSettings.compatibility.deprecationWarning) {
            warnings.push(targetSettings.compatibility.deprecationWarning);
          }
          const backupPath = await this.createBackupPath(projectConfig.projectId);
          const migration = MigrationState_1.MigrationStateManager.create({
            fromModel: projectConfig.aiModel,
            toModel: options.targetModel,
            projectId: projectConfig.projectId,
            backupPath,
            dryRun: options.dryRun || false
          });
          if (options.dryRun) {
            return {
              success: true,
              migrationId: migration.id,
              warnings: [...warnings, "Dry run completed - no changes made"]
            };
          }
          const result = await this.executeMigration(migration, projectConfig, options);
          return {
            ...result,
            warnings
          };
        } catch (error) {
          return {
            success: false,
            migrationId: "",
            errorMessage: error instanceof Error ? error.message : "Unknown error",
            warnings
          };
        }
      }
      async executeMigration(migration, projectConfig, options) {
        try {
          await this.validateProject(projectConfig);
          if (options.createBackup !== false) {
            await this.createBackup(migration, projectConfig);
          }
          const updatedConfig = await this.updateProjectConfig(projectConfig, migration.toModel, migration.id);
          await this.migrateSpecFiles(projectConfig, migration);
          await this.validateMigration(updatedConfig);
          const completedMigration = MigrationState_1.MigrationStateManager.complete(migration, true);
          return {
            success: true,
            migrationId: completedMigration.id,
            backupPath: migration.backup.path
          };
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : "Migration failed";
          if (migration.backup.files.length > 0 && MigrationState_1.MigrationStateManager.canRollback(migration)) {
            try {
              await this.rollbackMigration(migration);
            } catch (rollbackError) {
              return {
                success: false,
                migrationId: migration.id,
                errorMessage: `${errorMessage}. Rollback also failed: ${rollbackError}`
              };
            }
          }
          return {
            success: false,
            migrationId: migration.id,
            errorMessage,
            backupPath: migration.backup.path
          };
        }
      }
      async validateProject(config) {
        if (!config.isInitialized) {
          throw new Error("Project is not properly initialized");
        }
        if (!await fs2.pathExists(config.configPath)) {
          throw new Error("Project configuration file not found");
        }
        if (!await fs2.pathExists(config.specDirectory)) {
          throw new Error("Specification directory not found");
        }
      }
      async createBackup(migration, config) {
        await fs2.ensureDir(this.backupDirectory);
        const backupDir = path2.join(this.backupDirectory, migration.backup.id);
        await fs2.ensureDir(backupDir);
        const configBackupPath = path2.join(backupDir, "config.json");
        await fs2.copy(config.configPath, configBackupPath);
        const specBackupPath = path2.join(backupDir, "specs");
        await fs2.copy(config.specDirectory, specBackupPath);
        const stats = await fs2.stat(backupDir);
        migration.backup.size = await this.getDirectorySize(backupDir);
        migration.backup.checksum = await this.calculateChecksum(backupDir);
        migration.backup.files = [
          {
            originalPath: config.configPath,
            backupPath: configBackupPath,
            checksum: await this.calculateFileChecksum(configBackupPath),
            size: (await fs2.stat(configBackupPath)).size
          },
          {
            originalPath: config.specDirectory,
            backupPath: specBackupPath,
            checksum: await this.calculateFileChecksum(specBackupPath),
            size: await this.getDirectorySize(specBackupPath)
          }
        ];
      }
      async updateProjectConfig(config, targetModel, migrationId) {
        const updatedConfig = {
          ...config,
          aiModel: targetModel,
          updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
          migrationHistory: [
            ...config.migrationHistory,
            {
              id: migrationId,
              fromModel: config.aiModel,
              toModel: targetModel,
              timestamp: (/* @__PURE__ */ new Date()).toISOString(),
              success: true
            }
          ]
        };
        await this.configManager.saveConfig(updatedConfig);
        return updatedConfig;
      }
      async migrateSpecFiles(config, migration) {
        const specFiles = await this.getSpecFiles(config.specDirectory);
        for (const file of specFiles) {
          const content = await fs2.readFile(file, "utf8");
          await fs2.writeFile(file, content);
        }
      }
      async validateMigration(config) {
        if (!await fs2.pathExists(config.configPath)) {
          throw new Error("Configuration file missing after migration");
        }
        const savedConfig = await this.configManager.loadConfig(config.configPath);
        if (savedConfig.aiModel !== config.aiModel) {
          throw new Error("Configuration not properly updated");
        }
      }
      async rollbackMigration(migration) {
        const rollbackState = MigrationState_1.MigrationStateManager.startRollback(migration, "Migration failed, attempting rollback");
        for (const file of migration.backup.files) {
          if (await fs2.pathExists(file.backupPath)) {
            await fs2.copy(file.backupPath, file.originalPath);
            rollbackState.rollback.restoredFiles.push(file.originalPath);
          }
        }
        rollbackState.rollback.success = true;
        rollbackState.rollback.completedAt = (/* @__PURE__ */ new Date()).toISOString();
      }
      async createBackupPath(projectId) {
        const timestamp = (/* @__PURE__ */ new Date()).toISOString().replace(/[:.]/g, "-");
        return path2.join(this.backupDirectory, `${projectId}_${timestamp}`);
      }
      async getSpecFiles(specDirectory) {
        const files = [];
        const items = await fs2.readdir(specDirectory);
        for (const item of items) {
          const itemPath = path2.join(specDirectory, item);
          const stats = await fs2.stat(itemPath);
          if (stats.isDirectory()) {
            files.push(...await this.getSpecFiles(itemPath));
          } else if (item.endsWith(".md") || item.endsWith(".json")) {
            files.push(itemPath);
          }
        }
        return files;
      }
      async getDirectorySize(dirPath) {
        let size = 0;
        const items = await fs2.readdir(dirPath);
        for (const item of items) {
          const itemPath = path2.join(dirPath, item);
          const stats = await fs2.stat(itemPath);
          if (stats.isDirectory()) {
            size += await this.getDirectorySize(itemPath);
          } else {
            size += stats.size;
          }
        }
        return size;
      }
      async calculateChecksum(path3) {
        return `checksum_${Date.now()}_${Math.random()}`;
      }
      async calculateFileChecksum(filePath) {
        const stats = await fs2.stat(filePath);
        return `file_${stats.size}_${stats.mtime.getTime()}`;
      }
    };
    exports2.ModelSwitcher = ModelSwitcher;
  }
});

// dist/models/ProjectConfig.js
var require_ProjectConfig = __commonJS({
  "dist/models/ProjectConfig.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ProjectConfigValidator = void 0;
    var ProjectConfigValidator = class {
      static validate(config) {
        if (typeof config !== "object" || config === null) {
          return false;
        }
        const c = config;
        return typeof c.projectId === "string" && typeof c.name === "string" && (c.aiModel === "claude" || c.aiModel === "gemini" || c.aiModel === "copilot") && typeof c.version === "string" && typeof c.createdAt === "string" && typeof c.updatedAt === "string" && typeof c.specDirectory === "string" && typeof c.configPath === "string" && typeof c.isInitialized === "boolean" && Array.isArray(c.migrationHistory);
      }
      static create(params) {
        const now = (/* @__PURE__ */ new Date()).toISOString();
        return {
          ...params,
          version: "0.1.0",
          createdAt: now,
          updatedAt: now,
          isInitialized: false,
          migrationHistory: []
        };
      }
    };
    exports2.ProjectConfigValidator = ProjectConfigValidator;
  }
});

// dist/services/ConfigManager.js
var require_ConfigManager = __commonJS({
  "dist/services/ConfigManager.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ConfigManager = void 0;
    var ProjectConfig_1 = require_ProjectConfig();
    var fs2 = __importStar2(require_lib());
    var path2 = __importStar2(require("path"));
    var ConfigManager = class {
      constructor(options = {}) {
        this.options = {
          enableBackup: true,
          maxBackups: 10,
          validateOnLoad: true,
          atomicWrites: true,
          ...options
        };
        this.backupDirectory = "./.specify/backups/config";
      }
      async loadConfig(configPath) {
        try {
          if (!await fs2.pathExists(configPath)) {
            throw new Error(`Configuration file not found: ${configPath}`);
          }
          const configData = await fs2.readJson(configPath);
          if (this.options.validateOnLoad && !ProjectConfig_1.ProjectConfigValidator.validate(configData)) {
            throw new Error("Invalid configuration file format");
          }
          return configData;
        } catch (error) {
          throw new Error(`Failed to load configuration: ${error}`);
        }
      }
      async saveConfig(config) {
        try {
          if (!ProjectConfig_1.ProjectConfigValidator.validate(config)) {
            throw new Error("Invalid configuration data");
          }
          if (this.options.enableBackup && await fs2.pathExists(config.configPath)) {
            await this.createBackup(config.configPath);
          }
          await fs2.ensureDir(path2.dirname(config.configPath));
          const configToSave = {
            ...config,
            updatedAt: (/* @__PURE__ */ new Date()).toISOString()
          };
          if (this.options.atomicWrites) {
            await this.atomicWrite(config.configPath, configToSave);
          } else {
            await fs2.writeJson(config.configPath, configToSave, { spaces: 2 });
          }
        } catch (error) {
          throw new Error(`Failed to save configuration: ${error}`);
        }
      }
      async createConfig(params) {
        const configPath = path2.join(params.projectPath, ".specify", "config.json");
        const specDirectory = params.specDirectory || path2.join(params.projectPath, "specs");
        const config = ProjectConfig_1.ProjectConfigValidator.create({
          projectId: `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name: params.projectName,
          aiModel: params.aiModel,
          specDirectory,
          configPath
        });
        config.isInitialized = true;
        await this.saveConfig(config);
        return config;
      }
      async updateConfig(configPath, updates) {
        const existing = await this.loadConfig(configPath);
        const updated = {
          ...existing,
          ...updates,
          updatedAt: (/* @__PURE__ */ new Date()).toISOString()
        };
        await this.saveConfig(updated);
        return updated;
      }
      async validateConfig(configPath) {
        const errors = [];
        const warnings = [];
        try {
          if (!await fs2.pathExists(configPath)) {
            errors.push("Configuration file does not exist");
            return { valid: false, errors, warnings };
          }
          const configData = await fs2.readJson(configPath);
          if (!ProjectConfig_1.ProjectConfigValidator.validate(configData)) {
            errors.push("Invalid configuration file format");
          }
          const config = configData;
          if (!await fs2.pathExists(config.specDirectory)) {
            warnings.push("Specification directory does not exist");
          }
          const { AIModelSettingsProvider } = await Promise.resolve().then(() => __importStar2(require_AIModelSettings()));
          if (!AIModelSettingsProvider.getSettings(config.aiModel)) {
            errors.push(`Unknown AI model: ${config.aiModel}`);
          }
          const incompleteMigrations = config.migrationHistory.filter((m) => !m.success);
          if (incompleteMigrations.length > 0) {
            warnings.push(`${incompleteMigrations.length} incomplete migration(s) found`);
          }
          return {
            valid: errors.length === 0,
            errors,
            warnings
          };
        } catch (error) {
          errors.push(`Failed to validate configuration: ${error}`);
          return { valid: false, errors, warnings };
        }
      }
      async listBackups(configPath) {
        try {
          const configName = path2.basename(configPath);
          const backupPattern = path2.join(this.backupDirectory, `${configName}.backup.*`);
          const backupDir = path2.dirname(backupPattern);
          if (!await fs2.pathExists(backupDir)) {
            return [];
          }
          const files = await fs2.readdir(backupDir);
          const backupFiles = files.filter((file) => file.startsWith(`${configName}.backup.`)).map((file) => path2.join(backupDir, file));
          const backups = [];
          for (const backupPath of backupFiles) {
            try {
              const stats = await fs2.stat(backupPath);
              const timestampMatch = path2.basename(backupPath).match(/\.backup\.(.+)$/);
              backups.push({
                path: backupPath,
                timestamp: timestampMatch ? timestampMatch[1] : stats.mtime.toISOString(),
                originalPath: configPath,
                size: stats.size
              });
            } catch (error) {
            }
          }
          return backups.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        } catch (error) {
          return [];
        }
      }
      async restoreBackup(backupInfo) {
        try {
          if (!await fs2.pathExists(backupInfo.path)) {
            throw new Error("Backup file not found");
          }
          if (await fs2.pathExists(backupInfo.originalPath)) {
            await this.createBackup(backupInfo.originalPath);
          }
          await fs2.copy(backupInfo.path, backupInfo.originalPath);
        } catch (error) {
          throw new Error(`Failed to restore backup: ${error}`);
        }
      }
      async cleanupBackups(configPath) {
        try {
          const backups = await this.listBackups(configPath);
          if (backups.length <= this.options.maxBackups) {
            return 0;
          }
          const backupsToDelete = backups.slice(this.options.maxBackups);
          for (const backup of backupsToDelete) {
            try {
              await fs2.remove(backup.path);
            } catch (error) {
            }
          }
          return backupsToDelete.length;
        } catch (error) {
          return 0;
        }
      }
      async createBackup(configPath) {
        await fs2.ensureDir(this.backupDirectory);
        const timestamp = (/* @__PURE__ */ new Date()).toISOString().replace(/[:.]/g, "-");
        const configName = path2.basename(configPath);
        const backupPath = path2.join(this.backupDirectory, `${configName}.backup.${timestamp}`);
        await fs2.copy(configPath, backupPath);
        await this.cleanupBackups(configPath);
        return backupPath;
      }
      async atomicWrite(filePath, data) {
        const tempPath = `${filePath}.tmp`;
        try {
          await fs2.writeJson(tempPath, data, { spaces: 2 });
          await fs2.move(tempPath, filePath);
        } catch (error) {
          try {
            await fs2.remove(tempPath);
          } catch (cleanupError) {
          }
          throw error;
        }
      }
    };
    exports2.ConfigManager = ConfigManager;
  }
});

// dist/services/ProjectDetector.js
var require_ProjectDetector = __commonJS({
  "dist/services/ProjectDetector.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ProjectDetector = void 0;
    var ProjectConfig_1 = require_ProjectConfig();
    var fs2 = __importStar2(require_lib());
    var path2 = __importStar2(require("path"));
    var ProjectDetector = class _ProjectDetector {
      async detectProject(startPath = process.cwd(), options = {}) {
        const { searchDepth = 5, validateConfig = true, autoFix = false, includeDrafts = false } = options;
        const issues = [];
        const suggestions = [];
        try {
          const projectPath = await this.findSpecifyDirectory(startPath, searchDepth);
          if (!projectPath) {
            return {
              found: false,
              issues: [{
                type: "info",
                message: "No .specify directory found in current path or parent directories",
                fixable: true
              }],
              suggestions: [
                'Run "specify init" to initialize a new project',
                "Ensure you are in the correct project directory"
              ]
            };
          }
          const configPath = path2.join(projectPath, _ProjectDetector.SPECIFY_DIR, _ProjectDetector.CONFIG_FILE);
          if (!await fs2.pathExists(configPath)) {
            issues.push({
              type: "error",
              message: "Configuration file not found",
              path: configPath,
              fixable: true
            });
            if (autoFix) {
              await this.createDefaultConfig(projectPath);
              suggestions.push("Created default configuration file");
            } else {
              suggestions.push('Run "specify detect-project --auto-fix" to create default configuration');
            }
          }
          let config;
          if (await fs2.pathExists(configPath)) {
            try {
              const configData = await fs2.readJson(configPath);
              if (validateConfig && !ProjectConfig_1.ProjectConfigValidator.validate(configData)) {
                issues.push({
                  type: "error",
                  message: "Invalid configuration file format",
                  path: configPath,
                  fixable: true
                });
                if (autoFix) {
                  config = await this.repairConfig(configData, projectPath);
                  suggestions.push("Repaired configuration file");
                } else {
                  suggestions.push("Run with --auto-fix to repair configuration");
                }
              } else {
                config = configData;
              }
            } catch (error) {
              issues.push({
                type: "error",
                message: `Failed to read configuration: ${error}`,
                path: configPath,
                fixable: false
              });
            }
          }
          await this.validateProjectStructure(projectPath, config, issues, suggestions, includeDrafts);
          if (config) {
            await this.checkMigrationIssues(config, issues, suggestions);
          }
          return {
            found: true,
            projectPath,
            config,
            issues,
            suggestions
          };
        } catch (error) {
          return {
            found: false,
            issues: [{
              type: "error",
              message: `Detection failed: ${error}`,
              fixable: false
            }],
            suggestions: ["Check file permissions and try again"]
          };
        }
      }
      async validateProject(projectPath, config) {
        const issues = [];
        const requiredDirs = [
          path2.join(projectPath, _ProjectDetector.SPECIFY_DIR),
          config.specDirectory
        ];
        for (const dir of requiredDirs) {
          if (!await fs2.pathExists(dir)) {
            issues.push({
              type: "error",
              message: `Required directory missing: ${dir}`,
              path: dir,
              fixable: true
            });
          }
        }
        if (!await fs2.pathExists(config.configPath)) {
          issues.push({
            type: "error",
            message: "Configuration file missing",
            path: config.configPath,
            fixable: true
          });
        }
        const modelSettings = await Promise.resolve().then(() => __importStar2(require_AIModelSettings()));
        const settings = modelSettings.AIModelSettingsProvider.getSettings(config.aiModel);
        if (!settings) {
          issues.push({
            type: "error",
            message: `Unknown AI model: ${config.aiModel}`,
            fixable: false
          });
        }
        const specFiles = await this.getSpecFiles(config.specDirectory);
        if (specFiles.length === 0) {
          issues.push({
            type: "warning",
            message: "No specification files found",
            path: config.specDirectory,
            fixable: false
          });
        }
        return issues;
      }
      async repairProject(projectPath, config) {
        const issues = [];
        const suggestions = [];
        try {
          const specifyDir = path2.join(projectPath, _ProjectDetector.SPECIFY_DIR);
          await fs2.ensureDir(specifyDir);
          let repairedConfig = config;
          if (!config) {
            repairedConfig = await this.createDefaultConfig(projectPath);
            suggestions.push("Created default configuration");
          } else {
            const validation = await this.validateProject(projectPath, config);
            for (const issue of validation) {
              if (issue.fixable) {
                await this.fixIssue(issue, projectPath, config);
                suggestions.push(`Fixed: ${issue.message}`);
              } else {
                issues.push(issue);
              }
            }
          }
          if (repairedConfig) {
            await fs2.ensureDir(repairedConfig.specDirectory);
          }
          return {
            found: true,
            projectPath,
            config: repairedConfig,
            issues,
            suggestions
          };
        } catch (error) {
          return {
            found: false,
            issues: [{
              type: "error",
              message: `Repair failed: ${error}`,
              fixable: false
            }],
            suggestions: []
          };
        }
      }
      async findSpecifyDirectory(startPath, maxDepth) {
        let currentPath = path2.resolve(startPath);
        let depth = 0;
        while (depth <= maxDepth) {
          const specifyPath = path2.join(currentPath, _ProjectDetector.SPECIFY_DIR);
          if (await fs2.pathExists(specifyPath)) {
            const stats = await fs2.stat(specifyPath);
            if (stats.isDirectory()) {
              return currentPath;
            }
          }
          const parentPath = path2.dirname(currentPath);
          if (parentPath === currentPath) {
            break;
          }
          currentPath = parentPath;
          depth++;
        }
        return null;
      }
      async createDefaultConfig(projectPath) {
        const projectName = path2.basename(projectPath);
        const configPath = path2.join(projectPath, _ProjectDetector.SPECIFY_DIR, _ProjectDetector.CONFIG_FILE);
        const specDirectory = path2.join(projectPath, _ProjectDetector.SPEC_DIR);
        const config = ProjectConfig_1.ProjectConfigValidator.create({
          projectId: `project_${Date.now()}`,
          name: projectName,
          aiModel: "claude",
          // Default to Claude
          specDirectory,
          configPath
        });
        config.isInitialized = true;
        await fs2.ensureDir(path2.dirname(configPath));
        await fs2.writeJson(configPath, config, { spaces: 2 });
        return config;
      }
      async repairConfig(configData, projectPath) {
        const projectName = path2.basename(projectPath);
        const configPath = path2.join(projectPath, _ProjectDetector.SPECIFY_DIR, _ProjectDetector.CONFIG_FILE);
        const repairedConfig = {
          projectId: configData.projectId || `project_${Date.now()}`,
          name: configData.name || projectName,
          aiModel: configData.aiModel || "claude",
          version: configData.version || "0.1.0",
          createdAt: configData.createdAt || (/* @__PURE__ */ new Date()).toISOString(),
          updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
          specDirectory: configData.specDirectory || path2.join(projectPath, _ProjectDetector.SPEC_DIR),
          configPath: configData.configPath || configPath,
          isInitialized: configData.isInitialized !== void 0 ? configData.isInitialized : true,
          migrationHistory: configData.migrationHistory || []
        };
        await fs2.writeJson(configPath, repairedConfig, { spaces: 2 });
        return repairedConfig;
      }
      async validateProjectStructure(projectPath, config, issues, suggestions, includeDrafts) {
        const expectedFiles = [
          "package.json",
          "tsconfig.json",
          ".gitignore"
        ];
        for (const file of expectedFiles) {
          const filePath = path2.join(projectPath, file);
          if (!await fs2.pathExists(filePath)) {
            issues.push({
              type: "info",
              message: `Recommended file missing: ${file}`,
              path: filePath,
              fixable: false
            });
          }
        }
        if (config) {
          const specDir = config.specDirectory;
          if (await fs2.pathExists(specDir)) {
            const specFiles = await this.getSpecFiles(specDir);
            if (specFiles.length === 0 && !includeDrafts) {
              suggestions.push('No specification files found - consider running "specify init" to create initial specs');
            }
            const hasFeatureSpecs = specFiles.some((f) => f.includes("spec.md"));
            const hasPlans = specFiles.some((f) => f.includes("plan.md"));
            const hasTasks = specFiles.some((f) => f.includes("tasks.md"));
            if (!hasFeatureSpecs && specFiles.length > 0) {
              issues.push({
                type: "info",
                message: "No feature specification files (spec.md) found",
                fixable: false
              });
            }
          }
        }
      }
      async checkMigrationIssues(config, issues, suggestions) {
        const incompleteMigrations = config.migrationHistory.filter((m) => !m.success);
        if (incompleteMigrations.length > 0) {
          issues.push({
            type: "warning",
            message: `${incompleteMigrations.length} incomplete migration(s) found`,
            fixable: true
          });
          suggestions.push('Run "specify reset-project --repair" to clean up incomplete migrations');
        }
        const backupDir = path2.join(path2.dirname(config.configPath), "..", "backups");
        if (await fs2.pathExists(backupDir)) {
          const backups = await fs2.readdir(backupDir);
          if (backups.length > 10) {
            suggestions.push(`${backups.length} backup files found - consider cleaning old backups`);
          }
        }
      }
      async getSpecFiles(specDirectory) {
        const files = [];
        try {
          const items = await fs2.readdir(specDirectory);
          for (const item of items) {
            const itemPath = path2.join(specDirectory, item);
            const stats = await fs2.stat(itemPath);
            if (stats.isDirectory()) {
              files.push(...await this.getSpecFiles(itemPath));
            } else if (item.endsWith(".md") || item.endsWith(".json")) {
              files.push(itemPath);
            }
          }
        } catch (error) {
        }
        return files;
      }
      async fixIssue(issue, projectPath, config) {
        if (!issue.path)
          return;
        switch (issue.type) {
          case "error":
            if (issue.message.includes("directory missing")) {
              await fs2.ensureDir(issue.path);
            } else if (issue.message.includes("Configuration file")) {
              await this.createDefaultConfig(projectPath);
            }
            break;
        }
      }
    };
    exports2.ProjectDetector = ProjectDetector;
    ProjectDetector.SPECIFY_DIR = ".specify";
    ProjectDetector.CONFIG_FILE = "config.json";
    ProjectDetector.SPEC_DIR = "specs";
  }
});

// node_modules/color-convert/index.js
var require_color_convert = __commonJS({
  "node_modules/color-convert/index.js"() {
  }
});

// node_modules/ansi-styles/index.js
var require_ansi_styles = __commonJS({
  "node_modules/ansi-styles/index.js"(exports2, module2) {
    "use strict";
    var wrapAnsi16 = (fn, offset) => (...args) => {
      const code = fn(...args);
      return `\x1B[${code + offset}m`;
    };
    var wrapAnsi256 = (fn, offset) => (...args) => {
      const code = fn(...args);
      return `\x1B[${38 + offset};5;${code}m`;
    };
    var wrapAnsi16m = (fn, offset) => (...args) => {
      const rgb = fn(...args);
      return `\x1B[${38 + offset};2;${rgb[0]};${rgb[1]};${rgb[2]}m`;
    };
    var ansi2ansi = (n) => n;
    var rgb2rgb = (r, g, b) => [r, g, b];
    var setLazyProperty = (object, property, get) => {
      Object.defineProperty(object, property, {
        get: () => {
          const value = get();
          Object.defineProperty(object, property, {
            value,
            enumerable: true,
            configurable: true
          });
          return value;
        },
        enumerable: true,
        configurable: true
      });
    };
    var colorConvert;
    var makeDynamicStyles = (wrap, targetSpace, identity, isBackground) => {
      if (colorConvert === void 0) {
        colorConvert = require_color_convert();
      }
      const offset = isBackground ? 10 : 0;
      const styles = {};
      for (const [sourceSpace, suite] of Object.entries(colorConvert)) {
        const name = sourceSpace === "ansi16" ? "ansi" : sourceSpace;
        if (sourceSpace === targetSpace) {
          styles[name] = wrap(identity, offset);
        } else if (typeof suite === "object") {
          styles[name] = wrap(suite[targetSpace], offset);
        }
      }
      return styles;
    };
    function assembleStyles() {
      const codes = /* @__PURE__ */ new Map();
      const styles = {
        modifier: {
          reset: [0, 0],
          // 21 isn't widely supported and 22 does the same thing
          bold: [1, 22],
          dim: [2, 22],
          italic: [3, 23],
          underline: [4, 24],
          inverse: [7, 27],
          hidden: [8, 28],
          strikethrough: [9, 29]
        },
        color: {
          black: [30, 39],
          red: [31, 39],
          green: [32, 39],
          yellow: [33, 39],
          blue: [34, 39],
          magenta: [35, 39],
          cyan: [36, 39],
          white: [37, 39],
          // Bright color
          blackBright: [90, 39],
          redBright: [91, 39],
          greenBright: [92, 39],
          yellowBright: [93, 39],
          blueBright: [94, 39],
          magentaBright: [95, 39],
          cyanBright: [96, 39],
          whiteBright: [97, 39]
        },
        bgColor: {
          bgBlack: [40, 49],
          bgRed: [41, 49],
          bgGreen: [42, 49],
          bgYellow: [43, 49],
          bgBlue: [44, 49],
          bgMagenta: [45, 49],
          bgCyan: [46, 49],
          bgWhite: [47, 49],
          // Bright color
          bgBlackBright: [100, 49],
          bgRedBright: [101, 49],
          bgGreenBright: [102, 49],
          bgYellowBright: [103, 49],
          bgBlueBright: [104, 49],
          bgMagentaBright: [105, 49],
          bgCyanBright: [106, 49],
          bgWhiteBright: [107, 49]
        }
      };
      styles.color.gray = styles.color.blackBright;
      styles.bgColor.bgGray = styles.bgColor.bgBlackBright;
      styles.color.grey = styles.color.blackBright;
      styles.bgColor.bgGrey = styles.bgColor.bgBlackBright;
      for (const [groupName, group] of Object.entries(styles)) {
        for (const [styleName, style] of Object.entries(group)) {
          styles[styleName] = {
            open: `\x1B[${style[0]}m`,
            close: `\x1B[${style[1]}m`
          };
          group[styleName] = styles[styleName];
          codes.set(style[0], style[1]);
        }
        Object.defineProperty(styles, groupName, {
          value: group,
          enumerable: false
        });
      }
      Object.defineProperty(styles, "codes", {
        value: codes,
        enumerable: false
      });
      styles.color.close = "\x1B[39m";
      styles.bgColor.close = "\x1B[49m";
      setLazyProperty(styles.color, "ansi", () => makeDynamicStyles(wrapAnsi16, "ansi16", ansi2ansi, false));
      setLazyProperty(styles.color, "ansi256", () => makeDynamicStyles(wrapAnsi256, "ansi256", ansi2ansi, false));
      setLazyProperty(styles.color, "ansi16m", () => makeDynamicStyles(wrapAnsi16m, "rgb", rgb2rgb, false));
      setLazyProperty(styles.bgColor, "ansi", () => makeDynamicStyles(wrapAnsi16, "ansi16", ansi2ansi, true));
      setLazyProperty(styles.bgColor, "ansi256", () => makeDynamicStyles(wrapAnsi256, "ansi256", ansi2ansi, true));
      setLazyProperty(styles.bgColor, "ansi16m", () => makeDynamicStyles(wrapAnsi16m, "rgb", rgb2rgb, true));
      return styles;
    }
    Object.defineProperty(module2, "exports", {
      enumerable: true,
      get: assembleStyles
    });
  }
});

// node_modules/has-flag/index.js
var require_has_flag = __commonJS({
  "node_modules/has-flag/index.js"(exports2, module2) {
    "use strict";
    module2.exports = (flag, argv = process.argv) => {
      const prefix = flag.startsWith("-") ? "" : flag.length === 1 ? "-" : "--";
      const position = argv.indexOf(prefix + flag);
      const terminatorPosition = argv.indexOf("--");
      return position !== -1 && (terminatorPosition === -1 || position < terminatorPosition);
    };
  }
});

// node_modules/supports-color/index.js
var require_supports_color = __commonJS({
  "node_modules/supports-color/index.js"(exports2, module2) {
    "use strict";
    var os = require("os");
    var tty = require("tty");
    var hasFlag = require_has_flag();
    var { env } = process;
    var forceColor;
    if (hasFlag("no-color") || hasFlag("no-colors") || hasFlag("color=false") || hasFlag("color=never")) {
      forceColor = 0;
    } else if (hasFlag("color") || hasFlag("colors") || hasFlag("color=true") || hasFlag("color=always")) {
      forceColor = 1;
    }
    if ("FORCE_COLOR" in env) {
      if (env.FORCE_COLOR === "true") {
        forceColor = 1;
      } else if (env.FORCE_COLOR === "false") {
        forceColor = 0;
      } else {
        forceColor = env.FORCE_COLOR.length === 0 ? 1 : Math.min(parseInt(env.FORCE_COLOR, 10), 3);
      }
    }
    function translateLevel(level) {
      if (level === 0) {
        return false;
      }
      return {
        level,
        hasBasic: true,
        has256: level >= 2,
        has16m: level >= 3
      };
    }
    function supportsColor(haveStream, streamIsTTY) {
      if (forceColor === 0) {
        return 0;
      }
      if (hasFlag("color=16m") || hasFlag("color=full") || hasFlag("color=truecolor")) {
        return 3;
      }
      if (hasFlag("color=256")) {
        return 2;
      }
      if (haveStream && !streamIsTTY && forceColor === void 0) {
        return 0;
      }
      const min = forceColor || 0;
      if (env.TERM === "dumb") {
        return min;
      }
      if (process.platform === "win32") {
        const osRelease = os.release().split(".");
        if (Number(osRelease[0]) >= 10 && Number(osRelease[2]) >= 10586) {
          return Number(osRelease[2]) >= 14931 ? 3 : 2;
        }
        return 1;
      }
      if ("CI" in env) {
        if (["TRAVIS", "CIRCLECI", "APPVEYOR", "GITLAB_CI", "GITHUB_ACTIONS", "BUILDKITE"].some((sign) => sign in env) || env.CI_NAME === "codeship") {
          return 1;
        }
        return min;
      }
      if ("TEAMCITY_VERSION" in env) {
        return /^(9\.(0*[1-9]\d*)\.|\d{2,}\.)/.test(env.TEAMCITY_VERSION) ? 1 : 0;
      }
      if (env.COLORTERM === "truecolor") {
        return 3;
      }
      if ("TERM_PROGRAM" in env) {
        const version = parseInt((env.TERM_PROGRAM_VERSION || "").split(".")[0], 10);
        switch (env.TERM_PROGRAM) {
          case "iTerm.app":
            return version >= 3 ? 3 : 2;
          case "Apple_Terminal":
            return 2;
        }
      }
      if (/-256(color)?$/i.test(env.TERM)) {
        return 2;
      }
      if (/^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux/i.test(env.TERM)) {
        return 1;
      }
      if ("COLORTERM" in env) {
        return 1;
      }
      return min;
    }
    function getSupportLevel(stream) {
      const level = supportsColor(stream, stream && stream.isTTY);
      return translateLevel(level);
    }
    module2.exports = {
      supportsColor: getSupportLevel,
      stdout: translateLevel(supportsColor(true, tty.isatty(1))),
      stderr: translateLevel(supportsColor(true, tty.isatty(2)))
    };
  }
});

// node_modules/chalk/source/util.js
var require_util = __commonJS({
  "node_modules/chalk/source/util.js"(exports2, module2) {
    "use strict";
    var stringReplaceAll = (string, substring, replacer) => {
      let index = string.indexOf(substring);
      if (index === -1) {
        return string;
      }
      const substringLength = substring.length;
      let endIndex = 0;
      let returnValue = "";
      do {
        returnValue += string.substr(endIndex, index - endIndex) + substring + replacer;
        endIndex = index + substringLength;
        index = string.indexOf(substring, endIndex);
      } while (index !== -1);
      returnValue += string.substr(endIndex);
      return returnValue;
    };
    var stringEncaseCRLFWithFirstIndex = (string, prefix, postfix, index) => {
      let endIndex = 0;
      let returnValue = "";
      do {
        const gotCR = string[index - 1] === "\r";
        returnValue += string.substr(endIndex, (gotCR ? index - 1 : index) - endIndex) + prefix + (gotCR ? "\r\n" : "\n") + postfix;
        endIndex = index + 1;
        index = string.indexOf("\n", endIndex);
      } while (index !== -1);
      returnValue += string.substr(endIndex);
      return returnValue;
    };
    module2.exports = {
      stringReplaceAll,
      stringEncaseCRLFWithFirstIndex
    };
  }
});

// node_modules/chalk/source/templates.js
var require_templates = __commonJS({
  "node_modules/chalk/source/templates.js"(exports2, module2) {
    "use strict";
    var TEMPLATE_REGEX = /(?:\\(u(?:[a-f\d]{4}|\{[a-f\d]{1,6}\})|x[a-f\d]{2}|.))|(?:\{(~)?(\w+(?:\([^)]*\))?(?:\.\w+(?:\([^)]*\))?)*)(?:[ \t]|(?=\r?\n)))|(\})|((?:.|[\r\n\f])+?)/gi;
    var STYLE_REGEX = /(?:^|\.)(\w+)(?:\(([^)]*)\))?/g;
    var STRING_REGEX = /^(['"])((?:\\.|(?!\1)[^\\])*)\1$/;
    var ESCAPE_REGEX = /\\(u(?:[a-f\d]{4}|{[a-f\d]{1,6}})|x[a-f\d]{2}|.)|([^\\])/gi;
    var ESCAPES = /* @__PURE__ */ new Map([
      ["n", "\n"],
      ["r", "\r"],
      ["t", "	"],
      ["b", "\b"],
      ["f", "\f"],
      ["v", "\v"],
      ["0", "\0"],
      ["\\", "\\"],
      ["e", "\x1B"],
      ["a", "\x07"]
    ]);
    function unescape(c) {
      const u = c[0] === "u";
      const bracket = c[1] === "{";
      if (u && !bracket && c.length === 5 || c[0] === "x" && c.length === 3) {
        return String.fromCharCode(parseInt(c.slice(1), 16));
      }
      if (u && bracket) {
        return String.fromCodePoint(parseInt(c.slice(2, -1), 16));
      }
      return ESCAPES.get(c) || c;
    }
    function parseArguments(name, arguments_) {
      const results = [];
      const chunks = arguments_.trim().split(/\s*,\s*/g);
      let matches;
      for (const chunk of chunks) {
        const number = Number(chunk);
        if (!Number.isNaN(number)) {
          results.push(number);
        } else if (matches = chunk.match(STRING_REGEX)) {
          results.push(matches[2].replace(ESCAPE_REGEX, (m, escape, character) => escape ? unescape(escape) : character));
        } else {
          throw new Error(`Invalid Chalk template style argument: ${chunk} (in style '${name}')`);
        }
      }
      return results;
    }
    function parseStyle(style) {
      STYLE_REGEX.lastIndex = 0;
      const results = [];
      let matches;
      while ((matches = STYLE_REGEX.exec(style)) !== null) {
        const name = matches[1];
        if (matches[2]) {
          const args = parseArguments(name, matches[2]);
          results.push([name].concat(args));
        } else {
          results.push([name]);
        }
      }
      return results;
    }
    function buildStyle(chalk, styles) {
      const enabled = {};
      for (const layer of styles) {
        for (const style of layer.styles) {
          enabled[style[0]] = layer.inverse ? null : style.slice(1);
        }
      }
      let current = chalk;
      for (const [styleName, styles2] of Object.entries(enabled)) {
        if (!Array.isArray(styles2)) {
          continue;
        }
        if (!(styleName in current)) {
          throw new Error(`Unknown Chalk style: ${styleName}`);
        }
        current = styles2.length > 0 ? current[styleName](...styles2) : current[styleName];
      }
      return current;
    }
    module2.exports = (chalk, temporary) => {
      const styles = [];
      const chunks = [];
      let chunk = [];
      temporary.replace(TEMPLATE_REGEX, (m, escapeCharacter, inverse, style, close, character) => {
        if (escapeCharacter) {
          chunk.push(unescape(escapeCharacter));
        } else if (style) {
          const string = chunk.join("");
          chunk = [];
          chunks.push(styles.length === 0 ? string : buildStyle(chalk, styles)(string));
          styles.push({ inverse, styles: parseStyle(style) });
        } else if (close) {
          if (styles.length === 0) {
            throw new Error("Found extraneous } in Chalk template literal");
          }
          chunks.push(buildStyle(chalk, styles)(chunk.join("")));
          chunk = [];
          styles.pop();
        } else {
          chunk.push(character);
        }
      });
      chunks.push(chunk.join(""));
      if (styles.length > 0) {
        const errMessage = `Chalk template literal is missing ${styles.length} closing bracket${styles.length === 1 ? "" : "s"} (\`}\`)`;
        throw new Error(errMessage);
      }
      return chunks.join("");
    };
  }
});

// node_modules/chalk/source/index.js
var require_source = __commonJS({
  "node_modules/chalk/source/index.js"(exports2, module2) {
    "use strict";
    var ansiStyles = require_ansi_styles();
    var { stdout: stdoutColor, stderr: stderrColor } = require_supports_color();
    var {
      stringReplaceAll,
      stringEncaseCRLFWithFirstIndex
    } = require_util();
    var { isArray } = Array;
    var levelMapping = [
      "ansi",
      "ansi",
      "ansi256",
      "ansi16m"
    ];
    var styles = /* @__PURE__ */ Object.create(null);
    var applyOptions = (object, options = {}) => {
      if (options.level && !(Number.isInteger(options.level) && options.level >= 0 && options.level <= 3)) {
        throw new Error("The `level` option should be an integer from 0 to 3");
      }
      const colorLevel = stdoutColor ? stdoutColor.level : 0;
      object.level = options.level === void 0 ? colorLevel : options.level;
    };
    var ChalkClass = class {
      constructor(options) {
        return chalkFactory(options);
      }
    };
    var chalkFactory = (options) => {
      const chalk2 = {};
      applyOptions(chalk2, options);
      chalk2.template = (...arguments_) => chalkTag(chalk2.template, ...arguments_);
      Object.setPrototypeOf(chalk2, Chalk.prototype);
      Object.setPrototypeOf(chalk2.template, chalk2);
      chalk2.template.constructor = () => {
        throw new Error("`chalk.constructor()` is deprecated. Use `new chalk.Instance()` instead.");
      };
      chalk2.template.Instance = ChalkClass;
      return chalk2.template;
    };
    function Chalk(options) {
      return chalkFactory(options);
    }
    for (const [styleName, style] of Object.entries(ansiStyles)) {
      styles[styleName] = {
        get() {
          const builder = createBuilder(this, createStyler(style.open, style.close, this._styler), this._isEmpty);
          Object.defineProperty(this, styleName, { value: builder });
          return builder;
        }
      };
    }
    styles.visible = {
      get() {
        const builder = createBuilder(this, this._styler, true);
        Object.defineProperty(this, "visible", { value: builder });
        return builder;
      }
    };
    var usedModels = ["rgb", "hex", "keyword", "hsl", "hsv", "hwb", "ansi", "ansi256"];
    for (const model of usedModels) {
      styles[model] = {
        get() {
          const { level } = this;
          return function(...arguments_) {
            const styler = createStyler(ansiStyles.color[levelMapping[level]][model](...arguments_), ansiStyles.color.close, this._styler);
            return createBuilder(this, styler, this._isEmpty);
          };
        }
      };
    }
    for (const model of usedModels) {
      const bgModel = "bg" + model[0].toUpperCase() + model.slice(1);
      styles[bgModel] = {
        get() {
          const { level } = this;
          return function(...arguments_) {
            const styler = createStyler(ansiStyles.bgColor[levelMapping[level]][model](...arguments_), ansiStyles.bgColor.close, this._styler);
            return createBuilder(this, styler, this._isEmpty);
          };
        }
      };
    }
    var proto = Object.defineProperties(() => {
    }, {
      ...styles,
      level: {
        enumerable: true,
        get() {
          return this._generator.level;
        },
        set(level) {
          this._generator.level = level;
        }
      }
    });
    var createStyler = (open, close, parent) => {
      let openAll;
      let closeAll;
      if (parent === void 0) {
        openAll = open;
        closeAll = close;
      } else {
        openAll = parent.openAll + open;
        closeAll = close + parent.closeAll;
      }
      return {
        open,
        close,
        openAll,
        closeAll,
        parent
      };
    };
    var createBuilder = (self, _styler, _isEmpty) => {
      const builder = (...arguments_) => {
        if (isArray(arguments_[0]) && isArray(arguments_[0].raw)) {
          return applyStyle(builder, chalkTag(builder, ...arguments_));
        }
        return applyStyle(builder, arguments_.length === 1 ? "" + arguments_[0] : arguments_.join(" "));
      };
      Object.setPrototypeOf(builder, proto);
      builder._generator = self;
      builder._styler = _styler;
      builder._isEmpty = _isEmpty;
      return builder;
    };
    var applyStyle = (self, string) => {
      if (self.level <= 0 || !string) {
        return self._isEmpty ? "" : string;
      }
      let styler = self._styler;
      if (styler === void 0) {
        return string;
      }
      const { openAll, closeAll } = styler;
      if (string.indexOf("\x1B") !== -1) {
        while (styler !== void 0) {
          string = stringReplaceAll(string, styler.close, styler.open);
          styler = styler.parent;
        }
      }
      const lfIndex = string.indexOf("\n");
      if (lfIndex !== -1) {
        string = stringEncaseCRLFWithFirstIndex(string, closeAll, openAll, lfIndex);
      }
      return openAll + string + closeAll;
    };
    var template;
    var chalkTag = (chalk2, ...strings) => {
      const [firstString] = strings;
      if (!isArray(firstString) || !isArray(firstString.raw)) {
        return strings.join(" ");
      }
      const arguments_ = strings.slice(1);
      const parts = [firstString.raw[0]];
      for (let i = 1; i < firstString.length; i++) {
        parts.push(
          String(arguments_[i - 1]).replace(/[{}\\]/g, "\\$&"),
          String(firstString.raw[i])
        );
      }
      if (template === void 0) {
        template = require_templates();
      }
      return template(chalk2, parts.join(""));
    };
    Object.defineProperties(Chalk.prototype, styles);
    var chalk = Chalk();
    chalk.supportsColor = stdoutColor;
    chalk.stderr = Chalk({ level: stderrColor ? stderrColor.level : 0 });
    chalk.stderr.supportsColor = stderrColor;
    module2.exports = chalk;
  }
});

// dist/cli/SwitchModelCommand.js
var require_SwitchModelCommand = __commonJS({
  "dist/cli/SwitchModelCommand.js"(exports2) {
    "use strict";
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.SwitchModelCommand = void 0;
    var commander_12 = require_commander();
    var ModelSwitcher_1 = require_ModelSwitcher();
    var ConfigManager_1 = require_ConfigManager();
    var ProjectDetector_1 = require_ProjectDetector();
    var chalk_12 = __importDefault2(require_source());
    var SwitchModelCommand = class {
      constructor() {
        this.configManager = new ConfigManager_1.ConfigManager();
        this.modelSwitcher = new ModelSwitcher_1.ModelSwitcher(this.configManager);
        this.projectDetector = new ProjectDetector_1.ProjectDetector();
      }
      create() {
        const command = new commander_12.Command("switch-model");
        command.description("Switch AI model without losing project progress").argument("<target>", "Target AI model (claude or gemini)").option("--backup", "Create backup before switching (default: true)", true).option("--dry-run", "Show what would be changed without making changes", false).option("--force", "Force switch even if validation fails", false).option("--no-validate", "Skip validation checks", false).action(async (target, options) => {
          await this.execute(target, options);
        });
        return command;
      }
      async execute(target, options) {
        try {
          if (!["claude", "gemini"].includes(target)) {
            console.error(chalk_12.default.red(`Error: Invalid target model '${target}'. Must be 'claude' or 'gemini'.`));
            process.exit(1);
          }
          const targetModel = target;
          console.log(chalk_12.default.blue("\u{1F504} Switching AI Model..."));
          console.log(chalk_12.default.gray(`Target model: ${targetModel}`));
          const detection = await this.projectDetector.detectProject();
          if (!detection.found || !detection.config) {
            console.error(chalk_12.default.red("\u274C No spec-kit project found in current directory"));
            console.error(chalk_12.default.gray('Run "specify detect-project" for more information'));
            process.exit(1);
          }
          const currentConfig = detection.config;
          if (currentConfig.aiModel === targetModel) {
            console.log(chalk_12.default.yellow(`\u26A0\uFE0F  Project is already using ${targetModel}`));
            return;
          }
          console.log(chalk_12.default.gray(`Current model: ${currentConfig.aiModel}`));
          if (options.validate !== false && !options.force) {
            console.log(chalk_12.default.blue("\u{1F50D} Validating project..."));
            const validation = await this.configManager.validateConfig(currentConfig.configPath);
            if (!validation.valid && !options.force) {
              console.error(chalk_12.default.red("\u274C Project validation failed:"));
              validation.errors.forEach((error) => {
                console.error(chalk_12.default.red(`  \u2022 ${error}`));
              });
              if (validation.warnings.length > 0) {
                console.warn(chalk_12.default.yellow("\u26A0\uFE0F  Warnings:"));
                validation.warnings.forEach((warning) => {
                  console.warn(chalk_12.default.yellow(`  \u2022 ${warning}`));
                });
              }
              console.error(chalk_12.default.gray("Use --force to proceed anyway"));
              process.exit(1);
            }
            if (validation.warnings.length > 0) {
              console.warn(chalk_12.default.yellow("\u26A0\uFE0F  Warnings found:"));
              validation.warnings.forEach((warning) => {
                console.warn(chalk_12.default.yellow(`  \u2022 ${warning}`));
              });
            }
          }
          if (options.dryRun) {
            console.log(chalk_12.default.cyan("\u{1F3C3} Dry run mode - no changes will be made"));
          }
          console.log(chalk_12.default.blue("\u{1F680} Starting model migration..."));
          const result = await this.modelSwitcher.switchModel(currentConfig, {
            targetModel,
            createBackup: options.backup,
            dryRun: options.dryRun,
            force: options.force
          });
          if (!result.success) {
            console.error(chalk_12.default.red(`\u274C Migration failed: ${result.errorMessage}`));
            if (result.backupPath) {
              console.error(chalk_12.default.gray(`Backup available at: ${result.backupPath}`));
            }
            process.exit(1);
          }
          if (options.dryRun) {
            console.log(chalk_12.default.green("\u2705 Dry run completed successfully"));
            console.log(chalk_12.default.gray("No actual changes were made to your project"));
          } else {
            console.log(chalk_12.default.green(`\u2705 Successfully switched to ${targetModel}!`));
            console.log(chalk_12.default.gray(`Migration ID: ${result.migrationId}`));
            if (result.backupPath) {
              console.log(chalk_12.default.gray(`Backup created: ${result.backupPath}`));
            }
          }
          if (result.warnings.length > 0) {
            console.warn(chalk_12.default.yellow("\u26A0\uFE0F  Warnings:"));
            result.warnings.forEach((warning) => {
              console.warn(chalk_12.default.yellow(`  \u2022 ${warning}`));
            });
          }
          if (!options.dryRun) {
            console.log(chalk_12.default.blue("\n\u{1F4CB} Next steps:"));
            console.log(chalk_12.default.gray("  \u2022 Test your project to ensure everything works correctly"));
            console.log(chalk_12.default.gray("  \u2022 Update any model-specific configurations if needed"));
            console.log(chalk_12.default.gray(`  \u2022 Use "specify list-models" to see ${targetModel} capabilities`));
          }
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Unexpected error: ${error}`));
          process.exit(1);
        }
      }
      async validateArgs(target) {
        const errors = [];
        const suggestions = [];
        if (!target) {
          errors.push("Target model is required");
          suggestions.push("Specify target model: specify switch-model <claude|gemini>");
        } else if (!["claude", "gemini"].includes(target)) {
          errors.push(`Invalid target model: ${target}`);
          suggestions.push("Valid models are: claude, gemini");
        }
        return {
          valid: errors.length === 0,
          errors,
          suggestions
        };
      }
      getUsageExamples() {
        return [
          "specify switch-model claude",
          "specify switch-model gemini --dry-run",
          "specify switch-model claude --force --no-backup",
          "specify switch-model gemini --validate"
        ];
      }
    };
    exports2.SwitchModelCommand = SwitchModelCommand;
  }
});

// dist/cli/ListModelsCommand.js
var require_ListModelsCommand = __commonJS({
  "dist/cli/ListModelsCommand.js"(exports2) {
    "use strict";
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ListModelsCommand = void 0;
    var commander_12 = require_commander();
    var AIModelSettings_1 = require_AIModelSettings();
    var ProjectDetector_1 = require_ProjectDetector();
    var chalk_12 = __importDefault2(require_source());
    var ListModelsCommand = class {
      constructor() {
        this.projectDetector = new ProjectDetector_1.ProjectDetector();
      }
      create() {
        const command = new commander_12.Command("list-models");
        command.description("Show available AI models and compatibility information").option("-f, --format <format>", "Output format (table, json, yaml)", "table").option("-d, --details", "Show detailed model information", false).option("-c, --current", "Show current project model only", false).option("--compatibility", "Show compatibility information", false).action(async (options) => {
          await this.execute(options);
        });
        return command;
      }
      async execute(options) {
        try {
          let currentProject = null;
          try {
            const detection = await this.projectDetector.detectProject();
            if (detection.found && detection.config) {
              currentProject = detection.config;
            }
          } catch (error) {
          }
          const allModels = AIModelSettings_1.AIModelSettingsProvider.getAllModels();
          const models = options.current && currentProject ? allModels.filter((model) => model.modelType === currentProject.aiModel) : allModels;
          if (models.length === 0) {
            if (options.current) {
              console.error(chalk_12.default.red("\u274C No current project found or invalid model configuration"));
            } else {
              console.error(chalk_12.default.red("\u274C No models available"));
            }
            process.exit(1);
          }
          switch (options.format) {
            case "json":
              await this.outputJson(models, currentProject, options);
              break;
            case "yaml":
              await this.outputYaml(models, currentProject, options);
              break;
            case "table":
            default:
              await this.outputTable(models, currentProject, options);
              break;
          }
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Error listing models: ${error}`));
          process.exit(1);
        }
      }
      async outputTable(models, currentProject, options) {
        console.log(chalk_12.default.blue("\u{1F916} Available AI Models\n"));
        if (currentProject) {
          console.log(chalk_12.default.gray(`Current project: ${currentProject.name} (${currentProject.aiModel})
`));
        }
        for (const model of models) {
          const isCurrent = currentProject?.aiModel === model.modelType;
          const marker = isCurrent ? chalk_12.default.green("\u25CF ") : "  ";
          const name = isCurrent ? chalk_12.default.green.bold(model.modelType) : chalk_12.default.white(model.modelType);
          console.log(`${marker}${name} v${model.version}`);
          if (options.details) {
            console.log(chalk_12.default.gray(`    Max tokens: ${model.capabilities.maxTokens.toLocaleString()}`));
            console.log(chalk_12.default.gray(`    Rate limit: ${model.capabilities.rateLimit.requestsPerMinute}/min`));
            console.log(chalk_12.default.gray(`    Features: ${model.capabilities.features.length} available`));
            if (model.capabilities.features.length > 0) {
              const enabledFeatures = model.capabilities.features.filter((f) => f.enabled).map((f) => f.name);
              console.log(chalk_12.default.gray(`    Enabled: ${enabledFeatures.join(", ")}`));
            }
            if (options.compatibility) {
              const compatible = currentProject ? AIModelSettings_1.AIModelSettingsProvider.isCompatible(model.modelType, "0.1.0") : true;
              console.log(chalk_12.default.gray(`    Compatible: ${compatible ? "\u2705" : "\u274C"}`));
              console.log(chalk_12.default.gray(`    Min CLI version: ${model.compatibility.minimumCliVersion}`));
            }
            if (model.compatibility.deprecationWarning) {
              console.log(chalk_12.default.yellow(`    \u26A0\uFE0F  ${model.compatibility.deprecationWarning}`));
            }
            console.log();
          }
        }
        if (!options.details) {
          console.log(chalk_12.default.gray("\nUse --details for more information"));
        }
        if (models.length > 1 && currentProject) {
          const otherModels = models.filter((m) => m.modelType !== currentProject.aiModel);
          if (otherModels.length > 0) {
            console.log(chalk_12.default.blue("\n\u{1F504} Migration Options:"));
            for (const model of otherModels) {
              console.log(chalk_12.default.gray(`  specify switch-model ${model.modelType}`));
            }
          }
        }
      }
      async outputJson(models, currentProject, options) {
        const output = {
          currentProject: currentProject ? {
            name: currentProject.name,
            model: currentProject.aiModel,
            version: currentProject.version
          } : null,
          models: models.map((model) => ({
            type: model.modelType,
            version: model.version,
            current: currentProject?.aiModel === model.modelType,
            capabilities: options.details ? model.capabilities : {
              maxTokens: model.capabilities.maxTokens,
              features: model.capabilities.features.length
            },
            compatibility: options.compatibility ? model.compatibility : {
              minimumCliVersion: model.compatibility.minimumCliVersion,
              migrationSupport: model.compatibility.migrationSupport
            },
            configuration: options.details ? model.configuration : void 0
          })),
          summary: {
            total: models.length,
            compatible: models.filter((m) => AIModelSettings_1.AIModelSettingsProvider.isCompatible(m.modelType, "0.1.0")).length
          }
        };
        console.log(JSON.stringify(output, null, 2));
      }
      async outputYaml(models, currentProject, options) {
        console.log("models:");
        for (const model of models) {
          console.log(`  ${model.modelType}:`);
          console.log(`    version: "${model.version}"`);
          console.log(`    current: ${currentProject?.aiModel === model.modelType}`);
          if (options.details) {
            console.log(`    capabilities:`);
            console.log(`      maxTokens: ${model.capabilities.maxTokens}`);
            console.log(`      features: ${model.capabilities.features.length}`);
            console.log(`      rateLimit:`);
            console.log(`        requestsPerMinute: ${model.capabilities.rateLimit.requestsPerMinute}`);
          }
          if (options.compatibility) {
            console.log(`    compatibility:`);
            console.log(`      minimumCliVersion: "${model.compatibility.minimumCliVersion}"`);
            console.log(`      migrationSupport: ${model.compatibility.migrationSupport}`);
          }
          console.log();
        }
        if (currentProject) {
          console.log("currentProject:");
          console.log(`  name: "${currentProject.name}"`);
          console.log(`  model: "${currentProject.aiModel}"`);
          console.log(`  version: "${currentProject.version}"`);
        }
      }
      getUsageExamples() {
        return [
          "specify list-models",
          "specify list-models --details",
          "specify list-models --format json",
          "specify list-models --current --compatibility",
          "specify list-models --format yaml --details"
        ];
      }
      async getModelSuggestions(currentModel) {
        const models = AIModelSettings_1.AIModelSettingsProvider.getAllModels();
        const suggestions = [];
        for (const model of models) {
          if (model.modelType !== currentModel) {
            const features = model.capabilities.features.filter((f) => f.enabled).map((f) => f.name);
            suggestions.push(`${model.modelType}: ${features.join(", ")} (${model.capabilities.maxTokens.toLocaleString()} tokens)`);
          }
        }
        return suggestions;
      }
      async compareModels(model1, model2) {
        const modelA = AIModelSettings_1.AIModelSettingsProvider.getSettings(model1);
        const modelB = AIModelSettings_1.AIModelSettingsProvider.getSettings(model2);
        if (!modelA || !modelB) {
          return null;
        }
        const differences = [];
        if (modelA.capabilities.maxTokens !== modelB.capabilities.maxTokens) {
          differences.push(`Max tokens: ${modelA.modelType} (${modelA.capabilities.maxTokens.toLocaleString()}) vs ${modelB.modelType} (${modelB.capabilities.maxTokens.toLocaleString()})`);
        }
        const featuresA = new Set(modelA.capabilities.features.map((f) => f.name));
        const featuresB = new Set(modelB.capabilities.features.map((f) => f.name));
        const onlyInA = [...featuresA].filter((f) => !featuresB.has(f));
        const onlyInB = [...featuresB].filter((f) => !featuresA.has(f));
        if (onlyInA.length > 0) {
          differences.push(`${modelA.modelType} exclusive features: ${onlyInA.join(", ")}`);
        }
        if (onlyInB.length > 0) {
          differences.push(`${modelB.modelType} exclusive features: ${onlyInB.join(", ")}`);
        }
        return {
          model1: modelA,
          model2: modelB,
          differences
        };
      }
    };
    exports2.ListModelsCommand = ListModelsCommand;
  }
});

// dist/cli/DetectProjectCommand.js
var require_DetectProjectCommand = __commonJS({
  "dist/cli/DetectProjectCommand.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.DetectProjectCommand = void 0;
    var commander_12 = require_commander();
    var ProjectDetector_1 = require_ProjectDetector();
    var chalk_12 = __importDefault2(require_source());
    var path2 = __importStar2(require("path"));
    var DetectProjectCommand = class {
      constructor() {
        this.projectDetector = new ProjectDetector_1.ProjectDetector();
      }
      create() {
        const command = new commander_12.Command("detect-project");
        command.description("Auto-detect existing spec-kit projects and validate configuration").option("--validate", "Perform detailed validation of project configuration", true).option("--auto-fix", "Automatically fix detected issues when possible", false).option("--repair", "Attempt to repair broken project configuration", false).option("-v, --verbose", "Show detailed information about detection process", false).option("-d, --depth <number>", "Search depth for project detection (default: 5)", "5").option("--include-drafts", "Include draft specifications in validation", false).action(async (options) => {
          await this.execute(options);
        });
        return command;
      }
      async execute(options) {
        try {
          const searchDepth = options.depth ? parseInt(options.depth.toString()) : 5;
          console.log(chalk_12.default.blue("\u{1F50D} Detecting spec-kit projects..."));
          if (options.verbose) {
            console.log(chalk_12.default.gray(`Search path: ${process.cwd()}`));
            console.log(chalk_12.default.gray(`Search depth: ${searchDepth}`));
            console.log(chalk_12.default.gray(`Auto-fix enabled: ${options.autoFix ? "Yes" : "No"}`));
          }
          const result = await this.projectDetector.detectProject(process.cwd(), {
            searchDepth,
            validateConfig: options.validate,
            autoFix: options.autoFix,
            includeDrafts: options.includeDrafts
          });
          if (!result.found) {
            console.log(chalk_12.default.yellow("\u274C No spec-kit project detected"));
            if (result.issues.length > 0) {
              console.log(chalk_12.default.gray("\nDetection issues:"));
              this.displayIssues(result.issues);
            }
            if (result.suggestions.length > 0) {
              console.log(chalk_12.default.blue("\n\u{1F4A1} Suggestions:"));
              result.suggestions.forEach((suggestion) => {
                console.log(chalk_12.default.gray(`  \u2022 ${suggestion}`));
              });
            }
            return;
          }
          console.log(chalk_12.default.green("\u2705 Spec-kit project detected!"));
          console.log(chalk_12.default.gray(`Project path: ${result.projectPath}`));
          if (result.config) {
            console.log(chalk_12.default.blue("\n\u{1F4CB} Project Information:"));
            console.log(`  Name: ${chalk_12.default.white(result.config.name)}`);
            console.log(`  AI Model: ${chalk_12.default.white(result.config.aiModel)}`);
            console.log(`  Version: ${chalk_12.default.white(result.config.version)}`);
            console.log(`  Initialized: ${result.config.isInitialized ? chalk_12.default.green("Yes") : chalk_12.default.yellow("No")}`);
            console.log(`  Spec Directory: ${chalk_12.default.gray(path2.relative(process.cwd(), result.config.specDirectory))}`);
            if (result.config.migrationHistory.length > 0) {
              console.log(`  Migrations: ${chalk_12.default.white(result.config.migrationHistory.length)} completed`);
              if (options.verbose) {
                console.log(chalk_12.default.blue("\n\u{1F504} Migration History:"));
                result.config.migrationHistory.slice(-3).forEach((migration) => {
                  const status = migration.success ? chalk_12.default.green("\u2705") : chalk_12.default.red("\u274C");
                  console.log(`    ${status} ${migration.fromModel} \u2192 ${migration.toModel} (${new Date(migration.timestamp).toLocaleDateString()})`);
                });
              }
            }
          }
          if (result.issues.length > 0) {
            const errors = result.issues.filter((i) => i.type === "error");
            const warnings = result.issues.filter((i) => i.type === "warning");
            const info = result.issues.filter((i) => i.type === "info");
            if (errors.length > 0) {
              console.log(chalk_12.default.red("\n\u274C Errors found:"));
              this.displayIssues(errors);
            }
            if (warnings.length > 0) {
              console.log(chalk_12.default.yellow("\n\u26A0\uFE0F  Warnings:"));
              this.displayIssues(warnings);
            }
            if (info.length > 0 && options.verbose) {
              console.log(chalk_12.default.blue("\n\u2139\uFE0F  Information:"));
              this.displayIssues(info);
            }
            if ((errors.length > 0 || warnings.length > 0) && !options.repair) {
              const fixableCount = result.issues.filter((i) => i.fixable).length;
              if (fixableCount > 0) {
                console.log(chalk_12.default.blue(`
\u{1F527} ${fixableCount} issue(s) can be automatically fixed`));
                console.log(chalk_12.default.gray("Run with --repair to attempt automatic repairs"));
              }
            }
          }
          if (result.suggestions.length > 0) {
            console.log(chalk_12.default.blue("\n\u{1F4A1} Suggestions:"));
            result.suggestions.forEach((suggestion) => {
              console.log(chalk_12.default.gray(`  \u2022 ${suggestion}`));
            });
          }
          if (options.repair && result.issues.some((i) => i.fixable)) {
            console.log(chalk_12.default.blue("\n\u{1F527} Attempting to repair project..."));
            const repairResult = await this.projectDetector.repairProject(result.projectPath, result.config);
            if (repairResult.found) {
              console.log(chalk_12.default.green("\u2705 Project repair completed successfully"));
              if (repairResult.suggestions.length > 0) {
                console.log(chalk_12.default.blue("\nRepair actions taken:"));
                repairResult.suggestions.forEach((suggestion) => {
                  console.log(chalk_12.default.gray(`  \u2022 ${suggestion}`));
                });
              }
              if (repairResult.issues.length > 0) {
                console.log(chalk_12.default.yellow("\nRemaining issues after repair:"));
                this.displayIssues(repairResult.issues);
              }
            } else {
              console.error(chalk_12.default.red("\u274C Project repair failed"));
              if (repairResult.issues.length > 0) {
                this.displayIssues(repairResult.issues);
              }
            }
          }
          if (result.config && result.issues.length === 0) {
            console.log(chalk_12.default.blue("\n\u{1F680} Next steps:"));
            console.log(chalk_12.default.gray('  \u2022 Use "specify list-models" to see available AI models'));
            console.log(chalk_12.default.gray('  \u2022 Use "specify switch-model <model>" to change AI models'));
            console.log(chalk_12.default.gray('  \u2022 Use "specify track-tasks enable" for task tracking UI'));
          }
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Detection failed: ${error}`));
          process.exit(1);
        }
      }
      displayIssues(issues) {
        issues.forEach((issue) => {
          const icon = this.getIssueIcon(issue.type);
          const color = this.getIssueColor(issue.type);
          console.log(color(`  ${icon} ${issue.message}`));
          if (issue.path) {
            console.log(chalk_12.default.gray(`    Path: ${issue.path}`));
          }
          if (issue.fixable) {
            console.log(chalk_12.default.gray(`    Fixable: Yes`));
          }
        });
      }
      getIssueIcon(type) {
        switch (type) {
          case "error":
            return "\u274C";
          case "warning":
            return "\u26A0\uFE0F";
          case "info":
            return "\u2139\uFE0F";
          default:
            return "\u2022";
        }
      }
      getIssueColor(type) {
        switch (type) {
          case "error":
            return chalk_12.default.red;
          case "warning":
            return chalk_12.default.yellow;
          case "info":
            return chalk_12.default.blue;
          default:
            return chalk_12.default.gray;
        }
      }
      async validateCurrentProject() {
        try {
          const result = await this.projectDetector.detectProject(process.cwd(), {
            validateConfig: true,
            autoFix: false
          });
          return {
            valid: result.found && result.issues.filter((i) => i.type === "error").length === 0,
            projectPath: result.projectPath,
            config: result.config,
            issues: result.issues
          };
        } catch (error) {
          return {
            valid: false,
            issues: [{
              type: "error",
              message: `Validation failed: ${error}`,
              fixable: false
            }]
          };
        }
      }
      getUsageExamples() {
        return [
          "specify detect-project",
          "specify detect-project --verbose",
          "specify detect-project --repair",
          "specify detect-project --auto-fix --include-drafts",
          "specify detect-project --depth 10"
        ];
      }
      async searchProjectsInDirectory(directory, maxDepth = 3) {
        const projects = [];
        try {
          const result = await this.projectDetector.detectProject(directory, {
            searchDepth: maxDepth,
            validateConfig: true
          });
          if (result.found && result.projectPath) {
            projects.push({
              path: result.projectPath,
              config: result.config,
              valid: result.issues.filter((i) => i.type === "error").length === 0
            });
          }
        } catch (error) {
        }
        return {
          projects,
          totalFound: projects.length
        };
      }
    };
    exports2.DetectProjectCommand = DetectProjectCommand;
  }
});

// dist/cli/ResetProjectCommand.js
var require_ResetProjectCommand = __commonJS({
  "dist/cli/ResetProjectCommand.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.ResetProjectCommand = void 0;
    var commander_12 = require_commander();
    var ProjectDetector_1 = require_ProjectDetector();
    var ConfigManager_1 = require_ConfigManager();
    var chalk_12 = __importDefault2(require_source());
    var fs2 = __importStar2(require_lib());
    var path2 = __importStar2(require("path"));
    var ResetProjectCommand = class {
      constructor() {
        this.projectDetector = new ProjectDetector_1.ProjectDetector();
        this.configManager = new ConfigManager_1.ConfigManager();
      }
      create() {
        const command = new commander_12.Command("reset-project");
        command.description("Clean project reset with backup and recovery options").option("--backup", "Create backup before reset (default: true)", true).option("--force", "Force reset without confirmation prompts", false).option("--repair", "Repair mode - fix issues without full reset", false).option("--keep-specs", "Keep specification files during reset", false).option("--keep-tasks", "Keep task tracking data during reset", false).option("--dry-run", "Show what would be reset without making changes", false).action(async (options) => {
          await this.execute(options);
        });
        return command;
      }
      async execute(options) {
        try {
          console.log(chalk_12.default.blue("\u{1F504} Project Reset Utility"));
          const detection = await this.projectDetector.detectProject();
          if (!detection.found) {
            console.log(chalk_12.default.yellow("\u26A0\uFE0F  No spec-kit project found in current directory"));
            console.log(chalk_12.default.gray("Nothing to reset"));
            return;
          }
          const projectPath = detection.projectPath;
          const config = detection.config;
          console.log(chalk_12.default.gray(`Project: ${config?.name || "Unknown"}`));
          console.log(chalk_12.default.gray(`Path: ${projectPath}`));
          if (options.dryRun) {
            console.log(chalk_12.default.cyan("\u{1F3C3} Dry run mode - no changes will be made\n"));
          }
          if (options.repair) {
            await this.repairProject(detection, options);
          } else {
            await this.resetProject(detection, options);
          }
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Reset operation failed: ${error}`));
          process.exit(1);
        }
      }
      async repairProject(detection, options) {
        console.log(chalk_12.default.blue("\u{1F527} Repair Mode - Fixing project issues\n"));
        const issues = detection.issues || [];
        const fixableIssues = issues.filter((i) => i.fixable);
        if (fixableIssues.length === 0) {
          console.log(chalk_12.default.green("\u2705 No fixable issues found"));
          if (issues.length > 0) {
            console.log(chalk_12.default.yellow("\nRemaining issues that require manual attention:"));
            issues.filter((i) => !i.fixable).forEach((issue) => {
              console.log(chalk_12.default.yellow(`  \u2022 ${issue.message}`));
            });
          }
          return;
        }
        console.log(chalk_12.default.blue(`Found ${fixableIssues.length} fixable issues:`));
        fixableIssues.forEach((issue) => {
          console.log(chalk_12.default.gray(`  \u2022 ${issue.message}`));
        });
        if (!options.force && !options.dryRun) {
          console.log(chalk_12.default.yellow("\nWould proceed with repairs (use --force to skip confirmation)"));
        }
        if (options.dryRun) {
          console.log(chalk_12.default.cyan("Dry run complete - repairs would be applied"));
          return;
        }
        if (options.backup) {
          await this.createProjectBackup(detection.projectPath, detection.config);
        }
        const repairResult = await this.projectDetector.repairProject(detection.projectPath, detection.config);
        if (repairResult.found) {
          console.log(chalk_12.default.green("\n\u2705 Project repair completed successfully"));
          if (repairResult.suggestions.length > 0) {
            console.log(chalk_12.default.blue("\nActions taken:"));
            repairResult.suggestions.forEach((suggestion) => {
              console.log(chalk_12.default.gray(`  \u2022 ${suggestion}`));
            });
          }
          if (repairResult.issues.length > 0) {
            console.log(chalk_12.default.yellow("\nRemaining issues:"));
            repairResult.issues.forEach((issue) => {
              console.log(chalk_12.default.yellow(`  \u2022 ${issue.message}`));
            });
          }
        } else {
          console.error(chalk_12.default.red("\u274C Repair failed"));
          if (repairResult.issues.length > 0) {
            repairResult.issues.forEach((issue) => {
              console.error(chalk_12.default.red(`  \u2022 ${issue.message}`));
            });
          }
        }
      }
      async resetProject(detection, options) {
        console.log(chalk_12.default.blue("\u{1F504} Full Project Reset\n"));
        const projectPath = detection.projectPath;
        const config = detection.config;
        const resetItems = await this.getResetItems(projectPath, options);
        console.log(chalk_12.default.yellow("Items to be reset:"));
        resetItems.forEach((item) => {
          const icon = item.keep ? "\u{1F512}" : "\u{1F5D1}\uFE0F";
          const status = item.keep ? "KEEP" : "RESET";
          const color = item.keep ? chalk_12.default.green : chalk_12.default.gray;
          console.log(`  ${icon} ${item.name}: ${color(status)}`);
          if (item.description) {
            console.log(chalk_12.default.gray(`      ${item.description}`));
          }
        });
        if (options.dryRun) {
          console.log(chalk_12.default.cyan("\nDry run complete - no actual changes made"));
          return;
        }
        if (!options.force) {
          console.log(chalk_12.default.yellow("\nThis will permanently reset the selected items."));
          console.log(chalk_12.default.gray("Use --force to skip this confirmation"));
          console.log(chalk_12.default.yellow("Would proceed with reset..."));
        }
        let backupPath;
        if (options.backup) {
          backupPath = await this.createProjectBackup(projectPath, config);
          console.log(chalk_12.default.blue(`\u{1F4E6} Backup created: ${backupPath}`));
        }
        try {
          await this.performReset(projectPath, config, options);
          console.log(chalk_12.default.green("\n\u2705 Project reset completed successfully"));
          if (backupPath) {
            console.log(chalk_12.default.gray(`Backup available at: ${backupPath}`));
          }
          console.log(chalk_12.default.blue("\n\u{1F680} Next steps:"));
          console.log(chalk_12.default.gray('  \u2022 Run "specify detect-project" to verify the reset'));
          console.log(chalk_12.default.gray('  \u2022 Initialize project: "specify init" if starting fresh'));
          console.log(chalk_12.default.gray("  \u2022 Restore from backup if needed"));
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Reset failed: ${error}`));
          if (backupPath) {
            console.error(chalk_12.default.yellow(`\u{1F4BE} Backup available for recovery: ${backupPath}`));
            console.error(chalk_12.default.gray("You can manually restore files from the backup"));
          }
          throw error;
        }
      }
      async getResetItems(projectPath, options) {
        const items = [];
        items.push({
          name: "Project Configuration",
          description: "AI model settings, project metadata",
          path: path2.join(projectPath, ".specify", "config.json"),
          keep: false
        });
        items.push({
          name: "Task Tracking Data",
          description: "Task states, progress tracking",
          path: path2.join(projectPath, ".specify", "tasks.json"),
          keep: options.keepTasks || false
        });
        items.push({
          name: "Specification Files",
          description: "Feature specs, plans, contracts",
          path: path2.join(projectPath, "specs"),
          keep: options.keepSpecs || false
        });
        items.push({
          name: "Migration History",
          description: "Model switch history and backups",
          path: path2.join(projectPath, ".specify", "backups"),
          keep: false
        });
        items.push({
          name: "Cache & Temporary Files",
          description: "Cached data, temporary files",
          path: path2.join(projectPath, ".specify", "cache"),
          keep: false
        });
        return items;
      }
      async createProjectBackup(projectPath, config) {
        const timestamp = (/* @__PURE__ */ new Date()).toISOString().replace(/[:.]/g, "-");
        const backupName = `project-backup-${timestamp}`;
        const backupPath = path2.join(projectPath, ".specify", "backups", backupName);
        await fs2.ensureDir(backupPath);
        const configPath = path2.join(projectPath, ".specify", "config.json");
        if (await fs2.pathExists(configPath)) {
          await fs2.copy(configPath, path2.join(backupPath, "config.json"));
        }
        const taskPath = path2.join(projectPath, ".specify", "tasks.json");
        if (await fs2.pathExists(taskPath)) {
          await fs2.copy(taskPath, path2.join(backupPath, "tasks.json"));
        }
        const specsPath = path2.join(projectPath, "specs");
        if (await fs2.pathExists(specsPath)) {
          await fs2.copy(specsPath, path2.join(backupPath, "specs"));
        }
        const manifest = {
          createdAt: (/* @__PURE__ */ new Date()).toISOString(),
          projectName: config?.name || "Unknown",
          projectId: config?.projectId,
          aiModel: config?.aiModel,
          originalPath: projectPath,
          backupType: "full-project"
        };
        await fs2.writeJson(path2.join(backupPath, "manifest.json"), manifest, { spaces: 2 });
        return backupPath;
      }
      async performReset(projectPath, config, options) {
        const specifyDir = path2.join(projectPath, ".specify");
        const configPath = path2.join(specifyDir, "config.json");
        if (await fs2.pathExists(configPath)) {
          await fs2.remove(configPath);
        }
        if (!options.keepTasks) {
          const taskPath = path2.join(specifyDir, "tasks.json");
          if (await fs2.pathExists(taskPath)) {
            await fs2.remove(taskPath);
          }
        }
        if (!options.keepSpecs) {
          const specsPath = path2.join(projectPath, "specs");
          if (await fs2.pathExists(specsPath)) {
            await fs2.remove(specsPath);
          }
        }
        const backupsPath = path2.join(specifyDir, "backups");
        if (await fs2.pathExists(backupsPath)) {
          const backups = await fs2.readdir(backupsPath);
          const oldBackups = backups.filter((name) => !name.startsWith("project-backup-")).map((name) => path2.join(backupsPath, name));
          for (const backup of oldBackups) {
            await fs2.remove(backup);
          }
        }
        const cachePath = path2.join(specifyDir, "cache");
        if (await fs2.pathExists(cachePath)) {
          await fs2.remove(cachePath);
        }
      }
      getUsageExamples() {
        return [
          "specify reset-project",
          "specify reset-project --repair",
          "specify reset-project --dry-run",
          "specify reset-project --force --no-backup",
          "specify reset-project --keep-specs --keep-tasks"
        ];
      }
      async listBackups(projectPath) {
        const backupsDir = path2.join(projectPath, ".specify", "backups");
        if (!await fs2.pathExists(backupsDir)) {
          return [];
        }
        const backups = [];
        const items = await fs2.readdir(backupsDir);
        for (const item of items) {
          const itemPath = path2.join(backupsDir, item);
          const stats = await fs2.stat(itemPath);
          if (stats.isDirectory()) {
            const manifestPath = path2.join(itemPath, "manifest.json");
            let createdAt = stats.mtime.toISOString();
            if (await fs2.pathExists(manifestPath)) {
              try {
                const manifest = await fs2.readJson(manifestPath);
                createdAt = manifest.createdAt || createdAt;
              } catch {
              }
            }
            backups.push({
              name: item,
              path: itemPath,
              createdAt,
              size: await this.getDirectorySize(itemPath)
            });
          }
        }
        return backups.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      }
      async getDirectorySize(dirPath) {
        let size = 0;
        try {
          const items = await fs2.readdir(dirPath);
          for (const item of items) {
            const itemPath = path2.join(dirPath, item);
            const stats = await fs2.stat(itemPath);
            if (stats.isDirectory()) {
              size += await this.getDirectorySize(itemPath);
            } else {
              size += stats.size;
            }
          }
        } catch {
        }
        return size;
      }
    };
    exports2.ResetProjectCommand = ResetProjectCommand;
  }
});

// dist/models/TaskState.js
var require_TaskState = __commonJS({
  "dist/models/TaskState.js"(exports2) {
    "use strict";
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.TaskStateManager = void 0;
    var TaskStateManager = class {
      static create(params) {
        const now = (/* @__PURE__ */ new Date()).toISOString();
        return {
          ...params,
          status: "pending",
          priority: params.priority || "medium",
          tags: [],
          createdAt: now,
          updatedAt: now,
          dependencies: params.dependencies || [],
          blockedBy: [],
          progress: {
            percentage: 0,
            lastActivity: now
          },
          metadata: {
            category: params.category,
            isParallel: params.isParallel || false,
            retryCount: 0,
            maxRetries: 3
          }
        };
      }
      static transition(task, newStatus, metadata) {
        const now = (/* @__PURE__ */ new Date()).toISOString();
        const updated = {
          ...task,
          status: newStatus,
          updatedAt: now,
          progress: {
            ...task.progress,
            lastActivity: now
          },
          metadata: {
            ...task.metadata,
            ...metadata
          }
        };
        if (newStatus === "in_progress" && !task.startedAt) {
          updated.startedAt = now;
          updated.progress.percentage = 10;
        }
        if (newStatus === "completed" || newStatus === "failed") {
          updated.completedAt = now;
          updated.progress.percentage = newStatus === "completed" ? 100 : 0;
          if (updated.startedAt) {
            updated.actualDuration = new Date(now).getTime() - new Date(updated.startedAt).getTime();
          }
        }
        return updated;
      }
      static updateProgress(task, progress) {
        return {
          ...task,
          updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
          progress: {
            ...task.progress,
            ...progress,
            lastActivity: (/* @__PURE__ */ new Date()).toISOString()
          }
        };
      }
      static canStart(task, completedTaskIds) {
        if (task.status !== "pending")
          return false;
        if (task.blockedBy.length > 0)
          return false;
        return task.dependencies.every((depId) => completedTaskIds.includes(depId));
      }
      static getParallelTasks(tasks) {
        return tasks.filter((task) => task.metadata.isParallel && task.status === "pending");
      }
    };
    exports2.TaskStateManager = TaskStateManager;
  }
});

// dist/services/TaskTracker.js
var require_TaskTracker = __commonJS({
  "dist/services/TaskTracker.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.TaskTracker = void 0;
    var TaskState_1 = require_TaskState();
    var fs2 = __importStar2(require_lib());
    var path2 = __importStar2(require("path"));
    var TaskTracker = class {
      constructor(projectConfig, options = {}) {
        this.tasks = /* @__PURE__ */ new Map();
        this.listeners = [];
        this.saveTimeout = null;
        this.taskFilePath = path2.join(path2.dirname(projectConfig.configPath), "tasks.json");
        this.options = {
          enableRealTimeUpdates: true,
          autoSave: true,
          maxHistoryItems: 1e3,
          notificationThreshold: 5e3,
          // 5 seconds
          ...options
        };
      }
      async initialize() {
        await this.loadTasks();
      }
      async addTask(taskData) {
        const task = TaskState_1.TaskStateManager.create(taskData);
        if (taskData.estimatedDuration) {
          task.estimatedDuration = taskData.estimatedDuration;
        }
        if (taskData.tags) {
          task.tags = taskData.tags;
        }
        this.tasks.set(task.id, task);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return task;
      }
      async updateTask(taskId, updates) {
        const task = this.tasks.get(taskId);
        if (!task)
          return null;
        const updatedTask = {
          ...task,
          ...updates,
          updatedAt: (/* @__PURE__ */ new Date()).toISOString()
        };
        this.tasks.set(taskId, updatedTask);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return updatedTask;
      }
      async updateTaskStatus(taskId, status, metadata) {
        const task = this.tasks.get(taskId);
        if (!task)
          return null;
        const updatedTask = TaskState_1.TaskStateManager.transition(task, status, metadata);
        this.tasks.set(taskId, updatedTask);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return updatedTask;
      }
      async updateTaskProgress(taskId, progress) {
        const task = this.tasks.get(taskId);
        if (!task)
          return null;
        const updatedTask = TaskState_1.TaskStateManager.updateProgress(task, progress);
        this.tasks.set(taskId, updatedTask);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return updatedTask;
      }
      getTask(taskId) {
        return this.tasks.get(taskId) || null;
      }
      getAllTasks() {
        return Array.from(this.tasks.values());
      }
      getFilteredTasks(filter) {
        let filtered = this.getAllTasks();
        if (filter.status) {
          filtered = filtered.filter((task) => filter.status.includes(task.status));
        }
        if (filter.category) {
          filtered = filtered.filter((task) => filter.category.includes(task.metadata.category));
        }
        if (filter.priority) {
          filtered = filtered.filter((task) => filter.priority.includes(task.priority));
        }
        if (filter.tags && filter.tags.length > 0) {
          filtered = filtered.filter((task) => filter.tags.some((tag) => task.tags.includes(tag)));
        }
        if (filter.search) {
          const searchLower = filter.search.toLowerCase();
          filtered = filtered.filter((task) => task.title.toLowerCase().includes(searchLower) || task.description.toLowerCase().includes(searchLower) || task.id.toLowerCase().includes(searchLower));
        }
        return filtered;
      }
      getTaskStats() {
        const tasks = this.getAllTasks();
        const total = tasks.length;
        if (total === 0) {
          return {
            total: 0,
            pending: 0,
            inProgress: 0,
            completed: 0,
            failed: 0,
            skipped: 0,
            percentComplete: 0,
            estimatedTimeRemaining: 0
          };
        }
        const statusCounts = tasks.reduce((acc, task) => {
          acc[task.status] = (acc[task.status] || 0) + 1;
          return acc;
        }, {});
        const completed = statusCounts.completed || 0;
        const percentComplete = Math.round(completed / total * 100);
        const remainingTasks = tasks.filter((t) => ["pending", "in_progress"].includes(t.status));
        const estimatedTimeRemaining = remainingTasks.reduce((sum, task) => {
          return sum + (task.estimatedDuration || 0);
        }, 0);
        return {
          total,
          pending: statusCounts.pending || 0,
          inProgress: statusCounts.in_progress || 0,
          completed,
          failed: statusCounts.failed || 0,
          skipped: statusCounts.skipped || 0,
          percentComplete,
          estimatedTimeRemaining
        };
      }
      getReadyTasks() {
        const completedTaskIds = this.getAllTasks().filter((t) => t.status === "completed").map((t) => t.id);
        return this.getAllTasks().filter((task) => TaskState_1.TaskStateManager.canStart(task, completedTaskIds));
      }
      getParallelTasks() {
        const allTasks = this.getAllTasks();
        return TaskState_1.TaskStateManager.getParallelTasks(allTasks);
      }
      getBlockedTasks() {
        const completedTaskIds = this.getAllTasks().filter((t) => t.status === "completed").map((t) => t.id);
        return this.getAllTasks().filter((task) => {
          if (task.status !== "pending")
            return false;
          return !TaskState_1.TaskStateManager.canStart(task, completedTaskIds);
        });
      }
      async markTaskAsFailed(taskId, errorMessage, allowRetry = true) {
        const task = this.tasks.get(taskId);
        if (!task)
          return null;
        const updatedTask = TaskState_1.TaskStateManager.transition(task, "failed", {
          errorMessage,
          retryCount: allowRetry ? task.metadata.retryCount + 1 : task.metadata.maxRetries
        });
        this.tasks.set(taskId, updatedTask);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return updatedTask;
      }
      async retryTask(taskId) {
        const task = this.tasks.get(taskId);
        if (!task || task.status !== "failed")
          return null;
        if (task.metadata.retryCount >= task.metadata.maxRetries) {
          return null;
        }
        const updatedTask = TaskState_1.TaskStateManager.transition(task, "pending", {
          errorMessage: void 0
        });
        this.tasks.set(taskId, updatedTask);
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return updatedTask;
      }
      onTasksChanged(listener) {
        this.listeners.push(listener);
        return () => {
          const index = this.listeners.indexOf(listener);
          if (index > -1) {
            this.listeners.splice(index, 1);
          }
        };
      }
      async saveTasks() {
        const tasksData = {
          tasks: Object.fromEntries(this.tasks),
          savedAt: (/* @__PURE__ */ new Date()).toISOString(),
          version: "1.0"
        };
        await fs2.ensureDir(path2.dirname(this.taskFilePath));
        await fs2.writeJson(this.taskFilePath, tasksData, { spaces: 2 });
      }
      async loadTasks() {
        try {
          if (await fs2.pathExists(this.taskFilePath)) {
            const data = await fs2.readJson(this.taskFilePath);
            if (data.tasks) {
              this.tasks.clear();
              for (const [id, taskData] of Object.entries(data.tasks)) {
                this.tasks.set(id, taskData);
              }
            }
          }
        } catch (error) {
          this.tasks.clear();
        }
      }
      async clearCompleted() {
        const completedTasks = this.getAllTasks().filter((t) => t.status === "completed");
        for (const task of completedTasks) {
          this.tasks.delete(task.id);
        }
        await this.notifyListeners();
        await this.scheduleAutoSave();
        return completedTasks.length;
      }
      async reset() {
        this.tasks.clear();
        await this.notifyListeners();
        await this.saveTasks();
      }
      async notifyListeners() {
        if (!this.options.enableRealTimeUpdates)
          return;
        const tasks = this.getAllTasks();
        for (const listener of this.listeners) {
          try {
            listener(tasks);
          } catch (error) {
          }
        }
      }
      async scheduleAutoSave() {
        if (!this.options.autoSave)
          return;
        if (this.saveTimeout) {
          clearTimeout(this.saveTimeout);
        }
        this.saveTimeout = setTimeout(async () => {
          try {
            await this.saveTasks();
          } catch (error) {
          }
        }, 1e3);
      }
    };
    exports2.TaskTracker = TaskTracker;
  }
});

// dist/cli/TrackTasksCommand.js
var require_TrackTasksCommand = __commonJS({
  "dist/cli/TrackTasksCommand.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.TrackTasksCommand = void 0;
    var commander_12 = require_commander();
    var TaskTracker_1 = require_TaskTracker();
    var ProjectDetector_1 = require_ProjectDetector();
    var chalk_12 = __importDefault2(require_source());
    var fs2 = __importStar2(require_lib());
    var TrackTasksCommand = class {
      constructor() {
        this.taskTracker = null;
        this.watchMode = false;
        this.projectDetector = new ProjectDetector_1.ProjectDetector();
      }
      create() {
        const command = new commander_12.Command("track-tasks");
        command.description("Manage task tracking UI and display task status").argument("<action>", "Action to perform (enable, disable, status, list, clear)").option("--sidebar", "Enable terminal sidebar UI for task tracking", false).option("-f, --format <format>", "Output format (table, json, summary)", "table").option("--filter <filter>", "Filter tasks by status, category, or search term").option("-w, --watch", "Watch mode - continuously update task display", false).option("--export <file>", "Export tasks to file (JSON format)").action(async (action, options) => {
          await this.execute(action, options);
        });
        return command;
      }
      async execute(action, options) {
        try {
          await this.initializeTaskTracker();
          switch (action.toLowerCase()) {
            case "enable":
              await this.enableTaskTracking(options);
              break;
            case "disable":
              await this.disableTaskTracking(options);
              break;
            case "status":
              await this.showTaskStatus(options);
              break;
            case "list":
              await this.listTasks(options);
              break;
            case "clear":
              await this.clearTasks(options);
              break;
            case "stats":
              await this.showTaskStats(options);
              break;
            default:
              console.error(chalk_12.default.red(`\u274C Unknown action: ${action}`));
              console.error(chalk_12.default.gray("Valid actions: enable, disable, status, list, clear, stats"));
              process.exit(1);
          }
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Task tracking failed: ${error}`));
          process.exit(1);
        }
      }
      async initializeTaskTracker() {
        const detection = await this.projectDetector.detectProject();
        if (!detection.found || !detection.config) {
          throw new Error('No spec-kit project found. Run "specify detect-project" first.');
        }
        this.taskTracker = new TaskTracker_1.TaskTracker(detection.config);
        await this.taskTracker.initialize();
      }
      async enableTaskTracking(options) {
        console.log(chalk_12.default.blue("\u{1F680} Enabling task tracking..."));
        if (!this.taskTracker) {
          throw new Error("Task tracker not initialized");
        }
        const unsubscribe = this.taskTracker.onTasksChanged((tasks) => {
          if (options.sidebar || options.watch) {
            this.renderTaskSidebar(tasks);
          }
        });
        if (options.sidebar) {
          console.log(chalk_12.default.green("\u2705 Task tracking sidebar enabled"));
          console.log(chalk_12.default.gray("Task status will be displayed in sidebar during command execution"));
        } else {
          console.log(chalk_12.default.green("\u2705 Task tracking enabled"));
          console.log(chalk_12.default.gray("Use --sidebar for visual task tracking UI"));
        }
        if (options.watch) {
          console.log(chalk_12.default.blue("\u{1F440} Watch mode active - press Ctrl+C to stop"));
          this.watchMode = true;
          const tasks = this.taskTracker.getAllTasks();
          await this.displayTasks(tasks, options);
          const watchInterval = setInterval(async () => {
            if (!this.watchMode) {
              clearInterval(watchInterval);
              unsubscribe();
              return;
            }
            const updatedTasks = this.taskTracker.getAllTasks();
            console.clear();
            console.log(chalk_12.default.blue(`\u{1F4CA} Task Status (Updated: ${(/* @__PURE__ */ new Date()).toLocaleTimeString()})
`));
            await this.displayTasks(updatedTasks, options);
          }, 2e3);
          process.on("SIGINT", () => {
            console.log(chalk_12.default.yellow("\n\u{1F6D1} Stopping task tracking..."));
            this.watchMode = false;
            clearInterval(watchInterval);
            unsubscribe();
            process.exit(0);
          });
        } else {
          await this.saveTrackingPreferences({ enabled: true, sidebar: options.sidebar });
        }
      }
      async disableTaskTracking(options) {
        console.log(chalk_12.default.blue("\u{1F6D1} Disabling task tracking..."));
        this.watchMode = false;
        await this.saveTrackingPreferences({ enabled: false, sidebar: false });
        console.log(chalk_12.default.green("\u2705 Task tracking disabled"));
      }
      async showTaskStatus(options) {
        if (!this.taskTracker) {
          throw new Error("Task tracker not initialized");
        }
        const stats = this.taskTracker.getTaskStats();
        const tasks = this.taskTracker.getAllTasks();
        console.log(chalk_12.default.blue("\u{1F4CA} Task Tracking Status\n"));
        console.log(chalk_12.default.white("Overall Progress:"));
        console.log(`  Total Tasks: ${chalk_12.default.cyan(stats.total)}`);
        console.log(`  Completed: ${chalk_12.default.green(stats.completed)} (${stats.percentComplete}%)`);
        console.log(`  In Progress: ${chalk_12.default.yellow(stats.inProgress)}`);
        console.log(`  Pending: ${chalk_12.default.gray(stats.pending)}`);
        console.log(`  Failed: ${chalk_12.default.red(stats.failed)}`);
        if (stats.estimatedTimeRemaining > 0) {
          const timeStr = this.formatDuration(stats.estimatedTimeRemaining);
          console.log(`  Estimated Time Remaining: ${chalk_12.default.cyan(timeStr)}`);
        }
        const progressBar = this.createProgressBar(stats.percentComplete);
        console.log(`
${progressBar}
`);
        const readyTasks = this.taskTracker.getReadyTasks();
        if (readyTasks.length > 0) {
          console.log(chalk_12.default.green(`\u{1F7E2} Ready to Start (${readyTasks.length}):`));
          readyTasks.slice(0, 5).forEach((task) => {
            console.log(`  \u2022 ${task.title}`);
          });
          if (readyTasks.length > 5) {
            console.log(chalk_12.default.gray(`    ... and ${readyTasks.length - 5} more`));
          }
          console.log();
        }
        const blockedTasks = this.taskTracker.getBlockedTasks();
        if (blockedTasks.length > 0) {
          console.log(chalk_12.default.red(`\u{1F534} Blocked Tasks (${blockedTasks.length}):`));
          blockedTasks.slice(0, 3).forEach((task) => {
            console.log(`  \u2022 ${task.title}`);
            console.log(chalk_12.default.gray(`    Waiting for: ${task.dependencies.join(", ")}`));
          });
          if (blockedTasks.length > 3) {
            console.log(chalk_12.default.gray(`    ... and ${blockedTasks.length - 3} more`));
          }
          console.log();
        }
        const parallelTasks = this.taskTracker.getParallelTasks();
        if (parallelTasks.length > 1) {
          console.log(chalk_12.default.blue(`\u26A1 Parallel Execution Available (${parallelTasks.length}):`));
          parallelTasks.forEach((task) => {
            console.log(`  \u2022 ${task.title}`);
          });
          console.log();
        }
        if (options.format === "json") {
          console.log(chalk_12.default.gray("\nDetailed data (JSON):"));
          console.log(JSON.stringify({ stats, readyTasks: readyTasks.length, blockedTasks: blockedTasks.length }, null, 2));
        }
      }
      async listTasks(options) {
        if (!this.taskTracker) {
          throw new Error("Task tracker not initialized");
        }
        let tasks = this.taskTracker.getAllTasks();
        if (options.filter) {
          tasks = this.applyTaskFilter(tasks, options.filter);
        }
        if (tasks.length === 0) {
          console.log(chalk_12.default.yellow("\u{1F4DD} No tasks found"));
          return;
        }
        console.log(chalk_12.default.blue(`\u{1F4CB} Task List (${tasks.length} tasks)
`));
        await this.displayTasks(tasks, options);
        if (options.export) {
          await this.exportTasks(tasks, options.export);
          console.log(chalk_12.default.green(`
\u{1F4BE} Tasks exported to ${options.export}`));
        }
      }
      async clearTasks(options) {
        if (!this.taskTracker) {
          throw new Error("Task tracker not initialized");
        }
        const stats = this.taskTracker.getTaskStats();
        if (stats.total === 0) {
          console.log(chalk_12.default.yellow("\u{1F4DD} No tasks to clear"));
          return;
        }
        console.log(chalk_12.default.yellow(`\u26A0\uFE0F  This will remove all task tracking data (${stats.total} tasks)`));
        console.log(chalk_12.default.gray("Use Ctrl+C to cancel..."));
        await new Promise((resolve) => setTimeout(resolve, 3e3));
        const clearedCount = await this.taskTracker.clearCompleted();
        await this.taskTracker.reset();
        console.log(chalk_12.default.green(`\u2705 Task tracking data cleared (${stats.total} tasks removed)`));
        if (clearedCount > 0) {
          console.log(chalk_12.default.gray(`${clearedCount} completed tasks were cleared`));
        }
      }
      async showTaskStats(options) {
        if (!this.taskTracker) {
          throw new Error("Task tracker not initialized");
        }
        const stats = this.taskTracker.getTaskStats();
        const tasks = this.taskTracker.getAllTasks();
        const categoryStats = tasks.reduce((acc, task) => {
          const category = task.metadata.category;
          acc[category] = (acc[category] || 0) + 1;
          return acc;
        }, {});
        const priorityStats = tasks.reduce((acc, task) => {
          acc[task.priority] = (acc[task.priority] || 0) + 1;
          return acc;
        }, {});
        console.log(chalk_12.default.blue("\u{1F4C8} Task Statistics\n"));
        console.log(chalk_12.default.white("\u{1F4CA} Overall:"));
        console.log(`  Total: ${stats.total}`);
        console.log(`  Completion Rate: ${stats.percentComplete}%`);
        console.log(`  Active: ${stats.inProgress}`);
        console.log(`  Failed: ${stats.failed}
`);
        console.log(chalk_12.default.white("\u{1F4C2} By Category:"));
        Object.entries(categoryStats).forEach(([category, count]) => {
          console.log(`  ${category}: ${count}`);
        });
        console.log();
        console.log(chalk_12.default.white("\u2B50 By Priority:"));
        Object.entries(priorityStats).forEach(([priority, count]) => {
          const color = this.getPriorityColor(priority);
          console.log(`  ${color(priority)}: ${count}`);
        });
        console.log();
        if (options.format === "json") {
          console.log(JSON.stringify({
            stats,
            categoryStats,
            priorityStats,
            tasks: tasks.length
          }, null, 2));
        }
      }
      async displayTasks(tasks, options) {
        switch (options.format) {
          case "json":
            console.log(JSON.stringify(tasks, null, 2));
            break;
          case "summary":
            this.displayTaskSummary(tasks);
            break;
          case "table":
          default:
            this.displayTaskTable(tasks);
            break;
        }
      }
      displayTaskTable(tasks) {
        tasks.forEach((task) => {
          const statusIcon = this.getStatusIcon(task.status);
          const priorityColor = this.getPriorityColor(task.priority);
          console.log(`${statusIcon} ${chalk_12.default.white(task.title)}`);
          console.log(`   ${chalk_12.default.gray(task.description)}`);
          console.log(`   Priority: ${priorityColor(task.priority)} | Category: ${chalk_12.default.cyan(task.metadata.category)} | Progress: ${task.progress.percentage}%`);
          if (task.status === "failed" && task.metadata.errorMessage) {
            console.log(`   ${chalk_12.default.red("Error:")} ${task.metadata.errorMessage}`);
          }
          if (task.dependencies.length > 0) {
            console.log(`   ${chalk_12.default.gray("Depends on:")} ${task.dependencies.join(", ")}`);
          }
          console.log();
        });
      }
      displayTaskSummary(tasks) {
        const grouped = tasks.reduce((acc, task) => {
          acc[task.status] = acc[task.status] || [];
          acc[task.status].push(task);
          return acc;
        }, {});
        Object.entries(grouped).forEach(([status, statusTasks]) => {
          const icon = this.getStatusIcon(status);
          console.log(`${icon} ${chalk_12.default.white(status.toUpperCase())} (${statusTasks.length})`);
          statusTasks.forEach((task) => {
            console.log(`   \u2022 ${task.title}`);
          });
          console.log();
        });
      }
      renderTaskSidebar(tasks) {
        const stats = {
          completed: tasks.filter((t) => t.status === "completed").length,
          inProgress: tasks.filter((t) => t.status === "in_progress").length,
          pending: tasks.filter((t) => t.status === "pending").length,
          failed: tasks.filter((t) => t.status === "failed").length
        };
        const total = tasks.length;
        const progress = total > 0 ? Math.round(stats.completed / total * 100) : 0;
        console.log(chalk_12.default.gray(`[Tasks: ${progress}% | \u2705${stats.completed} \u26A1${stats.inProgress} \u23F3${stats.pending} \u274C${stats.failed}]`));
      }
      applyTaskFilter(tasks, filter) {
        const lowerFilter = filter.toLowerCase();
        if (["pending", "in_progress", "completed", "failed", "skipped"].includes(lowerFilter)) {
          return tasks.filter((task) => task.status === lowerFilter);
        }
        if (["setup", "test", "implementation", "ui", "integration", "polish"].includes(lowerFilter)) {
          return tasks.filter((task) => task.metadata.category === lowerFilter);
        }
        if (["low", "medium", "high", "critical"].includes(lowerFilter)) {
          return tasks.filter((task) => task.priority === lowerFilter);
        }
        return tasks.filter((task) => task.title.toLowerCase().includes(lowerFilter) || task.description.toLowerCase().includes(lowerFilter) || task.id.toLowerCase().includes(lowerFilter));
      }
      getStatusIcon(status) {
        switch (status) {
          case "completed":
            return chalk_12.default.green("\u2705");
          case "in_progress":
            return chalk_12.default.yellow("\u26A1");
          case "pending":
            return chalk_12.default.gray("\u23F3");
          case "failed":
            return chalk_12.default.red("\u274C");
          case "skipped":
            return chalk_12.default.blue("\u23ED\uFE0F");
          default:
            return "\u2022";
        }
      }
      getPriorityColor(priority) {
        switch (priority) {
          case "critical":
            return chalk_12.default.red.bold;
          case "high":
            return chalk_12.default.red;
          case "medium":
            return chalk_12.default.yellow;
          case "low":
            return chalk_12.default.gray;
          default:
            return chalk_12.default.white;
        }
      }
      createProgressBar(percentage, width = 30) {
        const filled = Math.round(percentage / 100 * width);
        const empty = width - filled;
        const bar = chalk_12.default.green("\u2588").repeat(filled) + chalk_12.default.gray("\u2591").repeat(empty);
        return `${bar} ${percentage}%`;
      }
      formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1e3);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`;
        } else {
          return `${seconds}s`;
        }
      }
      async saveTrackingPreferences(prefs) {
      }
      async exportTasks(tasks, filePath) {
        const exportData = {
          exportedAt: (/* @__PURE__ */ new Date()).toISOString(),
          taskCount: tasks.length,
          tasks
        };
        await fs2.writeJson(filePath, exportData, { spaces: 2 });
      }
      getUsageExamples() {
        return [
          "specify track-tasks enable --sidebar",
          "specify track-tasks status",
          "specify track-tasks list --filter completed",
          "specify track-tasks list --watch --format summary",
          "specify track-tasks clear",
          "specify track-tasks stats --format json"
        ];
      }
    };
    exports2.TrackTasksCommand = TrackTasksCommand;
  }
});

// dist/cli/InitProjectCommand.js
var require_InitProjectCommand = __commonJS({
  "dist/cli/InitProjectCommand.js"(exports2) {
    "use strict";
    var __createBinding2 = exports2 && exports2.__createBinding || (Object.create ? (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      var desc = Object.getOwnPropertyDescriptor(m, k);
      if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
        desc = { enumerable: true, get: function() {
          return m[k];
        } };
      }
      Object.defineProperty(o, k2, desc);
    }) : (function(o, m, k, k2) {
      if (k2 === void 0) k2 = k;
      o[k2] = m[k];
    }));
    var __setModuleDefault2 = exports2 && exports2.__setModuleDefault || (Object.create ? (function(o, v) {
      Object.defineProperty(o, "default", { enumerable: true, value: v });
    }) : function(o, v) {
      o["default"] = v;
    });
    var __importStar2 = exports2 && exports2.__importStar || /* @__PURE__ */ (function() {
      var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function(o2) {
          var ar = [];
          for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
          return ar;
        };
        return ownKeys(o);
      };
      return function(mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) {
          for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding2(result, mod, k[i]);
        }
        __setModuleDefault2(result, mod);
        return result;
      };
    })();
    var __importDefault2 = exports2 && exports2.__importDefault || function(mod) {
      return mod && mod.__esModule ? mod : { "default": mod };
    };
    Object.defineProperty(exports2, "__esModule", { value: true });
    exports2.InitProjectCommand = void 0;
    var commander_12 = require_commander();
    var chalk_12 = __importDefault2(require_source());
    var fs2 = __importStar2(require_lib());
    var path2 = __importStar2(require("path"));
    var InitProjectCommand = class {
      create() {
        return new commander_12.Command("init").argument("[project-name]", "Name of the project to initialize").option("--here", "Initialize in the current directory").option("--ai <type>", "AI agent type (claude, gemini, copilot)").option("--script <type>", "Script type (sh, ps)", "sh").option("--ignore-agent-tools", "Skip agent tools validation").option("--force", "Overwrite existing spec-kit configuration").description("Initialize a new spec-kit project").action((projectName, options) => this.execute(projectName, options));
      }
      async execute(projectName, options) {
        try {
          console.log(chalk_12.default.blue("\u{1F680} Initializing spec-kit project...\n"));
          if (!projectName && !options.here) {
            console.error(chalk_12.default.red("\u274C Please specify a project name or use --here flag"));
            console.log(chalk_12.default.yellow("\nExamples:"));
            console.log("  specify init my-project");
            console.log("  specify init --here");
            process.exit(1);
          }
          let targetDir;
          let projectNameForConfig;
          if (options.here) {
            targetDir = process.cwd();
            projectNameForConfig = path2.basename(targetDir);
            console.log(chalk_12.default.cyan(`\u{1F4CD} Initializing in current directory: ${targetDir}`));
          } else if (projectName) {
            targetDir = path2.join(process.cwd(), projectName);
            projectNameForConfig = projectName;
            console.log(chalk_12.default.cyan(`\u{1F4CD} Creating new project: ${projectName}`));
          } else {
            throw new Error("Invalid arguments");
          }
          if (!options.here && fs2.existsSync(targetDir)) {
            if (!options.force) {
              console.error(chalk_12.default.red(`\u274C Directory ${projectName} already exists`));
              console.log(chalk_12.default.yellow("Use --force to overwrite existing directory"));
              process.exit(1);
            }
          }
          if (!options.here) {
            await fs2.ensureDir(targetDir);
          }
          await this.createBasicStructure(targetDir, projectNameForConfig, options);
          console.log(chalk_12.default.green("\n\u2705 Spec-kit project initialized successfully!\n"));
          console.log(chalk_12.default.white("\u{1F4CB} Next steps:"));
          if (!options.here) {
            console.log(`  1. cd ${projectName}`);
          } else {
            console.log("  1. You're ready to go!");
          }
          console.log("  2. Start with: /specify <your-feature-description>");
          console.log("  3. Then use: /plan and /tasks");
          console.log("  4. Track progress with: specify track-tasks enable");
          console.log(chalk_12.default.white("\n\u{1F527} Available commands:"));
          console.log("  specify detect-project   - Validate project setup");
          console.log("  specify list-models      - See available AI models");
          console.log("  specify switch-model     - Change AI model");
          console.log("  specify track-tasks      - Manage task tracking");
          console.log(chalk_12.default.gray('\nRun "specify --help" for more information'));
        } catch (error) {
          console.error(chalk_12.default.red(`\u274C Failed to initialize project: ${error.message}`));
          process.exit(1);
        }
      }
      async createBasicStructure(targetDir, projectName, options) {
        console.log(chalk_12.default.cyan("\u{1F4C2} Creating project structure..."));
        const specifyDir = path2.join(targetDir, ".specify");
        await fs2.ensureDir(specifyDir);
        await fs2.ensureDir(path2.join(specifyDir, "scripts"));
        await fs2.ensureDir(path2.join(specifyDir, "scripts", "bash"));
        await fs2.ensureDir(path2.join(specifyDir, "scripts", "powershell"));
        await fs2.ensureDir(path2.join(specifyDir, "state"));
        const specsDir = path2.join(targetDir, "specs");
        await fs2.ensureDir(specsDir);
        const aiModel = options.ai || "claude";
        const config = {
          projectId: `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name: projectName,
          aiModel,
          version: "0.1.0",
          createdAt: (/* @__PURE__ */ new Date()).toISOString(),
          updatedAt: (/* @__PURE__ */ new Date()).toISOString(),
          specDirectory: specsDir,
          configPath: path2.join(specifyDir, "config.json"),
          isInitialized: true,
          migrationHistory: []
        };
        const configPath = path2.join(specifyDir, "config.json");
        await fs2.writeJSON(configPath, config, { spaces: 2 });
        const specsReadme = `# Specifications Directory

This directory contains all feature specifications, implementation plans, and task breakdowns.

## Structure

Each feature should have its own directory with the following structure:

\`\`\`
specs/
\u251C\u2500\u2500 001-feature-name/
\u2502   \u251C\u2500\u2500 spec.md          # Feature specification
\u2502   \u251C\u2500\u2500 plan.md          # Implementation plan
\u2502   \u251C\u2500\u2500 tasks.md         # Task breakdown
\u2502   \u251C\u2500\u2500 research.md      # Research notes (optional)
\u2502   \u251C\u2500\u2500 data-model.md    # Data model (if applicable)
\u2502   \u251C\u2500\u2500 quickstart.md    # Quick start guide (optional)
\u2502   \u2514\u2500\u2500 contracts/       # API contracts and schemas
\u2502       \u251C\u2500\u2500 api.yaml
\u2502       \u2514\u2500\u2500 schema.json
\u2514\u2500\u2500 README.md            # This file
\`\`\`

## Creating New Specifications

Use the AI agent commands:

1. \`/specify <feature-description>\` - Create a new specification
2. \`/plan <feature-name>\` - Generate implementation plan
3. \`/tasks <feature-name>\` - Break down into tasks

## Naming Convention

Use the format: \`NNN-feature-name\` where:
- \`NNN\` is a zero-padded sequence number (001, 002, etc.)
- \`feature-name\` is a kebab-case description
`;
        await fs2.writeFile(path2.join(specsDir, "README.md"), specsReadme);
        const readmePath = path2.join(targetDir, "README.md");
        if (!await fs2.pathExists(readmePath)) {
          const projectReadme = `# ${projectName}

## Overview

This project uses hjLabs spec-kit for specification-driven development with AI assistance.

## Getting Started

### Prerequisites

- Node.js 16+
- Git
- AI Agent: ${aiModel}

### Development Workflow

1. **Specify**: Create feature specifications using \`/specify\`
2. **Plan**: Generate implementation plans using \`/plan\`
3. **Tasks**: Break down into actionable tasks using \`/tasks\`
4. **Implement**: Follow the generated plan and tasks
5. **Track**: Monitor progress with task tracking

### Available Commands

- \`specify detect-project\` - Validate project setup
- \`specify list-models\` - See available AI models
- \`specify switch-model <type>\` - Change AI model
- \`specify track-tasks <action>\` - Manage task tracking

## Project Structure

- \`specs/\` - Feature specifications and plans
- \`.specify/\` - Configuration and automation scripts
- \`README.md\` - This file

## AI Model Configuration

Current AI Model: **${aiModel}**

Switch models with:
\`\`\`bash
specify switch-model claude    # For Claude
specify switch-model gemini    # For Google Gemini
specify switch-model copilot   # For GitHub Copilot
\`\`\`

## Contributing

1. Create specifications before implementing
2. Follow the generated implementation plans
3. Track progress using the task system
4. Update documentation as needed

---

*Generated by hjLabs spec-kit*
`;
          await fs2.writeFile(readmePath, projectReadme);
        }
        const gitignorePath = path2.join(targetDir, ".gitignore");
        if (!await fs2.pathExists(gitignorePath)) {
          const gitignoreContent = `# Spec-kit state files
.specify/state/
*.tmp
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Dependency directories
node_modules/
.npm
.yarn

# Build outputs
dist/
build/
*.tgz

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
`;
          await fs2.writeFile(gitignorePath, gitignoreContent);
        }
        console.log(chalk_12.default.green("\u2705 Project structure created"));
      }
      isValidAIModel(model) {
        const validModels = ["claude", "gemini", "copilot"];
        return validModels.includes(model);
      }
    };
    exports2.InitProjectCommand = InitProjectCommand;
  }
});

// dist/cli/index.js
var __createBinding = exports && exports.__createBinding || (Object.create ? (function(o, m, k, k2) {
  if (k2 === void 0) k2 = k;
  var desc = Object.getOwnPropertyDescriptor(m, k);
  if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
    desc = { enumerable: true, get: function() {
      return m[k];
    } };
  }
  Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
  if (k2 === void 0) k2 = k;
  o[k2] = m[k];
}));
var __setModuleDefault = exports && exports.__setModuleDefault || (Object.create ? (function(o, v) {
  Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
  o["default"] = v;
});
var __importStar = exports && exports.__importStar || /* @__PURE__ */ (function() {
  var ownKeys = function(o) {
    ownKeys = Object.getOwnPropertyNames || function(o2) {
      var ar = [];
      for (var k in o2) if (Object.prototype.hasOwnProperty.call(o2, k)) ar[ar.length] = k;
      return ar;
    };
    return ownKeys(o);
  };
  return function(mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) {
      for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
    }
    __setModuleDefault(result, mod);
    return result;
  };
})();
var __importDefault = exports && exports.__importDefault || function(mod) {
  return mod && mod.__esModule ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecifyCLI = void 0;
var commander_1 = require_commander();
var SwitchModelCommand_1 = require_SwitchModelCommand();
var ListModelsCommand_1 = require_ListModelsCommand();
var DetectProjectCommand_1 = require_DetectProjectCommand();
var ResetProjectCommand_1 = require_ResetProjectCommand();
var TrackTasksCommand_1 = require_TrackTasksCommand();
var InitProjectCommand_1 = require_InitProjectCommand();
var chalk_1 = __importDefault(require_source());
var fs = __importStar(require_lib());
var path = __importStar(require("path"));
var SpecifyCLI = class {
  constructor() {
    this.program = new commander_1.Command();
    this.version = this.loadVersion();
    this.setupProgram();
    this.setupCommands();
    this.setupGlobalOptions();
    this.setupErrorHandling();
  }
  loadVersion() {
    try {
      const packageJsonPath = path.join(__dirname, "../../package.json");
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
      return packageJson.version || "0.1.0";
    } catch (error) {
      return "0.1.0";
    }
  }
  setupProgram() {
    this.program.name("specify").description("AI Model Switching and Task Tracking CLI for Spec-Driven Development").version(this.version, "-v, --version", "Output the current version").helpOption("-h, --help", "Display help for command");
  }
  setupCommands() {
    const initProjectCmd = new InitProjectCommand_1.InitProjectCommand();
    this.program.addCommand(initProjectCmd.create());
    const switchModelCmd = new SwitchModelCommand_1.SwitchModelCommand();
    this.program.addCommand(switchModelCmd.create());
    const listModelsCmd = new ListModelsCommand_1.ListModelsCommand();
    this.program.addCommand(listModelsCmd.create());
    const detectProjectCmd = new DetectProjectCommand_1.DetectProjectCommand();
    this.program.addCommand(detectProjectCmd.create());
    const resetProjectCmd = new ResetProjectCommand_1.ResetProjectCommand();
    this.program.addCommand(resetProjectCmd.create());
    const trackTasksCmd = new TrackTasksCommand_1.TrackTasksCommand();
    this.program.addCommand(trackTasksCmd.create());
    this.program.command("switch <target>").description("Alias for switch-model command").action((target, options) => {
      const switchCmd = new SwitchModelCommand_1.SwitchModelCommand();
      switchCmd.execute(target, options);
    });
    this.program.command("models").description("Alias for list-models command").action((options) => {
      const listCmd = new ListModelsCommand_1.ListModelsCommand();
      listCmd.execute(options);
    });
    this.program.command("detect").description("Alias for detect-project command").action((options) => {
      const detectCmd = new DetectProjectCommand_1.DetectProjectCommand();
      detectCmd.execute(options);
    });
    this.program.command("status").description("Show project and task status").action(async () => {
      await this.showStatus();
    });
    this.program.command("info").description("Show detailed project information").action(async () => {
      await this.showInfo();
    });
  }
  setupGlobalOptions() {
    this.program.option("--debug", "Enable debug output", false).option("--no-color", "Disable colored output", false).option("--config <path>", "Path to configuration file").option("--quiet", "Suppress non-error output", false);
  }
  setupErrorHandling() {
    this.program.exitOverride();
    process.on("unhandledRejection", (error) => {
      console.error(chalk_1.default.red("Unhandled promise rejection:"), error);
      process.exit(1);
    });
    process.on("uncaughtException", (error) => {
      console.error(chalk_1.default.red("Uncaught exception:"), error);
      process.exit(1);
    });
    process.on("SIGINT", () => {
      console.log(chalk_1.default.yellow("\n\u{1F44B} Goodbye!"));
      process.exit(0);
    });
  }
  async showStatus() {
    try {
      console.log(chalk_1.default.blue("\u{1F4CA} Specify Project Status\n"));
      const { DetectProjectCommand } = await Promise.resolve().then(() => __importStar(require_DetectProjectCommand()));
      const detectCmd = new DetectProjectCommand();
      const validation = await detectCmd.validateCurrentProject();
      if (!validation.valid) {
        console.log(chalk_1.default.yellow("\u26A0\uFE0F  No valid spec-kit project found"));
        console.log(chalk_1.default.gray('Run "specify detect-project" for more details'));
        return;
      }
      const config = validation.config;
      console.log(chalk_1.default.white("\u{1F4CB} Project Information:"));
      console.log(`  Name: ${chalk_1.default.cyan(config.name)}`);
      console.log(`  AI Model: ${chalk_1.default.cyan(config.aiModel)}`);
      console.log(`  Version: ${chalk_1.default.gray(config.version)}`);
      console.log(`  Path: ${chalk_1.default.gray(validation.projectPath)}`);
      try {
        const { TaskTracker } = await Promise.resolve().then(() => __importStar(require_TaskTracker()));
        const taskTracker = new TaskTracker(config);
        await taskTracker.initialize();
        const stats = taskTracker.getTaskStats();
        console.log(chalk_1.default.white("\n\u{1F4C8} Task Status:"));
        console.log(`  Total: ${chalk_1.default.cyan(stats.total)}`);
        console.log(`  Completed: ${chalk_1.default.green(stats.completed)} (${stats.percentComplete}%)`);
        console.log(`  In Progress: ${chalk_1.default.yellow(stats.inProgress)}`);
        console.log(`  Pending: ${chalk_1.default.gray(stats.pending)}`);
        if (stats.failed > 0) {
          console.log(`  Failed: ${chalk_1.default.red(stats.failed)}`);
        }
        const progressBar = this.createProgressBar(stats.percentComplete);
        console.log(`
  ${progressBar}`);
      } catch (error) {
        console.log(chalk_1.default.gray("\n\u{1F4C8} Task Status: No task data available"));
      }
      const { AIModelSettingsProvider } = await Promise.resolve().then(() => __importStar(require_AIModelSettings()));
      const modelSettings = AIModelSettingsProvider.getSettings(config.aiModel);
      if (modelSettings) {
        console.log(chalk_1.default.white("\n\u{1F916} AI Model Status:"));
        console.log(`  Current: ${chalk_1.default.cyan(modelSettings.modelType)} v${modelSettings.version}`);
        console.log(`  Max Tokens: ${chalk_1.default.gray(modelSettings.capabilities.maxTokens.toLocaleString())}`);
        console.log(`  Features: ${chalk_1.default.gray(modelSettings.capabilities.features.length)} available`);
      }
    } catch (error) {
      console.error(chalk_1.default.red(`\u274C Failed to get status: ${error}`));
    }
  }
  async showInfo() {
    try {
      console.log(chalk_1.default.blue(`\u{1F527} Specify CLI v${this.version}
`));
      console.log(chalk_1.default.white("\u{1F4E6} Available Commands:"));
      console.log("  switch-model <target>  Switch AI model (claude/gemini)");
      console.log("  list-models           Show available AI models");
      console.log("  detect-project        Auto-detect and validate project");
      console.log("  reset-project         Clean project reset with backup");
      console.log("  track-tasks <action>  Manage task tracking UI");
      console.log("");
      console.log(chalk_1.default.white("\u{1F517} Aliases:"));
      console.log("  switch <target>       Alias for switch-model");
      console.log("  models               Alias for list-models");
      console.log("  detect               Alias for detect-project");
      console.log("  status               Show project and task status");
      console.log("  info                 Show this information");
      console.log("");
      console.log(chalk_1.default.white("\u{1F3AF} Examples:"));
      console.log("  specify switch claude");
      console.log("  specify models --details");
      console.log("  specify detect --repair");
      console.log("  specify track-tasks enable --sidebar");
      console.log("");
      console.log(chalk_1.default.white("\u{1F3D7}\uFE0F  Architecture:"));
      console.log("  \u2022 Library-first design with CLI wrappers");
      console.log("  \u2022 Real-time task tracking with terminal UI");
      console.log("  \u2022 Automatic project detection and validation");
      console.log("  \u2022 AI model migration with rollback support");
      console.log("");
      console.log(chalk_1.default.gray("Use --help with any command for detailed usage information"));
    } catch (error) {
      console.error(chalk_1.default.red(`\u274C Failed to show info: ${error}`));
    }
  }
  createProgressBar(percentage, width = 20) {
    const filled = Math.round(percentage / 100 * width);
    const empty = width - filled;
    const bar = chalk_1.default.green("\u2588").repeat(filled) + chalk_1.default.gray("\u2591").repeat(empty);
    return `${bar} ${percentage}%`;
  }
  async run(args = process.argv) {
    try {
      if (args.length <= 2) {
        this.program.outputHelp();
        return;
      }
      await this.program.parseAsync(args);
    } catch (error) {
      if (error.code === "commander.invalidArgument") {
        console.error(chalk_1.default.red(`\u274C Invalid argument: ${error.message}`));
        console.error(chalk_1.default.gray("Use --help for usage information"));
      } else if (error.code === "commander.unknownCommand") {
        console.error(chalk_1.default.red(`\u274C Unknown command: ${error.message}`));
        console.error(chalk_1.default.gray("Use --help to see available commands"));
      } else if (error.code === "commander.help") {
        return;
      } else if (error.code === "commander.version") {
        return;
      } else {
        console.error(chalk_1.default.red(`\u274C Error: ${error.message || error}`));
      }
      process.exit(1);
    }
  }
  getProgram() {
    return this.program;
  }
  getVersion() {
    return this.version;
  }
};
exports.SpecifyCLI = SpecifyCLI;
if (require.main === module) {
  const cli = new SpecifyCLI();
  cli.run().catch((error) => {
    console.error(chalk_1.default.red("Fatal error:"), error);
    process.exit(1);
  });
}
