# afreports
Python HTML Report Builder


Create self-contained, professional HTML reports directly from Python. Reports can include a title,
table of contents, section headings, paragraphs, pandas DataFrames, figures, and a linked appendix
of automatically numbered table and figure captions.

---

## Repository Structure

```
afreports/
│
├── afreports/          # Main Python package
│   ├── __init__.py              # Package initialization - exports Report class
│   ├── report.py                # Core Report class - handles report building and rendering
│   ├── static/
│   │   └── report.css           # Stylesheet - defines report colors, fonts, spacing, and layout
│   ├── templates/
│   │   ├── report.html          # Base HTML template - main report wrapper
│   │   └── blocks/              # Reusable Jinja2 template blocks
│   │       ├── heading1.html    # Top-level heading template
│   │       ├── heading2.html    # Subsection heading template
│   │       ├── paragraph.html   # Text paragraph template
│   │       ├── table.html       # Data table template
│   │       ├── figure.html      # Image/figure template
│   │       ├── table_of_contents.html  # Contents list template
│   │       └── appendix.html    # Linked table and figure captions
│   └── Planning-Inspectorate-logo-stacked.png  # Default branding logo
│
├── pyproject.toml               # Project metadata - package name, version, dependencies, build config
├── requirements.txt             # Pip dependencies - Jinja2, pandas, and versions
├── LICENSE                      # MIT License file
└── README.md                    # Documentation - usage guide, installation, API reference
```

---

## Requirements and Installation

- **Python:** 3.10 or newer
- **Dependencies:** Jinja2 >= 3.1, pandas >= 2.0

> **Tip:** VS Code disables word wrap by default, so while using this package, long lines of documentation may extend beyond the editor window. Enable **Word Wrap** to display them across multiple lines. Toggle it with **Alt+Z**. For more information on this, check this out: https://code.visualstudio.com/docs/editing/codebasics?referrer=vsc-search#_how-do-i-turn-on-word-wrap

### Install the Package

There are two ways to install the package, depending on whether you want to use the package or contribute to its development.

#### Option 1: Install from GitHub (Normal Use)

Open Anaconda Prompt or Command Prompt, activate the environment in which you want to use the package, and run:

```bash
python -m pip install "git+https://github.com/ririwome/afreports.git"
```

#### Option 2: Install in Editable Mode
If you are developing or contributing to the package, first clone the repository:


```bash
git clone https://github.com/ririwome/afreports.git



```

Navigate to the repository in the command prompt:

```bash
cd afreports
```

Then, install the package in editable mode:

```bash
python -m pip install -e .
```

Editable mode links the installed package to your local source code, so changes made to the package are available without reinstalling it.

#### Import the Package

The package is imported by the command:

```python
from afreports import Report
```

---

## Quick Start

Create a Python file (for example, `my_report.py`):

```python
import pandas as pd

from afreports import Report

# Initialize a report with title and optional subtitle
report = Report(
    "Public Service Performance Summary",
    subtitle="Quarterly service delivery overview",
)

# Add a table of contents
report.table_of_contents()

# Add content sections
report.heading1("Executive Summary")
report.p("This report summarises performance across key public services.")

report.heading2("Performance Against Target")
report.table(
    pd.DataFrame(
        {
            "Performance": ["Met target", "Below target"],
            "Number of Services": [12, 4],
        }
    ),
    caption="Service performance against target",
)

# Add an appendix linking to captioned tables and figures
report.appendix()

# Render the report to an HTML file
output_path = report.render("public-service-performance-summary.html")
print(f"Report saved to {output_path.resolve()}")
```

Run it from the repository directory:

```bash
python my_report.py
```

The `render()` method creates the output directory if needed, writes UTF-8 HTML, and
returns the output path. The output filename must end in `.html`.

---

## Report API Reference

### Creating a Report

```python
report = Report(title, subtitle="")
```

- `title` (str): The report title (appears in browser tab and page heading)
- `subtitle` (str, optional): Subtitle text displayed below the title

### Adding Content

All content methods return the report object, enabling method chaining:

```python
report = (
    Report("Monthly Summary")
    .table_of_contents()
    .heading1("Overview")
    .p("Summary text here.")
)
```

#### Available Methods

- **`table_of_contents()`** – Inserts a clickable contents list linking to report headings
- **`appendix()`** – Adds a clickable list of captioned tables and figures at the end of the report
- **`heading1(text)`** – Adds a top-level section heading (numbered as 1, 2, 3...)
- **`heading2(text)`** – Adds a subsection heading (numbered as 1.1, 1.2, 2.1...)
- **`p(text)`** – Adds a paragraph of text
- **`table(dataframe, caption="", index=False, na_rep="", float_format=None)`** – Embeds a pandas DataFrame as a styled HTML table
- **`figure(figure_or_path, caption="", alt_text="", image_format="png", dpi=150)`** – Adds an image or Matplotlib figure
  - Pass a file path to link to an image
  - Pass a Matplotlib figure object to embed it in the report
  - Provide `alt_text` for accessibility

### Captions and Appendix

Supply only the description in `caption`; the report adds the number automatically:

```python
report.table(outcomes_dataframe, caption="Case outcomes by decision")
# Caption: Table 1. Case outcomes by decision

report.figure(
        "monthly-outcomes.png",
        caption="Monthly case outcomes",
        alt_text="Bar chart of monthly approved and dismissed cases",
)
# Caption: Figure 1 Monthly case outcomes

report.table(regions_dataframe, caption="Cases by region")
# Caption: Table 2. Cases by region

report.appendix()
```

- Tables and figures are numbered separately, starting at 1, in the order they are added.
- All tables and figures count toward their sequence, including items without captions.
- Captions are optional. Items without captions have no visible label and are omitted from the appendix.
- Call `appendix()` once to include the list. It always appears after all report content,
    even if more content is added after the call.
- Appendix entries follow report order and show the same number and description as the caption.
    Each entry links directly to its table or figure.
- Rendering again recalculates the numbers without modifying the original caption text.

### Rendering

```python
output_path = report.render(output_file)
```

- Creates the output directory if it doesn't exist
- Writes UTF-8 encoded HTML
- Returns a `Path` object to the generated file
- Output filename must end in `.html`


---

## Package Details

- **License:** MIT
- **Author:** Rishika Vashishtha
- **Python Support:** 3.10+
- **Main Dependencies:**
  - Jinja2 (template rendering)
  - pandas (DataFrame support)

---