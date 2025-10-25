import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.login_page import LoginPage
from pages.add_cart_page import AddCartPage
from utils.data_reader import read_csv_data
from utils.screenshot_helper import ScreenshotHelper
from utils.custom_reporter import CustomReporter
from queries.add_cart_queries import (
    get_user_id_by_username,
    query_cart_items_by_user,
    clear_cart_by_user_id
)

raw = read_csv_data("data/Data_Add_Cart.csv")
test_data = []
for i, row in enumerate(raw):
    username, password, _, product_names, quantities, expected_total = row
    names = product_names.split("|")
    qtys = list(map(int, quantities.split("|")))
    test_data.append((i + 1, username.strip(), password.strip(), list(zip(names, qtys)), int(expected_total)))

reporter = CustomReporter("Add_Cart")
LOGIN_URL = "http://127.0.0.1:5500/log%20in/log%20in.html"
def _normalize_cart(lst):
    return sorted(f"{it['name'].strip()} x{it['qty']} = {int(it['price'])}" for it in lst)

@pytest.mark.parametrize("index,username,password,products,expected_total", test_data)
def test_add_cart(index, username, password, products, expected_total, driver):
    test_name = f"test_add_cart_{index}"
    status = "PASS"
    screenshot_path = ""
    actual_total = 0
    db_items = []
    ui_items = []

    user_id = get_user_id_by_username(username)
    clear_cart_by_user_id(user_id)

    lp = LoginPage(driver)
    lp.open(LOGIN_URL)
    lp.login(username, password)
    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present()).accept()
    except TimeoutException:
        pass

    cart_page = AddCartPage(driver, base_url="http://127.0.0.1:5500")
    cart_page.go_to_product_page()

    try:
        for name, qty in products:
            cart_page.go_to_product_detail(name)
            cart_page.add_to_cart(qty)
            cart_page.go_to_product_page()

        ui_items = cart_page.open_cart_and_get_items()
        actual_total = sum(item["price"] for item in ui_items)
        if actual_total != expected_total:
            raise AssertionError(f"Tổng tiền không khớp: mong đợi {expected_total}, thực tế {actual_total}")

        db_items = query_cart_items_by_user(user_id)
        if _normalize_cart(db_items) != _normalize_cart(ui_items):
            raise AssertionError(f"{test_name} DB & UI mismatch.")

    except Exception as e:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        _record_result(test_name, username, products, expected_total, actual_total, db_items, ui_items, status, screenshot_path)
        pytest.fail(f"[{test_name}] Lỗi: {e}")

    _record_result(test_name, username, products, expected_total, actual_total, db_items, ui_items, status, screenshot_path)
    assert status == "PASS"
def _record_result(test_name, username, products, expected_total, actual_total, db_items, ui_items, status, screenshot_path):
    inputs = username  # chỉ hiện tên user
    extra_info = {
        "Products": ", ".join(f"{p[0]} x{p[1]}" for p in products),
        "Expected Total": expected_total,
        "Actual Total": actual_total,
        "DB Result": ", ".join(_normalize_cart(db_items)),
        "UI Result": ", ".join(_normalize_cart(ui_items))
    }
    reporter.log_result(
        test_name=test_name,
        inputs_dict=inputs,
        expected=f"Tổng tiền: {expected_total}",
        actual=f"Tổng tiền: {actual_total}",
        status=status,
        screenshot_path=screenshot_path,
        extra_fields=extra_info
    )
def teardown_module(module):
    reporter.save_excel_report()
