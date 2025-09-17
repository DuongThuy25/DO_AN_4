import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


class AddCartPage:
    LINK_SAN_PHAM = (By.LINK_TEXT, "Sản phẩm")
    CARD = (By.CSS_SELECTOR, ".card")
    CARD_TITLE = (By.CSS_SELECTOR, ".card-title")
    BTN_ADD_TO_CART_ID = (By.ID, "add-to-cart")
    BTN_ADD_TO_CART_CSS = (By.CSS_SELECTOR, "a.btn.btn-outline-success")
    PRODUCT_TITLE = (By.ID, "product-title")
    INPUT_QUANTITY = (By.ID, "quantity")
    CART_LINK = (By.CSS_SELECTOR, "a[href*='cart']")
    CART_ITEM_ROW = (By.CSS_SELECTOR, ".cart-item-row")
    CART_ITEM_NAME = (By.CSS_SELECTOR, "p.m-0")
    CART_ITEM_QTY = (By.CSS_SELECTOR, "input.quantity")
    CART_ITEM_PRICE = (By.CSS_SELECTOR, ".total-price")

    CART_ITEM_BY_NAME = lambda self, name: (
        By.XPATH,
        f"//div[contains(@class, 'cart-item-row')][.//p[@class='m-0' and normalize-space(text())='{name}']]"
    )

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def go_to_product_page(self):
        self.driver.get(f"{self.base_url}/product-list/product-list.html")
        self.wait.until(EC.presence_of_element_located(self.LINK_SAN_PHAM))

    def go_to_product_detail(self, product_name):
        self.driver.find_element(*self.LINK_SAN_PHAM).click()
        self.wait.until(EC.presence_of_all_elements_located(self.CARD))

        for card in self.driver.find_elements(*self.CARD):
            title = card.find_element(*self.CARD_TITLE).text.strip()
            if product_name.strip().lower() == title.lower():
                try:
                    btn = card.find_element(*self.BTN_ADD_TO_CART_ID)
                except Exception:
                    btn = card.find_element(*self.BTN_ADD_TO_CART_CSS)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                self.wait.until(EC.presence_of_element_located(self.PRODUCT_TITLE))
                return
        raise ValueError(f"Không tìm thấy sản phẩm: {product_name}")

    def add_to_cart(self, quantity: int):
        qty_input = self.wait.until(EC.presence_of_element_located(self.INPUT_QUANTITY))
        qty_input.clear()
        qty_input.send_keys(str(quantity))

        add_btn = self.wait.until(EC.element_to_be_clickable(self.BTN_ADD_TO_CART_ID))
        try:
            add_btn.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", add_btn)

        try:
            self.wait.until(EC.alert_is_present()).accept()
        except TimeoutException:
            pass

    def _parse_price_to_int(self, price_text: str) -> int:

        cleaned = re.sub(r"\D", "", price_text)
        return int(cleaned) if cleaned else 0

    def open_cart_and_get_items(self):

        cart_link = self.wait.until(EC.element_to_be_clickable(self.CART_LINK))
        cart_link.click()

        self.wait.until(EC.url_contains("cart"))
        self.wait.until(EC.presence_of_all_elements_located(self.CART_ITEM_ROW))

        items = []
        for elem in self.driver.find_elements(*self.CART_ITEM_ROW):
            name = elem.find_element(*self.CART_ITEM_NAME).text.strip()
            qty = int(elem.find_element(*self.CART_ITEM_QTY).get_attribute("value").strip())

            price_elem = elem.find_element(*self.CART_ITEM_PRICE)
            price_text = price_elem.get_attribute("data-totalprice") or price_elem.text
            total_price = self._parse_price_to_int(price_text)
            unit_price = total_price // qty if qty > 0 else total_price

            items.append({
                "name": name,
                "qty": qty,
                "unit_price": unit_price,
                "price": total_price
            })
        return items

    def get_cart_item_by_product_name(self, product_name):
        return self.wait.until(
            EC.visibility_of_element_located(self.CART_ITEM_BY_NAME(product_name))
        )
