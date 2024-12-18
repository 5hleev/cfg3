import re
import sys
import toml

class SyntaxError(Exception):
    pass

# Лексер: разбиение входного текста на токены
def lexer(input_text):
    token_specification = [
        ('TABLE', r'table'),  # Ключевое слово table
        ('LBRACKET', r'\['),  # Открывающая квадратная скобка
        ('RBRACKET', r'\]'),  # Закрывающая квадратная скобка
        ('EQUALS', r'='),  # Равно
        ('NAME', r'[a-zA-Z][a-zA-Z0-9]*'),  # Имена (буквы + цифры)
        ('NUMBER', r'\d+'),  # Числа
        ('STRING', r"'[^']*'"),  # Строки
        ('CONST_DECL', r':='),  # Объявление константы
        ('EXPR_START', r'\?\{'),  # Начало выражения
        ('EXPR_END', r'\}'),  # Конец выражения
        ('SEMICOLON', r';'),  # Конец объявления
        ('COMMA', r','),  # Запятая
        ('LPAREN', r'\('),  # Открывающая круглая скобка
        ('RPAREN', r'\)'),  # Закрывающая круглая скобка
        ('COMMENT', r'\".*'),  # Однострочный комментарий
        ('SKIP', r'[ \t\n]+'),  # Пропуски
        ('MISMATCH', r'.'),  # Любой другой символ
    ]
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
    tokens = []
    in_multiline_comment = False
    line_number = 1

    for mo in re.finditer(tok_regex, input_text):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'SKIP':
            line_number += value.count('\\n')
            continue

        if in_multiline_comment:
            if kind == 'MCOMMENT_END':
                in_multiline_comment = False
            continue

        if kind == 'MCOMMENT_START':
            in_multiline_comment = True
            continue

        if kind == 'COMMENT':
            continue  # Игнорируем однострочные комментарии

        if kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value} at line {line_number}')

        tokens.append((kind, value))

    if in_multiline_comment:
        raise SyntaxError('Unclosed multi-line comment. Ensure every "(comment" has a closing ")".')

    return tokens