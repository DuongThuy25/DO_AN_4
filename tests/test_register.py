import pytest
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException

from pages.register_page import RegisterPage
from utils.data_reader import read_excel_data
from utils.screenshot_helper import ScreenshotHelper
from utils.custom_reporter import CustomReporter


test_data = read_excel_data("data/Data_Register.xlsx")
REGISTER_URL = "http://127.0.0.1:5500/log%20in/register.html"


reporter = CustomReporter("Register")

@pytest.mark.parametrize(
    "index,username,email,password,sdt,expected_result",[(i + 1,
            row["Username"],
            row["Email"],
            row["Password"],
            row["SDT"],
            row["ExpectedResult"])
        for i, row in enumerate(test_data)])

def test_register(driver, index, username, email, password, sdt, expected_result):
    register_page = RegisterPage(driver)
    register_page.open(REGISTER_URL)
    register_page.register(username, email, password, sdt)

    test_name = f"test_register_{index}"
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

    inputs = {
        "Username": username,
        "Email": email,
        "Password": password,
        "SDT": sdt
    }
    reporter.log_result(
        test_name=test_name,
        inputs_dict=inputs,
        expected=expected_result,
        actual=actual_result,
        status=status,
        screenshot_path=screenshot_path
    )

    assert status == "PASS", f"[{test_name}] Expected: {expected_result}, but got: {actual_result}"

def teardown_module(module):
    reporter.save_excel_report()

