"""
Trabalho de Compiladores - Calculadora RPN
Fase 1: Implementação de uma calculadora de expressões aritméticas em notação RPN

Integrantes do grupo:
- Andre Ruan Cesar Dal Negro
- Felipe Abdullah
- Luiz Augusto Signorelli Toledo
- Matheus Conzatti De Souza

Nome do grupo no Canvas: RA1 10
"""

import sys
import re
import struct
import math

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
    
    def convertFloatToHalf(f):
        """
        Converte um número para formato de meia precisão (16 bits) conforme padrão IEEE754.
        
        Parâmetros:
            value: Valor float a ser convertido
            
        Retorna:
            Valor convertido para representação de meia precisão (16 bits)
        """
        # Coverte o float para bits (uint32)
        bin_f = struct.unpack('>I', struct.pack('>f', f))[0]

        sinal = (bin_f >> 16) & 0x8000
        exp = ((bin_f >> 23) & 0xFF) - 127 +15
        mantissa = (bin_f >> 13) & 0x03FF

        if exp <= 0:
            return sinal # Subnormal ou zero
        elif exp >= 31:
            return sinal | 0x7C00 # Ifinito ou NaN
        return sinal | (exp << 10) | mantissa
    
    def convertHalfToFloat(f16):
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
            # Verifica se é o comando (N RES)
            res_match = re.match(r'^\(\s*(\d+)\s+RES\s*\)$', expression.strip())
            if res_match:
                n = int(res_match.group(1))
                if n < len(self.results):
                    return self.results[-(n+1)]
                else:
                    raise ValueError(f"Erro: Não há {n} resultados anteriores.")
            
            # Verifica se é o comando (V MEM)
            mem_store_match = re.match(r'^\(\s*([0-9.+-]+)\s+MEM\s*\)$', expression.strip())
            if mem_store_match:
                value = float(mem_store_match.group(1))
                self.memory = self.to_half_precision(value)
                return self.memory
            
            # Verifica se é o comando (MEM)
            if re.match(r'^\(\s*MEM\s*\)$', expression.strip()):
                return self.memory
            
            # Processamento normal da expressão RPN
            return self.evaluate_tokens(self.tokenize_expression(expression))
        except Exception as e:
            print(f"Erro ao avaliar expressão '{expression}': {str(e)}")
            return 0.0
    
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
        # Pilha para armazenar os operandos durante a avaliação
        stack = []
        
        # Índice para percorrer a lista de tokens
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token == '(':
                # CASO 1: INÍCIO DE SUB-EXPRESSÃO
                # Quando encontramos um parêntese de abertura, precisamos localizar
                # o parêntese de fechamento correspondente e processar o conteúdo entre eles
                
                # Contador para controlar o aninhamento de parênteses
                j = i + 1
                count = 1  # Começamos com 1 parêntese aberto
                
                # Busca o parêntese de fechamento correspondente
                while j < len(tokens) and count > 0:
                    if tokens[j] == '(':
                        count += 1  # Encontrou outro parêntese de abertura, incrementa o contador
                    elif tokens[j] == ')':
                        count -= 1  # Encontrou um parêntese de fechamento, decrementa o contador
                    j += 1
                
                # Verifica se os parênteses estão balanceados
                if count != 0:
                    raise ValueError("Erro: Parênteses não balanceados.")
                
                # Extrai a sub-expressão entre os parênteses (excluindo os parênteses)
                subexpr = tokens[i+1:j-1]
                
                # PROCESSAMENTO DE COMANDOS ESPECIAIS E SUB-EXPRESSÕES
                
                if len(subexpr) == 2 and subexpr[1] == 'RES':
                    # CASO 1.1: COMANDO (N RES)
                    # Recupera o resultado de N linhas anteriores
                    n = int(subexpr[0])
                    if n < len(self.results):
                        # Acessa o resultado N posições para trás no histórico (-1 para índice 0)
                        stack.append(self.results[-(n+1)])
                    else:
                        raise ValueError(f"Erro: Não há {n} resultados anteriores.")
                elif len(subexpr) == 2 and subexpr[1] == 'MEM':
                    # CASO 1.2: COMANDO (V MEM)
                    # Armazena um valor na memória
                    value = float(subexpr[0])
                    # Converte para meia precisão antes de armazenar
                    self.memory = self.to_half_precision(value)
                    # Empilha o valor armazenado para continuar o cálculo
                    stack.append(self.memory)
                elif len(subexpr) == 1 and subexpr[0] == 'MEM':
                    # CASO 1.3: COMANDO (MEM)
                    # Recupera o valor armazenado na memória
                    stack.append(self.memory)
                else:
                    # CASO 1.4: SUB-EXPRESSÃO NORMAL
                    # Avalia recursivamente a sub-expressão e empilha o resultado
                    result = self.evaluate_tokens(subexpr)
                    stack.append(result)
                
                # Avança o índice para depois do parêntese de fechamento
                i = j
            elif token == ')':
                # CASO 2: FIM DE SUB-EXPRESSÃO
                # Parênteses de fechamento são tratados implicitamente no 'CASO 1'
                i += 1
            elif token in ['+', '-', '*', '|', '/', '%', '^']:
                # CASO 3: OPERADORES
                # Todos os operadores requerem exatamente dois operandos
                if len(stack) < 2:
                    raise ValueError(f"Erro: Operador {token} requer dois operandos.")
                
                # Remove os dois operandos do topo da pilha (ordem é importante!)
                b = stack.pop()  # Segundo operando (topo da pilha)
                a = stack.pop()  # Primeiro operando (abaixo do topo)
                
                # Aplica o operador aos operandos e empilha o resultado
                result = self.operate(a, b, token)
                stack.append(result)
                i += 1
            else:
                # CASO 4: OPERANDOS (NÚMEROS)
                # Tenta converter o token para um número de ponto flutuante
                try:
                    num = float(token)
                    # Converte para meia precisão antes de empilhar
                    stack.append(self.to_half_precision(num))
                except ValueError:
                    # Se não for possível converter para float, o token é inválido
                    raise ValueError(f"Token inválido: {token}")
                i += 1
        
        # VALIDAÇÃO FINAL
        # Ao final da avaliação, a pilha deve conter exatamente um valor (o resultado final)
        if len(stack) != 1:
            raise ValueError("Erro: Expressão inválida ou incompleta.")
        
        # Retorna o único valor na pilha, que é o resultado da expressão
        return stack[0]
    
    def tokenize_expression(self, expression):
        """
        Converte uma string de expressão RPN em uma lista de tokens.
        Separa parênteses, operadores e operandos para processamento.
        
        Parâmetros:
            expression: String contendo a expressão RPN
            
        Retorna:
            Lista de tokens extraídos da expressão
        """
        # Substitui ( e ) por " ( " e " ) " para facilitar o split
        expression = expression.replace('(', ' ( ').replace(')', ' ) ')
        # Remove espaços extras e divide os tokens
        tokens = [token for token in expression.split() if token]
        return tokens
    
    def operate(self, a, b, operator):
        """
        Realiza a operação especificada entre dois operandos.
        Suporta +, -, *, |, /, %, ^ com tratamento adequado para cada tipo.
        
        Parâmetros:
            a: Primeiro operando
            b: Segundo operando
            operator: Operador a ser aplicado
            
        Retorna:
            Resultado da operação entre a e b
        """
        if operator == '+':
            return self.to_half_precision(a + b)
        elif operator == '-':
            return self.to_half_precision(a - b)
        elif operator == '*':
            return self.to_half_precision(a * b)
        elif operator == '|':
            if b == 0:
                raise ValueError("Erro: Divisão por zero.")
            return self.to_half_precision(a / b)  # Divisão real
        elif operator == '/':
            if b == 0:
                raise ValueError("Erro: Divisão por zero.")
            return int(a) // int(b)  # Divisão de inteiros
        elif operator == '%':
            if b == 0:
                raise ValueError("Erro: Divisão por zero.")
            return int(a) % int(b)  # Resto da divisão de inteiros
        elif operator == '^':
            if not float(b).is_integer() or b < 0:
                raise ValueError("Erro: Expoente deve ser um inteiro positivo.")
            return self.to_half_precision(a ** b)  # Potenciação
        else:
            raise ValueError(f"Operador desconhecido: {operator}")
    
    def process_file(self, filename):
        """
        Processa um arquivo contendo expressões RPN (uma por linha).
        Avalia cada expressão e armazena o resultado.
        
        Parâmetros:
            filename: Caminho do arquivo a ser processado
            
        Retorna:
            Lista com os resultados de cada expressão no arquivo
        """
        try:
            with open(filename, 'r') as file: lines = file.readlines()
            
            results = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    print(f"Linha {i+1}: {line}")
                    result = self.evaluate_expression(line)
                    self.results.append(result)
                    results.append(result)
                    print(f"Resultado: {result}")
                    print()
            
            return results
        except FileNotFoundError:
            print(f"Erro: Arquivo '{filename}' não encontrado.")
            return []
        except Exception as e:
            print(f"Erro ao processar arquivo: {str(e)}")
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
                    assembly_code.append("    ; Operação de multiplicação")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    mult r16, r17  ; Multiplicacao")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "/" in line:
                    assembly_code.append("    ; Operação de divisão")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    div r16, r17  ; Divisão")
                    assembly_code.append("    st X+, r16    ; Armazena resultado")
                elif "^" in line:
                    assembly_code.append("    ; Operação de potência")
                    assembly_code.append("    ld r16, X+    ; Carrega primeiro operando")
                    assembly_code.append("    ld r17, X+    ; Carrega segundo operando")
                    assembly_code.append("    pow r16, r17  ; Potência")
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

def main():
    """
    Função principal que coordena a execução do programa.
    Processa o arquivo de entrada especificado como argumento de linha de comando,
    avalia as expressões e gera o código Assembly para Arduino.
    """
    # Verifica se foi fornecido um arquivo de entrada
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <arquivo_de_entrada>")
        sys.exit(1)
    
    # Nome do arquivo de entrada
    input_file = sys.argv[1]
    
    # Cria uma instância da calculadora
    calculator = RPNCalculator()
    
    # Processa o arquivo de entrada
    print(f"Processando arquivo: {input_file}")
    calculator.process_file(input_file)
    
    # Gera o código assembly para Arduino
    calculator.generate_arduino_assembly(input_file)


if __name__ == "__main__":
    main()