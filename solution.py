import json
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
import logging
from dateutil import parser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
load_dotenv()

## Initial values from TEST TASK
countries_list = ['ua', 'us', 'gb']
start_time = datetime(year=1992, month=1, day=1)
end_time = datetime(year=1992, month=12, day=31)


class HolidayCollector:
    def __init__(self):
        self.API_key = os.getenv('CALENDARIFIC_API_KEY')
        self.API_base_URL = "https://calendarific.com/api/v2"
        self.API_holidays_url = "/holidays"
        self.logger = logging.getLogger(__name__)

        self.expected_result_path = os.path.join(os.path.dirname(__file__), 'expected_result')

    def collect(self, countries_list: list, start_time: datetime, end_time: datetime):
        years = self._generate_years_range(start_time, end_time)
        for country in countries_list:
            filtered_holidays_per_country = self._process_country_data(country, years)
            self._wrote_results(filtered_holidays_per_country, country, start_time, end_time)

    def _process_country_data(self, country: str, years: list):
        parsed_holidays = []
        for year in years:
            list_of_holidays_per_year = self._request_holidays_per_year(country, year)
            parsed_holidays.extend(self._filter_holidays_by_date(list_of_holidays_per_year, start_time, end_time))
        return parsed_holidays

    def _filter_holidays_by_date(self, list_of_holidays_per_year: list, start_time: datetime, end_time: datetime):
        start_time = start_time.replace(tzinfo=None)
        end_time = end_time.replace(tzinfo=None)

        return [
            holiday for holiday in list_of_holidays_per_year
            if start_time <= parser.parse(holiday['date']['iso']).replace(tzinfo=None) <= end_time
        ]

    def _request_holidays_per_year(self, country: str, year: datetime):
        params = {
            "api_key": self.API_key,
            "country": country,
            "year": year
        }
        data_per_requested_year = requests.get(self.API_base_URL + self.API_holidays_url, params=params)
        if not data_per_requested_year.status_code == 200:
            self.logger.error(f"Error happend during processing _request_holidays_per_year with parameters {params}\n"
                              f"response from API ->> {data_per_requested_year.text}")
            return {}

        if data_per_requested_year.json()['response'] == []:
            self.logger.error(f"Error happend during processing _request_holidays_per_year with parameters {params}\n"
                              f"response from API ->> {data_per_requested_year.text}")
            return {}
        return data_per_requested_year.json()['response'].get('holidays', {})

    def _generate_years_range(self, start_time: datetime, end_time: datetime):
        """ in case of start_time and end_time is not same year"""
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise TypeError("Both start_time and end_time must be instances of datetime.")
        if start_time > end_time:
            raise ValueError("Start time cannot be later than end time.")

        return list(range(start_time.year, end_time.year + 1))

    def _wrote_results(self,
                       filtered_holidays_per_country: list,
                       country: str,
                       start_time: datetime,
                       end_time: datetime):
        file_name = self.expected_result_path + f"/{country}_{start_time.day}-{start_time.month}-{start_time.year}_{end_time.day}-{end_time.month}-{end_time.year}.txt"
        with open(file_name, 'w') as file:
            for holiday in filtered_holidays_per_country:
                file.write(json.dumps(holiday) + "\n")


HolidayCollector().collect(countries_list, start_time, end_time)
