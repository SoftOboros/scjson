/**
 * Agent Name: js-help-text-surface-tests
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 *
 * scjson 0.4.1 acceptance tests for the TypeScript ``helpText`` surface.
 *
 * The pydantic models gained ``help_text: list[str]`` under CONV-E (shipped
 * in 0.4.0), but ``js/src/scjsonProps.ts`` was generated before that change
 * landed and ``scjson@0.4.0`` on npm therefore shipped ``ScxmlProps``/etc.
 * interfaces without ``helpText``. After regenerating from the current
 * pydantic schema, all 26 CONV-E applies-to factories must:
 *
 *   1. Initialize ``helpText`` to a fresh empty array.
 *   2. Round-trip the field through ``JSON.stringify``/``JSON.parse`` with
 *      order preserved.
 *   3. Keep ``helpText`` distinct from ``otherAttributes`` so mutating one
 *      does not affect the other.
 *
 * See ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` §11 (2026-05-28 entry)
 * and ``docs/concepts/ERRATA.md`` ERRATA-001 for the normative contract.
 */

// The npm tsc build emits artifacts beneath ``dist/`` but the exact layout
// (top-level vs. ``dist/src/``) depends on whether non-.ts files are present
// in ``src/`` at build time. Resolve both so this suite stays robust across
// either layout.
let propsModule;
try {
    propsModule = require('../dist/scjsonProps.js');
} catch (_err) {
    propsModule = require('../dist/src/scjsonProps.js');
}

const {
    defaultAssign,
    defaultCancel,
    defaultContent,
    defaultData,
    defaultDatamodel,
    defaultDonedata,
    defaultElse,
    defaultElseif,
    defaultFinal,
    defaultFinalize,
    defaultForeach,
    defaultHistory,
    defaultIf,
    defaultInitial,
    defaultInvoke,
    defaultLog,
    defaultOnentry,
    defaultOnexit,
    defaultParallel,
    defaultParam,
    defaultRaise,
    defaultScript,
    defaultScxml,
    defaultSend,
    defaultState,
    defaultTransition,
} = propsModule;

/**
 * Parameterized list of the 26 CONV-E applies-to default factories. The
 * count is normative per CONV-E §11 — adding or removing an entry without
 * a matching spec amendment indicates a generator drift.
 */
const FACTORIES = [
    ['defaultAssign', defaultAssign],
    ['defaultCancel', defaultCancel],
    ['defaultContent', defaultContent],
    ['defaultData', defaultData],
    ['defaultDatamodel', defaultDatamodel],
    ['defaultDonedata', defaultDonedata],
    ['defaultElse', defaultElse],
    ['defaultElseif', defaultElseif],
    ['defaultFinal', defaultFinal],
    ['defaultFinalize', defaultFinalize],
    ['defaultForeach', defaultForeach],
    ['defaultHistory', defaultHistory],
    ['defaultIf', defaultIf],
    ['defaultInitial', defaultInitial],
    ['defaultInvoke', defaultInvoke],
    ['defaultLog', defaultLog],
    ['defaultOnentry', defaultOnentry],
    ['defaultOnexit', defaultOnexit],
    ['defaultParallel', defaultParallel],
    ['defaultParam', defaultParam],
    ['defaultRaise', defaultRaise],
    ['defaultScript', defaultScript],
    ['defaultScxml', defaultScxml],
    ['defaultSend', defaultSend],
    ['defaultState', defaultState],
    ['defaultTransition', defaultTransition],
];

describe('CONV-E helpText surface — default factories', () => {
    test('all 26 factories are exported', () => {
        expect(FACTORIES).toHaveLength(26);
        for (const [name, factory] of FACTORIES) {
            expect(typeof factory).toBe('function');
            // Helpful failure message if a binding is missing.
            if (typeof factory !== 'function') {
                throw new Error(`Factory ${name} is not a function`);
            }
        }
    });

    test.each(FACTORIES)(
        '%s().helpText is a fresh empty array',
        (_name, factory) => {
            const instance = factory();
            expect(Array.isArray(instance.helpText)).toBe(true);
            expect(instance.helpText.length).toBe(0);
        },
    );
});

describe('CONV-E helpText surface — semantics', () => {
    test('helpText survives JSON.parse(JSON.stringify(...)) round-trip with order preserved', () => {
        const original = defaultScxml();
        original.helpText = ['doc one', 'doc two'];
        const serialized = JSON.stringify(original);
        const restored = JSON.parse(serialized);
        expect(Array.isArray(restored.helpText)).toBe(true);
        expect(restored.helpText).toEqual(['doc one', 'doc two']);
        // Order is significant for the CONV-E contract: the emitted XML
        // comment block preserves source order.
        expect(restored.helpText[0]).toBe('doc one');
        expect(restored.helpText[1]).toBe('doc two');
    });

    test('helpText and otherAttributes are distinct fields (mutation is isolated)', () => {
        const instance = defaultScxml();
        expect(instance.helpText).not.toBe(instance.otherAttributes);
        instance.helpText.push('only on help text');
        expect(instance.helpText).toEqual(['only on help text']);
        expect(instance.otherAttributes).toEqual({});
        instance.otherAttributes.someAttr = 'value';
        expect(instance.helpText).toEqual(['only on help text']);
        expect(instance.otherAttributes).toEqual({ someAttr: 'value' });
    });

    test('helpText defaults are not shared between factory calls', () => {
        const a = defaultScxml();
        const b = defaultScxml();
        a.helpText.push('mutated a');
        expect(a.helpText).toEqual(['mutated a']);
        expect(b.helpText).toEqual([]);
    });
});
