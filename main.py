"""
Trabalho de Compiladores - Calculadora RPN
Fase 2: Análise Léxica e Sintática

Integrantes do grupo:
- Andre Ruan Cesar Dal Negro
- Felipe Abdullah
- Luiz Augusto Signorelli Toledo
- Matheus Conzatti De Souza

Nome do grupo no Canvas: RA1 10
"""

import math
import numpy as np
import sys

# Variáveis Globais
resultHalf = []  # Variável que armazena os resultados do half-precision em um vetor
memory = np.float16(0.0)  # Memória que auxilia nos comandos especiais

class calculatorRPN:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self.vazia():
            return self._items.pop()
        else:
            print("\tAviso: Tentativa de desempilhar de pilha vazia.", file=sys.stderr)
            return None

    def vazia(self):
        return len(self._items) == 0

    def tamanho(self):
        return len(self._items)

    def __str__(self):
        return str(self._items)

    def convertFloatToHalf(Fval):
        return np.float16(Fval)

    def convertHalfToFloat(f16_val):
        return float(f16_val)

    def operacao(a, b, op):
        a_F = float(a)
        b_F = float(b)
        try:
            if op == '+': return a_F + b_F
            elif op == '-': return a_F - b_F
            elif op == '*': return a_F * b_F
            elif op == '/':
                if b_F == 0:
                    print("\tErro: Divisão por zero!", file=sys.stderr)
                    return np.nan
                return a_F / b_F
            elif op == '^': return math.pow(a_F, b_F)
            elif op == '%': 
                if b_F == 0:
                    print("\tErro: Modulo por zero!", file=sys.stderr)
                    return np.nan
                return math.fmod(a_F, b_F)
            else:
                print(f"\tOperador binário desconhecido: {op}", file=sys.stderr)
                return np.nan
        except Exception as e:
            print(f"\tErro durante operação '{op}': {e}", file=sys.stderr)
            return np.nan

    @staticmethod
    def resolveExp(expressao):
        global memory, resultHalf

        calculator = calculatorRPN()
        tokens = list(expressao.split())
        operadoresBinarios = "+-/*^%"
        operadoresUnitarios = "&"
        idx = 0

        while idx < len(tokens):
            token = tokens[idx]

            if token.startswith('(') and token.endswith(')'):
                comando = token[1:-1].strip()
                if comando.endswith(" RES"):
                    try:
                        nStr = comando[:-4].strip()
                        n = int(nStr)
                        if 0 <= n < len(resultHalf):
                            valorRes = calculatorRPN.convertHalfToFloat(resultHalf[n])
                            calculator.push(valorRes)
                        else:
                            print(f"\tErro: Resultado N={n} não encontrado.", file=sys.stderr)
                    except ValueError:
                        print(f"\tErro: Comando RES inválido '{comando}'.", file=sys.stderr)
                    except Exception as e:
                        print(f"\tErro processando comando RES '{comando}': {e}", file=sys.stderr)
                elif comando == "MEM":
                    valorMem = calculatorRPN.convertHalfToFloat(memory)
                    calculator.push(valorMem)
                elif comando.startswith("V MEM"):
                    try:
                        vStr = comando[6:]
                        v = float(vStr)
                        memory = calculatorRPN.convertFloatToHalf(v)
                    except ValueError:
                        print(f"\tErro: Comando V MEM inválido '{comando}'.", file=sys.stderr)
                    except Exception as e:
                        print(f"\tErro processando comando V MEM '{comando}': {e}", file=sys.stderr)
                else:
                    print(f"\tErro: Comando especial desconhecido '{comando}'", file=sys.stderr)
            elif token in operadoresBinarios:
                if calculator.tamanho() < 2:
                    print(f"\tErro: Pilha nao contem elementos suficientes para a operacao '{token}'!", file=sys.stderr)
                    return np.nan
                n1 = calculator.pop()
                n2 = calculator.pop()
                if n1 is None or n2 is None: return np.nan

                resultadoOp = calculatorRPN.operacao(n2, n1, token)
                if np.isnan(resultadoOp): return np.nan
                calculator.push(resultadoOp)
                resultHalf.append(calculatorRPN.convertFloatToHalf(resultadoOp))
            elif token in operadoresUnitarios:
                if calculator.vazia():
                    print(f"\tErro: Pilha nao contem elementos suficientes para a operacao '{token}'!", file=sys.stderr)
                    return np.nan
                n1 = calculator.pop()
                if n1 is None: return np.nan

                if token == '&':
                    try:
                        if n1 < 0:
                            print(f"\tErro: Raiz quadrada de número negativo ({n1})!", file=sys.stderr)
                            resultadoOp = np.nan
                        else:
                            resultadoOp = math.sqrt(float(n1))
                    except Exception as e:
                        print(f"\tErro durante operacao '&': {e}", file=sys.stderr)
                else:
                    print(f"\tErro: Operador unitario desconhecido '{token}'", file=sys.stderr)
                    resultadoOp = np.nan

                if np.isnan(resultadoOp): return np.nan
                calculator.push(resultadoOp)
                resultHalf.append(calculatorRPN.convertFloatToHalf(resultadoOp))
            else:
                try:
                    num = float(token)
                    calculator.push(num)
                    resultHalf.append(calculatorRPN.convertFloatToHalf(num))
                except ValueError:
                    print(f"\tErro: Token invalido '{token}'.", file=sys.stderr)
                    return np.nan
            idx += 1

        if calculator.tamanho() == 1:
            resultadoFinal = calculator.pop()
            if resultadoFinal is None or np.isnan(resultadoFinal):
                print("\tErro: Calculo resultou em None ou NaN.", file=sys.stderr)
                return np.nan
            return resultadoFinal
        elif calculator.vazia():
            print("\tAviso: Pilha final vazia. Retornando 0.0", file=sys.stderr)
            return 0.0
        else:
            print(f"\tErro: Expressão mal formada, sobraram {calculator.tamanho()} itens.", file=sys.stderr)
            return np.nan

    @staticmethod
    def lerArquivo(nomeArquivos):
        global resultHalf
        for nomeArquivo in nomeArquivos:
            try:
                with open(nomeArquivo, 'r') as arquivo:
                    print(f"--- Resultados do arquivo {nomeArquivo}: ---")
                    for linha in arquivo:
                        expressaoOriginal = linha.strip()
                        if not expressaoOriginal: continue

                        resultHalf.clear()

                        resultado = calculatorRPN.resolveExp(expressaoOriginal)
                        if np.isnan(resultado):
                            print(f"Expressao: {expressaoOriginal} = ERRO")
                        else:
                            print(f"Expressao: {expressaoOriginal} = {resultado: .0f}")
                    print("-" * (len(nomeArquivo) + 26))
                    print("")
            except FileExistsError:
                print(f"Erro ao abrir o arquivo {nomeArquivo}.", file=sys.stderr)
            except Exception as e:
                print(f"Erro inesperado ao processar o arquivo {nomeArquivo}: {e}", file=sys.stderr)

# Função main fora da classe
def main():
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <arquivo_de_entrada>")
        sys.exit(1)

    input_file = sys.argv[1]
    print(f"Processando arquivo: {input_file}")
    calculatorRPN.lerArquivo([input_file])

# Executa apenas se for o script principal
if __name__ == "__main__":
    main()
