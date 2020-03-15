#!/bin/#!/usr/bin/env python3
import html5lib
from xml.dom.minidom import (Document, Element)
from html import escape
import tinycss
import esprima


class Logger:

    def __init__(self, reporter, level=0, points=0):
        self.reporter = reporter
        self.level = level
        self.level_max = points > 0
        self.level_ok = True
        self.rows = []
        self.points = 0
        self.max_points = points

    def add_level(self, msg, points=0):
        sublog = Logger(self.reporter, self.level + 1, points)
        self.rows.append(('level', msg, points, sublog))
        return sublog

    def message(self, msg):
        self.rows.append(('message', msg, 0))

    def success(self, msg, points=0):
        self.rows.append(('success', msg, points))
        self.add_points(points, True)

    def fail(self, msg, points=0):
        self.rows.append(('fail', msg, points))
        self.add_points(points, False)
        self.level_ok = False

    def __str__(self):
        return self.reporter.format(self)

    def add_points(self, points, earned):
        self.points += points if earned else 0
        self.max_points += 0 if self.level_max else points

    def points_total(self):
        points = min(self.points, self.max_points)
        if self.level_max and self.level_ok and self.points == 0:
            points = self.max_points
        max_points = self.max_points
        for row in self.rows:
            if row[0] == 'level':
                p, m = row[3].points_total()
                points += p
                max_points += m
        return (points, max_points)


class Reporter:

    FORMAT = {
        'level': '{index:d}. {message}{points}:\n{body}',
        'success': '* Success! {message}{points}',
        'fail': '* Fail! {message}{points}',
        'row': '* {message}{points}',
        'points_wrap': ' ({:d}p)',
        'separator': '\n',
    }

    def __init__(self):
        pass

    def format(self, logger):
        res = []
        for index, row in enumerate(logger.rows):
            res.append(self.format_row(
                logger.level, index + 1, row[0], row[1], row[2],
                None if len(row) < 4 else str(row[3])
            ))
        return (
            self.wrap_level(logger.level, self.FORMAT['separator'].join(res))
            + '\n' + self.points_lines(logger)
        )

    def format_row(self, level, index, type, message, points, body):
        key = type if type in self.FORMAT else 'row'
        return self.wrap_row(level, index, self.FORMAT[key].format(
            level=level, index=index, type=type,
            message=message, points=self.wrap_points(points), body=body
        ))

    def wrap_points(self, points):
        return self.FORMAT['points_wrap'].format(points) if points > 0 else ''

    def wrap_row(self, level, index, row):
        return row

    def wrap_level(self, level, body):
        return body

    def points_lines(self, logger):
        return (
            'TotalPoints: {:d}\nMaxPoints: {:d}\n'.format(*logger.points_total())
            if logger.level == 0 else
            ''
        )


class HtmlListReporter(Reporter):

    FORMAT = {
        'level': '<li class="check-level"><strong>{message}</strong>{points}\n{body}</li>',
        'success': '<li class="check-success"><span class="text-success">✔</span> {message}{points}</li>',
        'fail': '<li class="check-fail"><span class="text-danger">⨯</span> {message}{points}</li>',
        'row': '<li class="check-message">{message}{points}</li>',
        'level_wrap_numbered': '<ol>\n{}\n</ol>',
        'level_wrap': '<ul>\n{}\n</ul>',
        'points_wrap': ' ({:d}p)',
        'separator': '\n',
    }

    def wrap_level(self, level, body):
        return self.FORMAT['level_wrap_numbered' if level == 0 else 'level_wrap'].format(body)


def read_file(file_name):
    import os
    with open(os.path.join(os.getcwd(), file_name), 'r') as fp:
        return fp.read()

def html_parse(text):
    parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder("dom"), strict=True)
    try:
        return (parser.parse(text), tuple())
    except:
        return (
            None,
            ('Line: {:d} Character: {:d} Error: {}'.format(
                e[0][0], e[0][1], html5lib.constants.E[e[1]] % e[2]
            ) for e in parser.errors)
        )

def html_node_text(node):
    return ''.join(c.nodeValue for c in node.childNodes if c.nodeType == 3)

def html_cast_text(any):
    if type(any) == Element:
        return html_node_text(any)
    return any

def html_has_text(node, text):
    return ' '.join(html_node_text(node).split()) == text

def html_has_attributes(node, attrs):
    for k,v in (attrs or {}).items():
        if not node.hasAttribute(k) or node.getAttribute(k) != v:
            return False
    return True

def html_find_children(node, name, attrs=None, recursion=False):
    match = []
    for i,child in enumerate(node.childNodes):
        if child.localName == name and html_has_attributes(child, attrs):
            match.append((i, child))
        if recursion:
            match.extend(html_find_children(child, name, attrs, recursion))
    return match

def html_print_string(node, attrs=None):
    if type(node) == Document:
        return 'document root'
    if type(node) == Element:
        return html_print_string(
            node.localName,
            { k: v.value for k,v in dict(node.attributes).items() }
        )
    parts = [node]
    parts += ['{}="{}"'.format(k, v) for k,v in (attrs or {}).items() if not v is False and not v is True]
    parts += ['{}'.format(k) for k,v in (attrs or {}).items() if v is True]
    return '&lt;' + ' '.join(parts) + '&gt;'

def html_validate(logger, points, description_of_parse_location, text):
    html, errors = html_parse(text)
    if html:
        logger.success(
            'The {} contained proper HTML5 document, '
            'e.g. all elements were recognized, '
            'correctly closed '
            'and having valid parent elements.'.format(
                description_of_parse_location
            ),
            points
        )
        return html
    logger.fail(
        'The {} did not contain a proper HTML5 document. '
        'The possible reasons include unrecognized elements (tags), '
        'failures to close an element with the corresponding ending &lt;/tag&gt; '
        'and elements that are located inside invalid parent element. '
        'Below the raw output from the validator program is presented:\n'
        '<ul>{}</ul>'.format(
            description_of_parse_location,
            '\n'.join('<li>{}</li>'.format(e) for e in errors)
        ),
        points
    )
    return None

def html_require_child(logger, points, node, name, attrs=None, recursion=False, parent_name=None):
    match = html_find_children(node, name, attrs, recursion)
    tag_str = html_print_string(name, attrs)
    parent_str = parent_name or html_print_string(node)
    if len(match) > 1:
        logger.fail('More than one {} found inside {}.'.format(tag_str, parent_str), points)
        return None
    elif len(match) == 1:
        logger.success('Found {} inside {}.'.format(tag_str, parent_str), points)
        return match[0][1]
    logger.fail('No {} found inside {}.'.format(tag_str, parent_str), points)
    return None

def html_require_path(logger, points, node, path):
    element = node
    for name, attrs in path:
        element = html_require_child(logger, 0, element, name, attrs)
        if not element:
            logger.add_points(points, False)
            return None
    logger.add_points(points, True)
    return element

def html_require_text(logger, points, node, text, parent_name=None):
    parent_str = parent_name or html_print_string(node)
    if html_has_text(node, text):
        logger.success('Element {} has text "{}".'.format(parent_str, text), points)
        return node
    wrong = ' '.join(html_node_text(node).split())
    logger.fail('Element {} has not text "{}" but "{}".'.format(parent_str, text, wrong), points)
    return None

def html_require_attributes(logger, points, node, attrs, parent_name=None):
    parent_str = parent_name or html_print_string(node)
    result = True
    for k,v in (attrs or {}).items():
        if node.hasAttribute(k):
            if v is True:
                logger.success('Element {} has attribute {}.'.format(parent_str, k))
            elif v is False:
                logger.fail('Element {} has forbidden attribute {}.'.format(parent_str, k))
                result = False
            elif node.getAttribute(k) == v:
                logger.success('Element {} has expected attribute {}="{}".'.format(parent_str, k, v))
            else:
                logger.fail(
                    'Element {} has attribute {}="{}" '
                    'but value "{}" was expected.'.format(
                        parent_str, k, escape(node.getAttribute(k)), v)
                    )
                result = False
        elif v is False:
            logger.success('Element {} does not have forbidden attribute {}.'.format(parent_str, k))
        else:
            logger.fail('Element {} does not have expected attribute {}.'.format(parent_str, k))
            result = False
    logger.add_points(points, result)
    return node if result else None

def css_parse(text_or_node):
    parser = tinycss.make_parser('page3')
    css = parser.parse_stylesheet(html_cast_text(text_or_node))
    if len(css.errors) == 0:
        return (css, tuple())
    return (
        None,
        ('Line: {:d} Character: {:d} Error: {}'.format(
            e.line, e.column, e.reason
        ) for e in css.errors)
    )

def css_find_rules(css, selectors):
    return [rule for rule in css.rules if rule.selector.as_css() in selectors]

def css_find_declarations(rules, properties):
    return [dec for rule in rules for dec in rule.declarations if dec.name in properties]

def css_validate(logger, points, description_of_parse_location, text_or_node):
    css, errors = css_parse(text_or_node)
    if css:
        logger.success(
            'The {} contains valid CSS stylesheet syntax, '
            'e.g. all ruleset declarations are enclosed in curly brackets <code>{{}}</code>, '
            'all rules have property name and value separated by <code>:</code>-character '
            'and end with <code>;</code>-character.'.format(
                description_of_parse_location
            ),
            points
        )
        return css
    logger.fail(
        'The {} did not contain valid CSS stylesheet syntax. The possible reasons include '
        'failures to enclose ruleset declarions in curly brackets <code>{{}}</code>, '
        'rules that do not separate name and value by <code>:</code>-character '
        'or do not end with <code>;</code>-character. '
        'Below the raw output from the validator program is presented:\n'
        '<ul>{}</ul>'.format(
            description_of_parse_location,
            '\n'.join('<li>{}</li>'.format(e) for e in errors)
        ),
        points
    )
    return None

def css_require_rule(logger, points, css, selectors):
    rules = css_find_rules(css, selectors)
    select_str = ', '.join(selectors)
    if len(rules) == 0:
        logger.fail(
            'No rules found for selectors "{}".'.format(select_str),
            points
        )
    elif len(rules) == 1:
        logger.success(
            'A rule for selectors "{}" found.'.format(select_str),
            points
        )
    else:
        logger.success(
            'Multiple rules for selectors "{}" found. '
            'Last one is predominant.'.format(select_str),
            points
        )
    return rules

def css_require_declarations(logger, points, rules, properties):
    decs = css_find_declarations(rules, properties)
    property_str = ', '.join(properties)
    if len(decs) == 0:
        logger.fail(
            'No declarations found for properties "{}".'.format(property_str),
            points
        )
    elif len(decs) == 1:
        logger.success(
            'A declaration for properties "{}" found.'.format(property_str),
            points
        )
    else:
        logger.success(
            'Multiple declarations for properties "{}" found. '
            'Last one is predominant.'.format(property_str),
            points
        )
    return decs

def js_parse(text_or_node, module=False):
    try:
        js = (
            esprima.parseScript(html_cast_text(text_or_node))
            if not module else
            esprima.parseModule(html_cast_text(text_or_node))
        )
        assert js.type == 'Program'
        return (js, tuple())
    except esprima.error_handler.Error as e:
        return (None, [str(e)])

def js_validate(logger, points, description_of_parse_location, text_or_node, module=False):
    js, errors = js_parse(text_or_node, module)
    if js:
        body = [s for s in js.body if s.type != 'EmptyStatement']
        if len(body) == 0:
            logger.fail(
                'Empty JavaScript-code in {}.'.format(description_of_parse_location),
                points
            )
            return None
        logger.success(
            'Validated JavaScript-code in {}.'.format(description_of_parse_location),
            points
        )
        return body
    logger.fail(
        'Encountered syntax error while parsing the JavaScript-code in {}. '
        'Note, that programming languages are picky and you need to write the commands precisely. '
        'You should test your solution in browser and check that no errors appear in console panel. '
        'Below the raw output from the parser program is presented:\n'
        '<ul>{}</ul>'.format(
            description_of_parse_location,
            '\n'.join('<li>{}</li>'.format(e) for e in errors)
        ),
        points
    )
    return None

def js_find_variables(js, name, recursion=False):
    vars = []
    for s in js:
        if s.type == 'VariableDeclaration':
            vars.extend(js_find_variables(s.declarations, name, recursion))
        if s.type == 'VariableDeclarator' and s.id.type == 'Identifier' and s.id.name == name:
            vars.append(s.init)
        if recursion and hasattr(s, 'body'):
            bs = s.body if type(s.body) == list else [s.body]
            vars.extend(js_find_variables(bs, name, recursion))
    return vars

def js_find_functions(js, name, recursion=False):
    funcs = []
    for s in js:
        if s.type == 'FunctionDeclaration' and s.id.type == 'Identifier' and s.id.name == name:
            funcs.append(s)
        if recursion and hasattr(s, 'body'):
            bs = s.body if type(s.body) == list else [s.body]
            funcs.extend(js_find_functions(bs, name, recursion))
    funcs.extend(s for s in js_find_variables(js, name, recursion) if s.type == 'FunctionExpression')
    return funcs

def js_require_variable(logger, points, js, name, recursion=False):
    vars = js_find_variables(js, name, recursion)
    if len(vars) == 0:
        logger.fail('No variables found for name "{}".'.format(name), points)
    elif len(vars) == 1:
        logger.success('A variable of name "{}" found.'.format(name), points)
    else:
        logger.success(
            'Multiple variables for name "{}" found. '
            'Last one is predominant.'.format(name),
            points
        )
    return vars

def js_require_function(logger, points, js, name, recursion=False):
    funcs = js_find_functions(js, name, recursion)
    if len(funcs) == 0:
        logger.fail('No functions found for name "{}".'.format(name), points)
    elif len(funcs) == 1:
        logger.success('A function of name "{}" found.'.format(name), points)
    else:
        logger.success(
            'Multiple functions for name "{}" found. '
            'Last one is predominant.'.format(name),
            points
        )
    return funcs

# Command line interface:

def main(cmd, *arg):
    logger = Logger(HtmlListReporter(), 1)
    item = None
    if cmd == 'html_parse' and len(arg) > 0:
        item = html_validate(logger, 0, arg[0], read_file(arg[0]))
    elif cmd == 'css_parse' and len(arg) > 0:
        item = css_validate(logger, 0, arg[0], read_file(arg[0]))
    elif cmd == 'js_parse' and len(arg) > 0:
        item = js_validate(logger, 0, arg[0], read_file(arg[0]))
        if item and len(arg) > 2:
            if arg[1] == 'function':
                if len(js_require_function(logger, 0, item, arg[2])) == 0:
                    item = None
            elif arg[1] == 'variable':
                if len(js_require_variable(logger, 0, item, arg[2])) == 0:
                    item = None
    else:
        logger.fail('Unknown command: {}'.format(cmd))
    print(logger)
    return not item is None

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: cmd arguments..')
        print('  html_parse file_name')
        print('  css_parse file_name')
        print('  js_parse file_name [function|variable name]')
        sys.exit(0)
    ok = main(sys.argv[1], *sys.argv[2:])
    sys.exit(0 if ok else 1)
