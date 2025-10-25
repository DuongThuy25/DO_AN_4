import os
import pytest
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException

from utils.data_reader import read_excel_data
from utils.custom_reporter import CustomReporter
from utils.screenshot_helper import ScreenshotHelper
from pages.login_page import LoginPage

test_data = read_excel_data("data/Data_Login.xlsx")
reporter = CustomReporter("Login")
LOGIN_URL = "http://127.0.0.1:5500/log%20in/log%20in.html"


@pytest.mark.parametrize(
    "index,username,password,expected_result",
    [(i+1, row["Username"], row["Password"], row["ExpectedResult"]) for i, row in enumerate(test_data)]
)
def test_login(driver, index, username, password, expected_result):
    login_page = LoginPage(driver)
    login_page.open(LOGIN_URL)
    login_page.login(username, password)

    test_name = f"test_login_{index}"
    actual_result = ""
    status = "FAIL"
    screenshot_path = ""

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        actual_result = alert.text
        alert.accept()

        if actual_result == expected_result:
            status = "PASS"
        else:
            raise AssertionError("Actual result doesn't match expected result.")

    except (TimeoutException, UnexpectedAlertPresentException, AssertionError) as e:
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        if not actual_result:
            actual_result = str(e)

    inputs = {"username": username, "password": password}
    reporter.log_result(test_name, inputs, expected_result, actual_result, status, screenshot_path)

    assert status == "PASS", f"[{test_name}] Expected: {expected_result}, but got: {actual_result}"

def teardown_module(module):
    reporter.save_excel_report()

