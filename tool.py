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

def parse(tokens):
    config = {}
    index = 0

    def parse_value():
        nonlocal index
        if index >= len(tokens):
            raise SyntaxError('Unexpected end of input')
        kind, value = tokens[index]
        if kind == 'NUMBER':
            index += 1
            return int(value)
        elif kind == 'STRING':
            index += 1
            return value.strip("'")
        elif kind == 'TABLE':  # Обработка таблицы
            return parse_table()
        else:
            raise SyntaxError(f'Unexpected value: {value}')

    def parse_table():
        nonlocal index
        dictionary = {}
        if tokens[index][0] != 'TABLE':
            raise SyntaxError('Expected TABLE')
        index += 1
        if tokens[index][0] != 'LPAREN':
            raise SyntaxError('Expected ( after TABLE')
        index += 1  # Пропустить '('
        if tokens[index][0] != 'LBRACKET':
            raise SyntaxError('Expected [ after ( in TABLE')
        index += 1  # Пропустить '['

        while tokens[index][0] != 'RBRACKET':
            if tokens[index][0] == 'COMMA':  # Игнорируем запятые
                index += 1
                continue
            if tokens[index][0] == 'NAME':  # Ожидаем имя ключа
                key = tokens[index][1]
                index += 1
                if tokens[index][0] != 'EQUALS':  # Ожидаем равно
                    raise SyntaxError('Expected = after key')
                index += 1  # Пропустить '='
                value = parse_value()  # Обрабатываем значение
                dictionary[key] = value
            else:
                raise SyntaxError(f'Unexpected token in table: {tokens[index]}')

        index += 1  # Пропустить ']'
        if tokens[index][0] != 'RPAREN':
            raise SyntaxError('Expected ) after ] in TABLE')
        index += 1  # Пропустить ')'

        return dictionary

    def parse_constant():
        nonlocal index
        if tokens[index][0] != 'NAME':
            raise SyntaxError('Expected a name')
        name = tokens[index][1]
        index += 1
        if tokens[index][0] != 'CONST_DECL':
            raise SyntaxError('Expected :=')
        index += 1
        value = parse_value()
        if tokens[index][0] != 'SEMICOLON':
            raise SyntaxError('Expected ; at the end of declaration')
        index += 1
        config[name] = value

    while index < len(tokens):
        if tokens[index][0] == 'NAME':
            parse_constant()
        elif tokens[index][0] == 'TABLE':
            config["table"] = parse_table()
        else:
            raise SyntaxError(f"Unexpected token: {tokens[index]}")

    return config