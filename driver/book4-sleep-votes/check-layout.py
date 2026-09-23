#!/usr/bin/env python3
"""Check observer private layouts against a matching configured kernel source"""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('kernel', type=Path)
args = parser.parse_args()
observer = Path(__file__).with_name('sleep-votes.c').read_text()
for name, relative, ending in (
    ('clk_core', 'drivers/clk/clk.c', r'unsigned int\s+prepare_count;'),
    ('cache_req', 'drivers/soc/qcom/rpmh.c', r'^};'),
    ('batch_cache_req', 'drivers/soc/qcom/rpmh.c', r'^};'),
):
    pattern = rf'struct {name}\s*\{{.*?{ending}'
    actual = []
    for text in (observer, (args.kernel / relative).read_text()):
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        match = re.search(pattern, text, re.S | re.M)
        assert match, f'missing {name}'
        actual.append(re.findall(r'\w+|\S', match[0]))
    assert actual[0] == actual[1], f'private layout changed: {name}'
print('Observer private-layout declarations match, matching config/build still required')
