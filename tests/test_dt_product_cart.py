import os
import time
import pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from pages.login_page import LoginPage
from pages.add_cart_page import AddCartPage
from pages.delete_product_cart import DeleteCartPage
from utils.custom_reporter import CustomReporter
from utils.screenshot_helper import ScreenshotHelper

BASE_URL = "http://127.0.0.1:5500"

reporter = CustomReporter("Delete_Product")

def accept_alert(driver, timeout=5):
    """Chờ alert và accept nếu có"""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"[ALERT] {alert.text}")
        alert.accept()
        time.sleep(0.3)
    except TimeoutException:
        pass

@pytest.mark.parametrize("username,password,product_name", [
    ("dương thuỳ", "123", "Cà phê sữa đá")
])
def test_delete_product_case(username, password, product_name):
    driver = webdriver.Chrome()
    test_name = f"test_delete_product_{username}_{product_name}"
    status = "PASS"
    screenshot_path = ""

    try:
        # 1) Login
        login_page = LoginPage(driver)
        login_page.open(f"{BASE_URL}/log%20in/log%20in.html")
        login_page.login(username, password)
        accept_alert(driver)

        # 2) Add product
        add_page = AddCartPage(driver, BASE_URL)
        add_page.go_to_product_page()
        add_page.go_to_product_detail(product_name)
        add_page.add_to_cart(1)
        accept_alert(driver)

        # 3) Go to cart
        delete_page = DeleteCartPage(driver)
        delete_page.go_to_cart_page(BASE_URL)
        accept_alert(driver)

        # 4) Delete product
        try:
            delete_page.delete_product(product_name)
            accept_alert(driver)
        except UnexpectedAlertPresentException:
            accept_alert(driver)
            delete_page.delete_product(product_name)

        time.sleep(1)

        # 5) Verify product deleted
        product_row = delete_page.find_product_row(product_name)  # đổi tên biến row → product_row
        if product_row:  # nếu còn row thì fail
            status = "FAIL"
            screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
            reporter.log_result(
                test_name=test_name,
                inputs_dict=username,
                expected=f"Product '{product_name}' deleted successfully",
                actual=f"Product '{product_name}' still exists",
                status=status,
                screenshot_path=screenshot_path,
                extra_fields={"Product": product_name, "Action": "Delete"}
            )
            pytest.fail(f"BUG: Product '{product_name}' still exists in the cart!")
        else:
            reporter.log_result(
                test_name=test_name,
                inputs_dict=username,
                expected=f"Product '{product_name}' deleted successfully",
                actual=f"Product '{product_name}' deleted successfully",
                status=status,
                screenshot_path=screenshot_path,
                extra_fields={"Product": product_name, "Action": "Delete"}
            )

    except Exception as e:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        reporter.log_result(
            test_name=test_name,
            inputs_dict=username,
            expected=f"Product '{product_name}' deleted successfully",
            actual=f"Error: {e}",
            status=status,
            screenshot_path=screenshot_path,
            extra_fields={"Product": product_name, "Action": "Delete"}
        )
        raise

    finally:
        driver.quit()
        reporter.save_excel_report()
