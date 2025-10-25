import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from pages.login_page import LoginPage
from pages.search_page import SearchPage
from queries.search_queries import query_products_by_keyword
from utils.data_reader import read_csv_data
from utils.screenshot_helper import ScreenshotHelper
from utils.custom_reporter import CustomReporter

raw_data = read_csv_data("data/Data_Search.csv")
test_data = [(i + 1, row[0].strip() if row and row[0] else "") for i, row in enumerate(raw_data)]

reporter = CustomReporter("Search")
LOGIN_URL = "http://127.0.0.1:5500/log%20in/log%20in.html"

def normalize(lst):
    return sorted(s.strip().casefold() for s in lst)

@pytest.mark.parametrize("index,keyword", test_data)
def test_search(driver, index, keyword):
    test_name = f"test_search_{index}"
    status = "PASS"
    screenshot_path = ""
    db_raw = []
    ui_raw = []

    login_page = LoginPage(driver)
    login_page.open(LOGIN_URL)
    login_page.login("dương thuỳ", "123")

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present()).accept()
    except TimeoutException:
        pass

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Sản phẩm"))
    ).click()

    try:
        db_raw = query_products_by_keyword(keyword)
        db_clean = normalize(db_raw)
    except Exception as e:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        _record_result(test_name, keyword, db_raw, ui_raw, status, screenshot_path)
        pytest.fail(f"[{test_name}] Lỗi truy vấn DB: {e}")

    try:
        search_page = SearchPage(driver)
        search_page.enter_search_keyword(keyword)
        ui_raw = search_page.get_all_products_across_pages(keyword)
        ui_clean = normalize(ui_raw)
    except Exception as e:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        _record_result(test_name, keyword, db_raw, ui_raw, status, screenshot_path)
        pytest.fail(f"[{test_name}] Lỗi lấy dữ liệu UI: {e}")

    if ui_clean != db_clean:
        status = "FAIL"
        screenshot_path = ScreenshotHelper.capture(driver, test_name, folder=reporter.screenshot_dir)
        _record_result(test_name, keyword, db_raw, ui_raw, status, screenshot_path)
        pytest.fail(
            f"[{test_name}] UI & DB mismatch.\n"
            f"DB ({len(db_clean)}): {db_clean}\n"
            f"UI ({len(ui_clean)}): {ui_clean}"
        )

    _record_result(test_name, keyword, db_raw, ui_raw, status, screenshot_path)
    assert status == "PASS"

def _record_result(test_name, keyword, db_list, ui_list, status, screenshot_path):
    inputs = keyword
    expected = f"DB: {len(db_list)} sản phẩm"
    actual = f"UI: {len(ui_list)} sản phẩm"

    extra_info = {
        "DB Result": ", ".join(db_list),
        "UI Result": ", ".join(ui_list)
    }
    reporter.log_result(
        test_name=test_name,
        inputs_dict=inputs,
        expected=expected,
        actual=actual,
        status=status,
        screenshot_path=screenshot_path,
        extra_fields=extra_info
    )

def teardown_module(module):
    reporter.save_excel_report()
