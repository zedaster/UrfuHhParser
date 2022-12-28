from kazantsev.currency_rates import CurrencyRates
from kazantsev.hhparser import Report
from kazantsev.local_path import get_local_path
from kazantsev.vacancies_staticstics import PandasVacanciesStatistics


def execute_3_4_3():
    file_name = input('Введите название файла: ')
    path = get_local_path(file_name.strip())
    if not path.exists():
        print('Такого файла не существует!')
        exit()

    prof_name = input('Введите название профессии: ').strip()
    area_name = input('Введите название региона: ').strip()

    rates = CurrencyRates.from_csv(get_local_path('currency_rates.csv'))
    stats = PandasVacanciesStatistics(path, prof_name, rates, area_name=area_name)
    report = Report(stats)
    report.print()
    report.generate_pdf('3_4_3.pdf')


# tests/vacancies_by_year.csv
# аналитик
# Москва
if __name__ == '__main__':
    execute_3_4_3()
