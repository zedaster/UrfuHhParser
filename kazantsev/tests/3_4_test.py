from unittest import TestCase
from unittest.mock import patch
from kazantsev.pandas.task_3_4_2 import execute_3_4_2


class PandasTests(TestCase):
    @patch('builtins.input', side_effect=["tests/vacancies_dif_currencies_100k.csv", 'программист'])
    def test_task_3_4_2(self, mock_inputs):
        execute_3_4_2()
