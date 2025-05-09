"""
DFA Simulator for the lexical analyzer of the RPN language.
States: START, NUMBER, DECIMAL, IDENT, OPERATOR, PAREN, ERROR
Transitions:
    START: [digit] -> NUMBER, [.] -> DECIMAL, [letter] -> IDENT, [()+-*/%|^] -> OPERATOR/PAREN
    NUMBER: [digit] -> NUMBER, [.] -> DECIMAL, other -> emit NUMBER, go to START
    DECIMAL: [digit] -> DECIMAL, other -> emit NUMBER, go to START
    IDENT: [letter] -> IDENT, other -> emit IDENT, go to START

Usage: python dfa_simulator.py <string>
"""
import sys

def dfa_lex(input_str):
    tokens = []
    state = 'START'
    i = 0
    n = len(input_str)
    buf = ''
    pos = 0
    while i < n:
        c = input_str[i]
        if state == 'START':
            pos = i
            if c.isspace():
                i += 1
                continue
            elif c.isdigit():
                buf = c
                state = 'NUMBER'
            elif c == '.':
                buf = c
                state = 'DECIMAL'
            elif c.isalpha():
                buf = c
                state = 'IDENT'
            elif c in '()+-*/%|^':
                typ = 'PAREN' if c in '()' else 'OPERATOR'
                tokens.append({'value': c, 'type': typ, 'position': i})
                i += 1
                continue
            else:
                tokens.append({'value': c, 'type': 'ERROR', 'position': i})
                i += 1
                continue
            i += 1
        elif state == 'NUMBER':
            if i < n and input_str[i].isdigit():
                buf += input_str[i]
                i += 1
            elif i < n and input_str[i] == '.':
                buf += input_str[i]
                state = 'DECIMAL'
                i += 1
            else:
                tokens.append({'value': buf, 'type': 'NUMBER', 'position': pos})
                buf = ''
                state = 'START'
        elif state == 'DECIMAL':
            if i < n and input_str[i].isdigit():
                buf += input_str[i]
                i += 1
            else:
                tokens.append({'value': buf, 'type': 'NUMBER', 'position': pos})
                buf = ''
                state = 'START'
        elif state == 'IDENT':
            if i < n and input_str[i].isalpha():
                buf += input_str[i]
                i += 1
            else:
                tokens.append({'value': buf, 'type': 'IDENT', 'position': pos})
                buf = ''
                state = 'START'
    # Flush buffer
    if state == 'NUMBER' or state == 'DECIMAL':
        tokens.append({'value': buf, 'type': 'NUMBER', 'position': pos})
    elif state == 'IDENT':
        tokens.append({'value': buf, 'type': 'IDENT', 'position': pos})
    return tokens

from main import RPNCalculator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dfa_simulator.py '<string>'")
        sys.exit(1)
    input_str = sys.argv[1]
    tokens = dfa_lex(input_str)
    # Print as table
    print(f"{'Value':<10} | {'Type':<10} | {'Position':<8}")
    print('-'*34)
    for t in tokens:
        print(f"{t['value']:<10} | {t['type']:<10} | {t['position']:<8}")
    # Evaluate using main RPNCalculator
    calc = RPNCalculator()
    try:
        result = calc.evaluate_expression(input_str)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nError evaluating expression: {e}")
