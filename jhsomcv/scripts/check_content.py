#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Content checks on a fill_template.py content.json, before building the document.

The layout audit (Step 5) measures how the CV prints; this checks what it says, against the rules in
references/abmf-rules.md that can be checked mechanically:

  ETAL      "et al." anywhere. The template says "Please show all authors for all articles"; that covers
            abstracts, posters and podium entries too, not only Original Research.
  OWNER     a citation-style entry (numbered, in PUBLICATIONS or Section XII) with none of the owner's name
            forms in it. Usually an author list cut before the owner, sometimes a namesake.
  STATUS    submitted / in preparation / under review in PUBLICATIONS ("Include only those published or
            in press").
  FOCUS     Clinical Focus over 100 words ("Provide up to 100 word narrative"). The other focus statements
            have no stated limit.
  ORDER     an entry dated earlier than the one before it ("earliest first by start date under each
            subcategory"). Citations are dated by the year in their source details (2024;80(4) or 2024 Jan),
            never by the first year in the text: titles such as "From 2015 to 2019" carry years too.

Every hit is a candidate for the person to confirm, not an automatic fix.

Usage:  python3 check_content.py content.json        exit status 1 if anything was flagged
"""
import json, re, sys

MONTHS = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'


def cite_year(text):
    """Year of a citation from its source details, else None."""
    for pat in (r'\b((?:19|20)\d\d)\s*;', r'\b((?:19|20)\d\d)\s+(?:%s)\b' % MONTHS, r'\b((?:19|20)\d\d)\.\s*(?:Epub|In press|$)'):
        hits = re.findall(pat, text)
        if hits:
            return int(hits[-1])
    return None


def entry_year(e):
    if e.get('date'):
        m = re.search(r'(?:19|20)\d\d', e['date'])
        return int(m.group(0)) if m else None
    if e.get('kind') == 'num':
        return cite_year(e.get('text', ''))
    return None


def check(content):
    owner = content.get('owner') or []
    out = []
    for leaf, entries in content.get('sections', {}).items():
        up = leaf.upper()
        is_pub = up.startswith('PUBLICATIONS')
        is_xii = up.startswith('OTHER PROFESSIONAL ACCOMPLISHMENTS')
        prev = None
        for i, e in enumerate(entries):
            text = e.get('text') or e.get('title') or ''
            if e.get('kind') == 'sub':
                prev = None
                continue
            tag = '%s #%d' % (leaf, i + 1)
            if re.search(r'\bet al\b', text):
                out.append(('ETAL', tag, text))
            if e.get('kind') == 'num' and (is_pub or is_xii) and owner and not any(o in text for o in owner):
                out.append(('OWNER', tag, text))
            if is_pub and re.search(r'(?i)\b(submitted|in preparation|under review)\b', text):
                out.append(('STATUS', tag, text))
            y = entry_year(e)
            if y is not None:
                if prev is not None and y < prev:
                    out.append(('ORDER', tag, '%d after %d: %s' % (y, prev, text)))
                prev = y
        if leaf.split('>')[-1].strip().lower() == 'clinical focus':
            words = sum(len((e.get('text') or '').split()) for e in entries)
            if words > 100:
                out.append(('FOCUS', leaf, '%d words (limit 100)' % words))
    return out


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    hits = check(json.load(open(sys.argv[1])))
    for code, where, text in hits:
        print('%-6s %s\n       %s' % (code, where, text[:200]))
    print('%d flagged' % len(hits))
    sys.exit(1 if hits else 0)
