import os
import time
import shutil

WIDTH = 60
HEIGHT = 16
GROUND_Y = HEIGHT - 3  # Ground is always at this row

class Entity:
    def __init__(self, x, char):
        self.x = x
        self.char = char

class Player(Entity):
    def __init__(self, x):
        super().__init__(x, '@')

    def update(self):
        pass

class Room:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # In the future: add obstacles, decorations, etc.

    def get_landscape_line(self, y):
        # For now, just empty space everywhere except ground
        return [' '] * self.width

class UI:
    def __init__(self):
        self.title = "ASCII Roguelike Demo"
        self.hp = 10
        self.max_hp = 10

    def draw(self, pad_left, width):
        print(' ' * pad_left + f"[HP: {self.hp}/{self.max_hp}] [Press Ctrl+C to quit]".ljust(width + 2))
        print('\n' * 2)

class Renderer:
    def __init__(self, width, height, ground_y):
        self.width = width
        self.height = height
        self.ground_y = ground_y

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render(self, player, room, ui):
        term_size = shutil.get_terminal_size((80, 24))
        pad_left = (term_size.columns - (self.width + 2)) // 2  # +2 for frame

        # UI area above
        print('\n' * 6)
        print(' ' * pad_left + ui.title.center(self.width + 2))
        print(' ' * pad_left + "+" + "-" * self.width + "+")  # Top frame

        # Game area
        for y in range(self.height):
            if y == self.ground_y - 1:
                # Player line (just above ground)
                line = room.get_landscape_line(y)
                if 0 <= player.x < self.width:
                    line[player.x] = player.char
                print(' ' * pad_left + "|" + ''.join(line) + "|")
            elif y == self.ground_y:
                # Ground line
                print(' ' * pad_left + "|" + '_' * self.width + "|")
            else:
                # Landscape or empty
                line = room.get_landscape_line(y)
                print(' ' * pad_left + "|" + ''.join(line) + "|")

        # Screen bottom line (frame)
        print(' ' * pad_left + "+" + "-" * self.width + "+")  # Bottom frame

        # UI area below
        ui.draw(pad_left, self.width)

class Game:
    def __init__(self):
        self.player = Player(x=5)
        self.room = Room(WIDTH, HEIGHT)
        self.ui = UI()
        self.renderer = Renderer(WIDTH, HEIGHT, GROUND_Y)
        self.running = True

    def update(self):
        self.player.update()

    def run(self):
        while self.running:
            self.renderer.clear()
            self.renderer.render(self.player, self.room, self.ui)
            time.sleep(0.1)

if __name__ == "__main__":
    game = Game()
    game.run()