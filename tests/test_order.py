import os, csv, unicodedata, time, pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.login_page import LoginPage
from pages.order_page import OrderPage
from pages.add_cart_page import AddCartPage
from queries.add_cart_queries import get_user_id_by_username
from queries.order_queries import get_user_info_by_id, get_order_details_by_order_id, get_latest_order_from_db
from utils.custom_reporter import CustomReporter
from utils.screenshot_helper import ScreenshotHelper

BASE_URL = "http://127.0.0.1:5500"
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Data_Order.csv")

# Reporter cho Order
reporter = CustomReporter("Order")

def read_csv():
    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            clean_row = {}
            for k, v in r.items():
                if k:
                    clean_row[k.strip().lower()] = v
            rows.append(clean_row)
        return rows

def parse_row(row):
    test_id = row.get("test_id", "").strip()
    username = row.get("username", "").strip()
    password = row.get("password", "").strip()
    address = row.get("address", "").strip()
    expected_note = row.get("expected_note", "").strip()
    product_names = [p.strip() for p in row.get("product_name","").split("|")] if row.get("product_name") else []
    quantities = [int(q.strip()) for q in row.get("quantities","").split("|")] if row.get("quantities") else []
    products = list(zip(product_names, quantities))
    return test_id, username, password, products, address, expected_note

test_data = [parse_row(r) for r in read_csv()]

def norm(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFC", s)
    return " ".join(s.split()).strip()

@pytest.mark.parametrize("test_id, username, password, products, address, expected_note", test_data)
def test_order_flow(test_id, username, password, products, address, expected_note):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    status = "PASSED"
    error_message = ""
    screenshot_path = ""
    start_time = datetime.now()
    addr_validation_msg = ""
    order_msg = ""

    try:
        # login
        login_page = LoginPage(driver)
        driver.get(f"{BASE_URL}/log%20in/log%20in.html")
        login_page.login(username, password)
        try: wait.until(EC.alert_is_present()).accept()
        except TimeoutException: pass

        # clear cart + orders
        user_id = get_user_id_by_username(username)
        order_page = OrderPage(driver, BASE_URL, user_id=user_id)
        order_page.clear_cart(user_id, clear_orders_too=True)

        # add products
        add_page = AddCartPage(driver, BASE_URL)
        for product_name, qty in products:
            add_page.go_to_product_page()
            add_page.go_to_product_detail(product_name)
            add_page.add_to_cart(qty)

        # checkout
        order_page.go_to_cart_page()
        order_page.select_all_and_checkout()
        time.sleep(0.5)

        # verify customer info
        db_user = get_user_info_by_id(user_id)
        customer_info = order_page.get_customer_info()
        if db_user:
            if db_user.get("username"): assert norm(customer_info["name"]) == norm(db_user.get("username"))
            if db_user.get("phone_number"): assert norm(customer_info["phone"]) == norm(db_user.get("phone_number"))
            if db_user.get("email"): assert norm(customer_info["email"]) == norm(db_user.get("email"))

        # case thiếu địa chỉ
        if not address:
            order_page.enter_address_and_checkout("")
            addr_validation_msg = order_page.get_address_error_message().strip()
            if expected_note: assert norm(addr_validation_msg) == norm(expected_note)
            else: assert addr_validation_msg != ""
            status = "PASSED"
            return

        # đặt hàng
        order_page.enter_address_and_checkout(address)
        order_msg = order_page.get_toast_message().strip()
        assert norm(order_msg) == norm(expected_note)

        # so sánh UI ↔ DB
        STATUS_MAP = {
            "pending": "chưa hoàn thành",
            "completed": "hoàn thành",
            "cancelled": "đã hủy"
        }
        ui_order = order_page.get_latest_order_from_ui()
        db_order = get_latest_order_from_db(user_id)

        assert ui_order is not None, "Không tìm thấy đơn hàng trên UI"
        assert db_order is not None, "Không tìm thấy đơn hàng trong DB"
        assert ui_order["order_id"] == db_order["order_id"]

        db_status = db_order["status"].strip().lower()
        expected_ui_status = STATUS_MAP.get(db_status, db_status)
        ui_status = ui_order["status"].strip().lower()
        assert ui_status == expected_ui_status, f"Status mismatch: UI='{ui_status}', DB='{db_status}'"

        # tổng tiền
        def normalize_amount(val: str) -> int:
            digits = "".join(ch for ch in val if ch.isdigit())
            return int(digits) if digits else 0

        ui_amount = normalize_amount(ui_order["total_amount"])
        db_amount = int(float(db_order["total_amount"]))
        assert ui_amount == db_amount, f"Total mismatch: UI='{ui_order['total_amount']}', DB='{db_order['total_amount']}'"

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        screenshot_path = ScreenshotHelper.capture(driver, f"order_{test_id}", folder=reporter.screenshot_dir)
        pytest.fail(f"[{test_id}] Error: {e}")
    finally:
        # ghi báo cáo giống UpdateCart/Delete
        reporter.log_result(
            test_name=f"order_{test_id}",
            inputs_dict=username,
            expected=expected_note,
            actual=addr_validation_msg or order_msg or error_message,
            status=status,
            screenshot_path=screenshot_path,
            extra_fields={
                "Products": str(products),
                "Address": address
            }
        )
        driver.quit()
        reporter.save_excel_report()
