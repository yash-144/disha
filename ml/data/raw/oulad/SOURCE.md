# OULAD source

Open University Learning Analytics Dataset (OULAD), anonymised student data from 22 course
presentations (2013B, 2013J, 2014B, 2014J) of the Open University, UK. About 32,600 enrolments,
10.6M VLE click rows.

- Official page: https://analyse.kmi.open.ac.uk/open_dataset (now redirects to
  https://research.stem.open.ac.uk/ouanalyse/dataset/).
- The official download link (`.../open_dataset/download`) no longer serves the zip. The file used
  here is the Internet Archive capture of that official link, taken 2025-04-30:
  `https://web.archive.org/web/20250430070439id_/https://analyse.kmi.open.ac.uk/open-dataset/download`
  (`anonymisedData.zip`, 46,750,706 bytes, SHA-256
  `90dda45037939953f979072fa70a809ebe07e90ec783c408762af7698a3825ec`). Files are dated 2015-09-25.
- Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
- Citation: Kuzilek, J., Hlosta, M., Zdrahal, Z. "Open University Learning Analytics dataset."
  Scientific Data 4, 170171 (2017). https://doi.org/10.1038/sdata.2017.171

The seven CSVs (`studentInfo`, `assessments`, `studentAssessment`, `studentRegistration`,
`studentVle`, `vle`, `courses`) are data only and are git-ignored (`ml/.gitignore`); this note is
the tracked record. Re-create the folder by downloading the zip above and `unzip -j` into it.
Converter: `python -m disha_ml.converters.oulad`. Do not commit the CSVs.
