import os
import tempfile
import unittest
from unittest import mock

import convert_to_wechat


class ConvertLocalImagePathTest(unittest.TestCase):
    def test_existing_absolute_local_image_is_made_relative_to_preview(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            article_dir = os.path.join(temp_dir, "article")
            image_dir = os.path.join(article_dir, "images")
            preview_dir = os.path.join(temp_dir, "preview", "articles")
            os.makedirs(image_dir)
            os.makedirs(preview_dir)

            image_path = os.path.join(image_dir, "example.png")
            with open(image_path, "wb") as image_file:
                image_file.write(b"not-a-real-png")

            markdown_path = os.path.join(article_dir, "article.md")
            with open(markdown_path, "w", encoding="utf-8") as markdown_file:
                markdown_file.write(f"![示例图]({image_path})\n")

            html_path = os.path.join(preview_dir, "article.html")
            with mock.patch("subprocess.run"):
                convert_to_wechat.convert_file(markdown_path, html_path)

            with open(html_path, "r", encoding="utf-8") as html_file:
                rendered_html = html_file.read()

            expected_src = os.path.relpath(image_path, preview_dir)
            self.assertIn(f'src="{expected_src}"', rendered_html)
            self.assertNotIn(f'src="{image_path}"', rendered_html)


if __name__ == "__main__":
    unittest.main()
