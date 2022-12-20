import concurrent.futures
from datetime import datetime
from unittest import TestCase

from kazantsev.api_worker import HhApiWorker
from kazantsev.local_path import get_local_path


class ApiWorkerTest(TestCase):
    def test_csv_loading(self):
        worker = HhApiWorker()
        worker.load_vacancies_to_csv(get_local_path('api_vacancies.csv'), datetime(2022, 12, 19))

    @staticmethod
    def _execute_task(i):
        worker = HhApiWorker()
        csv_path = get_local_path(f'./tests/api_vacancies/{i}.csv')
        print(f'Start getting {i} file')
        worker.load_vacancies_to_csv(csv_path, datetime(2022, 12, 19))
        return i

    def test_many_csv_loading(self):
        with concurrent.futures.ProcessPoolExecutor() as pool:
            for i in pool.map(self._execute_task, range(100)):
                pass

