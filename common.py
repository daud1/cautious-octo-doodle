import random
from curses import (
    A_BLINK,
    COLOR_BLACK,
    COLOR_GREEN,
    COLOR_RED,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_UP,
    color_pair,
    init_pair,
    start_color,
)
from queue import Queue

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

MOVT_CHARS = {KEY_UP: (-1, 0), KEY_DOWN: (1, 0), KEY_LEFT: (0, -1), KEY_RIGHT: (0, 1)}


def make_maze(dim):
    maze = np.ones((dim * 2 + 1, dim * 2 + 1))

    x, y = (0, 0)
    maze[2 * x + 1, 2 * y + 1] = 0

    stack = [(x, y)]
    while len(stack) > 0:
        x, y = stack[-1]
        directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if nx >= 0 and ny >= 0 and nx < dim and ny < dim and maze[2 * nx + 1, 2 * ny + 1] == 1:
                maze[2 * nx + 1, 2 * ny + 1] = 0  # clear cell
                maze[2 * x + 1 + dx, 2 * y + 1 + dy] = 0  # clear wall to next cell
                stack.append((nx, ny))
                break
        else:
            stack.pop()
    maze[1, 0] = 0
    maze[-2, -1] = 0
    return maze


def draw_maze_and_player_to_terminal(stdscr, dimension):
    start_color()
    init_pair(1, COLOR_GREEN, COLOR_BLACK)
    init_pair(2, COLOR_RED, COLOR_BLACK)

    # draw maze and help text in the middle bounded by window size
    height, width = stdscr.getmaxyx()
    max_dimension = max(1, min((height - 4) // 2, (width - 2) // 2))
    dimension = min(dimension, max_dimension)
    start_x = int((width - (2 * dimension + 1)) / 2)

    maze = make_maze(dimension)
    stdscr.clear()
    for y, v in enumerate(maze):
        for x, vv in enumerate(v):
            x += start_x
            if y < height - 1 and x < width - 1:
                stdscr.addstr(y, x, " " if vv == 0 else "-")
    stdscr.refresh()
    stdscr.addstr(maze.shape[0] + 2, start_x, "Press q to quit", color_pair(2))

    # move in maze
    curr_pos = 1, start_x
    stdscr.addch(*curr_pos, "@", color_pair(1))
    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        if key in MOVT_CHARS:
            y, x = get_new_position(curr_pos, MOVT_CHARS[key])
            try:
                if maze[y][x - start_x] == 0:
                    stdscr.addch(*curr_pos, " ")
                    stdscr.addch(y, x, "@")
                    curr_pos = y, x
                    stdscr.refresh()
            except IndexError:
                win_message = "You Win!!"
                stdscr.clear()
                stdscr.addstr(height // 2, start_x, win_message, color_pair(1) | A_BLINK)


def get_new_position(a, b):
    return a[0] + b[0], a[1] + b[1]


def walk_in_maze(stdscr, key, maze):
    # place player char at start_coords
    # listen to keys and draw player in new coords if valid, clearing the old coords.
    curr_pos = (0, 0)
    stdscr.addch(*curr_pos, "@")
    if key in MOVT_CHARS:
        y, x = get_new_position(curr_pos, MOVT_CHARS[key])
        if maze[y][x] == 0:
            stdscr.addch(*curr_pos, " ")
            stdscr.addch(y, x, "@")
            curr_pos = y, x
            stdscr.refresh()


def solve_maze(maze):
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    start = (1, 1)
    end = (maze.shape[0] - 2, maze.shape[1] - 2)

    parent = {start: None}
    visited = np.zeros_like(maze, dtype=bool)
    visited[start] = True

    queue = Queue()
    queue.put(start)

    while not queue.empty():
        node = queue.get()

        if node == end:
            path = []
            while node is not None:
                path.append(node)
                node = parent[node]
            return path[::-1]

        for dx, dy in directions:
            next_node = (node[0] + dx, node[1] + dy)

            if (
                0 <= next_node[0] < maze.shape[0]
                and 0 <= next_node[1] < maze.shape[1]
                and maze[next_node] == 0
                and not visited[next_node]
            ):
                visited[next_node] = True
                parent[next_node] = node
                queue.put(next_node)
    return None


def animate_maze(maze, path=None):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Set the border color to white
    fig.patch.set_edgecolor("white")
    fig.patch.set_linewidth(0)

    ax.imshow(maze, cmap=plt.cm.binary, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])

    # Prepare for path animation
    if path is not None:
        (line,) = ax.plot([], [], color="red", linewidth=2)

        def init():
            line.set_data([], [])
            return (line,)

        # update is called for each path point in the maze
        def update(frame):
            x, y = path[frame]
            line.set_data(*zip(*[(p[1], p[0]) for p in path[: frame + 1]]))  # update the data
            return (line,)

        ani = animation.FuncAnimation(
            fig,
            update,
            frames=range(len(path)),
            init_func=init,
            blit=True,
            repeat=False,
            interval=20,
        )

    # Draw entry and exit arrows
    ax.arrow(0, 1, 0.4, 0, fc="green", ec="green", head_width=0.3, head_length=0.3)
    ax.arrow(
        maze.shape[1] - 1,
        maze.shape[0] - 2,
        0.4,
        0,
        fc="blue",
        ec="blue",
        head_width=0.3,
        head_length=0.3,
    )

    plt.show()


# represent the maze as a matrix, walls as 1, cells as 0
# use stack for the position of unexplored nodes
# use dfs to create the maze
# starting from the starting point (0,0) of a matrix of walls (1's),
# check neighbors randomly, move to the cell and open it if its a wall and push to stack,
# repeat with new cell,
# if none of the neighbors are walls, all have been visited and should beremoved from stack
