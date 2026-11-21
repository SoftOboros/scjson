/**
 * Preserve the direct executable child order of SCXML action containers.
 * Part of the scjson project. Developed by Softoboros Technology Inc.
 * Licensed under the BSD 1-Clause License.
 */
const { XMLParser, XMLBuilder } = require('fast-xml-parser');
const { nodeDataKey, isElementNode, modelAttrForTag } = require('./comment_promotion.js');

const SCXML = 'http://www.w3.org/2005/07/scxml';
const XI = 'http://www.w3.org/2001/XInclude';
const containers = new Set(['transition', 'onentry', 'onexit', 'finalize', 'foreach', 'if']);
const actions = ['assign', 'log', 'raise', 'if', 'foreach', 'send', 'cancel', 'script'];
const payloadParents = new Set(['send', 'donedata', 'invoke']);
const field = modelAttrForTag;
const emptyActions = new Set([...actions, 'elseif', 'else'].flatMap(tag => [tag, field(tag)]));
const list = value => value == null ? [] : Array.isArray(value) ? value : [value];
const options = { preserveOrder: true, ignoreAttributes: false, parseTagValue: false,
  trimValues: false, commentPropName: '#comment', suppressEmptyNode: true,
  suppressBooleanAttributes: false };
const parse = xml => new XMLParser(options).parse(xml);
const serialize = tree => new XMLBuilder(options).build(tree);

function element(node, parentNamespaces) {
  const name = nodeDataKey(node);
  const ns = new Map(parentNamespaces);
  ns.set('xml', 'http://www.w3.org/XML/1998/namespace');
  const attributes = node[':@'] || {};
  for (const [key, uri] of Object.entries(attributes)) {
    if (key === '@_xmlns') ns.set('', uri);
    if (key.startsWith('@_xmlns:')) ns.set(key.slice(8), uri);
  }
  const colon = name.indexOf(':');
  const local = name.slice(colon + 1);
  const uri = ns.get(colon < 0 ? '' : name.slice(0, colon)) || '';
  return { name, local, uri, ns, kind: uri === SCXML ? local : '{' + uri + '}' + local };
}

function wildcard(node, tag) {
  const result = { qname: tag.uri ? '{' + tag.uri + '}' + tag.local : tag.local, text: '' };
  for (const [name, value] of Object.entries(node[':@'] || {})) {
    if (name === '@_xmlns' || name.startsWith('@_xmlns:')) continue;
    const key = name.slice(2);
    const index = key.indexOf(':');
    const expanded = index < 0 ? key : '{' + tag.ns.get(key.slice(0, index)) + '}' + key.slice(index + 1);
    (result.attributes ||= {})[expanded] = value;
  }
  let previous;
  for (const child of node[tag.name]) {
    if (isElementNode(child)) {
      previous = wildcard(child, element(child, tag.ns));
      (result.children ||= []).push(previous);
    } else if ('#text' in child) {
      if (previous) previous.tail = (previous.tail || '') + child['#text'];
      else result.text += child['#text'];
    }
  }
  return result;
}

// Namespace declarations are local to each emitted element. Attribute names
// stay qualified even when their namespace differs from the element's.
function wildcardNode(value) {
  const attrs = {};
  const prefixes = new Map([['http://www.w3.org/XML/1998/namespace', 'xml']]);
  function qualify(qname) {
    if (!qname.startsWith('{')) return qname;
    const end = qname.indexOf('}');
    const uri = qname.slice(1, end);
    const local = qname.slice(end + 1);
    if (!uri) return local;
    if (!prefixes.has(uri)) {
      const prefix = 'ns' + prefixes.size;
      attrs['@_xmlns:' + prefix] = uri;
      prefixes.set(uri, prefix);
    }
    return prefixes.get(uri) + ':' + local;
  }
  const name = qualify(value.qname);
  if (!name.includes(':')) attrs['@_xmlns'] = '';
  for (const [key, content] of Object.entries(value.attributes || {})) {
    attrs['@_' + qualify(key)] = content;
  }
  const children = value.text ? [{ '#text': value.text }] : [];
  for (const child of value.children || []) {
    children.push(wildcardNode(child));
    if (child.tail) children.push({ '#text': child.tail });
  }
  return { [name]: children, ':@': attrs };
}

function orderedChildren(model, tag) {
  const order = model.execution_order;
  if (!Array.isArray(order)) throw new Error('execution_order must be an array');
  const available = new Map();
  for (const action of [...actions, 'elseif', 'else']) {
    const count = list(model[field(action)]).length;
    if (count) available.set(action, count);
  }
  for (const child of list(model.other_element)) {
    if (!child || !child.qname || typeof child.qname !== 'string' || child.qname.startsWith('{' + SCXML + '}')) {
      throw new Error('An ordered extension needs a foreign qname');
    }
    const kind = child.qname.startsWith('{') ? child.qname : '{}' + child.qname;
    available.set(kind, (available.get(kind) || 0) + 1);
  }
  let sawElse = false;
  for (const kind of order) {
    if (!available.get(kind)) throw new Error('execution_order references an absent child: ' + kind);
    if (kind === 'else' || kind === 'elseif') {
      if (tag !== 'if' || sawElse) throw new Error('Invalid conditional marker in execution_order');
      if (kind === 'else') sawElse = true;
    }
    available.set(kind, available.get(kind) - 1);
  }
  if ([...available.values()].some(count => count)) throw new Error('execution_order omits a child');
}

/** Validate the metadata before pruning empty fields or applying schema defaults. */
function validateModel(model, tag = 'scxml') {
  if (!model || typeof model !== 'object') return false;
  let needsProjection = false;
  if (Object.hasOwn(model, 'execution_order')) {
    if (!containers.has(tag)) throw new Error('execution_order is invalid on ' + tag);
    orderedChildren(model, tag);
    needsProjection = true;
  }
  // other_attributes and foreign content can carry arbitrary user data.
  for (const kind of [...actions, 'transition', 'state', 'parallel', 'final', 'initial', 'history',
    'onentry', 'onexit', 'invoke', 'finalize', 'elseif', 'else', 'donedata', 'datamodel', 'data', 'param']) {
    for (const child of list(model[field(kind)])) {
      if (validateModel(child, kind)) needsProjection = true;
    }
  }
  for (const content of list(model.content)) {
    if (content && typeof content === 'object' && !content.qname && validateModel(content, 'content')) {
      needsProjection = true;
    }
  }
  return needsProjection || (containers.has(tag) && list(model.other_element).length > 0)
    || (payloadParents.has(tag) && list(model.content).length > 0);
}

// Payload text and XML wildcards live outside the SCXML action grammar. Read
// them from the ordered nodes so embedded markup and whitespace stay intact.
function capturePayloads(tree, model, readChart) {
  function contentBlock(node, tag) {
    const xml = wildcard(node, tag);
    const block = {};
    if (xml.attributes) {
      const { expr, ...other } = xml.attributes;
      if (expr !== undefined) block.expr = expr;
      if (Object.keys(other).length) block.other_attributes = other;
    }
    const parts = [];
    const nodes = node[tag.name];
    const hasElements = nodes.some(isElementNode);
    for (const child of nodes) {
      if ('#text' in child) {
        const text = child['#text'];
        const previous = parts[parts.length - 1];
        if (previous?.qname) previous.tail = (previous.tail || '') + text;
        else if (!hasElements || text.trim()) parts.push(text);
      } else if (isElementNode(child)) {
        const inner = element(child, tag.ns);
        if (inner.kind === 'scxml') {
          const attrs = { ...child[':@'] };
          for (const [prefix, uri] of inner.ns) {
            if (prefix !== 'xml') attrs[prefix ? '@_xmlns:' + prefix : '@_xmlns'] = uri;
          }
          parts.push(readChart(serialize([{ ...child, ':@': attrs }])));
        } else parts.push(wildcard(child, inner));
      }
    }
    if (parts.length) block.content = parts;
    return block;
  }
  function walk(node, current, tag) {
    if (!current || tag.uri !== SCXML) return;
    const counts = new Map();
    const blocks = [];
    for (const child of node[tag.name].filter(isElementNode)) {
      const inner = element(child, tag.ns);
      if (inner.uri !== SCXML) continue;
      if (payloadParents.has(tag.local) && inner.local === 'content') {
        blocks.push(contentBlock(child, inner));
        continue;
      }
      const key = field(inner.local);
      const index = counts.get(key) || 0;
      counts.set(key, index + 1);
      if (payloadParents.has(inner.local) && list(current[key]).length <= index) {
        (current[key] ||= []).push({});
      }
      walk(child, list(current[key])[index], inner);
    }
    if (blocks.length) current.content = tag.local === 'donedata' ? blocks[0] : blocks;
  }
  const root = tree.find(isElementNode);
  if (root) walk(root, model, element(root, new Map([['', SCXML]])));
}

// The grouped parser supplies values and attributes. Use the ordered parser's
// direct children to associate each value with its original expanded XML name.
function captureOrder(tree, grouped) {
  function walk(node, raw, tag) {
    if (!raw || typeof raw !== 'object' || tag.uri !== SCXML) return;
    const executable = containers.has(tag.local);
    const original = new Map();
    const structural = new Map();
    const order = [];
    for (const child of node[tag.name].filter(isElementNode)) {
      const name = nodeDataKey(child);
      if (!original.has(name)) original.set(name, { values: list(raw[name]), used: 0 });
      const group = original.get(name);
      const childTag = element(child, tag.ns);
      let value = group.values[group.used++];
      if (executable) order.push(childTag.kind);
      if (executable && childTag.uri !== SCXML) {
        (raw.other_element ||= []).push(wildcard(child, childTag));
        continue;
      }
      const key = childTag.uri === SCXML ? childTag.local : name;
      if (executable && value === '') value = {};
      walk(child, value, childTag);
      if (!structural.has(key)) structural.set(key, []);
      structural.get(key).push(value);
    }
    for (const key of original.keys()) {
      if (!structural.has(key)) delete raw[key];
    }
    for (const [key, values] of structural) raw[key] = values.length === 1 ? values[0] : values;
    if (order.includes('else') || order.includes('elseif')) {
      const firstElse = order.indexOf('else');
      if (tag.local !== 'if' || (firstElse >= 0 && order.slice(firstElse + 1).some(k => k === 'else' || k === 'elseif'))) {
        throw new Error('Invalid conditional marker sequence');
      }
    }
    if (new Set(order).size > 1) raw.execution_order = order;
  }
  const root = tree.find(isElementNode);
  if (root) {
    const tag = element(root, new Map([['', SCXML]]));
    walk(root, grouped[tag.name], tag);
    if (tag.uri === SCXML && tag.local === 'scxml' && tag.local !== tag.name) {
      grouped.scxml = grouped[tag.name];
      delete grouped[tag.name];
    }
  }
}

function restoreOrder(tree, model, writeChart) {
  function walk(node, current, tag) {
    if (!current || typeof current !== 'object' || tag.uri !== SCXML) return;
    if (payloadParents.has(tag.local) && list(current.content).length) {
      let index = 0;
      const original = list(current.content);
      const blocks = original.map(block => {
        const parts = [];
        for (const item of list(block.content)) {
          if (typeof item === 'string') parts.push({ '#text': item });
          else if (item.qname) {
            parts.push(wildcardNode(item));
            if (item.tail) parts.push({ '#text': item.tail });
          } else parts.push(parse(writeChart(item)).find(isElementNode));
        }
        const payload = wildcardNode({ qname: 'content', attributes: block.other_attributes });
        // 'content' is a structural SCXML element in the parent's namespace.
        delete payload[':@']['@_xmlns'];
        if (block.expr !== undefined && block.expr !== null) payload[':@']['@_expr'] = block.expr;
        payload.content = parts;
        return payload;
      });
      node[tag.name] = node[tag.name].flatMap(child => {
        if (!isElementNode(child) || element(child, tag.ns).kind !== 'content') return [child];
        return index < blocks.length ? [blocks[index++]] : [];
      });
      node[tag.name].push(...blocks.slice(index));
    }
    const children = node[tag.name];
    const entries = children.filter(isElementNode).map(child => ({ child, tag: element(child, tag.ns) }));
    const executable = containers.has(tag.local);
    const counts = new Map();
    for (const entry of entries) {
      const key = field(entry.tag.local);
      if (entry.tag.uri !== SCXML) continue;
      let value = current[key];
      if (key === 'scxml' && current.content) value = current.content;
      const index = counts.get(key) || 0;
      counts.set(key, index + 1);
      walk(entry.child, list(value)[index], entry.tag);
    }
    if (!executable) return;
    const extensions = new Map();
    for (const value of list(current.other_element)) {
      const kind = value.qname.startsWith('{') ? value.qname : '{}' + value.qname;
      if (!extensions.has(kind)) extensions.set(kind, []);
      extensions.get(kind).push(value);
    }
    const queues = new Map();
    for (const entry of entries) {
      if (!queues.has(entry.tag.kind)) queues.set(entry.tag.kind, []);
      const queue = queues.get(entry.tag.kind);
      const foreign = extensions.get(entry.tag.kind)?.[queue.length];
      queue.push(foreign ? wildcardNode(foreign) : entry.child);
    }
    const used = new Map();
    const order = current.execution_order || entries.map(entry => entry.tag.kind);
    const ordered = order.map(kind => {
      const index = used.get(kind) || 0;
      used.set(kind, index + 1);
      const child = queues.get(kind)?.[index];
      if (!child) throw new Error('Missing serialized child in execution_order: ' + kind);
      return child;
    });
    let index = 0;
    node[tag.name] = children.map(child => isElementNode(child) ? ordered[index++] : child);
  }
  const root = tree.find(isElementNode);
  if (root) walk(root, model, element(root, new Map([['', SCXML]])));
}

// Expand includes in the ordered tree before grouping siblings of the same kind.
function expandIncludes(tree, load, namespaces = new Map([['', SCXML]])) {
  return tree.flatMap(node => {
    if (!isElementNode(node)) return [node];
    const tag = element(node, namespaces);
    if (tag.uri === XI && tag.local === 'include') {
      const href = node[':@']?.['@_href'];
      if (!href) throw new Error('XInclude element is missing href');
      return expandIncludes(parse(load(href)).filter(isElementNode), load, tag.ns);
    }
    node[tag.name] = expandIncludes(node[tag.name], load, tag.ns);
    return [node];
  });
}

module.exports = { captureOrder, capturePayloads, restoreOrder, expandIncludes, parse, serialize, validateModel, emptyActions };
