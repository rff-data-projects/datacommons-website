# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from parameterized import parameterized
import os
import unittest
from unittest.mock import patch
import lib.config as libconfig


class TestConfig(unittest.TestCase):

    @parameterized.expand([
        ('test', {
            'TEST': True,
            'WEBDRIVER': False,
            'DEVELOPMENT': False,
            'LITE': False,
            'SVOBS': False,
            'CACHE_TYPE': 'simple',
            'API_ROOT': 'api-root',
            'GCS_BUCKET': 'gcs-bucket',
            'SECRET_PROJECT': '',
            'GA_ACCOUNT': '',
            'MAPS_API_KEY': '',
            'SCHEME': 'http',
        }),
        ('development', {
            'TEST': False,
            'WEBDRIVER': False,
            'DEVELOPMENT': True,
            'LITE': False,
            'SVOBS': False,
            'CACHE_TYPE': 'simple',
            'API_ROOT': 'https://autopush.api.datacommons.org',
            'GCS_BUCKET': 'datcom-website-autopush-resources',
            'SECRET_PROJECT': 'datcom-website-dev',
            'GA_ACCOUNT': '',
            'MAPS_API_KEY': '',
            'SCHEME': 'http',
        }),
        ('development-lite', {
            'TEST': False,
            'WEBDRIVER': False,
            'DEVELOPMENT': True,
            'LITE': True,
            'SVOBS': False,
            'CACHE_TYPE': 'simple',
            'API_ROOT': 'https://autopush.api.datacommons.org',
            'GCS_BUCKET': '',
            'SECRET_PROJECT': '',
            'GA_ACCOUNT': '',
            'MAPS_API_KEY': '',
            'SCHEME': 'http',
        }),
        ('development-svobs', {
            'TEST':
                False,
            'WEBDRIVER':
                False,
            'DEVELOPMENT':
                True,
            'LITE':
                False,
            'SVOBS':
                True,
            'CACHE_TYPE':
                'simple',
            'API_ROOT':
                'https://mixer.endpoints.datcom-mixer-statvar.cloud.goog',
            'GCS_BUCKET':
                'datcom-website-statvar-migrate-resources',
            'SECRET_PROJECT':
                'datcom-website-statvar-migrate',
            'GA_ACCOUNT':
                '',
            'MAPS_API_KEY':
                '',
            'SCHEME':
                'http',
        }),
        ('webdriver', {
            'TEST': False,
            'WEBDRIVER': True,
            'DEVELOPMENT': False,
            'LITE': False,
            'SVOBS': False,
            'CACHE_TYPE': 'simple',
            'API_ROOT': 'https://staging.api.datacommons.org',
            'GCS_BUCKET': '',
            'SECRET_PROJECT': 'datcom-website-dev',
            'GA_ACCOUNT': '',
            'MAPS_API_KEY': '',
            'SCHEME': 'http',
        })
    ])
    def test_format_title(self, env, expected):
        with patch.dict(os.environ, {
                "FLASK_ENV": env,
        }):
            self.assertConfigEqual(libconfig.get_config(), expected)

    def assertConfigEqual(self, config, expected):
        self.assertEqual(config.TEST, expected['TEST'])
        self.assertEqual(config.WEBDRIVER, expected['WEBDRIVER'])
        self.assertEqual(config.DEVELOPMENT, expected['DEVELOPMENT'])
        self.assertEqual(config.LITE, expected['LITE'])
        self.assertEqual(config.SVOBS, expected['SVOBS'])
        self.assertEqual(config.CACHE_TYPE, expected['CACHE_TYPE'])
        self.assertEqual(config.API_ROOT, expected['API_ROOT'])
        self.assertEqual(config.GCS_BUCKET, expected['GCS_BUCKET'])
        self.assertEqual(config.SECRET_PROJECT, expected['SECRET_PROJECT'])
        self.assertEqual(config.GA_ACCOUNT, expected['GA_ACCOUNT'])
        self.assertEqual(config.MAPS_API_KEY, expected['MAPS_API_KEY'])
        self.assertEqual(config.SCHEME, expected['SCHEME'])
