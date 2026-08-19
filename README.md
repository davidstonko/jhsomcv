# jhsomCV

An open-source [Claude](https://claude.ai) skill that converts any curriculum vitae into the format required by the Advisory Board of the Medical Faculty (ABMF) for appointment and promotion at the **Johns Hopkins University School of Medicine**.

The Silver Book contains no CV rules of its own — it points to the ABMF CV Template and CV Instructions. This skill implements those.

## What it does

- Restructures a CV into the full **I–XII ABMF taxonomy**, with `NONE` under every empty subcategory. Nothing is deleted to make the document shorter; that is the rule candidates most often break.
- **Verifies every publication against PubMed** and classifies it from PubMed's own `PublicationType` tags rather than from where the entry happened to sit on the old CV. Case reports stop living in Original Research; supplement abstracts move to Proceedings Reports.
- Reports discrepancies instead of silently fixing them — authorship mismatches, epub citations superseded by a final volume/issue, duplicate PMIDs, indexed papers missing from the CV.
- Normalizes author initials to the indexed record across the whole document, and applies the ABMF formatting rules: bold the CV owner, underline mentees, number consecutively within each subcategory, show all authors, chronological order earliest-first.
- Writes the activity sections in **first-person active voice**, and asks what your role on each project actually was rather than inferring leadership from an author list.
- **Audits the layout before anything is delivered** — block fit against a real word-wrap simulation, horizontal spill, pagination at the scale the document actually prints at, orphaned headings, numbering continuity, geometric clipping measured from the rendered PDF, line-collision detection, and heading-gap uniformity — then fixes what it finds and re-measures.

Output is a Microsoft Word `.docx`.

## Install

Clone this repository into your Claude skills directory:

```
git clone <this-repo-url> ~/.claude/skills/jhsomcv
```

## Use

```
/jhsomcv
```

or just ask: *"put my CV in the Hopkins promotions format."* Attach the CV in any format — Word, PDF, Excel, or pasted text.

## Layout

```
SKILL.md                       the procedure
references/abmf-rules.md       the binding ABMF rules, quoted verbatim
references/word-format-spec.md page geometry from a confirmed-correct departmental CV
assets/                        the I-XII skeleton, pre-formatted
scripts/verify_pubs.py         PubMed verification and publication-type classification
scripts/taxonomy.py            the section tree
scripts/wrapcalc.py            word-wrap line counting from real font advance widths
scripts/audit_layout.py        analytic layout audit
scripts/check_clipping.py      geometric clipping detection from the rendered PDF
scripts/fix_layout.py          the render -> measure -> correct loop
scripts/build_template.py      document assembly
```

## What this does not do

It does not decide whether a CV is ready for the committee, and it will not tell you that it is. It reports what was checked, what was changed, and what still needs your judgment — Section XII, thin categories, placeholders you have to write yourself, and any content that serves a purpose outside promotion.

## License

MIT. See [LICENSE](LICENSE).
