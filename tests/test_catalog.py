import tempfile
import unittest
from pathlib import Path
from skill_meta.cli import SkillCatalog

class CatalogTest(unittest.TestCase):
    def test_discover_search_load_and_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/"a"; b=Path(tmp)/"b"
            for root,desc in [(a,"Design iOS screens"),(b,"shadowed")]:
                d=root/"ios-design"; d.mkdir(parents=True)
                (d/"SKILL.md").write_text("---\nname: ios-design\ndescription: "+desc+"\n---\nUse adjacent references.")
            c=SkillCatalog([str(a),str(b)])
            self.assertEqual(c.search("ios")[0]["description"],"Design iOS screens")
            self.assertIn("adjacent",c.get_skill_content("ios-design")["content"])
            self.assertIsNone(c.get_skill_content("missing"))

if __name__ == "__main__": unittest.main()
