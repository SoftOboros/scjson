/**
 * Agent Name: js-comment-promotion
 *
 * Part of the scjson project.
 * Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 *
 * CONV-F (SCXML Comment Promotion) — JavaScript parity.
 *
 * See ``docs/concepts/SCJSON-CONV-00-CONCEPTS.md`` (CONV-F, ~lines 270-388)
 * for the normative contract this module implements and
 * ``py/scjson/comment_promotion.py`` for the canonical Python implementation
 * this module mirrors.
 *
 * Public surface:
 *
 * - ``extractHelpTextFromXml(xmlStr)`` — XML pre-pass. Parses ``xmlStr`` with
 *   ``fast-xml-parser`` in ``preserveOrder`` + ``commentPropName`` mode,
 *   assigns deterministic addresses to every element, partitions XML comment
 *   nodes onto their owning element per CONV-F rules 1-8, and returns the
 *   comment-free XML plus an ``address -> [comment_text, ...]`` map.
 * - ``attachHelpTextToModel(model, addressMap)`` — after the existing
 *   ``xmlToJson`` pipeline produces a JS object from the comment-free XML,
 *   walks the model in the same deterministic order and appends each comment
 *   string to the matching element's ``help_text`` array.
 * - ``injectHelpTextCommentsIntoXml(xmlStr, model)`` — post-pass for the
 *   SCJSON-to-SCXML direction. Takes the model and the comment-free XML
 *   produced by ``jsonToXml`` and inserts ``<!-- ... -->`` nodes immediately
 *   before the owning element (or before the ``<scxml>`` root for root-level
 *   entries).
 *
 * Addressing
 * ----------
 *
 * Each element gets an address of shape
 * ``[["scxml", 0], ["state", 1], ["transition", 0], ...]`` where each
 * segment is ``[local_tag_name, index_among_same-tag_element_siblings]``.
 * This MUST match the Python tuple shape byte-for-byte (after canonical
 * JSON serialization) so cross-language fixtures align.
 *
 * XML-local element names are used (the parser drops the ``xmlns`` prefix
 * because SCXML elements are not namespace-qualified in serialized form;
 * any future namespaced extensions would be opaque and not promoted).
 *
 * Model-attribute mapping
 * -----------------------
 *
 * The JS model surface renames a few XML tags to avoid JavaScript reserved
 * words:
 *
 * - ``<if>``     -> ``if_value``
 * - ``<raise>``  -> ``raise_value``
 * - ``<else>``   -> ``else_value``
 *
 * Address segments always use the XML local name; resolution into the model
 * goes through ``TAG_TO_ATTR`` below.
 *
 * Singleton vs. array fields
 * --------------------------
 *
 * Most child fields are arrays in the JS model (mirrors xsdata's
 * ``list[Element]`` shape). Two exceptions match the Python model:
 *
 * - ``History.transition`` is a singleton object.
 * - ``Initial.transition`` is a singleton object.
 *
 * Address-shape parity with Python only requires that the *first* sibling at
 * index ``0`` resolves to that object; index > 0 returns ``null``.
 *
 * Script / Data exclusion (rule 5)
 * --------------------------------
 *
 * Comments inside ``<script>`` and ``<data>`` are body content of opaque
 * source. They are not promoted.
 *
 * Extension subtree exclusion (rule 6)
 * ------------------------------------
 *
 * Any element whose local name is not in ``APPLIES_TO_TAGS`` is treated as an
 * opaque extension. Comments inside such subtrees are not promoted.
 *
 * Emission text safety (§340-344)
 * -------------------------------
 *
 * Comment text containing ``--`` is replaced with ``- -``; a body ending in
 * ``-`` gets one trailing space appended; the builder handles XML
 * metacharacters because comment bodies are emitted literally.
 */

'use strict';

const { XMLParser, XMLBuilder } = require('fast-xml-parser');

/**
 * Local tag names that own a ``help_text`` field on the model side.
 * Mirrors ``APPLIES_TO_TAGS`` in ``py/scjson/comment_promotion.py``.
 */
const APPLIES_TO_TAGS = new Set([
  'scxml',
  'state',
  'parallel',
  'final',
  'history',
  'initial',
  'transition',
  'onentry',
  'onexit',
  'invoke',
  'finalize',
  'datamodel',
  'data',
  'donedata',
  'content',
  'param',
  'assign',
  'log',
  'raise',
  'if',
  'elseif',
  'else',
  'foreach',
  'send',
  'cancel',
  'script',
]);

/**
 * Tags whose textual content is opaque target-language source. Comments
 * inside these elements remain content and MUST NOT be promoted (CONV-F
 * rule 5).
 */
const SOURCE_BODY_TAGS = new Set(['script', 'data']);

/**
 * XML local-tag -> JS model attribute name. Mirrors xsdata's renames.
 */
const TAG_TO_ATTR = {
  if: 'if_value',
  raise: 'raise_value',
  else: 'else_value',
};

/**
 * Fields in the JS model that hold a *singleton* object rather than an
 * array of objects under XML elements named ``transition``.
 *
 * Used by ``resolveAddress`` so a singleton field can still satisfy an
 * address segment ``["transition", 0]`` even though it is not wrapped in
 * a JS array.
 */
const SINGLETON_TRANSITION_PARENTS = new Set(['history', 'initial']);

/**
 * Return the JS model attribute name for an XML local tag.
 *
 * @param {string} tag - XML local tag name.
 * @returns {string} Attribute name on the JS model object.
 */
function modelAttrForTag(tag) {
  return Object.prototype.hasOwnProperty.call(TAG_TO_ATTR, tag)
    ? TAG_TO_ATTR[tag]
    : tag;
}

/**
 * Canonical key for a tuple-address. Used as a Map key so two addresses
 * with the same shape collide.
 *
 * @param {Array<[string, number]>} address - Tuple address.
 * @returns {string} JSON serialization of the address.
 */
function addressKey(address) {
  return JSON.stringify(address);
}

// ---------------------------------------------------------------------------
// Comment text repair (parser side + emitter side share this).
// ---------------------------------------------------------------------------

/**
 * Repair raw XML comment body text per CONV-F §294-299.
 *
 * Strips a common leading indentation margin from multi-line block comments
 * and trims leading/trailing blank lines. Does NOT paragraph-wrap or
 * coalesce. Single-line comments are stripped only of edge whitespace.
 *
 * @param {string} raw - Comment body text without the ``<!--`` / ``-->``
 *     delimiters.
 * @returns {string} Repaired text suitable for storage in ``help_text``.
 */
function repairCommentText(raw) {
  if (raw === null || raw === undefined) {
    return '';
  }
  const str = String(raw);
  if (!str.includes('\n')) {
    return str.replace(/^[ \t\r\n]+|[ \t\r\n]+$/g, '');
  }
  const lines = str.split('\n');
  while (lines.length && lines[0].trim() === '') {
    lines.shift();
  }
  while (lines.length && lines[lines.length - 1].trim() === '') {
    lines.pop();
  }
  if (lines.length === 0) {
    return '';
  }
  const indents = [];
  for (const line of lines) {
    if (line.trim() === '') continue;
    const m = line.match(/^[ \t]*/);
    indents.push(m ? m[0].length : 0);
  }
  const common = indents.length ? Math.min(...indents) : 0;
  if (common) {
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      lines[i] = line.length >= common ? line.slice(common) : line;
    }
  }
  return lines.join('\n');
}

/**
 * Return a body string safe to wrap in ``<!-- ... -->``.
 *
 * Per CONV-F §340-344: the forbidden sequence ``--`` is replaced with
 * ``- -`` and a body ending in ``-`` gets one trailing space appended.
 *
 * @param {string} text - Repaired help_text entry.
 * @returns {string} Comment-safe body.
 */
function emitSafeCommentText(text) {
  let safe = String(text == null ? '' : text).replace(/--/g, '- -');
  if (safe.endsWith('-')) {
    safe = safe + ' ';
  }
  return safe;
}

// ---------------------------------------------------------------------------
// Pre-pass node classifiers + helpers.
// ---------------------------------------------------------------------------

/**
 * The preserveOrder shape of fast-xml-parser v5 represents every node as an
 * object with exactly one own-data key plus an optional ``:@`` attributes
 * group. This helper returns the data key, or ``null`` for the attributes
 * group key itself.
 *
 * @param {object} node - preserveOrder node.
 * @returns {string|null} The data key (tag name or ``#text`` / ``#comment``).
 */
function nodeDataKey(node) {
  if (node === null || typeof node !== 'object') return null;
  for (const k of Object.keys(node)) {
    if (k !== ':@') return k;
  }
  return null;
}

/**
 * @param {object} node - preserveOrder node.
 * @returns {boolean}
 */
function isCommentNode(node) {
  return nodeDataKey(node) === '#comment';
}

/**
 * @param {object} node - preserveOrder node.
 * @returns {boolean}
 */
function isTextNode(node) {
  return nodeDataKey(node) === '#text';
}

/**
 * @param {object} node - preserveOrder node.
 * @returns {boolean} True if this is a processing instruction node.
 */
function isProcessingInstructionNode(node) {
  const k = nodeDataKey(node);
  return typeof k === 'string' && k.startsWith('?');
}

/**
 * @param {object} node - preserveOrder node.
 * @returns {boolean} True for element nodes (tag-named, not PI/comment/text).
 */
function isElementNode(node) {
  const k = nodeDataKey(node);
  if (k === null) return false;
  if (k === '#text' || k === '#comment') return false;
  if (k.startsWith('?')) return false;
  if (k.startsWith('!')) return false;
  return true;
}

/**
 * Extract the body text from a ``#comment`` node.
 *
 * @param {object} node - preserveOrder comment node.
 * @returns {string} Raw body text.
 */
function commentBody(node) {
  const arr = node['#comment'];
  if (!Array.isArray(arr) || arr.length === 0) return '';
  const first = arr[0];
  if (first && typeof first === 'object' && '#text' in first) {
    return String(first['#text'] == null ? '' : first['#text']);
  }
  return '';
}

/**
 * Extract the body text from a ``#text`` node.
 */
function textBody(node) {
  if (!node || typeof node !== 'object') return '';
  const v = node['#text'];
  return v == null ? '' : String(v);
}

/**
 * Strip a local prefix from a tag returned by fast-xml-parser. The parser
 * already drops the ``xmlns`` URI; this helper survives any future
 * namespace-aware caller using ``{namespace}local`` form.
 *
 * @param {string} tag - Tag name.
 * @returns {string} Local tag name.
 */
function localName(tag) {
  if (typeof tag !== 'string') return tag;
  if (tag.startsWith('{')) {
    const end = tag.indexOf('}');
    if (end !== -1) return tag.slice(end + 1);
  }
  return tag;
}

// ---------------------------------------------------------------------------
// Pre-pass: tree walker that builds the address map.
// ---------------------------------------------------------------------------

/**
 * Walk an element's preserveOrder children, partition comments onto
 * deterministic addresses per CONV-F rules, and recurse.
 *
 * Mutates ``addressMap`` in place. Does NOT strip comments — that happens
 * separately in ``buildCleanedTree``.
 *
 * @param {object} elem - preserveOrder element node.
 * @param {Array<[string, number]>} address - Address of ``elem`` itself.
 * @param {Map<string, string[]>} addressMap - canonical address-key ->
 *     comment list.
 * @param {boolean} insideSourceBody - True if any ancestor is
 *     ``<script>`` / ``<data>``.
 * @param {boolean} insideExtension - True if any ancestor is an opaque
 *     extension element.
 */
function walkPromotion(
  elem,
  address,
  addressMap,
  insideSourceBody,
  insideExtension
) {
  const elemTag = nodeDataKey(elem);
  if (elemTag === null) return;
  const elemLocal = localName(elemTag);
  const elemInSource = insideSourceBody || SOURCE_BODY_TAGS.has(elemLocal);
  // The root element is always treated as inside-known: APPLIES_TO_TAGS
  // contains "scxml" so the root passes; for any other root we still walk
  // its subtree but no promotions will land because elemInExtension stays
  // true at every step.
  const elemInExtension =
    insideExtension || (!APPLIES_TO_TAGS.has(elemLocal) && address.length > 0);

  const children = elem[elemTag];
  if (!Array.isArray(children) || children.length === 0) return;

  // Pending: comments awaiting a next element sibling.
  let pending = [];
  // Per-local-tag sibling counters for child elements.
  const perTagCounter = Object.create(null);

  for (const child of children) {
    if (isTextNode(child)) {
      const t = textBody(child);
      if (t && t.trim() !== '') {
        // Non-whitespace text severs the "pending -> next element"
        // relationship; flush pending to *this* element (its parent).
        if (pending.length) {
          if (
            !elemInSource &&
            !elemInExtension &&
            APPLIES_TO_TAGS.has(elemLocal) &&
            address.length > 0
          ) {
            const key = addressKey(address);
            const existing = addressMap.get(key) || [];
            addressMap.set(key, existing.concat(pending));
          }
          pending = [];
        }
      }
      // whitespace-only text does not flush
      continue;
    }

    if (isProcessingInstructionNode(child)) {
      // PIs never promote, never sever.
      continue;
    }

    if (isCommentNode(child)) {
      const raw = commentBody(child);
      pending.push(repairCommentText(raw));
      continue;
    }

    if (isElementNode(child)) {
      const childTag = nodeDataKey(child);
      const childLocal = localName(childTag);
      const idx = perTagCounter[childLocal] || 0;
      perTagCounter[childLocal] = idx + 1;
      const childAddr = address.concat([[childLocal, idx]]);

      const targetEligible =
        APPLIES_TO_TAGS.has(childLocal) &&
        !elemInSource &&
        !elemInExtension;

      if (pending.length && targetEligible) {
        const key = addressKey(childAddr);
        const existing = addressMap.get(key) || [];
        addressMap.set(key, existing.concat(pending));
      } else if (pending.length) {
        // Try flushing to parent if parent is promotion-eligible.
        if (
          address.length > 0 &&
          !elemInSource &&
          !elemInExtension &&
          APPLIES_TO_TAGS.has(elemLocal)
        ) {
          const key = addressKey(address);
          const existing = addressMap.get(key) || [];
          addressMap.set(key, existing.concat(pending));
        }
        // Else silently drop (extension subtree).
      }
      pending = [];

      walkPromotion(
        child,
        childAddr,
        addressMap,
        elemInSource,
        elemInExtension
      );
      continue;
    }

    // Anything else (DOCTYPE, etc.) — ignore.
  }

  // After all children, leftover pending comments attach to this element
  // (rule 3). Suppressed under script/data and extension subtrees.
  if (pending.length) {
    if (
      !elemInSource &&
      !elemInExtension &&
      APPLIES_TO_TAGS.has(elemLocal) &&
      address.length > 0
    ) {
      const key = addressKey(address);
      const existing = addressMap.get(key) || [];
      addressMap.set(key, existing.concat(pending));
    }
  }
}

/**
 * Build a comment-free copy of the preserveOrder tree, preserving
 * processing instructions but dropping every ``#comment``.
 *
 * @param {Array<object>} tree - Top-level preserveOrder array.
 * @returns {Array<object>} Cleaned tree (new array, deep-cloned bodies).
 */
function buildCleanedTree(tree) {
  function clean(node) {
    if (node === null || typeof node !== 'object') return node;
    const dataKey = nodeDataKey(node);
    if (dataKey === '#comment') return null;
    const out = {};
    for (const k of Object.keys(node)) {
      const v = node[k];
      if (k === ':@') {
        out[k] = Array.isArray(v) ? v.slice() : Object.assign({}, v);
      } else if (Array.isArray(v)) {
        const cleaned = [];
        for (const c of v) {
          const r = clean(c);
          if (r !== null) cleaned.push(r);
        }
        out[k] = cleaned;
      } else {
        out[k] = v;
      }
    }
    return out;
  }
  const result = [];
  for (const n of tree) {
    const r = clean(n);
    if (r !== null) result.push(r);
  }
  return result;
}

/**
 * Locate the root element in a preserveOrder top-level tree.
 *
 * @param {Array<object>} tree - Top-level array.
 * @returns {object|null} Root element node or null.
 */
function findRootElement(tree) {
  for (const node of tree) {
    if (isElementNode(node)) return node;
  }
  return null;
}

/**
 * Extract help_text promotion metadata from an SCXML string.
 *
 * @param {string} xmlStr - Raw SCXML string.
 * @returns {{cleanedXml: string, addressMap: Map<string, string[]>, addressMapJson: Array<{address: Array<[string,number]>, comments: string[]}>}}
 *     The comment-free XML serialization and the address map.
 *     ``addressMapJson`` provides a stable JSON-friendly projection for
 *     downstream callers or cross-language fixture comparison.
 *     On parse failure returns the original string and an empty map.
 */
function extractHelpTextFromXml(xmlStr) {
  if (typeof xmlStr !== 'string' || xmlStr.length === 0) {
    return { cleanedXml: xmlStr, addressMap: new Map(), addressMapJson: [] };
  }
  const parser = new XMLParser({
    ignoreAttributes: false,
    trimValues: false,
    preserveOrder: true,
    commentPropName: '#comment',
    ignoreDeclaration: false,
    ignorePiTags: false,
    parseTagValue: false,
  });
  let tree;
  try {
    tree = parser.parse(xmlStr);
  } catch (e) {
    return { cleanedXml: xmlStr, addressMap: new Map(), addressMapJson: [] };
  }
  if (!Array.isArray(tree)) {
    return { cleanedXml: xmlStr, addressMap: new Map(), addressMapJson: [] };
  }

  const root = findRootElement(tree);
  const addressMap = new Map();
  if (root === null) {
    return { cleanedXml: xmlStr, addressMap, addressMapJson: [] };
  }

  const rootLocal = localName(nodeDataKey(root));
  const rootAddr = [[rootLocal, 0]];

  // CONV-F rule 4: pre-root and post-root comments attach to root.
  if (APPLIES_TO_TAGS.has(rootLocal)) {
    const preRoot = [];
    const postRoot = [];
    let sawRoot = false;
    for (const node of tree) {
      if (node === root) {
        sawRoot = true;
        continue;
      }
      if (isCommentNode(node)) {
        const repaired = repairCommentText(commentBody(node));
        if (sawRoot) {
          postRoot.push(repaired);
        } else {
          preRoot.push(repaired);
        }
      }
    }
    if (preRoot.length || postRoot.length) {
      const key = addressKey(rootAddr);
      const existing = addressMap.get(key) || [];
      addressMap.set(key, existing.concat(preRoot).concat(postRoot));
    }
  }

  walkPromotion(root, rootAddr, addressMap, false, false);

  // Strip comments and re-serialize.
  const cleaned = buildCleanedTree(tree);
  const builder = new XMLBuilder({
    ignoreAttributes: false,
    preserveOrder: true,
    commentPropName: '#comment',
    format: false,
    suppressEmptyNode: true,
  });
  let cleanedXml;
  try {
    cleanedXml = builder.build(cleaned);
  } catch (e) {
    cleanedXml = xmlStr;
  }

  const addressMapJson = [];
  for (const [k, v] of addressMap.entries()) {
    addressMapJson.push({ address: JSON.parse(k), comments: v.slice() });
  }
  return { cleanedXml, addressMap, addressMapJson };
}

// ---------------------------------------------------------------------------
// Attach helper: walk the JS model in lockstep with the address map.
// ---------------------------------------------------------------------------

/**
 * Locate a child by ``(local_tag, index)`` segment on a JS model object.
 *
 * Handles both array-shaped collections and singleton transition fields
 * (``History.transition`` / ``Initial.transition``).
 *
 * @param {object} parent - Parent model node.
 * @param {string} parentTag - Local XML tag of the parent.
 * @param {string} tag - Child local XML tag.
 * @param {number} index - Sibling index.
 * @returns {object|null}
 */
function resolveChild(parent, parentTag, tag, index) {
  if (parent === null || typeof parent !== 'object') return null;
  const attr = modelAttrForTag(tag);
  const coll = parent[attr];
  if (coll === undefined || coll === null) return null;
  if (Array.isArray(coll)) {
    if (index >= 0 && index < coll.length) return coll[index];
    return null;
  }
  // Non-array: a singleton object. Only index 0 maps to it.
  if (typeof coll === 'object' && index === 0) return coll;
  return null;
}

/**
 * Navigate ``modelRoot`` to the element at ``address``.
 *
 * Address ``[["scxml", 0]]`` resolves to ``modelRoot`` itself.
 *
 * @param {object} modelRoot - Root SCJSON object.
 * @param {Array<[string, number]>} address - Address tuple.
 * @returns {object|null}
 */
function resolveAddress(modelRoot, address) {
  if (!Array.isArray(address) || address.length === 0) return null;
  let node = modelRoot;
  let parentTag = address[0][0];
  for (let i = 1; i < address.length; i++) {
    const [tag, idx] = address[i];
    node = resolveChild(node, parentTag, tag, idx);
    if (node === null) return null;
    parentTag = tag;
  }
  return node;
}

/**
 * Append each address's comment list to the corresponding model element's
 * ``help_text`` array.
 *
 * Comments are appended to any existing ``help_text`` entries per CONV-F
 * rule 7.
 *
 * @param {object} model - Root SCJSON object.
 * @param {Map<string, string[]>} addressMap - Map produced by
 *     ``extractHelpTextFromXml``.
 */
function attachHelpTextToModel(model, addressMap) {
  if (!model || typeof model !== 'object') return;
  if (!addressMap || addressMap.size === 0) return;
  for (const [key, comments] of addressMap.entries()) {
    if (!comments || comments.length === 0) continue;
    const address = JSON.parse(key);
    const target = resolveAddress(model, address);
    if (target === null || typeof target !== 'object') continue;
    if (Array.isArray(target.help_text)) {
      target.help_text = target.help_text.concat(comments);
    } else if (target.help_text === undefined) {
      target.help_text = comments.slice();
    } else {
      // Scalar / non-array — coerce to array preserving existing.
      target.help_text = [String(target.help_text)].concat(comments);
    }
  }
}

// ---------------------------------------------------------------------------
// Post-pass: inject comments into already-serialized SCXML.
// ---------------------------------------------------------------------------

/**
 * Walk a model and record every non-empty ``help_text`` keyed by address.
 *
 * @param {object} node - Model node.
 * @param {Array<[string, number]>} address - Address of ``node``.
 * @param {Map<string, string[]>} out - Output map.
 */
function collectHelpTextAddresses(node, address, out) {
  if (node === null || typeof node !== 'object') return;
  if (Array.isArray(node.help_text) && node.help_text.length > 0) {
    out.set(addressKey(address), node.help_text.slice());
  }
  // Recurse into typed child fields.
  // We discover children by enumerating the model's own keys and treating
  // any value that is an array of objects or a singleton object as a
  // potential XML child collection — but we map JS attr name back to XML
  // local tag name.
  const reverseTagMap = Object.create(null);
  for (const [tag, attr] of Object.entries(TAG_TO_ATTR)) {
    reverseTagMap[attr] = tag;
  }
  for (const [attr, value] of Object.entries(node)) {
    if (attr === 'help_text') continue;
    if (attr === 'other_attributes') continue;
    if (attr.startsWith('@_')) continue;
    if (attr.endsWith('_attribute')) continue;
    // Skip scalar attributes; only objects/arrays-of-objects are XML
    // children we care about for addressing.
    const tag = Object.prototype.hasOwnProperty.call(reverseTagMap, attr)
      ? reverseTagMap[attr]
      : attr;
    // Only descend into collections whose attr name is plausibly an SCXML
    // child element tag (or its renamed JS form).
    if (!APPLIES_TO_TAGS.has(tag)) continue;
    if (Array.isArray(value)) {
      for (let i = 0; i < value.length; i++) {
        const child = value[i];
        if (child && typeof child === 'object') {
          collectHelpTextAddresses(child, address.concat([[tag, i]]), out);
        }
      }
    } else if (value && typeof value === 'object') {
      collectHelpTextAddresses(value, address.concat([[tag, 0]]), out);
    }
  }
}

/**
 * Find a preserveOrder element at an address under ``rootNode``.
 *
 * @param {object} rootNode - Root preserveOrder element node.
 * @param {Array<[string, number]>} address - Address tuple.
 * @returns {{node: object, parent: Array<object>|null, indexInParent: number}|null}
 */
function navigateXml(rootNode, address) {
  if (!Array.isArray(address) || address.length === 0) return null;
  let node = rootNode;
  let parentList = null;
  let indexInParent = -1;
  for (let i = 1; i < address.length; i++) {
    const [tag, idx] = address[i];
    const dk = nodeDataKey(node);
    if (dk === null) return null;
    const children = node[dk];
    if (!Array.isArray(children)) return null;
    let count = 0;
    let found = -1;
    for (let j = 0; j < children.length; j++) {
      const child = children[j];
      if (!isElementNode(child)) continue;
      if (localName(nodeDataKey(child)) === tag) {
        if (count === idx) {
          found = j;
          break;
        }
        count++;
      }
    }
    if (found < 0) return null;
    parentList = children;
    indexInParent = found;
    node = children[found];
  }
  return { node, parent: parentList, indexInParent };
}

/**
 * Build a ``#comment`` preserveOrder node with safe body text.
 *
 * @param {string} text - Repaired help_text entry.
 * @returns {object}
 */
function makeCommentNode(text) {
  return { '#comment': [{ '#text': emitSafeCommentText(text) }] };
}

/**
 * Re-emit ``xmlStr`` with each model element's ``help_text`` entries as
 * leading XML comments.
 *
 * @param {string} xmlStr - Comment-free SCXML produced by the existing
 *     ``jsonToXml`` pipeline.
 * @param {object} model - The SCJSON model whose ``help_text`` lists drive
 *     injection.
 * @returns {string} SCXML with leading comments inserted.
 */
function injectHelpTextCommentsIntoXml(xmlStr, model) {
  if (!model || typeof model !== 'object') return xmlStr;
  const collected = new Map();
  // Determine the root local tag by parsing once. xsdata-equivalent JS
  // output always starts with ``<scxml`` (or `<?xml ... ?><scxml`); for
  // safety we read the actual root from the parsed tree.
  const parser = new XMLParser({
    ignoreAttributes: false,
    trimValues: false,
    preserveOrder: true,
    commentPropName: '#comment',
    ignoreDeclaration: false,
    ignorePiTags: false,
    parseTagValue: false,
  });
  let tree;
  try {
    tree = parser.parse(xmlStr);
  } catch (e) {
    return xmlStr;
  }
  if (!Array.isArray(tree)) return xmlStr;
  const root = findRootElement(tree);
  if (root === null) return xmlStr;
  const rootLocal = localName(nodeDataKey(root));
  const rootAddr = [[rootLocal, 0]];

  collectHelpTextAddresses(model, rootAddr, collected);
  if (collected.size === 0) return xmlStr;

  // Pop the root entries (special handling: insert as document-level
  // siblings before the root element).
  const rootKey = addressKey(rootAddr);
  const rootEntries = collected.get(rootKey);
  collected.delete(rootKey);

  // For deterministic order, sort the remaining addresses lexically so
  // re-emit order is stable regardless of Map iteration order.
  const sortedKeys = Array.from(collected.keys()).sort();

  // To preserve correct sibling indexes while inserting, process each
  // address fresh by re-navigating after each insertion at that address.
  for (const key of sortedKeys) {
    const address = JSON.parse(key);
    const found = navigateXml(root, address);
    if (found === null) continue;
    const { parent, indexInParent } = found;
    if (parent === null) continue;
    const entries = collected.get(key);
    // Determine the leading whitespace that precedes ``target`` in the
    // already-formatted XML. The XML builder is run with format:false
    // (below) so we explicitly reproduce input indentation between
    // injected comments and the target element.
    let leadingWhitespace = '';
    if (indexInParent > 0) {
      const prev = parent[indexInParent - 1];
      if (isTextNode(prev)) {
        const t = textBody(prev);
        if (/\n/.test(t)) {
          leadingWhitespace = '\n' + t.split('\n').pop();
        } else {
          leadingWhitespace = t;
        }
      }
    }
    const insertion = [];
    for (let i = 0; i < entries.length; i++) {
      insertion.push(makeCommentNode(entries[i]));
      if (leadingWhitespace) {
        insertion.push({ '#text': leadingWhitespace });
      }
    }
    // Insert all comments + spacing at the same position; the target
    // shifts right.
    parent.splice(indexInParent, 0, ...insertion);
  }

  // Insert root-level comments as document-level siblings BEFORE the root.
  if (rootEntries && rootEntries.length) {
    const rootIdx = tree.indexOf(root);
    if (rootIdx >= 0) {
      const insertion = [];
      for (let i = 0; i < rootEntries.length; i++) {
        insertion.push(makeCommentNode(rootEntries[i]));
        // Insert a newline between adjacent root-level siblings so the
        // result is human-readable.
        insertion.push({ '#text': '\n' });
      }
      tree.splice(rootIdx, 0, ...insertion);
    }
  }

  const builder = new XMLBuilder({
    ignoreAttributes: false,
    preserveOrder: true,
    commentPropName: '#comment',
    format: false,
    suppressEmptyNode: true,
  });
  let out;
  try {
    out = builder.build(tree);
  } catch (e) {
    return xmlStr;
  }
  return out;
}

module.exports = {
  APPLIES_TO_TAGS,
  SOURCE_BODY_TAGS,
  TAG_TO_ATTR,
  SINGLETON_TRANSITION_PARENTS,
  modelAttrForTag,
  addressKey,
  repairCommentText,
  emitSafeCommentText,
  extractHelpTextFromXml,
  attachHelpTextToModel,
  injectHelpTextCommentsIntoXml,
};
