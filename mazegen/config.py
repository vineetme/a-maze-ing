def parse_config(path: str) -> None:
    with open(path) as f:
        lines = f.readlines()

    raw_pairs: dict[str, str] = {} 

    for line in lines:
        line = line.strip()

        if line == "" or line.startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(f"(no '='): {line!r}")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        raw_pairs[key] = value
        
    required_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    for req_key in required_keys:
        if req_key not in raw_pairs:
            raise ValueError(f"Missing mandatory config key: {req_key}")
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

    entry_parts = raw_pairs["ENTRY"].split(",")
    if len(entry_parts) != 2:
        raise ValueError (f"ENTRY must be 'x,y', got {raw_pairs['ENTRY']!r}")
    try:
        entry_x, entry_y = int(entry_parts[0]), int(entry_parts[1])
    except ValueError:
        raise ValueError(f"ENTRY coordinates must be integers, got {raw_pairs['ENTRY']!r}")
    if not (0 <= entry_x < width) or not (0 <= entry_y < height):
        raise ValueError(f"ENTRY {entry_x}, {entry_y} is out of bounds for {width}*{height} maze")
    entry = (entry_x, entry_y)

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
    
    if entry == exit_:
        raise ValueError ("ENTRY and EXIT must be different cells")

    perfect_str = raw_pairs["PERFECT"].strip().lower()
    if perfect_str not in ("true", "false"):
        raise ValueError(f"PERFECT must be 'True' or  'False', got {raw_pairs['PERFECT']!r}")
    perfect = perfect_str == "true"

    output_file = raw_pairs["OUTPUT_FILE"]

    seed = None
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
