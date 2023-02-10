import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

tree = ET.parse("cov.xml")
root = tree.getroot()

cov = float(root.attrib["line-rate"]) * 100
covp = quote(f"{cov:.0f}%")

if 0 < cov <= 60:
    color = "red"
elif 60 < cov < 85:
    color = "orange"
else:
    color = "green"

file = Path("README.md")
old_part = r"badge/coverage-.+?-.+?\)"
new_part = rf"badge/coverage-{covp}-{color})"
content = file.read_text()
content = re.sub(old_part, new_part, content)
file.write_text(content)
