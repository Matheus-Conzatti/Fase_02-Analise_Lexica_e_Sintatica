import sys
import re
import struct
import math
import os

class RPNCalculator:
    """
    Implements a calculator for evaluating expressions in Reverse Polish Notation (RPN).
    Supports basic arithmetic operations, special memory commands, and nested expressions.
    """
    
    def __init__(self):
        """
        Initializes the RPN calculator with default values.
        Sets up the list of previous results and memory.
        """
        # Stores previous results of expressions
        self.results = []
        # Memory for (V MEM) command
        self.memory = 0.0
    
    def convertFloatToHalf(self, f):
        """
        Converts a number to half-precision (16 bits) according to IEEE754 standard.
        
        Parameters:
            value: Float value to be converted
        Returns:
            Value converted to half-precision (16 bits) representation
        """
        # Converts float to bits (uint32)
        bin_f = struct.unpack('>I', struct.pack('>f', f))[0]

        sinal = (bin_f >> 16) & 0x8000
        exp = ((bin_f >> 23) & 0xFF) - 127 + 15
        mantissa = (bin_f >> 13) & 0x03FF

        if exp <= 0:
            return sinal # Subnormal or zero
        elif exp >= 31:
            return sinal | 0x7C00 # Infinity or NaN
        return sinal | (exp << 10) | mantissa
    
    def convertHalfToFloat(self, f16):
        """
        Converts a half-precision (16 bits) number to float according to IEEE754 standard.
        
        Parameters:
            f16: Value in half-precision (16 bits) to be converted
        Returns:
            Value converted to float
        """
        sinal = (f16 >> 15) & 0x1
        exp = (f16 >> 10) & 0x1F
        frac = f16 & 0x03FF
        f32Sinal = sinal << 31
        f32Exp = 0
        f32Frac = 0

        if exp == 0:
            if frac == 0:
                f32Sinal = 0
                f32Frac = 0
            else:
                exp = 1
                while (frac & 0x0400) == 0:
                    frac <<= 1
                    exp -= 1
                frac &= 0x03FF
                f32Exp = (127 - 15 + exp) << 23
                f32Frac = frac << 13
        elif exp == 0x1F:
            f32Exp = 0xFF << 23
            f32Frac = frac << 13
        else:
            f32Exp = (exp + (127 - 15)) << 23
            f32Frac = frac << 13
        
        f32Bits = f32Sinal | f32Exp | f32Frac
        return struct.unpack('>f', struct.pack('>I', f32Bits))[0]

    def evaluate_expression(self, expression):
        """
        Avalia uma expressão RPN e retorna o resultado final.
        Suporta comandos especiais como (N RES), (V MEM) e (MEM).
        
        - Se você escrever (2 RES), ele vai buscar o resultado que calculou 2 linhas atrás
        - Se você escrever (5 MEM), ele vai guardar o número 5 na memória da calculadora
        - Se você escrever (MEM), ele vai pegar de volta o número que estava guardado na memória
        
        Parâmetros:
            expression: String contendo a expressão RPN a ser avaliada
            
        Retorna:
            Resultado da avaliação da expressão
        """
        try:
            tokens = self.lexical_analyzer(expression.strip())

            self.syntactic_analyzer(tokens)

            res_match = re.match(r'^\(\s*(\d+)\s+RES\s*\)$', expression.strip())
            if res_match:
                n = int(res_match.group(1))
                if n < len(self.results):
                    return self.convertFloatToHalf(self.results[-(n+1)])
                else:
                    raise ValueError(f"Error: There are not {n} previous results.")
                
            mem_store_match = re.match(r'^\(\s*([0-9.+-]+)\s+MEM\s*\)$', expression.strip())
            if mem_store_match:
                value = float(mem_store_match.group(1))
                self.memory = self.convertFloatToHalf(value)
                return self.memory
            
            return self.evaluate_tokens(self.tokenize_expression(expression))
        except Exception as e:
            print(f"Error evaluating expression '{expression}': {str(e)}")
            return None
    
    def evaluate_tokens(self, tokens):
        """
        Avalia uma lista de tokens em notação RPN e retorna o resultado.
        Lida com a lógica de processamento de expressões, pilha de operandos,
        e tratamento de sub-expressões aninhadas.
        
        Parâmetros:
            tokens: Lista de tokens (operandos, operadores e parênteses)
            
        Retorna:
            Resultado da avaliação dos tokens
        """
        stack = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '(':
                j = i + 1
                count = 1
                while j < len(tokens) and count > 0:
                    if tokens[j] == '(':
                        count += 1
                    elif tokens[j] == ')':
                        count -= 1
                    j += 1
                if count != 0:
                    raise ValueError("Erro: Parênteses não balanceados.")
                subexpr = tokens[i+1:j-1]

                if len(subexpr) == 2 and subexpr[1] == 'RES':
                    n = int(subexpr[0])
                    if n < len(self.results):
                        stack.append(self.results[-(n+1)])
                    else:
                        raise ValueError(f"Erro: Não há {n} resultados anteriores.")
                elif len(subexpr) == 2 and subexpr[1] == 'MEM':
                    value = float(subexpr[0])
                    self.memory = self.convertFloatToHalf(value)
                    stack.append(self.memory)
                elif len(subexpr) == 1 and subexpr[0] == 'MEM':
                    stack.append(self.memory)
                else:
                    result = self.evaluate_tokens(subexpr)
                    stack.append(self.convertFloatToHalf(result))
                i = j
            elif token == ')':
                i += 1
            elif token in ['+', '-', '*', '|', '/', '%', '^']:
                if len(stack) < 2:
                    raise ValueError(f"Erro: Operador {token} requer dois operandos.")
                b = self.convertHalfToFloat(stack.pop())
                a = self.convertHalfToFloat(stack.pop())
                result = self.operate(a, b, token)
                stack.append(self.convertFloatToHalf(result))
                i += 1
            else:
                try:
                    num = float(token)
                    stack.append(self.convertFloatToHalf(num))
                except ValueError:
                    raise(f"Erro: Token 'token' não é válido.")
                i += 1
            
        if len(stack) != 1:
            raise ValueError(f"Erro: A pilha tem {len(stack)} elementos após a avaliação.")
        return self.convertHalfToFloat(stack.pop())

    def operate(self, a, b, operator):
        """
        Performs the mathematical operation between two operands a and b with the given operator.
        
        Parameters:
            a: First operand (float)
            b: Second operand (float)
            operator: Operator (string)
        Returns:
            Result of the operation
        """
        if operator == '+':
            return a + b
        elif operator == '-':
            return a - b
        elif operator == '*':
            return a * b
        elif operator == '/':
            if b == 0:
                raise ValueError("Erro: Divisão por zero.")
            return a / b
        elif operator == '%':
            return a % b
        elif operator == '^':
            return math.pow(a, b)
        elif operator == '|':
            return max(a, b)
        else:
            raise ValueError(f"Error: Invalid operator '{operator}'")
    
    def tokenize_expression(self, expression):
        """
        Tokenizes the RPN expression, splitting it into its components (operators, operands, special commands).
        
        Parameters:
            expression: RPN expression as a string
        Returns:
            List of tokens
        """
        # Clean up the expression
        expression = expression.strip()
        # Use regular expressions to split the expression into tokens (now including keywords)
        return re.findall(r'\d+\.\d+|\d+|[()+\-*/^%|]|[A-Z]+', expression, flags=re.IGNORECASE)
    
    def process_input(self, path):
        """
            Processes individual files or directories.
        """
        if os.path.isfile(path):
            if path.endswith('.txt'):
                self.process_file(path)
            else:
                print(f"Error: '{path}' is not a .txt file")
        elif os.path.isdir(path):
            self.process_File(path)  # original method for directories
        else:
            print(f"Error: '{path}' not found or is not valid")
    
    def process_File(self, filename):
        """
            Processes a file containing RPN expressions (one per line).
            Evaluates each expression and stores the result.
            
            Parameters:
                filename: Path to the file to be processed
            Returns:
                List with the results of each expression in the file
        """
        print(f"---- File: {os.path.basename(filename)} ----\n")
        with open(filename, 'r') as f:
            lines = f.readlines()
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    print(f"Expression {i+1}: {line}")
                    # Show token string
                    tok_list = self.lexical_analyzer(line)
                    token_str = ' '.join([f"< {t['value']}, {t['type']}, {t['position']} >" for t in tok_list])
                    print(f"Tokens: {token_str}")
                    result = self.evaluate_expression(line)
                    if result is not None:
                        self.results.append(result)
                        print(f"Result: {result}\n")
    
    def lexical_analyzer(self, expression):
        """
            Lexical Analyzer - Transforms the expression into tokens with additional information
            Returns a list of dictionaries containing:
            - 'value': token value
            - 'type': token type (NUMBER, OPERATOR, PAREN, COMMAND)
            - 'position': initial position in the expression
            - 'type': tipo do token (NUMBER, OPERATOR, PAREN, COMMAND)
            - 'position': posição inicial na expressão
        """
        tokens = []
        i = 0
        n = len(expression)
        
        while i < n:
            if expression[i].isspace():
                i += 1
                continue
                
            # Verifica parênteses
            if expression[i] in '()':
                tokens.append({'value': expression[i], 'type': 'PAREN', 'position': i})
                i += 1
                continue
                
            # Verifica operadores
            if expression[i] in '+-*/%|^':
                tokens.append({'value': expression[i], 'type': 'OPERATOR', 'position': i})
                i += 1
                continue
                
            # Verifica números (inteiros e decimais)
            if expression[i].isdigit() or expression[i] == '.':
                start = i
                has_decimal = False
                while i < n:
                    if expression[i].isdigit():
                        i += 1
                    elif expression[i] == '.' and not has_decimal:
                        has_decimal = True
                        i += 1
                    else:
                        break
                
                # Verifica se o token é válido (não termina com ponto)
                if expression[i-1] == '.':
                    raise ValueError(f"Número inválido na posição {start}")
                
                tokens.append({'value': expression[start:i],'type': 'NUMBER','position': start})
                continue
                
            # Verifica comandos (RES, MEM)
            if expression[i].isalpha():
                start = i
                while i < n and expression[i].isalpha():
                    i += 1
                token_value = expression[start:i].upper()
                
                if token_value in ('RES', 'MEM'):
                    tokens.append({'value': token_value,'type': 'COMMAND','position': start})
                else:
                    raise ValueError(f"Comando desconhecido '{token_value}' na posição {start}")
                continue
            raise ValueError(f"Caractere inválido '{expression[i]}' na posição {i}") 
        return tokens
    
    def syntactic_analyzer(self, tokens):
        """
            Verifica se a estrutura dos tokéns é válida
            Retorna True se a sintaxe estiver correta, False caso contrário
        """
        stack = []
        i = 0
        n = len(tokens)
        
        def expect(token_type=None, token_value=None):
            nonlocal i
            if i >= n:
                raise ValueError("Fim inesperado da expressão")
            if token_type and tokens[i]['type'] != token_type:
                raise ValueError(f"Esperado {token_type}, encontrado {tokens[i]['type']} na posição {tokens[i]['position']}")
            if token_value and tokens[i]['value'] != token_value:
                raise ValueError(f"Esperado '{token_value}', encontrado '{tokens[i]['value']}' na posição {tokens[i]['position']}")
            i += 1
        
            try:
                while i < n:
                    if tokens[i]['value'] == '(':
                        stack.append(tokens[i])
                        expect('PAREN', '(')
                        
                        # Verifica se é um comando especial
                        if i + 2 < n and tokens[i]['type'] == 'NUMBER' and tokens[i+1]['type'] == 'COMMAND':
                            expect('NUMBER')
                            expect('COMMAND')
                            expect('PAREN', ')')
                            stack.pop()
                            continue
                        elif i + 1 < n and tokens[i]['type'] == 'COMMAND' and tokens[i]['value'] == 'MEM':
                            expect('COMMAND', 'MEM')
                            expect('PAREN', ')')
                            stack.pop()
                            continue
                        
                        # Caso contrário, deve ser uma expressão normal
                        # Primeiro operando (pode ser número ou subexpressão)
                        if i < n and tokens[i]['type'] in ('NUMBER', 'PAREN'):
                            if tokens[i]['value'] == '(':
                                self.syntactic_analyzer(tokens[i:])
                            else:
                                expect('NUMBER')
                        
                        # Segundo operando
                        if i < n and tokens[i]['type'] in ('NUMBER', 'PAREN'):
                            if tokens[i]['value'] == '(':
                                self.syntactic_analyzer(tokens[i:])
                            else:
                                expect('NUMBER')
                        
                        # Operador
                        expect('OPERATOR')
                        
                        # Fechamento
                        expect('PAREN', ')')
                        stack.pop()
                    else:
                        i += 1
                
                if stack:
                    raise ValueError(f"Parêntese não fechado na posição {stack[-1]['position']}")
                
                return True
            except ValueError as e:
                raise ValueError(f"Erro sintático: {str(e)}")
            
def main():
    """
        Função principal que coordena a execução do programa.
        Processa o arquivo de entrada especificado como argumento de linha de comando,
        avalia as expressões e gera o código Assembly para Arduino.
    """
    calculator = RPNCalculator()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        calculator.process_File(path)
    else:
         print("Uso: python3 main.py <arquivo_de_entrada>")

# Exemplo de uso:
if __name__ == "__main__":
    main()