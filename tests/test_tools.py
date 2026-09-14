"""Tests for file tools, permission gating, and system info tool."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_tools import ReadFileTool, WriteFileTool, ListDirTool, DeleteFileTool
from tools.system_info_tool import SystemInfoTool
from tools.permission import PermissionManager
from core.paths import DATA_DIR


class TestFileTools(unittest.TestCase):
    def setUp(self):
        self.test_filename = "isha_test_file.txt"
        self.full_path = os.path.join(DATA_DIR, self.test_filename)
        if os.path.exists(self.full_path):
            os.remove(self.full_path)

    def tearDown(self):
        if os.path.exists(self.full_path):
            os.remove(self.full_path)

    def test_write_and_read(self):
        write_tool = WriteFileTool()
        result = write_tool.run(path=self.test_filename, content="hello isha")
        self.assertTrue(result.success)

        read_tool = ReadFileTool()
        result = read_tool.run(path=self.test_filename)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "hello isha")

    def test_read_missing_file(self):
        read_tool = ReadFileTool()
        result = read_tool.run(path="this_file_does_not_exist_12345.txt")
        self.assertFalse(result.success)

    def test_list_dir(self):
        list_tool = ListDirTool()
        result = list_tool.run(path=".")
        self.assertTrue(result.success)

    def test_delete_requires_confirmation(self):
        write_tool = WriteFileTool()
        write_tool.run(path=self.test_filename, content="to be deleted")

        delete_tool = DeleteFileTool()
        self.assertTrue(delete_tool.dangerous)

        # Permission manager set to auto-deny -> file must survive
        pm = PermissionManager(require_confirmation_for_dangerous=True,
                                confirm_callback=lambda msg: False)
        result = pm.execute(delete_tool, path=self.test_filename)
        self.assertFalse(result.success)
        self.assertTrue(os.path.exists(self.full_path))

        # Permission manager set to auto-approve -> file should be removed
        pm_approve = PermissionManager(require_confirmation_for_dangerous=True,
                                        confirm_callback=lambda msg: True)
        result2 = pm_approve.execute(delete_tool, path=self.test_filename)
        self.assertTrue(result2.success)
        self.assertFalse(os.path.exists(self.full_path))

    def test_blocked_system_path(self):
        write_tool = WriteFileTool()
        result = write_tool.run(path=os.path.join(os.path.sep, "Windows", "System32", "evil.txt"),
                                 content="nope")
        self.assertFalse(result.success)


class TestSystemInfoTool(unittest.TestCase):
    def test_system_info_runs(self):
        tool = SystemInfoTool()
        self.assertFalse(tool.dangerous)
        result = tool.run()
        self.assertTrue(result.success)
        self.assertIn("OS:", result.output)


if __name__ == "__main__":
    unittest.main()
