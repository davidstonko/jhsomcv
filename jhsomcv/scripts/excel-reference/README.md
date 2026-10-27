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
