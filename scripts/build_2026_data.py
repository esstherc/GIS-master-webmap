"""Build the reviewable 2026 program inventory from the untouched 2025 CSV."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "archive" / "all_msgis_institutions_2025.csv"
OUTPUT = ROOT / "data" / "all_msgis_institutions_2026.csv"
COORD_SOURCE = ROOT / "data" / "archive" / "universities_coordinates_2025.csv"
COORD_OUTPUT = ROOT / "data" / "universities_coordinates_2026.csv"
TRACK_OUTPUT = ROOT / "data" / "program_tracks_2026.csv"

# The 2025 "program count" is used only to locate a source row. It is
# regenerated after the 2026 additions and removals are complete.
REMOVED = {20, 58, 61, 93, 104, 164}

UPDATES = {
    19: {"link": "https://calvin.edu/majors-programs/master-science-geographic-information-science-gis",
         "institution type": "1 GIS Program"},
    77: {"link": "https://ess.utah.edu/graduate/mssds.php",
         "coursework": "", "Program": "MS Spatial Data Science",
         "graduation requirement": "non-thesis (portfolio)",
         "institution type": ">1 GIS Program"},
    95: {"link": "https://www.binghamton.edu/geography/graduate/"},
    97: {"link": "https://geo.appstate.edu/graduate-students/academics"},
    98: {"link": "https://cosam.auburn.edu/geosciences/students/graduate/masters-geography-environmental-studies.php"},
    108: {"link": "https://www.liberty.edu/online/arts-and-sciences/masters/geography/geographic-information-systems/",
          "institution type": ">1 GIS Program"},
    107: {"link": "https://www.k-state.edu/geography/academics/graduate/ms_geog.html"},
    115: {"link": "https://go.okstate.edu/graduate-academics/programs/masters/geography-ms"},
    120: {"link": "https://www.maxwell.syr.edu/academics/geography-and-the-environment-department/graduate-studies/master-of-arts-in-geography"},
    135: {"link": "https://www.geography.uga.edu/ma-ms-degree",
          "Program": "MA/MS Geography"},
    136: {"link": "https://geography.manoa.hawaii.edu/graduate/",
          "Program": "MA Geography (Geospatial Technologies specialization)"},
    148: {"link": "https://www.unt.edu/academics/programs/geography-masters.html",
          "Program": "MS Geography (GIS and Remote Sensing focus)"},
    160: {"link": "https://wmich.edu/environment/academics/masters",
          "Program": "MS Geography (Geographic Information Science focus)"},
    162: {"link": "https://degrees.ecu.edu/degree/geography-and-environment-ms/",
          "Program": "MS Geography and Environment (Geography concentration: geospatial techniques)"},
    166: {"link": "https://geography.ucdavis.edu/academic-programs"},
}


NEW_PROGRAMS = [
    {
        "Institution": "Colorado School of Mines",
        "id": "184",
        "link": "https://www.mines.edu/academics/graduate-academics/gis-and-geoinformatics-msnt/",
        "coursework": "https://catalog.mines.edu/graduate/programs/interdisciplinaryprograms/geographicinformationsystemgeoinformatics/",
        "Program": "MS GIS and Geoinformatics (Non-Thesis)",
        "graduation requirement": "non-thesis (applied project or professional report)",
        "internship": "/",
        "location": "online",
        "pathway": "yes",
        "duration": "30 cr",
        "program type": "professional",
        "institution type": "1 GIS Program",
    },
    {
        "Institution": "Liberty University",
        "id": "53",
        "link": "https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/",
        "coursework": "https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/",
        "Program": "MS Geographic Information Systems",
        "graduation requirement": "non-thesis (coursework and internship)",
        "internship": "required",
        "location": "online",
        "pathway": "/",
        "duration": "36 cr",
        "program type": "professional",
        "institution type": ">1 GIS Program",
    },
    {
        "Institution": "The City College of New York",
        "id": "185",
        "link": "https://www.ccny.cuny.edu/sustainability/joint-unu-ccny-ms",
        "coursework": "https://www.ccny.cuny.edu/sustainability/joint-unu-ccny-ms",
        "Program": "MS Sustainability in the Urban Environment (Joint UNU-CCNY; Geospatial Data Sciences focus)",
        "graduation requirement": "non-thesis (capstone team research project)",
        "internship": "/",
        "location": "",
        "pathway": "/",
        "duration": "30 cr",
        "program type": "mixed",
        "institution type": "GIS Concentration",
    },
]


PROGRAM_TRACKS = [
    {
        "Institution": "Liberty University",
        "Program": "MS Geographic Information Systems",
        "Track": "Cartography & Remote Sensing",
        "link": "https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/cartography-remote-sensing/",
    },
    {
        "Institution": "Liberty University",
        "Program": "MS Geographic Information Systems",
        "Track": "Commercial Logistics",
        "link": "https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/commercial-logistics/",
    },
    {
        "Institution": "Liberty University",
        "Program": "MS Geographic Information Systems",
        "Track": "Geospatial Intelligence",
        "link": "https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/geospatial-intelligence/",
    },
]


NEW_COORDINATES = [
    {
        "University": "Colorado School of Mines",
        "Latitude": "39.7504",
        "Longitude": "-105.22348",
        "Address": "1500 Illinois St, Golden, CO 80401, United States of America",
        "State": "CO",
        "City": "Golden",
    },
    {
        "University": "The City College of New York",
        "Latitude": "40.81815",
        "Longitude": "-73.95004",
        "Address": "160 Convent Avenue, New York, NY 10031, United States of America",
        "State": "NY",
        "City": "New York City",
    },
]


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        assert fields is not None
        original = list(reader)

    assert len(original) == 176, "The 2025 source changed; review mappings before rebuilding."
    numbers = [int(row["program count"]) for row in original]
    assert numbers == list(range(1, 177)), "Unexpected 2025 row identifiers."
    assert all(row["Institution"] == "University of Utah" for row in original if row["program count"] == "77")
    assert all(row["Institution"] == "Liberty University" for row in original if row["program count"] == "108")

    revised = []
    for row in original:
        source_number = int(row["program count"])
        if source_number in REMOVED:
            continue
        updated = row.copy()
        updated.update(UPDATES.get(source_number, {}))
        revised.append(updated)

        if source_number == 77:
            geography = {field: "" for field in fields}
            geography.update({
                "Institution": "University of Utah",
                "id": "167",
                "link": "https://ess.utah.edu/graduate/geography-ms.php",
                "Program": "MS Geography",
                "graduation requirement": "thesis",
                "internship": "/",
                "location": "on-site",
                "pathway": "/",
                "program type": "research",
                "institution type": ">1 GIS Program",
            })
            revised.append(geography)

    for new_program in NEW_PROGRAMS:
        new_row = {field: "" for field in fields}
        new_row.update(new_program)
        revised.append(new_row)

    for number, row in enumerate(revised, start=1):
        row["program count"] = str(number)

    assert len(revised) == 174
    assert len({row["Institution"] for row in revised}) == 140
    assert Counter(row["Institution"] for row in revised)["University of Utah"] == 2
    assert Counter(row["Institution"] for row in revised)["Liberty University"] == 2
    assert all(row["Institution"] not in {
        "Elmhurst University", "Eastern Illinois University",
        "Indiana University-Indianapolis", "Georgia Southern University",
    } for row in revised)

    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(revised)

    assert all(any(row["Institution"] == track["Institution"] and row["Program"] == track["Program"]
                   for row in revised) for track in PROGRAM_TRACKS)
    with TRACK_OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Institution", "Program", "Track", "link"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(PROGRAM_TRACKS)

    with COORD_SOURCE.open("r", encoding="utf-8-sig", newline="") as file:
        coordinate_reader = csv.DictReader(file)
        coordinate_fields = coordinate_reader.fieldnames
        assert coordinate_fields is not None
        coordinates = list(coordinate_reader)
    assert len(coordinates) == 142
    active_schools = {row["Institution"] for row in revised}
    revised_coordinates = [row for row in coordinates if row["University"] in active_schools]
    revised_coordinates.extend(NEW_COORDINATES)
    assert len(revised_coordinates) == 140
    assert {row["University"] for row in revised_coordinates} == active_schools
    with COORD_OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=coordinate_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(revised_coordinates)

    print(f"2025 program archive: {SOURCE}")
    print(f"2025 coordinate archive: {COORD_SOURCE}")
    print(f"2026 inventory: {OUTPUT}")
    print(f"2026 coordinates: {COORD_OUTPUT}")
    print(f"2026 tracks: {TRACK_OUTPUT}")
    print(f"Rows: {len(original)} -> {len(revised)}; institutions: 142 -> 140")


if __name__ == "__main__":
    main()
