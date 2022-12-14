import doctest
from datetime import datetime
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

from kazantsev import hhparser
from kazantsev.hhparser import *


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(hhparser))
    return tests


test_vacancy_1 = Vacancy('ТестВакансия1', Salary(100, 200, 'RUR', False), 'Москва', datetime.now(), 'Описание',
                         key_skills=['скилл1', 'скилл2'], experience_id='between1And3', premium=False,
                         employer_name='UnitTest')
test_vacancy_2 = Vacancy('ТестВакансия2', Salary(100, 200, 'RUR', False), 'Москва', datetime.now(), 'Описание',
                         key_skills=['скилл1', 'скилл2'], experience_id='between3And6', premium=True,
                         employer_name='UnitTest')


class HhParserTest(TestCase):
    # Five functions

    # 1: Transform value
    def test_transform_tag_value(self):
        result = DataSet._transform_value('<a href="ya.ru">Test</a>')
        self.assertEqual("Test", result)

    def test_transform_many_tags_value(self):
        result = DataSet._transform_value('<div class="a-b"><div class="w-c" style="color: red;"><a '
                                          'href="ya.ru">Test</a></div></div>')
        self.assertEqual("Test", result)

    def test_transform_many_lines(self):
        result = DataSet._transform_value('one\ntwo\nthree')
        self.assertListEqual(['one', 'two', 'three'], result)

    def test_transform_tagged_many_lines(self):
        result = DataSet._transform_value('<div class="a" style="color:red;">one\ntwo\nthree</div>')
        self.assertListEqual(['one', 'two', 'three'], result)

    def test_transform_many_lines_with_spaces(self):
        result = DataSet._transform_value('one      \n   two    \n   three  ')
        self.assertListEqual(['one', 'two', 'three'], result)

    def test_transform_many_lines_with_spaces_and_tabs(self):
        result = DataSet._transform_value('one       \n   two           \n       three  ')
        self.assertListEqual(['one', 'two', 'three'], result)

    # 2: Salary parsing
    def test_salary_parsing(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_gross': 'True',
            'salary_currency': 'RUR'
        }
        salary = Salary.parse_from_dict(salary_dict)
        self.assertEqual(80000, salary.from_amount)
        self.assertEqual(100000, salary.to_amount)
        self.assertEqual(True, salary.gross)
        self.assertEqual('RUR', salary.currency)

    def test_salary_parsing_wrong_gross(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_gross': 1,
            'salary_currency': 'RUR'
        }
        with self.assertRaises(ValueError):
            Salary.parse_from_dict(salary_dict)

    def test_salary_parsing_wrong_currency_type(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_gross': 'True',
            'salary_currency': Path(),
        }
        with self.assertRaises(ValueError):
            Salary.parse_from_dict(salary_dict)

    def test_salary_parsing_wrong_currency(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_gross': 'True',
            'salary_currency': 'ERR'
        }
        with self.assertRaises(ValueError):
            Salary.parse_from_dict(salary_dict)

    def test_salary_parsing_without_gross(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_currency': 'RUR'
        }
        salary = Salary.parse_from_dict(salary_dict)
        self.assertEqual(80000, salary.from_amount)
        self.assertEqual(100000, salary.to_amount)
        self.assertIsNone(salary.gross)
        self.assertEqual('RUR', salary.currency)

    def test_salary_parsing_wrong_from_key(self):
        salary_dict = {
            'salary_fro': '80000',
            'salary_to': '100000',
            'salary_gross': 1,
            'salary_currency': 'RUR',
        }
        with self.assertRaises(KeyError):
            Salary.parse_from_dict(salary_dict)

    def test_salary_parsing_wrong_to_key(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_t': '100000',
            'salary_gross': 1,
            'salary_currency': 'RUR',
        }
        with self.assertRaises(KeyError):
            Salary.parse_from_dict(salary_dict)

    def test_salary_parsing_wrong_currency_key(self):
        salary_dict = {
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_gross': 1,
            'salary_cur': 'RUR',
        }
        with self.assertRaises(KeyError):
            Salary.parse_from_dict(salary_dict)

    # 3: Avg salary
    def test_avg_salary(self):
        salary = Salary(from_amount=80000, to_amount=100000, currency='RUR')
        self.assertEqual(90000, salary.avg_ruble_amount)

    def test_avg_salary_one_value_range(self):
        salary = Salary(from_amount=80000, to_amount=80000, currency='RUR')
        self.assertEqual(80000, salary.avg_ruble_amount)

    def test_foreign_avg_salary(self):
        salary = Salary(from_amount=2000, to_amount=3000, currency='EUR')
        self.assertEqual(2500 * 59.90, salary.avg_ruble_amount)

    def test_foreign_avg_salary_one_value_range(self):
        salary = Salary(from_amount=3000, to_amount=3000, currency='EUR')
        self.assertEqual(3000 * 59.90, salary.avg_ruble_amount)

    # 4: To row dict of VacanciesStatics
    def test_to_row_dict(self):
        title_row = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
        row = ['Программист', '80000', '100000', 'RUR', 'Екатеринбург', '2021-12-10T22:06:44+0300']
        row_dict = VacanciesStatistics._to_row_dict(title_row, row)
        self.assertDictEqual({
            'name': 'Программист',
            'salary_from': '80000',
            'salary_to': '100000',
            'salary_currency': 'RUR',
            'area_name': 'Екатеринбург',
            'published_at': '2021-12-10T22:06:44+0300'
        }, row_dict)

    def test_to_row_dict_less_title(self):
        title_row = ['name', 'salary_from', 'salary_to', 'salary_currency']
        row = ['Программист', '80000', '100000', 'RUR', 'Екатеринбург', '2021-12-10T22:06:44+0300']
        row_dict = VacanciesStatistics._to_row_dict(title_row, row)
        self.assertIsNone(row_dict)

    def test_to_row_dict_bigger_title(self):
        title_row = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at', 'bruh']
        row = ['Программист', '80000', '100000', 'RUR', 'Екатеринбург', '2021-12-10T22:06:44+0300']
        row_dict = VacanciesStatistics._to_row_dict(title_row, row)
        self.assertIsNone(row_dict)

    def test_to_row_dict_empty_values(self):
        title_row = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
        row = ['Программист', '80000', '100000', 'RUR', 'Екатеринбург', '2021-12-10T22:06:44+0300']
        for i in range(len(row)):
            test_row = list(row)
            test_row[i] = ''
            row_dict = VacanciesStatistics._to_row_dict(title_row, test_row)
            self.assertIsNone(row_dict)

    # 5: All equal
    def test_all_equal(self):
        hhparser.check_all_equal([1, 1, 1], Exception('Not all equal'))

    def test_one_equals(self):
        hhparser.check_all_equal([1], Exception('Not all equal'))

    def test_not_all_equal(self):
        e = Exception('Test: Not all equal')
        with self.assertRaises(Exception) as exc:
            hhparser.check_all_equal([1, 1, 1, 2, 1, 1], e)
        self.assertEqual('Test: Not all equal', str(exc.exception))

    # Some other functions
    def test_wrong_bool_values(self):
        for val in ['0', '1', 'Да', 'Нет']:
            with self.assertRaises(ValueError):
                hhparser.to_bool(val)

    def test_wrong_skills_type(self):
        with self.assertRaises(TypeError):
            Vacancy._list_skills(Path())

    # Test the program

    @patch('builtins.input',
           side_effect=["Вакансии", "./tests/vacancies_medium.csv", "Премиум-вакансия: Нет", "Название", "Нет", "10 30",
                        "Название, Навыки, Опыт работы, Премиум-вакансия, Компания, Оклад, "
                        "Название региона, Дата публикации вакансии"])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_vacancies_case(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual(194, mock_stdout.getvalue().count('\n'))

    @patch('builtins.input', side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "", "", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_all_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual(3539, mock_stdout.getvalue().count('\n'))

    @patch('builtins.input', side_effect=["Статистика", "./tests/vacancies_by_year_100k.csv", "Программист"])
    def test_statics(self, mock_inputs):
        execute_program()

    @patch('builtins.input', side_effect=["Чушь-муть", "./tests/vacancies_by_year_100k.csv", "Программист"])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wrong_subprogram(self, mock_stdout, mock_inputs):
        execute_program()
        err_msg = 'Такого мы пока еще не разработали. Перезапустите программу и введите одно из возможных значений.\n'
        self.assertEqual(err_msg, mock_stdout.getvalue())

    @patch('builtins.input',
           side_effect=["Вакансии", "./tests/vacancies_medium.csv", "Премиум-вакансия Нет", "", "", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wrong_format_filter_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual("Формат ввода некорректен\n", mock_stdout.getvalue())

    @patch('builtins.input',
           side_effect=["Вакансии", "./tests/vacancies_medium.csv", "Премиум-бред: Нет", "", "", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wrong_param_filter_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual('Параметр поиска некорректен\n', mock_stdout.getvalue())

    @patch('builtins.input',
           side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "Бред для сортировки", "", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wrong_param_sort_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual('Параметр сортировки некорректен\n', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_sort_vacancies(self, mock_stdout):
        conect = InputConect()
        conect.set_sort_params('Название', 'Нет')
        conect.print_as_table([test_vacancy_1, test_vacancy_2])
        output = mock_stdout.getvalue()
        self.assertTrue(test_vacancy_1.name in output)
        self.assertTrue(test_vacancy_2.name in output)
        self.assertLess(output.find(test_vacancy_1.name), output.find(test_vacancy_2.name))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_reverse_sort_vacancies(self, mock_stdout):
        conect = InputConect()
        conect.set_sort_params('Название', 'Да')
        conect.print_as_table([test_vacancy_1, test_vacancy_2])
        output = mock_stdout.getvalue()
        self.assertTrue(test_vacancy_1.name in output)
        self.assertTrue(test_vacancy_2.name in output)
        self.assertLess(output.find(test_vacancy_2.name), output.find(test_vacancy_1.name))

    @patch('builtins.input',
           side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "Название", "Бред", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_wrong_order_sort_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual('Порядок сортировки задан некорректно\n', mock_stdout.getvalue())

    @patch('builtins.input', side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "", "", "10", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_start_range(self, mock_stdout, mock_inputs):
        execute_program()
        # Assert 3469 line breaks
        self.assertEqual(3469, mock_stdout.getvalue().count('\n'))

    @patch('builtins.input', side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "", "", "10 20", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_full_range(self, mock_stdout, mock_inputs):
        execute_program()
        # Assert 92 line breaks
        self.assertEqual(91, mock_stdout.getvalue().count('\n'))

    @patch('builtins.input', side_effect=["Вакансии", "./tests/vacancies_medium.csv", "", "", "", "1 2 3", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_many_numbers_range_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual('Диапазон вакансий должен содержать 1 или 2 числа.\n', mock_stdout.getvalue())

    @patch('builtins.input', side_effect=["Вакансии", "./tests/vacancies_medium.csv", "Название: НичегоНеДелатель",
                                          "", "", "", ""])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_zero_filtered_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        self.assertEqual('Ничего не найдено\n', mock_stdout.getvalue())

    @patch('builtins.input', side_effect=["Вакансии", "./tests/empty.csv", "Премиум-вакансия: Нет", "", "", "",
                                          "Название, Навыки, Опыт работы, Премиум-вакансия, Компания, Оклад, "
                                          "Название региона, Дата публикации вакансии"])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_empty_vacancies(self, mock_stdout, mock_inputs):
        execute_program()
        err_msg = 'Пустой файл\n'
        self.assertEqual(err_msg, mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_no_vacancies_print(self, mock_stdout):
        conect = InputConect()
        conect.print_as_table([])
        self.assertEqual('Нет данных\n', mock_stdout.getvalue())

    # Test to profile the program
    # def test_dataset_initializing(self):
    #     data = DataSet('./tests/vacancies_by_year.csv')


if __name__ == "__main__":
    main()
