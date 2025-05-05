import sys
import re
import struct
import math
import os

class RPNCalculator:
    """
    Implementa uma calculadora para avaliação de expressões na Notação Polonesa Reversa (RPN).
    Suporta operações aritméticas básicas, comandos especiais de memória, e expressões aninhadas.
    """
    
    def __init__(self):
        """
        Inicializa a calculadora RPN com valores padrão.
        Configura a lista de resultados anteriores e a memória.
        """
        # Armazena resultados das expressões anteriores
        self.results = []
        # Memória para comando (V MEM)
        self.memory = 0.0
    
    def convertFloatToHalf(self, f):
        """
        Converte um número para formato de meia precisão (16 bits) conforme padrão IEEE754.
        
        Parâmetros:
            value: Valor float a ser convertido
            
        Retorna:
            Valor convertido para representação de meia precisão (16 bits)
        """
        # Converte o float para bits (uint32)
        bin_f = struct.unpack('>I', struct.pack('>f', f))[0]

        sinal = (bin_f >> 16) & 0x8000
        exp = ((bin_f >> 23) & 0xFF) - 127 + 15
        mantissa = (bin_f >> 13) & 0x03FF

        if exp <= 0:
            return sinal # Subnormal ou zero
        elif exp >= 31:
            return sinal | 0x7C00 # Infinito ou NaN
        return sinal | (exp << 10) | mantissa
    
    def convertHalfToFloat(self, f16):
        sinal = (f16 >> 15) & 0x1
        exp = (f16 >> 10) & 0x1F
        frac = f16 & 0x03FF
        f32Sinal = sinal << 31

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
            res_match = re.match(r'^\(\s*(\d+)\s+RES\s*\)$', expression.strip())
            if res_match:
                n = int(res_match.group(1))
                if n < len(self.results):
                    return self.convertFloatToHalf(self.results[-(n+1)])
                else:
                    raise ValueError(f"Erro: Não já {n} resultados anteriores.")
            
            mem_store_match = re.match(r'^\(\s*([0-9.+-]+)\s+MEM\s*\)$', expression.strip())
            if mem_store_match:
                value = float(mem_store_match(1))
                self.memory = self.convertFloatToHalf(self.memory)
            
            return self.evaluate_tokens(self.tokenize_expression(expression))
        except Exception as e:
            print(f"Erro ao avaliar expressão '{expression}': {str(e)}")

    
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
        Realiza a operação matemática entre dois operandos a e b com o operador fornecido.
        
        Parâmetros:
            a: Primeiro operando (float)
            b: Segundo operando (float)
            operator: Operador (string)
            
        Retorna:
            Resultado da operação
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
            raise ValueError(f"Erro: Operador '{operator}' inválido.")
    
    def tokenize_expression(self, expression):
        """
        Tokeniza a expressão RPN, dividindo-a em seus componentes (operadores, operandos, comandos especiais).
        
        Parâmetros:
            expression: Expressão RPN em formato de string
            
        Retorna:
            Lista de tokens
        """
        # Limpeza da expressão
        expression = expression.strip()
        # Usa expressões regulares para dividir a expressão em tokens
        return re.findall(r'\d+\.\d+|\d+|[()+\-*/^%|]', expression)
    
    def process_File(self, filename):
        """
            Processa um arquivo contendo expressões RPN (uma por linha).
            Avalia cada expressão e armazena o resultado.
            
            Parâmetros:
                filename: Caminho do arquivo a ser processado
                
            Retorna:
                Lista com os resultados de cada expressão no arquivo
        """
        try:
            results = []
            for file in os.listdir(filename):
                filepath = os.path.join(filename, file)
                # Verifica se é um arquivo e termina com .txt
                if os.path.isfile(filepath) and file.endswith('.txt'):
                    print(f"---- Arquivo: {file} ---------\n")
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if line:
                                print(f"Expressão: {line}")
                                result = self.evaluate_expression(line)
                                self.results.append(result)
                                results.append(result)
                                print(f"Resultado: {result}")
                                print()
            return results
        except FileNotFoundError:
            print(f"Erro: Diretório '{filename}' não encontrado.")
            return []
        except Exception as e:
            print(f"Erro ao processar diretório: {str(e)}")
            return []
        
    def generate_arduino_assembly(self, filename, output_filename="arduino_code.asm"):
        """
        Gera código Assembly para Arduino a partir do arquivo de expressões RPN.
        Cria um esqueleto básico do código Assembly que implementa as operações.
        
        Parâmetros:
            filename: Caminho do arquivo de entrada com expressões RPN
            output_filename: Caminho do arquivo de saída para o código Assembly
            
        Retorna:
            Booleano indicando sucesso ou falha na geração do código
        """
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
            
            assembly_code = []
            assembly_code.append("; Código Assembly gerado para Arduino UNO")
            assembly_code.append("; Este código implementa as expressões RPN do arquivo de entrada")
            assembly_code.append("")
            assembly_code.append(".include \"m328pdef.inc\"")
            assembly_code.append("")
            assembly_code.append("; Inicialização")
            assembly_code.append("setup:")
            assembly_code.append("    ; Configuração inicial do Arduino")
            assembly_code.append("    ; Seria implementado o código para inicializar registradores, etc.")
            assembly_code.append("")
            
            # Espaço para memória
            assembly_code.append("; Memória para comando (MEM)")
            assembly_code.append("    .dseg")
            assembly_code.append("memory: .byte 2    ; 2 bytes para half-precision float")
            assembly_code.append("results: .byte 20   ; Espaço para armazenar 10 resultados (2 bytes cada)")
            assembly_code.append("    .cseg")
            assembly_code.append("")
            
            # Loop principal para implementar as expressões
            assembly_code.append("main:")
            assembly_code.append("    ; Código principal")
            
            # Implementação das expressões
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                assembly_code.append(f"    ; Expressão da linha {i+1}: {line}")
                assembly_code.append(f"expression_{i+1}:")
                
                # Implementação básica para gerar código assembly
                # Na prática, este seria um compilador mais complexo
                if "+" in line:
                    assembly_code.append("    ; Operação de adição")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    add r16, r17  ; Soma")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "-" in line:
                    assembly_code.append("    ; Operação de subtração")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    sub r16, r17  ; Subtrai")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "*" in line:
                    assembly_code.append("    ; Operação de Multiplicação")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    mult r16, r17  ; Mult")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "/" in line:
                    assembly_code.append("    ; Operação de Divisão")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    div r16, r17  ; div")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "^" in line:
                    assembly_code.append("    ; Operação de Pontência")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    pow r16, r17  ; pow")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "%" in line:
                    assembly_code.append("    ; Operação de Resto da Divisão")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    mod r16, r17  ; mod")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                
            # Fim do programa
            assembly_code.append("")
            assembly_code.append("end:")
            assembly_code.append("    rjmp end    ; Loop infinito")
            
            # Escreve o código assembly no arquivo de saída
            with open(output_filename, 'w') as out_file:
                out_file.write('\n'.join(assembly_code))
            
            print(f"Código Assembly gerado e salvo em '{output_filename}'.")
            return True
        except Exception as e:
            print(f"Erro ao gerar código Assembly: {str(e)}")
            return False

    def lexical_analyzer(self, expression):
        """
            Analisador léxico - Transforma as expressões em tokens.
            Retorna uma lista de dicionários contendo:
            - 'value': valor do token
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

            # Verifica os parênteses
            if expression[i] in '()':
                tokens.append({'value': expression[i], 'type': 'PAREN', 'position': i})
                i += 1
                continue
            
               
        
def main():
    """
        Função principal que coordena a execução do programa.
        Processa o arquivo de entrada especificado como argumento de linha de comando,
        avalia as expressões e gera o código Assembly para Arduino.
    """
    calculator = RPNCalculator()

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        calculator.process_File(folder)
    else:
         print("Uso: python3 main.py <arquivo_de_entrada>")

# Exemplo de uso:
if __name__ == "__main__":
    main()