import os
import time
import shutil
import msvcrt

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
        self.hp = 10
        self.max_hp = 10

    def update(self):
        pass

class Room:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.description = "A plain room."
        # In the future: add obstacles, decorations, etc.

    def get_landscape_line(self, y):
        # For now, just empty space everywhere except ground
        return [' '] * self.width

class UI:
    def __init__(self):
        self.title = "ASCII Roguelike Demo"
        # UI layout info could go here

    def draw(self, pad_left, width, player, room):
        # Draw title
        print(' ' * pad_left + self.title.center(width + 2))
        # Draw player stats from player entity
        print(' ' * pad_left + f"[HP: {player.hp}/{player.max_hp}]".ljust(width + 2))
        # Draw room description from room
        print(' ' * pad_left + room.description.center(width + 2))
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
        ui.draw(pad_left, self.width, player, room)
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

        # UI area below (could add more info here if needed)
        print('\n' * 2)

class InputHandler:
    def __init__(self):
        self.quit = False

    def poll(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC key
                self.quit = True

class Game:
    def __init__(self):
        self.player = Player(x=5)
        self.room = Room(WIDTH, HEIGHT)
        self.ui = UI()
        self.renderer = Renderer(WIDTH, HEIGHT, GROUND_Y)
        self.input_handler = InputHandler()
        self.running = True

    def update(self):
        self.player.update()
        self.input_handler.poll()
        if self.input_handler.quit:
            self.running = False

    def run(self):
        while self.running:
            self.renderer.clear()
            self.renderer.render(self.player, self.room, self.ui)
            self.update()
            time.sleep(0.1)

if __name__ == "__main__":
    game = Game()
    game.run()