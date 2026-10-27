# excel-reference

Reference implementation of the measured layout audit, as built for an Excel version of the same CV. The skill's deliverable is a Word `.docx`, and none of this runs against one; it is here so the method in Step 5 of `SKILL.md` can be read as working code rather than description.

- `audit_layout.py` analytic audit: block fit from a word-wrap simulation, page overflow, orphaned headings, numbering, stray columns, fonts. Optionally cross-checks against the rendered PDF.
- `check_clipping.py` geometric clipping and slack, measured from the rendered PDF.
- `fix_layout.py` the render, measure, correct loop: grows blocks that clip or collide, then trims the rows it can take back.

They need `openpyxl`, poppler's `pdftotext`, `../wrapcalc.py` with `../p052_widths.json`, and a renderer of your own that turns the workbook into a PDF. `fix_layout.py` takes that renderer as `--build CMD` or `JHSOMCV_BUILD`; nothing here supplies one. The sheet geometry (column widths, row height, print scale, the `CURRICULUM` / `Date` calibration anchors) is that of the original workbook and is hard-coded.

## Rendering on macOS

The calibration assumes LibreOffice draws Book Antiqua with URW P052's metrics. On Linux a fontconfig alias does it. On macOS there is a trap: with P052 installed in `~/Library/Fonts` (`brew install --cask font-urw-base35`), LibreOffice 26.8 still did not use it, not even for a cell set to P052 by name. It fell back to Linux Libertine without a warning, so the PDF no longer matched the workbook's geometry: `check_clipping.py` reported 161 blocks it could not trace, and every wrap was suspect. Clearing the quarantine attribute did not help. What works:

1. Use a dedicated profile, `soffice -env:UserInstallation=file:///path/to/profile ...`, so the CV build does not change the person's own LibreOffice.
2. Copy the four `P052-*.otf` files into `<profile>/user/fonts/`. LibreOffice loads fonts from there.
3. In `<profile>/user/registrymodifications.xcu`, substitute P052 for Book Antiqua under `/org.openoffice.Office.Common/Font/Substitution` (`Replacement` true; a `FontPairs` node with `ReplaceFont` Book Antiqua, `SubstituteFont` P052, `Always` true, `OnScreenOnly` false). The path is not `org.openoffice.VCL/FontSubstitutions`, which LibreOffice ignores for this.

Check with `pdffonts preview.pdf`: it should list `P052-Roman`, `P052-Bold` and `P052-Italic`, with no Linux Libertine. With this setup, a CV last rendered by LibreOffice 24.2 on Linux re-rendered on macOS with LibreOffice 26.8 with the same 20 page breaks and the same words on every page, and 0 clipped or untraced blocks. The only differences were five places where a hyphenated word or URL broke at a different point.

## Even spacing: size blocks to their text, in whole pixels

A wrapped cell's lines print closer together than the rows they sit in. With Book Antiqua/P052 14 pt the lines are 14 pt apart, but the rows are 19.5 pt. A block of n uniform rows therefore leaves (n − 1) × 5.5 pt of white under its text, so the gap after an entry grows with its length: one-line entries sit tight on the next one, and three-line entries leave a visible hole. Reviewers notice this. Size each block to its text instead: numbered entries n × 14 pt plus a fixed gap, dated rows 19.5 pt plus 14 pt per extra line.

Two consequences:

- **Use whole pixels.** LibreOffice draws each row rounded down to a whole pixel (0.75 pt at 96 dpi): measured, 17.67 pt prints as 17.25 and 14.0 as 13.5. With odd heights the error builds up down the page, 7 pt by the foot, and the audit stops tracing blocks. Split each block's total into whole-pixel rows that add up to it.
- **Measure in height, not rows.** Page capacity becomes a height. `check_clipping.py` now reads each row's real height. It reports spare space in units of `JHSOMCV_LINE_PT` (the line pitch, default the row height), after allowing `JHSOMCV_GAP_PT` of intended white under each entry. With uniform rows and neither variable set, it behaves exactly as before.
