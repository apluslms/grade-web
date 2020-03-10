#!/bin/#!/usr/bin/env python3
import html5lib
from xml.dom.minidom import (Document, Element)
from html import escape
import tinycss
import esprima

def html_parse(text, description_of_parse_location):
    parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder("dom"), strict=True)
    try:
        document = parser.parse(text)
        return (
            True, document,
            'The {} contained proper HTML5 document, '
            'e.g. all elements were recognized, correctly closed and having valid parent elements.'.format(
                description_of_parse_location
            )
        )
    except:
        return (
            False, None,
            'The {} did not contain a proper HTML5 document. '
            'The possible reasons include unrecognized elements (tags), '
            'failures to close an element with the corresponding ending &lt;/tag&gt; '
            'and elements that are located inside invalid parent element. '
            'Below the raw output from the validator program is presented:\n<ul>{}</ul>'.format(
                description_of_parse_location,
                '\n'.join(
                    '<li>Line: {:d} Character: {:d} Error: {}</li>'.format(
                        e[0][0],
                        e[0][1],
                        html5lib.constants.E[e[1]] % e[2]
                    ) for e in parser.errors
                )
            )
        )

def html_node_text(node):
    return ''.join(c.nodeValue for c in node.childNodes if c.nodeType == 3)

def html_cast_text(any):
    if type(any) == Element:
        return html_node_text(any)
    return any

def html_has_attributes(node, attrs):
    for k,v in (attrs or {}).items():
        if not node.hasAttribute(k) or node.getAttribute(k) != v:
            return False
    return True

def html_has_text(node, text):
    return ' '.join(html_node_text(node).split()) == text

def html_find_children(node, name, attrs = None):
    match = []
    for i,child in enumerate(node.childNodes):
        if child.localName == name and html_has_attributes(child, attrs):
            match.append((i, child))
    return match

def html_find_recursively(node, name, attrs = None):
    match = []
    for i,child in enumerate(node.childNodes):
        if child.localName == name and html_has_attributes(child, attrs):
            match.append((i, child))
        match.extend(html_find_recursively(child, name, attrs))
    return match

def html_print_string(node, attrs = None):
    if type(node) == Document:
        return 'document root'
    if type(node) == Element:
        return html_print_string(
            node.localName,
            { k: v.value for k,v in dict(node.attributes).items() }
        )
    parts = [node] + ['{}="{}"'.format(k, v) for k,v in (attrs or {}).items()]
    return '&lt;' + ' '.join(parts) + '&gt;'

def html_require_child(node, name, attrs = None, recursion = False):
    match = (
        html_find_recursively(node, name, attrs)
        if recursion else
        html_find_children(node, name, attrs)
    )
    tag_str = html_print_string(name, attrs)
    parent_str = html_print_string(node)
    if len(match) > 1:
        return (
            False, None,
            'More than one {} found inside {}.'.format(tag_str, parent_str)
        )
    elif len(match) == 1:
        return (
            True, match[0][1],
            'Found {} inside {}.'.format(tag_str, parent_str)
        )
    return (
        False, None,
        'No {} found inside {}.'.format(tag_str, parent_str)
    )

def html_require_path(node, path):
    result = []
    element = node
    for name,attrs in path:
        ok, element, desc = html_require_child(element, name, attrs)
        result.append((ok, element, desc))
        if not ok:
            return False, None, result
    return True, element, result

def html_require_text(node, text):
    parent_str = html_print_string(node)
    if html_has_text(node, text):
        return (
            True, node,
            'Element {} has text {}.'.format(parent_str, text)
        )
    return (
        False, None,
        'Element {} has not text {}.'.format(parent_str, text)
    )

def html_require_attributes(node, attrs, node_name=None):
    parent_str = node_name or html_print_string(node)
    result = True
    msgs = []
    for k,v in (attrs or {}).items():
        if node.hasAttribute(k):
            if v is None:
                msgs.append((True, 'Element {} has attribute {}.').format(parent_str, k))
            elif node.getAttribute(k) == v:
                msgs.append((True, 'Element {} has attribute {}="{}".'.format(parent_str, k, v)))
            else:
                msgs.append((False, 'Element {} does not have attribute {}="{}" but {}="{}" instead.'.format(parent_str, k, v, k, escape(node.getAttribute(k)))))
                result = False
        else:
            msgs.append((False, 'Element {} does not have attribute {}.'.format(parent_str, k)))
            result = False
    return result, msgs

def css_parse(text_or_node, description_of_parse_location):
    parser = tinycss.make_parser('page3')
    css = parser.parse_stylesheet(html_cast_text(text_or_node))
    if len(css.errors) == 0:
        return (
            True, css,
            'The {} contains valid CSS stylesheet syntax, '
            'e.g. all ruleset declarations are enclosed in curly brackets <code>{{}}</code>, '
            'all rules have property name and value separated by <code>:</code>-character and end with <code>;</code>-character.'.format(
                description_of_parse_location
            )
        )
    else:
        return (
            False, None,
            'The {} did not contain valid CSS stylesheet syntax. '
            'The possible reasons include failures to enclose ruleset declarions in curly brackets <code>{{}}</code>, '
            'rules that do not separate name and value by <code>:</code>-character or do not end with <code>;</code>-character. '
            'Below the raw output from the validator program is presented:\n<ul>{}</ul>'.format(
                description_of_parse_location,
                '\n'.join(
                    '<li>Line: {:d} Character: {:d} Error: {}</li>'.format(
                        e.line,
                        e.column,
                        e.reason
                    ) for e in css.errors
                )
            )
        )

def js_parse(text_or_node, description_of_parse_location, module=False):
    try:
        js = (
            esprima.parseScript(html_cast_text(text_or_node))
            if not module else
            esprima.parseModule(html_cast_text(text_or_node))
        )
        assert js.type == 'Program'
        body = [s for s in js.body if s.type != 'EmptyStatement']
        if len(body) == 0:
            return (
                False, None,
                'Empty JavaScript-code in {}.'.format(description_of_parse_location)
            )
        return (
            True, body,
            'Validated JavaScript-code in {}.'.format(description_of_parse_location)
        )
    except esprima.error_handler.Error as e:
        return (
            False, None,
            'Encountered syntax error while parsing the JavaScript-code in {}. '
            'Note, that programming languages are picky and you need to write the commands precisely. '
            'You should test your solution in browser and check that no errors appear in console panel. '
            'Below the raw output from the parser program is presented:\n<ul><li>{}</li></ul>'.format(
                description_of_parse_location,
                str(e)
            )
        )

def js_has_function(js, function_name):
    for s in js:
        if s.type == 'FunctionDeclaration' and s.id.type == 'Identifier' and s.id.name == function_name:
            return (
                True, s,
                'Found the declaration of function "{}".'.format(function_name)
            )
    return (
        False, None,
        'Could not find the declaration of function "{}".'.format(function_name)
    )

# Command line interface:

OK_LI = '<li><span class="text-success">✔</span> {}</li>'
ERROR_LI = '<li><span class="text-danger">⨯</span> {}</li>'
def li_msg(success, message):
    print((OK_LI if success else ERROR_LI).format(message))

def read_file(file_name):
    import os
    with open(os.path.join(os.getcwd(), file_name), 'r') as fp:
        return fp.read()

def main(cmd, *arg):
    ok = True
    print('<ul>')
    if cmd == 'html_parse' and len(arg) > 0:
        ok, html, msg = html_parse(read_file(arg[0]), arg[0])
        li_msg(ok, msg)
    if cmd == 'css_parse' and len(arg) > 0:
        ok, css, msg = css_parse(read_file(arg[0]), arg[0])
        li_msg(ok, msg)
    if cmd == 'js_parse' and len(arg) > 0:
        ok, js, msg = js_parse(read_file(arg[0]), arg[0])
        li_msg(ok, msg)
        if ok and len(arg) > 2:
            if arg[1] == 'function':
                ok, dec, msg = js_has_function(js, arg[2])
                li_msg(ok, msg)
    print('</ul>')
    return ok

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: cmd arguments..')
        print('  html_parse file_name')
        print('  css_parse file_name')
        print('  js_parse file_name [function function_name]')
        sys.exit(0)
    ok = main(sys.argv[1], *sys.argv[2:])
    sys.exit(0 if ok else 1)
