
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from main import app


class TestRedirects(unittest.TestCase):
    def test_gni(self):
        response = app.test_client().get('/gni', follow_redirects=True)
        assert response.status_code == 200
        assert b"Welcome to Data Commons." in response.data


    def test_download(self):
        response = app.test_client().get('/download', follow_redirects=True)
        assert response.status_code == 200
        assert b"By using these API/Data" in response.data


    def test_scatter(self):
        response = app.test_client().get('/scatter', follow_redirects=True)
        assert response.status_code == 200
        assert b"Please select two variables from the left menu" in response.data


    def test_browser(self):
        response = app.test_client().get('/kg', follow_redirects=True)
        assert response.status_code == 200
        assert b"The Data Commons Graph (DCG)" in response.data


    def test_browser_with_args(self):
        response = app.test_client().get('/kg?dcid=geoId/06', follow_redirects=True)
        assert response.status_code == 200
        assert b"geoId/06" in response.data


    def test_documentation(self):
        response = app.test_client().get('/documentation', follow_redirects=False)
        assert response.status_code == 302


    def test_colab(self):
        response = app.test_client().get('/colab', follow_redirects=False)
        assert response.status_code == 302