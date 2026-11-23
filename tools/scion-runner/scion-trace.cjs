#!/usr/bin/env node
/**
 * Canonical SCION trace runner for source-tree comparisons and the npm CLI.
 * Agent Name: scion-reference-runner
 * Part of the scjson project. Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM } = require("jsdom");
require("regenerator-runtime/runtime");
// The source-tree lock installs the identical compiler from its vendored tarball.
const { documentStringToModel, core } = require("scxml/dist/scxml.js");
const DEFAULT_INVOKERS = Object.assign({}, core.InterpreterScriptingContext.invokers || {});

function createMockSession(interpreter, invokeObj, payload, hooks = {}) {
  let done = false;
  let cancelled = false;
  const registry = interpreter && interpreter.opts && interpreter.opts.sessionRegistry;

  const session = {
    id: invokeObj.id || `mock-${Math.random().toString(36).slice(2)}`,
    cancel() {
      if (cancelled) return;
      cancelled = true;
      done = true;
      if (registry && invokeObj.id && typeof registry.delete === "function") {
        registry.delete(invokeObj.id);
      }
      if (typeof hooks.onCancel === "function") {
        try {
          hooks.onCancel();
        } catch (err) {
          interpreter._log && interpreter._log("mock cancel error", err);
        }
      }
    },
    gen(evt) {
      if (cancelled || done || !evt) {
        return;
      }
      const name = typeof evt === "string" ? evt : (evt && evt.name) || "";
      const data = evt && typeof evt === "object" ? evt.data : undefined;
      if (typeof hooks.onEvent === "function") {
        try {
          hooks.onEvent(name, data, complete, session);
        } catch (err) {
          interpreter._log && interpreter._log("mock event error", err);
        }
      }
    },
    genAsync(evt) {
      this.gen(evt);
      return Promise.resolve();
    },
  };

  if (registry && invokeObj.id && typeof registry.set === "function") {
    registry.set(invokeObj.id, session);
  }

  function emitDone(outcome) {
    const eventData = outcome === undefined ? payload : outcome;
    if (invokeObj.id) {
      interpreter._scriptingContext.send({
        target: "#_parent",
        name: `done.invoke.${invokeObj.id}`,
        data: eventData,
        invokeid: invokeObj.id,
      });
      interpreter._scriptingContext.send({
        target: "#_parent",
        name: "done.invoke",
        data: eventData,
        invokeid: invokeObj.id,
      });
    } else {
      interpreter._scriptingContext.send({
        target: "#_parent",
        name: "done.invoke",
        data: eventData,
      });
    }
  }

  function complete(outcome) {
    if (done) return;
    done = true;
    if (registry && invokeObj.id && typeof registry.delete === "function") {
      registry.delete(invokeObj.id);
    }
    emitDone(outcome);
    if (typeof hooks.onComplete === "function") {
      try {
        hooks.onComplete(outcome === undefined ? payload : outcome, session);
      } catch (err) {
        interpreter._log && interpreter._log("mock complete error", err);
      }
    }
  }

  if (typeof hooks.onInit === "function") {
    setImmediate(() => {
      if (!cancelled && !done) {
        try {
          hooks.onInit(complete, session);
        } catch (err) {
          interpreter._log && interpreter._log("mock init error", err);
        }
      }
    });
  }

  return { session, complete };
}

const MOCK_INVOKERS = {
  "mock:immediate": (interpreter, invokeObj, _execCtx, cb) => {
    const payload = invokeObj.params || null;
    const { session, complete } = createMockSession(interpreter, invokeObj, payload, {
      onInit: (finish) => finish(payload),
    });
    cb(null, session);
  },
  "mock:deferred": (interpreter, invokeObj, _execCtx, cb) => {
    const payload = invokeObj.params || null;
    const { session } = createMockSession(interpreter, invokeObj, payload, {
      onEvent: (name, data, finish) => {
        if (name === "complete") {
          finish(payload);
        }
      },
    });
    cb(null, session);
  },
  "mock:record": (interpreter, invokeObj, _execCtx, cb) => {
    const payload = invokeObj.params || null;
    const recorded = [];
    const { session } = createMockSession(interpreter, invokeObj, payload, {
      onEvent: (name, data) => {
        recorded.push({ name, data });
      },
    });
    session._recordedEvents = recorded;
    cb(null, session);
  },
};

const COMBINED_INVOKERS = Object.assign({}, DEFAULT_INVOKERS, MOCK_INVOKERS);

const usage = "Usage: scjson-scion-trace -I <chart.scxml> [-e events.jsonl] [-o trace.jsonl]";

function parseArgs(argv) {
  const opts = { isXml: false };
  const options = { "-I": "input", "--input": "input", "-e": "events", "--events": "events",
                    "-o": "out", "--out": "out" };
  for (let i = 0; i < argv.length; ++i) {
    const arg = argv[i];
    if (arg === "--xml") opts.isXml = true;
    else if (Object.hasOwn(options, arg)) {
      const value = argv[++i];
      if (!value || value.startsWith("-")) throw new Error("Missing value for " + arg);
      opts[options[arg]] = value;
    } else {
      throw new Error("Unknown argument: " + arg);
    }
  }
  if (!opts.input) throw new Error(usage);
  return opts;
}

function readEvents(filePath) {
  if (!filePath) {
    return [];
  }
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  const events = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    const obj = JSON.parse(line);
    const name = obj.event || obj.name;
    if (!name) continue;
    events.push({ name, data: Object.prototype.hasOwnProperty.call(obj, "data") ? obj.data : null });
  }
  return events;
}

function makeDom(url) {
  const dom = new JSDOM("", { url });
  global.window = dom.window;
  global.document = dom.window.document;
  global.location = dom.window.location;
  return dom;
}

function createContext(event) {
  return {
    event,
    entered: new Set(),
    exited: new Set(),
    transitions: [],
    actionLog: [],
    beforeSnapshot: null,
    afterSnapshot: null,
  };
}

function cloneConfig(snapshot) {
  return snapshot && Array.isArray(snapshot[0]) ? new Set(snapshot[0]) : new Set();
}

function cloneDatamodel(snapshot) {
  if (!snapshot || typeof snapshot[3] !== "object" || snapshot[3] === null) {
    return {};
  }
  return JSON.parse(JSON.stringify(snapshot[3]));
}

function computeDelta(before, after) {
  const delta = {};
  const keys = new Set([
    ...Object.keys(before || {}),
    ...Object.keys(after || {})
  ]);
  for (const key of keys) {
    const beforeVal = before ? before[key] : undefined;
    const afterVal = after ? after[key] : undefined;
    const beforeJson = JSON.stringify(beforeVal);
    const afterJson = JSON.stringify(afterVal);
    if (beforeJson !== afterJson) {
      delta[key] = afterVal === undefined ? null : afterVal;
    }
  }
  return delta;
}

function formatLogArg(arg) {
  if (typeof arg === "string") return arg;
  try {
    return JSON.stringify(arg);
  } catch (err) {
    return String(arg);
  }
}

function isUserState(stateId) {
  return Boolean(stateId) && !String(stateId).startsWith("$generated-");
}

function filterStates(iterable) {
  return Array.from(iterable).filter((sid) => isUserState(sid));
}

function traceFrame(ctx, step) {
  const beforeConfig = cloneConfig(ctx.beforeSnapshot);
  const afterConfig = cloneConfig(ctx.afterSnapshot);
  const beforeDatamodel = cloneDatamodel(ctx.beforeSnapshot);
  const afterDatamodel = cloneDatamodel(ctx.afterSnapshot);

  let enteredStates = filterStates(ctx.entered);
  if (enteredStates.length === 0) {
    const diff = filterStates([...afterConfig].filter((state) => !beforeConfig.has(state)));
    enteredStates = diff;
  }

  let exitedStates = filterStates(ctx.exited);
  if (exitedStates.length === 0) {
    const diff = filterStates([...beforeConfig].filter((state) => !afterConfig.has(state)));
    exitedStates = diff;
  }

  const firedTransitions = ctx.transitions
    .filter((t) => isUserState(t.source))
    .map((t) => ({
      source: t.source,
      targets: t.targets.filter((target) => isUserState(target)),
      event: ctx.event ? ctx.event.name : null,
      cond: null,
    }))
    .filter((t) => t.targets.length > 0);

  const configuration = filterStates(afterConfig);

  return {
    step,
    event: ctx.event ? { name: ctx.event.name, data: ctx.event.data } : null,
    firedTransitions,
    enteredStates: enteredStates.sort(),
    exitedStates: exitedStates.sort(),
    configuration: configuration.sort(),
    actionLog: ctx.actionLog.slice(),
    datamodelDelta: computeDelta(beforeDatamodel, afterDatamodel),
  };

}

async function execute(opts, convertJson, emit) {
  const chartPath = path.resolve(opts.input);
  const url = pathToFileURL(chartPath).href;
  let xml = fs.readFileSync(chartPath, "utf8");
  if (convertJson && !opts.isXml && /\.(scjson|json)$/i.test(chartPath)) xml = convertJson(xml);
  const events = opts.events ? readEvents(opts.events) : [];
  const dom = makeDom(new URL(".", url).href);
  try {
    const factory = await new Promise((resolve, reject) => {
      documentStringToModel(url, xml, (err, model) => err ? reject(err) : resolve(model));
    });
    const prepared = await new Promise((resolve, reject) => {
      factory.prepare((err, model) => err ? reject(err) : resolve(model), undefined,
                      { document: dom.window.document });
    });
    const interpreter = new core.Statechart(prepared, { invokers: COMBINED_INVOKERS });
    const listenerState = { current: null };
    const originalLog = console.log;

    const listener = {
      onEntry(stateId) {
        if (listenerState.current) listenerState.current.entered.add(stateId);
      },
      onExit(stateId) {
        if (listenerState.current) listenerState.current.exited.add(stateId);
      },
      onTransition(source, targets) {
        if (listenerState.current) {
          const arr = Array.isArray(targets) ? targets.slice() : [targets];
          listenerState.current.transitions.push({ source, targets: arr });
        }
      },
    };
    interpreter.registerListener(listener);

    function runWithContext(ctx, fn) {
      listenerState.current = ctx;
      const actionLogger = (...args) => {
        const formatted = args.map(formatLogArg);
        let payload;
        if (formatted.length === 2 && typeof args[0] === "string") {
          payload = `${formatted[0]}:${formatted[1]}`;
        } else {
          payload = formatted.join(" ");
        }
        listenerState.current.actionLog.push(payload);
      };
      console.log = actionLogger;
      try {
        fn();
      } finally {
        console.log = originalLog;
        listenerState.current = null;
      }
    }

    // Initial step
    const startCtx = createContext(null);
    startCtx.beforeSnapshot = [[], {}, false, {}, []];
    runWithContext(startCtx, () => interpreter.start());
    startCtx.afterSnapshot = interpreter.getSnapshot();
    emit(traceFrame(startCtx, 0));

    // Event steps
    let stepNo = 1;
    for (const evt of events) {
      const eventObj = { name: evt.name, data: evt.data };
      const ctx = createContext(eventObj);
      ctx.beforeSnapshot = interpreter.getSnapshot();
      runWithContext(ctx, () => {
        interpreter.gen({ name: evt.name, data: evt.data });
      });
      ctx.afterSnapshot = interpreter.getSnapshot();
      emit(traceFrame(ctx, stepNo));
      stepNo += 1;
    }
  } finally {
    dom.window.close();
  }
}

/**
 * Run the reference CLI, optionally converting saved SCJSON and normalizing frames.
 * @param {string[]} argv CLI arguments, after any caller-specific flags.
 * @param {object} hooks Package converter and frame normalization callbacks.
 * @returns {Promise<void>} Resolves after the last frame is written or an error is reported.
 */
async function runCli(argv, { convertJson, normalize = frame => frame } = {}) {
  if (argv.includes("--help") || argv.includes("-h")) {
    console.log(usage);
    return;
  }
  // An unresolved compiler callback with no remaining Node work must fail the CLI.
  process.exitCode = 1;
  let temporary, fd;
  try {
    const opts = parseArgs(argv);
    if (opts.out) {
      temporary = fs.mkdtempSync(path.join(path.dirname(path.resolve(opts.out)), ".scjson-trace-"));
      fd = fs.openSync(path.join(temporary, "trace.jsonl"), "wx");
    }
    let count = 0;
    await execute(opts, convertJson, frame => {
      const line = JSON.stringify(normalize(frame)) + "\n";
      if (fd === undefined) process.stdout.write(line);
      else fs.writeFileSync(fd, line);
      ++count;
    });
    if (!count) throw new Error("SCION produced no trace frames");
    if (fd !== undefined) {
      fs.closeSync(fd);
      fd = undefined;
      fs.renameSync(path.join(temporary, "trace.jsonl"), path.resolve(opts.out));
    }
    process.exitCode = 0;
  } catch (error) {
    console.error("SCION trace failed:", error.message || error);
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
    if (temporary) fs.rmSync(temporary, { recursive: true, force: true });
  }
}

module.exports = { runCli };
if (require.main === module) runCli(process.argv.slice(2));
