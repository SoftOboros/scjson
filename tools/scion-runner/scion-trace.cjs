#!/usr/bin/env node

"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
let JSDOM = null;
try {
  ({ JSDOM } = require("jsdom"));
} catch (e) {
  // Optional: jsdom not installed; we'll use a minimal stub DOM
}
try {
  require("regenerator-runtime/runtime");
} catch (e) {
  // Optional: when not present, Node's native async should suffice
}

const SCION_NPM_URL = "https://www.npmjs.com/package/scion";
function loadScxmlBundle() {
  // Attempt normal resolution first
  try {
    return require("scxml/dist/scxml.js");
  } catch (e) {
    // Fallback: extract from vendored tarball on the fly
    const zlib = require("zlib");
    const vendorTgz = path.resolve(__dirname, "vendor", "scxml-5.0.4.tgz");
    // Prefer pre-extracted vendor path if present
    const preExtracted = path.resolve(__dirname, "vendor", "package", "dist", "scxml.js");
    const outJs = path.resolve(__dirname, "vendor", "scxml.dist.js");
    try {
      if (fs.existsSync(preExtracted)) {
        return require(preExtracted);
      }
      // Try extracting via system tar if available
      try {
        const { execSync } = require("child_process");
        if (fs.existsSync(vendorTgz)) {
          const vendorDir = path.resolve(__dirname, "vendor");
          execSync(`tar -xzf ${JSON.stringify(vendorTgz)} -C ${JSON.stringify(vendorDir)} package/dist/scxml.js`, { stdio: "ignore" });
          if (fs.existsSync(preExtracted)) {
            return require(preExtracted);
          }
        }
      } catch (tarErr) {
        // fall through to manual extraction
      }
      if (!fs.existsSync(outJs)) {
        const gzData = fs.readFileSync(vendorTgz);
        const tarData = zlib.gunzipSync(gzData);
        // Tar format: 512-byte headers; filename at 0..99, size at 124..135 (octal)
        let offset = 0;
        const BLOCK = 512;
        const target = "package/dist/scxml.js";
        while (offset + BLOCK <= tarData.length) {
          const header = tarData.subarray(offset, offset + BLOCK);
          const name = header.subarray(0, 100).toString().replace(/\0+$/, "");
          if (!name) break; // two consecutive zero blocks indicate end of archive
          const sizeOct = header.subarray(124, 136).toString().replace(/\0+$/, "").trim();
          const size = parseInt(sizeOct || "0", 8);
          offset += BLOCK;
          if (name === target) {
            const fileBuf = tarData.subarray(offset, offset + size);
            fs.writeFileSync(outJs, fileBuf);
            break;
          }
          // Skip file content (rounded up to 512)
          const pad = ((size + BLOCK - 1) & ~(BLOCK - 1));
          offset += pad;
        }
      }
      if (fs.existsSync(outJs)) {
        return require(outJs);
      }
    } catch (ex) {
      // fall through
    }
    throw e;
  }
}

const scxmlBundle = loadScxmlBundle();
const { documentStringToModel, core } = scxmlBundle;
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

function usage() {
  console.error(
    "Usage: scjson-scion-trace -I <chart.scxml> [-e events.jsonl] [-o trace.jsonl]"
  );
  process.exit(1);
}

function parseArgs(argv) {
  const opts = { isXml: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case "-I":
      case "--input":
        opts.input = argv[++i];
        break;
      case "-e":
      case "--events":
        opts.events = argv[++i];
        break;
      case "-o":
      case "--out":
        opts.out = argv[++i];
        break;
      case "--xml":
        opts.isXml = true;
        break;
      case "-h":
      case "--help":
        usage();
        break;
      default:
        if (arg.startsWith("-")) {
          console.error(`Unknown option: ${arg}`);
          usage();
        }
    }
  }
  if (!opts.input) usage();
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
  if (JSDOM) {
    const dom = new JSDOM("", { url });
    global.window = dom.window;
    global.document = dom.window.document;
    global.location = dom.window.location;
    return dom;
  }
  // Fallback stub when jsdom is unavailable
  const stub = {
    window: {
      close() {},
      document: undefined,
      location: { href: url },
    },
  };
  global.window = stub.window;
  global.document = stub.window.document;
  global.location = stub.window.location;
  return stub;
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

function emitTrace(ctx, step, sink) {
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

  const trace = {
    step,
    event: ctx.event ? { name: ctx.event.name, data: ctx.event.data } : null,
    firedTransitions,
    enteredStates: enteredStates.sort(),
    exitedStates: exitedStates.sort(),
    configuration: configuration.sort(),
    actionLog: ctx.actionLog.slice(),
    datamodelDelta: computeDelta(beforeDatamodel, afterDatamodel),
  };

  sink.write(`${JSON.stringify(trace)}\n`);
}

(function main() {
  const opts = parseArgs(process.argv.slice(2));
  const chartPath = path.resolve(opts.input);
  if (!fs.existsSync(chartPath)) {
    console.error(`Chart not found: ${chartPath}`);
    process.exit(1);
  }
  const events = opts.events ? readEvents(path.resolve(opts.events)) : [];

  const sink = opts.out
    ? fs.createWriteStream(path.resolve(opts.out), { encoding: "utf8" })
    : process.stdout;

  const dom = makeDom("file:///" + path.dirname(chartPath) + "/");

  const xml = fs.readFileSync(chartPath, "utf8");
  const url = pathToFileURL(chartPath).toString();

  documentStringToModel(url, xml, (err, modelFactory) => {
    if (err) {
      console.error(`SCION (${SCION_NPM_URL}) compile error`, err);
      process.exit(1);
    }

    modelFactory.prepare(
      (prepErr, prepared) => {
        if (prepErr) {
          console.error(`SCION (${SCION_NPM_URL}) prepare error`, prepErr);
          process.exit(1);
        }

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
        emitTrace(startCtx, 0, sink);

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
          emitTrace(ctx, stepNo, sink);
          stepNo += 1;
        }

        if (sink !== process.stdout) {
          sink.end();
        }
        dom.window.close();
      },
      undefined,
      { document: global.document }
    );
  });
})();
