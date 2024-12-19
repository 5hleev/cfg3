import unittest
from tool import lexer, parse, to_toml

class TestUpdatedTool(unittest.TestCase):
    def test_constants(self):
        tokens = lexer("name := 'example';")
        config = parse(tokens)
        self.assertEqual(config, {'name': 'example'})

    def test_numbers(self):
        tokens = lexer("number := 42;")
        config = parse(tokens)
        self.assertEqual(config, {'number': 42})

    def test_table(self):
        tokens = lexer("mytable := table([ key1 = 'value1', key2 = 42 ]);")
        config = parse(tokens)
        self.assertEqual(config, {'mytable': {'key1': 'value1', 'key2': 42}})

    def test_nested_table(self):
        tokens = lexer("nested := table([ outer = table([ inner = 123 ]) ]);")
        config = parse(tokens)
        self.assertEqual(config, {'nested': {'outer': {'inner': 123}}})

    def test_toml_conversion(self):
        config = {'name': 'example', 'table_example': {'key1': 'value1', 'key2': 42}}
        toml_output = to_toml(config)
        expected_toml = """name = "example"

[table_example]
key1 = "value1"
key2 = 42
"""
        self.assertEqual(toml_output.strip(), expected_toml.strip())

if __name__ == '__main__':
    unittest.main()
