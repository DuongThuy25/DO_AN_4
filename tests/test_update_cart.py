import os
import pytest
import openpyxl
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.login_page import LoginPage
from pages.add_cart_page import AddCartPage
from pages.update_cart_page import UpdateCartPage
from utils.data_reader import read_excel_data
from utils.screenshot_helper import ScreenshotHelper
from utils.custom_reporter import CustomReporter

BASE_URL = "http://127.0.0.1:5500"
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Data_UpdateCart.xlsx")
raw_data = read_excel_data(DATA_FILE)

def safe_str(val):
    return str(val).strip() if val is not None else ""

test_data = []
for row in raw_data:
    test_data.append((
        safe_str(row["username"]),
        safe_str(row["password"]),
        safe_str(row["product_name"]),
        int(row["initial_quantity"] or 0),
        safe_str(row["update_action"]),
        int(row["expected_quantity"] or 0),
        int(row["expected_total"] or 0)
    ))

reporter = CustomReporter("Update_Cart")

@pytest.mark.parametrize("username,password,product_name,initial_qty,update_action,expected_qty,expected_total", test_data)
def test_update_cart(username, password, product_name, initial_qty, update_action, expected_qty, expected_total, driver):
    test_name = f"test_update_cart_{username}_{product_name}_{update_action}"
    status = "PASS"
    screenshot_path = ""
    ui_total = None

    try:
        login_page = LoginPage(driver)
        login_page.open(f"{BASE_URL}/log%20in/log%20in.html")
        login_page.login(username, password)
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present()).accept()
        except TimeoutException:
            pass

        cart_page = UpdateCartPage(driver, BASE_URL, username=username)
        cart_page.clear_cart()

        add_page = AddCartPage(driver, BASE_URL)
        add_page.go_to_product_page()
        add_page.go_to_product_detail(product_name)
        add_page.add_to_cart(initial_qty)

        cart_page.go_to_cart_page()
        row = cart_page.find_product_row(product_name)
        assert row is not None, f"Không tìm thấy {product_name} trong giỏ!"

        if update_action == "+" or update_action == "-":
            ok = cart_page.click_until_quantity(row, expected_qty)
            assert ok, f"Không đưa được qty tới {expected_qty}"
        elif update_action.lower() == "edit":
            cart_page.set_quantity_and_enter(row, expected_qty)
        else:
            raise ValueError(f"Unknown update_action: {update_action}")

        ui_total = cart_page.get_item_total_from_ui(row)
        assert ui_total == expected_total, f"Sai tổng tiền - expected {expected_total}, got {ui_total}"

    except Exception as e:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        _record_result(test_name, username, product_name, update_action, initial_qty, expected_qty, expected_total, ui_total, status, screenshot_path)
        pytest.fail(f"[{test_name}] Lỗi: {e}")

    else:
        _record_result(test_name, username, product_name, update_action, initial_qty, expected_qty, expected_total, ui_total, status, screenshot_path)


def _record_result(test_name, username, product_name, action, initial_qty, expected_qty, expected_total, actual_total, status, screenshot_path):
    extra_info = {
        "Product": product_name,
        "Action": action,
        "Initial Qty": initial_qty,
        "Expected Qty": expected_qty,
        "Expected Total": expected_total,
        "Actual Total": actual_total if actual_total is not None else ""
    }
    reporter.log_result(
        test_name=test_name,
        inputs_dict=username,
        expected=f"Tổng tiền: {expected_total}",
        actual=f"Tổng tiền: {actual_total}",
        status=status,
        screenshot_path=screenshot_path,
        extra_fields=extra_info
    )

def teardown_module(module):
    reporter.save_excel_report()
