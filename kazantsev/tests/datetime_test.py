# import random
# from datetime import timezone, timedelta, datetime
# from unittest import TestCase
#
# from kazantsev import hhparser
#
#
# def check_single_million_datetimes(case, parse_method):
#     s = "2022-01-07T19:34:57+0300"
#     dt = datetime(2022, 1, 7, 19, 34, 57, tzinfo=timezone(timedelta(hours=3)))
#     for i in range(1_000_000):
#         parsed_dt = parse_method(s)
#         case.assertEqual(dt, parsed_dt)
#
#
# def check_different_datetimes(case, parse_method):
#     def pad2(number):
#         return str(number).zfill(2)
#
#     for day in range(1, 10):
#         for hour in range(24):
#             for min in range(60):
#                 for sec in range(60):
#                     dt = datetime(2022, 1, day, hour, min, sec, tzinfo=timezone(timedelta(hours=3)))
#                     s = f'2022-01-{pad2(day)}T{pad2(hour)}:{pad2(min)}:{pad2(sec)}+0300'
#                     parsed_dt = parse_method(s)
#                     case.assertEqual(dt, parsed_dt)
#
#
# def check_datetimes_with_wrong_strings(case, parse_method):
#     wrong_strings = (
#         '',
#         'ABCDERFDSFDSGFSGGFD',
#         'ABCDERFDSFDSGFSGGFDSGDFF',
#         '2022!01-07T19:34:57+0300',
#         '2022-01!07T19:34:57+0300',
#         '2022-01-07!19:34:57+0300',
#         '2022-01-07T19!34:57+0300',
#         '2022-01-07T19:34!57+0300',
#         '2022-01-07T19:34:57*0300',
#         '2022-01-07T-1:34:57+0300',
#     )
#     right_s = '2022-01-07T19:34:57+0300'
#     right_dt = datetime(2022, 1, 7, 19, 34, 57, tzinfo=timezone(timedelta(hours=3)))
#     for i in range(100_000):
#         wrong = random.choice(wrong_strings)
#         with case.assertRaises(Exception):
#             parse_method(wrong)
#         for j in range(9):
#             dt = parse_method(right_s)
#             case.assertEqual(right_dt, dt)
#
#
# class DatetimeTest(TestCase):
#     def test_single_million_default_parses(self):
#         check_single_million_datetimes(self, hhparser.parse_datetime_ordinary)
#
#     def test_single_million_ciso8601_parses(self):
#         check_single_million_datetimes(self, hhparser.parse_datetime_with_ciso8601)
#
#     def test_single_million_regex_parses(self):
#         check_single_million_datetimes(self, hhparser.parse_datetime_with_regex)
#
#     def test_single_million_direct_parses(self):
#         check_single_million_datetimes(self, hhparser.parse_datetime_directly)
#
#     def test_different_default_parses(self):
#         check_different_datetimes(self, hhparser.parse_datetime_ordinary)
#
#     def test_different_ciso8601_parses(self):
#         check_different_datetimes(self, hhparser.parse_datetime_with_ciso8601)
#
#     def test_different_regex_parses(self):
#         check_different_datetimes(self, hhparser.parse_datetime_with_regex)
#
#     def test_different_direct_parses(self):
#         check_different_datetimes(self, hhparser.parse_datetime_directly)
#
#     def test_mixed_strings_default_parses(self):
#         check_datetimes_with_wrong_strings(self, hhparser.parse_datetime_ordinary)
#
#     def test_mixed_strings_ciso8601_parses(self):
#         check_datetimes_with_wrong_strings(self, hhparser.parse_datetime_with_ciso8601)
#
#     def test_mixed_strings_regex_parses(self):
#         check_datetimes_with_wrong_strings(self, hhparser.parse_datetime_with_regex)
#
#     def test_mixed_strings_direct_parses(self):
#         check_datetimes_with_wrong_strings(self, hhparser.parse_datetime_directly)
