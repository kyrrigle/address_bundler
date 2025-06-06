
# Address Bundler

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

A CLI tool for organizing, geocoding, and bundling addresses for efficient delivery or distribution. Generates maps and PDFs for each bundle, making logistics simple for schools, campaigns, and organizations.

---

## Features

- Project-based workflow for managing multiple address lists
- Import CSVs with student or address data
- Geocode addresses and manually fix errors
- Cluster addresses into delivery bundles using K-Means
- Generate color-coded maps and printable PDFs for each bundle
- Simple, scriptable CLI interface

---

## Requirements

- Python 3.10 or higher
- pip

---

## Installation

```bash
git clone https://github.com/your-org/address_bundler.git
cd address_bundler
poetry install
eval $(poetry env activate)
# Now "ab" is on your PATH (via the Poetry environment)
```

> Tip The executable is called ab (short for address bundler) and is placed on your $PATH by the install step above.

**Using Poetry**

- If you don't have Poetry, install it with:
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- To add dependencies, use `poetry add <package>`.
- To run scripts or commands in the Poetry environment, use `poetry run <command>`.

---

## Getting Started

1. **Create or switch to a project:**
   ```bash
   ab work on my-project
   ```
2. **Import your address CSV:**
   ```bash
   ab import test-data/fake-student-addresses.csv
   ```
3. **Geocode addresses:**
   ```bash
   ab geocode
   ```
4. **Fix any addresses that failed geocoding:**
   ```bash
   ab fix addresses
   ```
5. **Cluster addresses into bundles:**
   ```bash
   ab cluster
   ```
6. **Generate maps and PDFs:**
   ```bash
   ab generate
   ```

---

## Project structure

Once the package is installed you’ll have:

```
address_bundler/        ← Core Python package
test-data/              ← Example CSV for experimentation
projects/               ← Created at runtime; one sub-dir per “project”
```

Each project holds its own project.yaml, generated maps, and PDFs.
Use `ab work on <project-name>` to create or switch between projects.

## CLI usage

The built-in help reproduced from address_bundler/main.py:

```
Usage:
    address-bundler [options] work on <project>
    address-bundler [options] configure
    address-bundler [options] import <file>
    address-bundler [options] geocode
    address-bundler [options] fix addresses
    address-bundler [options] cluster
    address-bundler [options] generate [maps|pdfs]

Options:
    --help -h             Print this message
    --debug               Debug logging
    --projects-root DIR   Projects directory [default: ./projects]

Commands
work on <project>   Create / switch to a project inside --projects-root  
configure           Interactive re-configuration of the current project  
import <file>       Import student CSV (requires “First Name”, “Last Name”, “Address”)  
geocode             Look up lat/long for any un-geocoded addresses  
fix addresses       Manually correct addresses that failed geocoding  
cluster             Run K-Means & group addresses into bundles  
generate maps       Produce PNG maps (master showing all addresses and per bundle)  
generate pdfs       Produce PDFs (master list + one per bundle)  
generate            Shortcut: generate maps **then** pdfs
```

## Worked example

Below is a full run that mirrors what you’d see in practice.
Lines starting with `$` are commands; the rest is program output.

```
$ ab work on washout-hs
Configure project settings (press Enter to keep current value)
School name: Washout High School
Bundle size [20]:
Configuration saved to project.yaml
Now working on project: washout-hs

$ ab import test-data/fake-student-addresses.csv
Imported 200 students.

$ ab geocode
WARNING: No geocode result for '29 HAWTHORNE ROAD MILTON 02186'
Geocoded 199/200 address(es).

$ ab fix addresses
Student: William Tate
Current address: 29 HAWTHORNE ROAD MILTON 02186
Enter new address (leave blank to keep):
Enter latitude,longitude (leave blank to skip): 42.264221011090434, -71.09083147395177
Saved.

$ ab cluster
Cluster 2: 79 students
  Bundle 2-A: 17 students
  Bundle 2-B: 10 students
  ...
Clustered 200 students into 4 clusters with bundle size 20 using KMEANS bundling.

$ ab generate
Cluster map generated → projects/washout-hs/clusters.png
   ↳ bundle 2-A: projects/washout-hs/bundle_2-A.png
   ↳ bundle 3-A: projects/washout-hs/bundle_3-A.png
   ...
Master PDF created → projects/washout-hs/master.pdf
   ↳ bundle 4-C: projects/washout-hs/bundle_4-C.pdf
PDF generation complete.
```

After the final step you’ll find:

* `master.png` – a bird’s-eye map with each cluster colour-coded
* `master.pdf` – the master roster
* `bundle_<letter>.png` – zoomed maps for each bundle
* `bundle_<letter>.pdf` – an address sheet for each delivery bundle

