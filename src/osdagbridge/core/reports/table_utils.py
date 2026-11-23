"""Helpers that post-process the generated LaTeX source.

add_repeating_headers() makes every longtable that has a single bold header
row (and no repeating header yet) repeat that header on every page.

It also puts the missing row end after the table caption. LaTeX requires
"\\caption{...}\\\\" inside a longtable head; without it LaTeX reports
"Misplaced \\noalign" errors, which were silently ignored before.
"""
import re

_BEGIN = '\\begin{longtable}'
_END = '\\end{longtable}'


def _skip_ws(s, i):
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def _match_brace(s, i):
    """s[i] must be '{'. Return the index of its matching '}', or -1."""
    depth = 0
    j = i
    n = len(s)
    while j < n:
        c = s[j]
        if c == '\\':
            j += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def _find_row_end(s, start):
    """Return the index just after the first top-level row end (two backslashes)."""
    depth = 0
    j = start
    n = len(s)
    while j < n:
        c = s[j]
        if c == '\\':
            if s[j:j + 2] == '\\\\' and depth == 0:
                return j + 2
            j += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        j += 1
    return -1


def _skip_optional_arg(s, i):
    """If s[i:] starts with [..], return the index after it, else i."""
    m = re.match(r'\[[^\]]*\]', s[i:])
    return i + m.end() if m else i


def _add_header_to_table(table):
    """table = text from \\begin{longtable} up to (not including) \\end{longtable}."""
    if '\\endhead' in table or '\\endfirsthead' in table:
        return table

    i = len(_BEGIN)
    i = _skip_optional_arg(table, _skip_ws(table, i))
    i = _skip_ws(table, i)
    if i >= len(table) or table[i] != '{':
        return table
    close = _match_brace(table, i)
    if close == -1:
        return table
    j = close + 1

    # Optional caption (and optional label / row end after it)
    caption_needs_row_end = None
    k = _skip_ws(table, j)
    if table.startswith('\\caption', k):
        p = _skip_optional_arg(table, k + len('\\caption'))
        if p >= len(table) or table[p] != '{':
            return table
        cc = _match_brace(table, p)
        if cc == -1:
            return table
        j = cc + 1
        k = _skip_ws(table, j)
        if table.startswith('\\label', k):
            lb = table.find('{', k)
            lc = _match_brace(table, lb) if lb != -1 else -1
            if lc == -1:
                return table
            j = lc + 1
            k = _skip_ws(table, j)
        if table.startswith('\\\\', k):
            j = _skip_optional_arg(table, k + 2)
        else:
            caption_needs_row_end = j

    # Header = \hline  one bold row  \hline
    k = _skip_ws(table, j)
    if not table.startswith('\\hline', k):
        return table
    head_start = k
    row_start = k + len('\\hline')
    row_end = _find_row_end(table, row_start)
    if row_end == -1:
        return table
    row_end = _skip_optional_arg(table, row_end)
    header_row = table[row_start:row_end]
    if '\\textbf' not in header_row or '&' not in header_row:
        return table
    k2 = _skip_ws(table, row_end)
    if not table.startswith('\\hline', k2):
        return table
    head_end = k2 + len('\\hline')

    header_block = table[head_start:head_end]
    insert = '\n\\endfirsthead\n' + header_block + '\n\\endhead\n'
    result = table[:head_end] + insert + table[head_end:]
    if caption_needs_row_end is not None:
        pos = caption_needs_row_end
        result = result[:pos] + '\\\\' + result[pos:]
    return result


def add_repeating_headers(tex):
    """Return tex with a repeating header added to every eligible longtable."""
    out = []
    pos = 0
    while True:
        b = tex.find(_BEGIN, pos)
        if b == -1:
            out.append(tex[pos:])
            break
        e = tex.find(_END, b)
        if e == -1:
            out.append(tex[pos:])
            break
        out.append(tex[pos:b])
        out.append(_add_header_to_table(tex[b:e]))
        out.append(_END)
        pos = e + len(_END)
    return ''.join(out)