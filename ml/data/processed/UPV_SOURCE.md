# upv_first_year.csv — source and licence

Derived from: Igualde-Sáez, A.; Maheut, J.; Garcia-Sabater, J. P.; Marin-Garcia, J. A.;
Turró, C.; Despujol Zabala, I.; Puche García, S.; Alonso, M.; Benlloch-Dualde, J. V.;
Soriano Jiménez, P. P. *StudentDropoutDataset*. Zenodo, 2025.
https://doi.org/10.5281/zenodo.17239943 — licensed CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/).

Changes made: kept first-year bachelor's students from the 2018, 2021 and 2022 files;
aggregated course rows to one row per student; converted credits to subject
equivalents (÷ 6); averaged course grades and rescaled to 0–20; averaged monthly
campus Wi-Fi days per semester; mapped `abandono_hash` A/B to Dropout/Retained;
dropped all other fields. Produced by `ml/disha_ml/converters/upv.py`.
Identifiers are the hashed values published in the source.
