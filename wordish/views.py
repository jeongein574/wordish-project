from django.shortcuts import render

import json
import ast
import re
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path
import logging
from pathlib import Path
from django.views.decorators.http import require_GET, require_POST

# Create your views here.

ROWS = 6
COLS = 5
RE_5 = re.compile(r"^[A-Za-z]{5}$")

def up5(s: str) -> str:
    return (s or "").upper()

def only_five_letters(s: str) -> bool:
    return bool(RE_5.fullmatch(s or ""))

# grid
@dataclass
class Row:
    letters: str
    classes: List[str]

def empty_row() -> Row:
    return Row(letters="", classes=["state-empty"] * COLS)

def empty_grid() -> List[Row]:
    return [empty_row() for _ in range(ROWS)]

def serialize_grid(grid: List[Row]) -> str:
    return json.dumps([asdict(r) for r in grid])

def deserialize_grid(s: Optional[str]) -> List[Row]:
    if not s:
        return empty_grid()
    try:
        data = json.loads(s)
        out: List[Row] = []
        for item in data:
            letters = up5(item.get("letters", ""))[:COLS].ljust(COLS)
            classes = (item.get("classes") or ["state-empty"] * COLS)[:COLS]
            classes += ["state-empty"] * (COLS - len(classes))
            out.append(Row(letters=letters, classes=classes))
        while len(out) < ROWS:
            out.append(empty_row())
        return out[:ROWS]
    except Exception:
        return empty_grid()

def grid_for_template(grid: List[Row]) -> List[List[dict]]:
    rows: List[List[dict]] = []
    for r in grid:
        row_cells: List[dict] = []
        for i in range(COLS):
            ch = r.letters[i] if i < len(r.letters) else ""
            cls = r.classes[i] if i < len(r.classes) else "state-empty"
            row_cells.append({"ch": ch, "cls": cls})
        rows.append(row_cells)
    return rows

#word list
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
_WORD_RE = re.compile(r"[A-Za-z]{5}")

def _parse_words_text(text: str, varname: str):
    m = re.search(rf"{re.escape(varname)}\s*=\s*(\[[\s\S]*?\])", text)
    if m:
        try:
            lst = ast.literal_eval(m.group(1))
            return [str(w).strip().upper()
                    for w in lst
                    if _WORD_RE.fullmatch(str(w).strip() or "")]
        except Exception:
            pass  # fall through
    try:
        maybe = ast.literal_eval(text.strip())
        if isinstance(maybe, list):
            return [str(w).strip().upper()
                    for w in maybe
                    if _WORD_RE.fullmatch(str(w).strip() or "")]
    except Exception:
        pass
    return [w.upper() for w in _WORD_RE.findall(text)]
def _load_words(file_name: str, varname: str):
    p = DATA_DIR / file_name
    if not p.exists():
        logger.warning("Word list file missing: %s", p)
        return []
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Failed reading %s: %s", p, e)
        return []
    return _parse_words_text(txt, varname)

ALL_WORDS_LIST = _load_words("all_words.txt", "all_words")
TARGET_WORDS   = _load_words("target_words.txt", "target_words")
ALL_WORDS_SET  = set(ALL_WORDS_LIST)

logger.warning("Loaded %d ALL words, %d TARGET words from %s",
               len(ALL_WORDS_SET), len(TARGET_WORDS), DATA_DIR)

def is_dictionary_word(word: str) -> bool:
    w = (word or "").strip()
    return bool(_WORD_RE.fullmatch(w)) and (w.upper() in ALL_WORDS_SET)

#score
def score_guess(guess: str, target: str) -> List[str]:
    g = up5(guess)
    t = up5(target)

    result = ["state-absent"] * COLS
    remaining = {}
    for i in range(COLS):
        if g[i] == t[i]:
            result[i] = "state-correct"
        else:
            remaining[t[i]] = remaining.get(t[i], 0) + 1

    for i in range(COLS):
        if result[i] == "state-correct":
            continue
        ch = g[i]
        if remaining.get(ch, 0) > 0:
            result[i] = "state-present"
            remaining[ch] -= 1
        else:
            result[i] = "state-absent"
    return result

@require_GET
def start_page(request):
    return render(request, "wordish/start.html", {"message": "Welcome to Wordish!"})

@require_POST
def game_page(request):
    target_text = request.POST.get("target_text", "").strip()
    if target_text:
        if not only_five_letters(target_text):
            return render(request, "wordish/start.html",
                {"message": "invalid input: target must be exactly five English letters."},
            )
        if not is_dictionary_word(target_text):
            return render(request, "wordish/start.html",
                {"message": "invalid input: not a valid English word."},
            )
        
        target = up5(target_text)
        grid = empty_grid()
        row_index = 0 

        return render(
            request,
            "wordish/game.html",
            {
                "status": "Game started. Enter your first guess!",
                "target": target,
                "grid": grid,
                "grid_cells": grid_for_template(grid),
                "grid_json": serialize_grid(grid),
                "row_index": row_index,
                "game_over": False,
            },
        )
    target = up5(request.POST.get("target", ""))

    raw_row_index = request.POST.get("row_index", "")
    if not raw_row_index.isdigit():
        return render(request, "wordish/start.html",
            {"message": "error: invalid input. Hidden fields were malformed; please start a new game."},
        )
    row_index = int(raw_row_index)
    if not (0 <= row_index < ROWS):
        return render(request, "wordish/start.html",
            {"message": "error: invalid input. Hidden fields were malformed; please start a new game."},
        )
    raw_grid = request.POST.get("grid_json", "")
    try:
        data = json.loads(raw_grid)
        if not isinstance(data, list) or len(data) != ROWS:
            raise ValueError("bad rows")
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("row not dict")
            letters = item.get("letters", "")
            classes = item.get("classes", [])
            if not isinstance(letters, str):
                raise ValueError("letters not str")
            if not isinstance(classes, list) or len(classes) != COLS:
                raise ValueError("classes bad")
    except Exception:
        return render(
            request, "wordish/start.html",
            {"message": "error: invalid input. Hidden fields were malformed; please start a new game."},
        )
    
    grid = deserialize_grid(request.POST.get("grid_json"))

    if not only_five_letters(target):
        return render(request, "wordish/start.html",
            {"message": "error: invalid input. Please enter a new target."},
        )
    game_over_val = request.POST.get("game_over", None)
    if game_over_val not in ("0", "1"):
        return render(
            request,
            "wordish/start.html",
            {"message": "error: invalid input. Hidden fields were malformed; please start a new game."},
        )
    game_over = (game_over_val == "1")

    if game_over:
        return render(
            request, "wordish/game.html",
            {
                "status": "Game over. Start a new game to play again.",
                "target": target,
                "grid": grid,
                "grid_cells": grid_for_template(grid),
                "grid_json": serialize_grid(grid),
                "row_index": row_index,
                "game_over": True,
            },
        )
    
    guess_text = request.POST.get("guess_text", "").strip()
    if not only_five_letters(guess_text):
        return render(
            request,
            "wordish/game.html",
            {
                "status": "error: invalid input. enter exactly five English letters.",
                "target": target,
                "grid": grid,
                "grid_cells": grid_for_template(grid),
                "grid_json": serialize_grid(grid),
                "row_index": row_index,
                "game_over": False,
            },
        )
    if not is_dictionary_word(guess_text):
        return render(
            request,
            "wordish/game.html",
            {
                "status": "error: invalid input. not a valid English word.",
                "target": target,
                "grid": grid,
                "grid_cells": grid_for_template(grid),
                "grid_json": serialize_grid(grid),
                "row_index": row_index,
                "game_over": False,
            },
        )

    guess = up5(guess_text)
    classes = score_guess(guess, target)
    grid[row_index] = Row(letters=guess, classes=classes)

    if guess == target:
        status = "You win!"
        game_over = True
    elif row_index + 1 >= ROWS:
        status = f"You lose. The word was {target}."
        game_over = True
    else:
        status = "Guess accepted."
        row_index += 1
        game_over = False

    return render(
        request,
        "wordish/game.html",
        {
            "status": status,
            "target": target,
            "grid": grid,
            "grid_cells": grid_for_template(grid),
            "grid_json": serialize_grid(grid),
            "row_index": row_index,
            "game_over": game_over,
        },
    )