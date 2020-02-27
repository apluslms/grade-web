#!/bin/#!/usr/bin/env python3
import pyjsparser

def js_parse(text, description_of_parse_location):
    try:
        js = pyjsparser.parse(text)
        if js['type'] != 'Program':
            return (
                False, None,
                'Unexpectedly JavaScript in {} could not be parsed as a "Program"-entity. '
                'Report to course staff for guidance.'.format(description_of_parse_location)
            )
        body = [s for s in js['body'] if s['type'] != 'EmptyStatement']
        if len(body) == 0:
            return (
                False, None,
                'Empty JavaScript-code in {}.'.format(description_of_parse_location)
            )
        return (
            True, body,
            'Validated JavaScript-code in {}.'.format(description_of_parse_location)
        )
    except pyjsparser.pyjsparserdata.JsSyntaxError as e:
        return (
            False, None,
            'Encountered syntax error while parsing the JavaScript-code in {}. '
            'Note, that programming languages are picky and you need to write the commands precisely. '
            'You should test your solution in browser and check that no errors appear in console panel. '
            'Below the raw output from the parser program is presented:<ul><li>{}</li></ul>'.format(
                description_of_parse_location,
                str(e)
            )
        )

def js_has_function(js, function_name):
    for s in js:
        if s['type'] == 'FunctionDeclaration' and s['id']['type'] == 'Identifier' and s['id']['name'] == function_name:
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
    with open(file_name, 'r') as fp:
        return fp.read()

def main(cmd, *arg):
    ok = True
    print('<ul>')
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
    if len(sys.argv) < 1:
        print('Usage: cmd arguments..')
        print('  js_parse file_name [function function_name]')
        sys.exit(0)
    ok = main(sys.argv[0], *sys.argv[1:])
    sys.exit(0 if ok else 1)
