import unittest

from harness.agents.file_patch import extract_generated_files, normalize_generated_path


class FilePatchTests(unittest.TestCase):
    def test_extracts_safe_file_blocks(self) -> None:
        response = """Notes.

```file src/index.html
<h1>Hello</h1>
```

```file src/app.js
console.log("ok");
```
"""
        files = extract_generated_files(response)
        self.assertEqual([file.path for file in files], ["src/index.html", "src/app.js"])
        self.assertIn("<h1>Hello</h1>", files[0].content)

    def test_rejects_paths_outside_src(self) -> None:
        with self.assertRaises(ValueError):
            normalize_generated_path("../secrets.env")
        with self.assertRaises(ValueError):
            normalize_generated_path("contracts/current_sprint.md")


if __name__ == "__main__":
    unittest.main()
