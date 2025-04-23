import unittest
import tempfile
from utils.file_extract import extract_text_from_file

class TestFileExtract(unittest.TestCase):

    def test_docx_extract(self):
        import docx
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tf:
            doc = docx.Document()
            doc.add_paragraph("Sample DOCX text")
            doc.save(tf.name)
            text = extract_text_from_file(tf.name, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            self.assertIn("Sample DOCX text", text)

if __name__ == "__main__":
    unittest.main()
