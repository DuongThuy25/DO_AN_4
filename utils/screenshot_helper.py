import os
from datetime import datetime

class ScreenshotHelper:
    @staticmethod
    def capture(driver, test_name, folder="report/screenshots"):

        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(folder, f"{test_name}_{timestamp}.png")
        driver.save_screenshot(file_path)
        return file_path
