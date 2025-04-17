import unittest
from mistletoe import Document
from typst_renderer import TypstRenderer


class TypstRendererTest(unittest.TestCase):
    def test_document(self):
        with open("test_typst_renderer.md", "r") as file:
            md = file.read()
        with open("test_typst_renderer.typ", "r") as file:
            expected = file.read()    

        renderer = TypstRenderer()
        doc = Document(md)
        output = renderer.render(doc)
        print(output)
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()