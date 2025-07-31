# Sofifa Scraper Tool (FC25 Modding Support)

This is a Python-based tool designed to assist modders of EA Sports FC25 (formerly FIFA) by automating the process of scraping player data from [Sofifa.com](https://sofifa.com). The collected data can help in generating `compdata`, custom league structures, or managing squad/player IDs.

## Features

- Two modular scripts:
  - `Script_1.py` – Full player data (Name, Age, Position, Height, Weight, Preferred Foot, Skill Moves, Weak Foot, Contract, Nationality, etc.)
  - `Script_2.py` – Focused scraping for `Value` and `Wage` (for stability)
- Python GUI (`Script_3.pyw`) with:
  - Dark mode toggle
  - Input field for Sofifa URL
  - Output directory selector
  - Progress bars, log viewer, and script controls
  - Clipboard export or file-based results
- Output formats: `.xlsx`, `.txt` (pipe-delimited), `.json`

## Installation

1. Clone the repository:

```bash
git clone https://github.com/nadhilm12/sofifa-scraper-fc25.git
cd sofifa-scraper-fc25
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Run the GUI:

```bash
python Script_3.pyw
```

## Notes

- Make sure [ChromeDriver](https://chromedriver.chromium.org/) is compatible with your installed version of Chrome.
- No login or API key is required. The tool simply mimics human browsing behavior.
- For educational and personal modding purposes only. Not affiliated with EA or Sofifa.

## License

This project is licensed under the MIT License. See `LICENSE` for more details.

---

**Created by:** [nadhilm12](https://github.com/nadhilm12)  
**Year:** 2025  
**Inspired by:** Paulv2k4, eshortX, Decoruiz
**Open-source | FC25 Modding Utility**

