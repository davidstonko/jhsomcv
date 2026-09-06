# jhsomCV

An open-source [Claude](https://claude.ai) skill that converts any curriculum vitae into the format required by the Advisory Board of the Medical Faculty (ABMF) for appointment and promotion at the **Johns Hopkins University School of Medicine**.

The Silver Book contains no CV rules of its own — it points to the ABMF CV Template and CV Instructions. This skill implements those.

## What it does

- Restructures a CV into the full **I–XII ABMF taxonomy**, with `NONE` under every empty subcategory. Nothing is deleted to make the document shorter; that is the rule candidates most often break.
- **Verifies every publication against PubMed** and classifies it from PubMed's own `PublicationType` tags rather than from where the entry happened to sit on the old CV. Case reports stop living in Original Research; supplement abstracts move to Proceedings Reports.
- Reports discrepancies instead of silently fixing them — authorship mismatches, epub citations superseded by a final volume/issue, duplicate PMIDs, indexed papers missing from the CV.
- Normalizes author initials to the indexed record across the whole document, and applies the ABMF formatting rules: bold the CV owner, underline mentees, number consecutively within each subcategory, show all authors, chronological order earliest-first.
- Writes the activity sections in **first-person active voice**, and asks what your role on each project actually was rather than inferring leadership from an author list.
- **Checks the layout before anything is delivered** — block fit, horizontal spill, pagination at the scale the document actually prints at, orphaned headings, numbering continuity, clipping, line collisions, and heading-gap uniformity. For the Word output this is a manual check of the rendered PDF against the Step 5 checklist in `SKILL.md`. The measured, self-correcting version of that audit was built for an Excel CV and is included as reference code only; see [Status and known limitations](#status-and-known-limitations).

Output is a Microsoft Word `.docx`.

## Install

The skill is the inner `jhsomcv/` folder, not the repository root. Clone the repository, then copy that folder into your Claude skills directory:

```
git clone https://github.com/davidstonko/jhsomcv.git
mkdir -p ~/.claude/skills
cp -r jhsomcv/jhsomcv ~/.claude/skills/
```

That leaves `~/.claude/skills/jhsomcv/SKILL.md`, which is where Claude Code looks for a personal skill. Cloning the repository itself into `~/.claude/skills/` puts `SKILL.md` one level too deep and Claude will not find it.

Cowork and claude.ai do not read `~/.claude/skills/`; they load the skills enabled for your claude.ai account. To use the skill there, add the same inner `jhsomcv/` folder from **Customize** in the Claude desktop app sidebar or from the skills settings on claude.ai.

The scripts need Python 3. `verify_pubs.py` uses only the standard library and internet access to PubMed. Building the document uses [python-docx](https://pypi.org/project/python-docx/) (`pip install python-docx`); Claude will install it on first use if it is missing, so this is only worth doing ahead of time on a machine that cannot install packages.

## Use

```
/jhsomcv
```

or just ask: *"put my CV in the Hopkins promotions format."* Attach the CV in any format — Word, PDF, Excel, or pasted text.

## Layout

The skill is the `jhsomcv/` folder; the repository root holds only this README and the license.

```
README.md, LICENSE
jhsomcv/                         the skill folder, which is what gets installed
  SKILL.md                       the procedure
  references/abmf-rules.md       the binding ABMF rules, quoted verbatim
  references/word-format-spec.md page geometry from a confirmed-correct departmental CV
  assets/                        the I-XII skeleton, pre-formatted
  scripts/verify_pubs.py         PubMed verification and publication-type classification
  scripts/taxonomy.py            the section tree
  scripts/wrapcalc.py            word-wrap line counting from real font advance widths
  scripts/p052_widths.json       the advance widths wrapcalc.py reads
  scripts/build_template.py      generates the blank template in assets/ from taxonomy.py
  scripts/excel-reference/       the measured layout audit for an Excel build, reference only:
    audit_layout.py              analytic layout audit
    check_clipping.py            geometric clipping detection from the rendered PDF
    fix_layout.py                the render -> measure -> correct loop
```

## Status and known limitations

This was extracted from a one-off reformatting of a single CV and has not been generalized much beyond it. What is automated and what is not:

- **Automated.** PubMed verification and publication-type classification (`scripts/verify_pubs.py`), the section tree (`scripts/taxonomy.py`), and generation of the blank I–XII template (`scripts/build_template.py`).
- **Manual.** The layout check for the Word output. Nothing in this repository measures a `.docx`. Render it to PDF and inspect at least the first page, a dense publications page, and the last page against the checklist in Step 5 of `SKILL.md`.
- **Reference only.** `scripts/excel-reference/` is the measured layout audit (word-wrap simulation, clipping and line-collision detection from the rendered PDF, then a grow-and-trim fix loop) as it was implemented for an Excel build of the same CV. It needs `openpyxl`, poppler's `pdftotext`, and a renderer of your own that turns the workbook into a PDF; `fix_layout.py` takes that renderer as `--build CMD` and stops with a message if it is not given one. It does not run against a `.docx`.
- **Calibrated to Excel.** `scripts/wrapcalc.py` counts wrapped lines from real font advance widths, which is the right method for any format, but as shipped its constants are Book Antiqua 14 pt in Excel column-width units, with Palatino-compatible widths in `p052_widths.json`. A Times New Roman 11 pt Word build needs its own width table and a line width in points before its output means anything.
- The rest of `SKILL.md` is procedure that Claude follows by hand, and the ABMF rules in `references/` are quoted from the template and instructions current when this was written. Check them against the version the committee is using before you rely on them.

## What this does not do

It does not decide whether a CV is ready for the committee, and it will not tell you that it is. It reports what was checked, what was changed, and what still needs your judgment — Section XII, thin categories, placeholders you have to write yourself, and any content that serves a purpose outside promotion.

## License

MIT. See [LICENSE](LICENSE).
