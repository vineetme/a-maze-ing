"""Configuration file parsing and validation for A-Maze-ing.

This module reads a plain-text KEY=VALUE configuration file and
converts it into a validated, typed dictionary ready to be consumed
by the maze generator. It only parses and validates — it never
prints or exits the program. Callers (e.g. a_maze_ing.py) decide how
to react to errors raised here (see Raises section below).


The file must contain one 'KEY=VALUE' pair per line. Blank lines
and lines starting with '#' are treated as comments and ignored.

Args:
    path: Path to the configuration file to read.

Returns:
    A dictionary with the following keys:
    width (int), height (int), entry (tuple[int, int]),
    exit (tuple[int, int]), output_file (str), perfect (bool),
    seed (int | None).

Raises:
    FileNotFoundError: If `path` does not point to an existing
        file (raised automatically by `open()`).
    ValueError: If the file is malformed, a mandatory key is
        missing, or a value fails validation (wrong type, out of
        bounds, etc.). This function never catches its own
        errors on purpose — it's a reusable library function, not
        the user-facing entry point. It's up to the caller to
        decide how to react (print an error, retry, log, etc.).
"""

def parse_config(path: str) -> dict[str, object]:
    # `with` guarantees the file is closed automatically, even if an
    # exception is raised while reading it (context manager pattern).
    with open(path) as f:
        lines = f.readlines()

    raw_pairs: dict[str, str] = {} 

    for line in lines:
        # Strip BEFORE checking for blank/comment lines: raw lines
        # end with '\n', and whitespace-only lines would otherwise
        # slip past an emptiness check that compares against "".
        line = line.strip()

        if line == "" or line.startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(f"(no '='): {line!r}")

        # split("=", 1): split on the FIRST '=' only, so a value that
        # itself contains '=' (e.g. a path) doesn't break unpacking.
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Last occurrence wins if a key is repeated in the file —
        # no duplicate-key detection is done here.
        raw_pairs[key] = value

    # Check ALL mandatory keys are present before converting any
    # values. Note: only the FIRST missing key is reported as 
    # error raised immediately)
    required_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    for req_key in required_keys:
        if req_key not in raw_pairs:
            raise ValueError(f"Missing mandatory config key: {req_key}")
    
    # --- WIDTH / HEIGHT ---
    # Two separate checks on purpose: the try/except catches "is
    # this even parseable as an int" (format problem); the range
    # check afterwards catches "is this a sensible value" (domain
    # problem). Note int() tolerates surrounding whitespace and a
    # leading '+' (e.g. int(" +10 ") == 10) but rejects "10.0".
    try:
        width = int(raw_pairs["WIDTH"])
    except ValueError:
        raise ValueError(f"WIDTH must be an integer, got {raw_pairs['WIDTH']!r}")

    if width <= 0:
        raise ValueError(f"WIDTH must be positive, got {width}")
    
    try:
        height = int(raw_pairs["HEIGHT"])
    except ValueError:
        raise ValueError(f"HEIGHT must be an integer, got {raw_pairs['HEIGHT']!r}")
    if height <= 0:
        raise ValueError(f"HEIGHT must be positive, got {height}")

    # --- ENTRY ---
    entry_parts = raw_pairs["ENTRY"].split(",")
    # Explicit length check BEFORE unpacking: indexing entry_parts[0]
    # / [1] would silently ignore a 3rd value (e.g. "1,2,3") instead
    # of erroring — a silent bug is worse than a crash, so we check
    # the shape of the data first.
    if len(entry_parts) != 2:
        raise ValueError (f"ENTRY must be 'x,y', got {raw_pairs['ENTRY']!r}")
    try:
        entry_x, entry_y = int(entry_parts[0]), int(entry_parts[1])
    except ValueError:
        raise ValueError(f"ENTRY coordinates must be integers, got {raw_pairs['ENTRY']!r}")
    if not (0 <= entry_x < width) or not (0 <= entry_y < height):
        raise ValueError(f"ENTRY {entry_x}, {entry_y} is out of bounds for {width}*{height} maze")
    entry = (entry_x, entry_y)

    # --- EXIT ---
    # Named `exit_` (trailing underscore) because `exit` is a
    # built-in name in Python (used to quit the interpreter) — this
    # avoids shadowing it.
    exit_parts = raw_pairs["EXIT"].split(",")
    if len(exit_parts) != 2:
        raise ValueError(f"EXIT must be 'x,y', got {raw_pairs['EXIT']!r}")
    try:
        exit_x, exit_y = int(exit_parts[0]), int(exit_parts[1])
    except ValueError:
        raise ValueError(f"EXIT coordinates must be integers, got {raw_pairs['EXIT']!r}")
    if not (0 <= exit_x < width) or not (0 <= exit_y < height):
        raise ValueError(f"EXIT {exit_x},{exit_y} is out of bounds for {width}*{height} maze")
    exit_ = (exit_x, exit_y)

    # Tuple equality compares element-by-element: (0,0) == (0,1) is
    # False because the second elements differ. This gives correct
    # "same coordinate" semantics for free.
    if entry == exit_:
        raise ValueError ("ENTRY and EXIT must be different cells")

    # --- PERFECT---
    perfect_str = raw_pairs["PERFECT"].strip().lower()
    if perfect_str not in ("true", "false"):
        raise ValueError(f"PERFECT must be 'True' or  'False', got {raw_pairs['PERFECT']!r}")
    perfect = perfect_str == "true"

    # --- OUTPUT_FILE --- (plain string, no conversion needed)
    output_file = raw_pairs["OUTPUT_FILE"]

    # --- SEED (optional) ---
    # Not in required_keys, so unlike WIDTH/HEIGHT/etc. we don't yet
    # know if this key exists — must check presence explicitly before
    # converting, otherwise a missing key raises KeyError (wrong
    # exception type) instead of being handled as "no seed given".
    seed: int |  None = None
    if "SEED" in raw_pairs:
        try:
            seed = int(raw_pairs["SEED"])
        except ValueError:
            raise ValueError(f"SEED must be an integer, got {raw_pairs['SEED']!r}")

    return {
        "width": width,
        "height": height,
        "entry": entry,
        "exit": exit_,
        "output_file": output_file,
        "perfect": perfect,
        "seed": seed,
    }
