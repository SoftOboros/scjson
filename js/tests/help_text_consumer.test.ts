/**
 * Agent Name: js-help-text-consumer-fixture
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 *
 * TypeScript compilation smoke fixture for the CONV-E ``helpText`` surface.
 *
 * This file is not run as part of the jest suite — it exists so that a
 * separate ``npx tsc --noEmit tests/help_text_consumer.test.ts`` invocation
 * proves the published interfaces declare ``helpText: string[]`` on each of
 * the five sampled CONV-E applies-to elements. If a future regeneration
 * drops the field, this file fails to type-check and surfaces the
 * regression before any runtime test would.
 *
 * The dist resolution is intentionally relative; the published npm package
 * resolves the same identifiers through ``package.json`` ``exports``.
 */

// @ts-ignore -- the dist directory lives outside the tsconfig include set.
import {
    defaultAssign,
    defaultScxml,
    defaultSend,
    defaultState,
    defaultTransition,
} from '../dist/scjsonProps';
// @ts-ignore -- same reason as the value import above.
import type {
    AssignProps,
    ScxmlProps,
    SendProps,
    StateProps,
    TransitionProps,
} from '../dist/scjsonProps';

const scxml: ScxmlProps = { ...defaultScxml(), helpText: ['doc'] };
const state: StateProps = { ...defaultState(), helpText: ['doc'] };
const transition: TransitionProps = { ...defaultTransition(), helpText: ['doc'] };
const assign: AssignProps = { ...defaultAssign(), helpText: ['doc'] };
const send: SendProps = { ...defaultSend(), helpText: ['doc'] };

// Side-effect-free log so the module is not considered purely declarative
// by some build orchestrators that prune type-only files.
// eslint-disable-next-line no-console
console.log(
    'help_text_consumer smoke fixture loaded',
    Array.isArray(scxml.helpText) && Array.isArray(state.helpText) &&
        Array.isArray(transition.helpText) && Array.isArray(assign.helpText) &&
        Array.isArray(send.helpText),
);
