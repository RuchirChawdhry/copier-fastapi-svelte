import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, relative, dirname, basename } from 'node:path';
import { parse } from 'svelte/compiler';
import ts from 'typescript';
import openapiTS, { astToString } from 'openapi-typescript';

const root = process.cwd();
const src = resolve(root, 'src');
const rel = (path) => 'frontend/' + relative(root, path).replaceAll('\\', '/');
function files(dir) {
  return existsSync(dir) ? readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const path = resolve(dir, entry.name);
    return entry.isDirectory() ? files(path) : [path];
  }) : [];
}
function script(path) {
  const source = readFileSync(path, 'utf8');
  if (!path.endsWith('.svelte')) return ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const ast = parse(source, { modern: true });
  const content = [ast.module, ast.instance].filter(Boolean).map(node => source.slice(node.content.start, node.content.end)).join('\n');
  return ts.createSourceFile(path + '.ts', content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
}
function walk(node, visit) {
  visit(node);
  ts.forEachChild(node, child => walk(child, visit));
}
function navigation() {
  const file = resolve(src, 'lib/shell/navigation.ts');
  if (!existsSync(file)) return [];
  const tree = script(file);
  const rows = [];
  walk(tree, node => {
    if (!ts.isObjectLiteralExpression(node)) return;
    const props = Object.fromEntries(node.properties.filter(ts.isPropertyAssignment).map(p => [p.name.getText(tree), p.initializer]));
    if (!props.id || !props.label || !ts.isStringLiteral(props.id) || !ts.isStringLiteral(props.label)) return;
    const value = key => props[key] && ts.isStringLiteral(props[key]) ? props[key].text : null;
    rows.push({ id: value('id'), label: value('label'), route: value('route'), source: value('component') ? rel(resolve(src, value('component'))) : null });
  });
  return rows;
}
function components(search, category, limit) {
  const all = files(src).filter(p => /\.(svelte|ts)$/.test(p) && !p.includes('/generated/') && !p.includes('\\generated\\'));
  const imports = new Map();
  const errors = [];
  const trees = new Map();
  for (const path of all) {
    try {
      const tree = script(path);
      trees.set(path, tree);
      walk(tree, node => {
        if (!ts.isImportDeclaration(node) || !ts.isStringLiteral(node.moduleSpecifier)) return;
        const spec = node.moduleSpecifier.text;
        const target = spec.startsWith('$lib/') ? resolve(src, 'lib', spec.slice(5)) : spec.startsWith('.') ? resolve(dirname(path), spec) : null;
        if (target) {
          const key = basename(target) === 'index.js' || basename(target) === 'index.ts' ? dirname(target) : target;
          const list = imports.get(key) ?? [];
          list.push(rel(path));
          imports.set(key, list);
        }
      });
    } catch (error) { errors.push({ source: rel(path), message: String(error).slice(0, 300) }); }
  }
  const rows = [];
  for (const [path, tree] of trees) {
    if (!path.endsWith('.svelte')) continue;
    const source = rel(path);
    const kind = source.includes('/components/ui/') ? 'ui' : source.includes('/pages/') ? 'page' : 'application';
    if (category !== 'all' && category !== kind || search && !source.toLowerCase().includes(search.toLowerCase())) continue;
    const props = [];
    walk(tree, node => {
      if (ts.isVariableDeclaration(node) && node.initializer && ts.isCallExpression(node.initializer) && node.initializer.expression.getText(tree) === '$props') {
        props.push({ binding: node.name.getText(tree), type: node.type?.getText(tree) ?? node.initializer.typeArguments?.[0]?.getText(tree) ?? null });
      }
      if (ts.isVariableStatement(node) && node.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword)) {
        for (const decl of node.declarationList.declarations) props.push({ binding: decl.name.getText(tree), type: decl.type?.getText(tree) ?? null });
      }
    });
    const direct = imports.get(path) ?? [];
    const group = kind === 'ui' ? imports.get(dirname(path)) ?? [] : [];
    rows.push({ name: basename(path, '.svelte'), source, category: kind, props, imported_by: [...new Set(direct)], namespace_imported_by: [...new Set(group)] });
  }
  return { total: rows.length, components: rows.slice(0, limit), parse_errors: errors.slice(0, 20) };
}
const printer = ts.createPrinter({ removeComments: true });
function members(type, tree) {
  if (!type || !ts.isTypeLiteralNode(type)) return {};
  return Object.fromEntries(type.members.filter(ts.isPropertySignature).map(member => [member.name.getText(tree).replace(/^['"]|['"]$/g, ''), member]));
}
function signatures(text) {
  const tree = ts.createSourceFile('api.d.ts', text, ts.ScriptTarget.Latest, true);
  const result = {};
  for (const node of tree.statements) {
    if (!ts.isInterfaceDeclaration(node)) continue;
    for (const field of node.members.filter(ts.isPropertySignature)) {
      const name = field.name.getText(tree).replace(/^['"]|['"]$/g, '');
      const prefix = node.name.text + '/' + name;
      if (node.name.text === 'components' || node.name.text === 'paths') {
        for (const [key, sub] of Object.entries(members(field.type, tree))) result[prefix + '/' + key] = printer.printNode(ts.EmitHint.Unspecified, sub, tree);
      } else if (node.name.text === 'operations') result[prefix] = printer.printNode(ts.EmitHint.Unspecified, field, tree);
    }
  }
  return result;
}
async function contract() {
  const schema = JSON.parse(readFileSync(0, 'utf8'));
  const path = resolve(src, 'lib/generated/api.d.ts');
  // Match the CLI export order (the backend exports sorted keys).
  const sortKeys = value => Array.isArray(value) ? value.map(sortKeys) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(key => [key, sortKeys(value[key])])) : value;
  const generated = astToString(await openapiTS(sortKeys(schema)));
  const previous = existsSync(path) ? readFileSync(path, 'utf8') : '';
  const before = signatures(previous);
  const after = signatures(generated);
  const changes = [...new Set([...Object.keys(before), ...Object.keys(after)])].filter(key => before[key] !== after[key]).map(key => ({ key, change: !(key in before) ? 'added' : !(key in after) ? 'removed' : 'modified' }));
  return { ok: existsSync(path) && changes.length === 0, generated_types_present: existsSync(path), changes, comparison: 'TypeScript paths, schema and operation member signatures' };
}
const [mode, search = '', category = 'all', limit = '100'] = process.argv.slice(2);
const result = mode === 'pages' ? navigation() : mode === 'components' ? components(search, category, Number(limit)) : mode === 'contract' ? await contract() : (() => { throw Error('Unknown inspection mode'); })();
process.stdout.write(JSON.stringify(result));
