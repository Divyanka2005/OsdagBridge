"""Central style configuration for the OsdagBridge design report.

Single source of truth for page layout, table spacing and colours.
Change a value here and every chapter of the report follows.
"""

# ---- Page layout (LaTeX geometry package options) ----
# The bottom margin and footskip were both raised by 0.25in so the footer
# stays in the same place, but the page body now ends higher and can no
# longer run into the footer rule or the "* Software default value" note.
PAGE_GEOMETRY = "a4paper, margin=1in, bottom=1.25in, footskip=0.75in, headheight=18pt"

# ---- Table spacing ----
TABCOLSEP = "6pt"          # left/right cell padding
ARRAYSTRETCH = "1.12"      # row height multiplier
EXTRAROWHEIGHT = "0.6pt"   # extra height added to each row
LTPOST = "6pt"             # space below a longtable
NEEDSPACE_LINES = 5        # a table starts on a new page if fewer lines remain

# ---- Colours (HTML hex, no #) ----
COLOR_OSDAG_GREEN = "91B014"