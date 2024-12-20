import re
import sys
import toml

# Класс обработки синтаксических ошибок
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
    line_number = 1

    for mo in re.finditer(tok_regex, input_text):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'SKIP':
            line_number += value.count('\n')
            continue

        if kind == 'COMMENT':
            continue  # Игнорируем однострочные комментарии

        if kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character: {value} at line {line_number}')

        tokens.append((kind, value))

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
        elif kind == 'EXPR_START':  # Обработка ?{имя}
            return evaluate_expression()
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

    def evaluate_expression():
        nonlocal index
        index += 1  # Пропустить ?{
        if tokens[index][0] != 'NAME':
            raise SyntaxError('Expected a name in expression')
        name = tokens[index][1]
        index += 1
        if tokens[index][0] != 'EXPR_END':
            raise SyntaxError('Expected } at the end of expression')
        index += 1  # Пропустить }
        if name not in config:
            raise SyntaxError(f'Undefined constant: {name}')
        return config[name]

    while index < len(tokens):
        if tokens[index][0] == 'NAME':
            parse_constant()
        elif tokens[index][0] == 'TABLE':
            config["table"] = parse_table()
        else:
            raise SyntaxError(f"Unexpected token: {tokens[index]}")

    return config

# Преобразование в TOML
def to_toml(config):
    toml_string = toml.dumps(config)
    return toml_string

# Основная функция
def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        input_text = sys.stdin.read()

    try:
        tokens = lexer(input_text)
        config = parse(tokens)
        print(to_toml(config))
    except SyntaxError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
