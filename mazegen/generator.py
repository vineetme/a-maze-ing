"""Maze generation logic for A-Maze-ing.

This module builds a maze's wall data and knows
nothing about how it gets displayed or written to a file. That
separation is what lets this module be reused elsewhere (e.g. the
pip-installable mazegen package).

It is important to begin with what A maze grid is - just a table of numbers,
For a 4-wide, 3-tall maze, imagine:
Row 0:  [15, 15, 15, 15]
Row 1:  [15, 15, 15, 15]
Row 2:  [15, 15, 15, 15]
Each row is a list of numbers (one per column). The whole grid is a list of
those rows. In Python, that's literally:
[
    [15, 15, 15, 15],
    [15, 15, 15, 15],
    [15, 15, 15, 15],
]
grid is a list of lists. grid[0] gives you the whole first row: [15, 15, 15, 15].
grid[0][2] gives you the 3rd item in the first row: 15.

WALL ENCODING
Now we come to a cell. Each cell is one integer, 0-15, using 4 bits — 
one bit per direction. A bit set to 1 means that wall is CLOSED. A 
bit set to 0 means open.

    Bit value 1 (0001) = North wall
    Bit value 2 (0010) = East wall
    Bit value 4 (0100) = South wall
    Bit value 8 (1000) = West wall

Example: a cell with only a North wall = 1. A cell fully closed on
all 4 sides = 1+2+4+8 = 15. A cell fully open = 0.
"""

import random

NORTH = 1  #0b0001
EAST = 2   #0b0010
SOUTH = 4  #0b0100
WEST = 8   #0b1000

# The opposite direction, used to update neighbouring cell. 
# OPPOSITE tells us: if I open MY wall in direction D, which wall on
# my NEIGHBOR did I just open too? (the shared wall, seen from their side)
OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}

# DELTA tells us: to move one step in direction D, how much do we
# change (x, y) by? Our convention: y=0 is the TOP row, and
# y increases downward. So moving "North" (up) means y DECREASES.
# x=0 is left most column, and x increases rightward. So moving "East" means
# x increases.
DELTA = {
    NORTH: (0, -1),  # x unchanged, y decreases (move up a row)
    SOUTH: (0, 1),   # x unchnaged, y increases (move downa a row)
    EAST: (1, 0),    # x increases, y unchanged (move right a column)
    WEST: (-1, 0),   # x decreases, y unchnaged (move left a column)
}

def remove_wall(grid: list[list[int]], x: int, y: int, direction: int) -> None:
    """Open a wall between cell (x, y) and it neighbour in  'direction.

    Clears the wall bit on BOTH cells involved, guaranteeing the grid
    stays coherent (a cell's East wall state always matches its
    eastern neighbor's West wall state, etc. It's structurally
    impossible to update one side without the other).

    Args:
        grid: The maze grid, grid[y][x] holding a 4-bit wall mask.
        x: Column of source cell.
        y: Row of source cell.
        direction: Which wall to open - NORTH/EAST/SOUTH/WEST
    """
    # Look up how much x and y change to reach the neighbor cell.
    dx, dy = DELTA[direction]
    nx, ny = x + dx, y + dy

    # &= ~direction clears just that one bit, leaving all others
    # untouched. Example: 15 (1111) & ~EAST -> 13 (1101): East's bit
    # (value 2) turned off, North/South/West bits unchanged.
    grid[y][x] &= ~direction

    # Do the SAME thing to the neighbor, but on the OPPOSITE side —
    # e.g. if I open my East wall, my eastern neighbor's West wall
    # (the same physical wall, seen from the other side) opens too. 
    # This is what keeps the two cells coherent with each other.
    grid[ny][nx] &= ~OPPOSITE[direction]

def generate_maze(width: int, height: int, seed: int | None = None) -> list[list[int]]:
    """Generate a perfect maze using the recursive backtracker algorithm.

    ALGORITHM: start at one cell, mark it visited.
    Repeatedly look at unvisited neighbors of the CURRENT cell (the
    most recently entered one); if there's one available, knock down
    the wall to it and move in. If there's nowhere left to go (dead
    end), backtrack to the previous cell and try again from there.
    Stop when we've backtracked all the way out and nowhere is left
    to explore. This visits every cell and creates exactly one path
    between any two cells (a spanning tree) — i.e. a perfect maze.

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Optional seed for reproducible generation.

    Returns:
        A grid (list of rows) where grid[y][x] is a 4-bit wall mask.
    """

    # A LOCAL random generator (not the global random module) — this
    # means multiple calls to generate_maze() in the same program run
    # (e.g. hitting "regenerate" in the terminal menu) don't interfere
    # with each other's randomness. If seed is a specific number, this
    #  generator will always produce the same sequence of "random" 
    # choices when re-run — that's what makes the maze reproducible.
    rng = random.Random(seed)

    # Start with every cell fully walled in (all 4 bits set = 15). 
    # The grid, in plain loop form
    #   grid = []
    #       for row_index in range(height):
    #           row = []
    #           for col_index in range(width):
    #               row.append(15)
    #           grid.append(row)
    # Make an empty list called grid. Repeat height times: make an empty 
    # list called row, repeat width times adding a 15 to it, then add that
    # whole row onto grid.
    grid = [[15 for _ in range(width)] for _ in range(height)]

    # The "visited" grid, same pattern, with "False" instead of "15"
    visited = [[False for _ in range(width)] for _ in range(height)]

    # start = (0, 0) — a tuple holding two values: an x-coordinate and a
    # y-coordinate. start[0] gets the first item in that tuple (0, the x-value).
    # start[1] gets the second item (0, the y-value — happens to also be 0 here
    # since we start at the corner, but conceptually it's a separate value)
    start = (0, 0)

    # Break it into steps:
    # start[1] → the y-coordinate → 0
    # start[0] → the x-coordinate → 0
    # So this line is really: visited[0][0] = True
    # Which means: "in the visited grid, go to row 0, then column 0 within that
    # row, and set it to True"
    # Remember our indexing convention: grid[y][x] — row first (y),
    # then column (x). That's why start[1] (the y-value) goes in the first
    # bracket and start[0] (the x-value) goes in the second bracket — 
    # it looks backwards compared to how we normally say "x, y," and that 
    # mismatch is exactly what makes this line hard to read at a glance.
    visited[start[1]][start[0]] = True

    # Now we create a list containing one item — the start tuple.
    # So stack = [(0, 0)]. This is our "trail of breadcrumbs," starting
    # with just the entrance.
    stack = [start]

    # stack is a list. In an if/while condition, Python treats a non-empty 
    # list as "truthy" and an empty list [] as "falsy." So while stack: means
    # "keep looping as long as the list has at least one item in it" — identical
    # meaning to while len(stack) > 0:, just more compact/idiomatic Python.
    while stack:
        # stack[-1] looks at the last item in the list (peeking at the top of the
        # stack, without removing it) — this is a tuple like (2, 1). x, y = (2, 1)
        # is tuple unpacking: Python takes the tuple and assigns its first value to
        # x and its second value to y in one line — equivalent to writing 
        # x = stack[-1][0] then y = stack[-1][1], just shorter.
        x, y = stack[-1]

        # Find unvisited neighbors of (x, y).
        # An empty list we're about to fill in with neighbor cells worth moving to
        unvisited_neighbors = [] 
        # DELTA is a dictionary: {NORTH: (0,-1), SOUTH: (0,1), EAST: (1,0), 
        # WEST: (-1,0)}. .items() lets you loop over both the key and value of 
        # each entry together. Here, direction becomes each key in turn (NORTH,
        # then SOUTH, etc.), and (dx, dy) unpacks the corresponding tuple value 
        # directly in the loop header — so on the NORTH iteration, direction =
        # NORTH and dx, dy = 0, -1 all at once.
        for direction, (dx, dy) in DELTA.items():
            nx, ny = x + dx, y + dy
            # Checks the neighbor is actually inside the grid — using the chained
            if 0 <= nx < width and 0 <= ny < height:
                # Checks that neighbor hasn't already been visited. 
                # visited[ny][nx] is True/False; not visited[ny][nx] flips it, 
                # so this reads "if this neighbor has NOT been visited yet."
                if not visited[ny][nx]:
                    # If it passed both checks (in bounds, unvisited), we record it 
                    # as a candidate move — bundling the direction and coordinates 
                    # together as a 3-item tuple, added to our list of options.
                    unvisited_neighbors.append((direction, nx, ny))

        # Same truthy-list trick as while stack: — "if there's at least one valid
        # neighbor to move to."
        if unvisited_neighbors:
            # rng.choice(list) picks one random item from the list. Here it picks
            # one of our candidate (direction, nx, ny) tuples, and immediately
            # unpacks it into three separate variables.
            direction, nx, ny = rng.choice(unvisited_neighbors)
            # Calls the function we traced thoroughly earlier — knocks down the
            # wall between the current cell and the chosen neighbor, on both
            # sides at once.
            remove_wall(grid, x, y, direction)
            # Marks the neighbor as visited now that we're moving into it.
            visited[ny][nx] = True
            # Pushes the neighbor's coordinates onto the stack — we've now 
            # "moved into" that room, and it becomes the new top of the stack 
            # for the next loop iteration.
            stack.append((nx, ny))
        # If there were no unvisited neighbors (unvisited_neighbors was empty), 
        # we're at a dead end — stack.pop() removes the top item from the list, 
        # which is exactly the "backtrack" step: we discard the current room from
        # our trail and go back to whatever room was pushed just before it.
        else:
            stack.pop()  # dead end, backtrack
    # Once the while stack: loop ends (stack became empty — nothing left to 
    # explore), we return the finished wall-grid.
    return grid
