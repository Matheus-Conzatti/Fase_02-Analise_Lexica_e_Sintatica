"""
Trabalho de Compiladores - Calculadora RPN
Fase 2: Análise Léxica e Sintática 

Integrantes do grupo:
- Andre Ruan Cesar Dal Negro
- Felipe Abdullah
- Luiz Augusto Signorelli Toledo
- Matheus Conzatti De Souza

"""
import math
import numpy as np
import sys

# Variáveis Globais
resultHalf = [] # Variavel que armazena os resultados do half-precision em um vetor
memory = np.float16(0.0) # Memória que auxilia nos comandos especiais

