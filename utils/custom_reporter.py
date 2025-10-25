import os
import openpyxl
from datetime import datetime

class CustomReporter:
    def __init__(self, feature_name):
        self.feature_name = feature_name
        self.results = []
        self.report_dir = "reports"
        self.screenshot_dir = os.path.join(self.report_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.dynamic_fields = set()

    def log_result(self, test_name, inputs_dict, expected, actual, status, screenshot_path="", extra_fields=None):
        row = {
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Test Name": test_name,
            "Inputs": inputs_dict if isinstance(inputs_dict, str) else str(inputs_dict),
            "Expected": expected,
            "Actual": actual,
            "Status": status,
            "Screenshot": screenshot_path
        }
        if extra_fields:
            row.update(extra_fields)
            self.dynamic_fields.update(extra_fields.keys())

        self.results.append(row)

    def _get_headers(self):
        base_headers = ["Time", "Test Name", "Inputs"]
        dynamic_headers = sorted(list(self.dynamic_fields))
        end_headers = ["Expected", "Actual", "Status", "Screenshot"]
        return base_headers + dynamic_headers + end_headers

    def save_excel_report(self):
        filename = os.path.join(self.report_dir, f"test_results_{self.feature_name}.xlsx")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{self.feature_name} Results"

        headers = self._get_headers()
        ws.append(headers)

        for result in self.results:
            row = [result.get(h, "") for h in headers]
            ws.append(row)

        wb.save(filename)
        print(f" Excel report saved: {filename}")
