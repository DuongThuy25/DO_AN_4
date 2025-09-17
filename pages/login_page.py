from selenium.webdriver.common.by import By

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.username_input = (By.ID, "username")
        self.password_input = (By.ID, "password")
        self.login_button = (By.CLASS_NAME, "login-btn")


    def open(self, url):
        self.driver.get(url)

    def login(self, username, password):

        self.driver.find_element(*self.username_input).clear()
        self.driver.find_element(*self.password_input).clear()

        if username:
            self.driver.find_element(*self.username_input).send_keys(username)
        if password:
            self.driver.find_element(*self.password_input).send_keys(password)

        self.driver.find_element(*self.login_button).click()

    def get_alert_text(self):
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return alert_text
        except:
            return ""

