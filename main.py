from curses import wrapper

from common import draw_maze_and_player_to_terminal

if __name__ == "__main__":
    dimension = int(input("enter the size of the maze you want. e.g 9 to get a 19x19 maze:"))
    wrapper(draw_maze_and_player_to_terminal, dimension)
