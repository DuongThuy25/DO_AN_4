import pytest
from selenium import webdriver

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    yield driver
    driver.quit()
