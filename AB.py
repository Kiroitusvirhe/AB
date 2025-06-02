import os
import time
import shutil
import msvcrt

# --- Game Constants ---
WIDTH = 60
HEIGHT = 16

# --- Entity Classes ---
class Entity:
    """Base class for all entities (player, enemies)."""
    def __init__(self, x, char):
        self.x = x
        self.char = char
        # Offensive stats
        self.attack = 1
        self.attack_speed = 1.0
        self.crit_chance = 0.05
        self.crit_damage = 2.0
        # Defensive stats
        self.hp = 10
        self.max_hp = 10
        self.defence = 0
        self.health_regen = 0
        self.thorn_damage = 0
        self.lifesteal = 0.0

class Player(Entity):
    """Player character."""
    def __init__(self, x):
        super().__init__(x, '@')

    def update(self):
        pass  # Placeholder for player update logic

class Enemy(Entity):
    """Enemy character with different types."""
    def __init__(self, x, enemy_type='basic'):
        if enemy_type == 'basic':
            char = 'E'
            super().__init__(x, char)
            self.hp = 8
            self.max_hp = 8
            self.attack = 2
            self.attack_speed = 1.0
            self.crit_chance = 0.1
            self.crit_damage = 2.0
            self.defence = 0
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
        elif enemy_type == 'speedy':
            char = 'S'
            super().__init__(x, char)
            self.hp = 5
            self.max_hp = 5
            self.attack = 1
            self.attack_speed = 2.0
            self.crit_chance = 0.2
            self.crit_damage = 1.5
            self.defence = 0
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
        elif enemy_type == 'tough':
            char = 'O'
            super().__init__(x, char)
            self.hp = 15
            self.max_hp = 15
            self.attack = 1
            self.attack_speed = 0.7
            self.crit_chance = 0.05
            self.crit_damage = 2.5
            self.defence = 2
            self.health_regen = 1
            self.thorn_damage = 1
            self.lifesteal = 0.0
        else:
            char = '?'
            super().__init__(x, char)

# --- Room and UI Classes ---
class Room:
    """Represents the game area."""
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_landscape_line(self, y):
        # Returns a blank line for the game area
        return [' '] * self.width

class UI:
    """Handles UI elements and stat formatting."""
    def __init__(self):
        self.title = "ASCII Roguelike Demo"

    def get_title_line(self, pad_left, width):
        # Return the title line as a string, centered
        return ' ' * pad_left + self.title.center(width + 2)

    def get_player_stats_lines(self, player, game_height):
        stats = [
            f"HP: {player.hp}/{player.max_hp}",
            f"ATK: {player.attack}",
            f"ATK SPD: {player.attack_speed}",
            f"CRIT%: {int(player.crit_chance * 100)}",
            f"CRIT DMG: {player.crit_damage}",
            f"DEF: {player.defence}",
            f"REGEN: {player.health_regen}",
            f"THORN: {player.thorn_damage}",
            f"LIFESTEAL: {player.lifesteal}",
        ]
        stats += [''] * (game_height - len(stats))
        return stats

# --- Renderer Class ---
class Renderer:
    """Handles all drawing to the terminal."""
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render(self, player, room, ui, boss_info_lines=None, battle_log_lines=None):
        # Layout constants
        stats_col_width = 16
        boss_col_width = 16
        term_size = shutil.get_terminal_size((80, 24))
        pad_left = (term_size.columns - (self.width + 2 + stats_col_width + boss_col_width)) // 2

        # Prepare UI/stat/boss info lines
        stats_lines = ui.get_player_stats_lines(player, self.height)
        if boss_info_lines is None:
            boss_info_lines = [''] * self.height
        else:
            boss_info_lines += [''] * (self.height - len(boss_info_lines))

        # Title and top frame
        print(ui.get_title_line(pad_left + stats_col_width, self.width))
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        # Game area (player at the bottom row)
        for y in range(self.height):
            print(' ' * pad_left + '|' + stats_lines[y].ljust(stats_col_width), end='')
            line = room.get_landscape_line(y)
            # Draw player on the bottom row
            if y == self.height - 1:
                if 0 <= player.x < self.width:
                    line[player.x] = player.char
            print('|' + ''.join(line) + '|', end='')
            print(boss_info_lines[y].ljust(boss_col_width) + '|')

        # Game screen bottom & battle log top (shared)
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        # Battle log extension (6 lines)
        battle_log_height = 6
        if battle_log_lines is None:
            battle_log_lines = []
        for i in range(battle_log_height):
            log = battle_log_lines[i] if i < len(battle_log_lines) else ''
            print(' ' * pad_left + '|' + ' ' * stats_col_width + '|' + log.ljust(self.width) + '|' + ' ' * boss_col_width + '|')

        # UI/battle log bottom
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

# --- Input Handler ---
class InputHandler:
    """Handles keyboard input."""
    def __init__(self):
        self.quit = False

    def poll(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':
                self.quit = True

# --- Main Game Loop ---
class Game:
    """Main game class."""
    def __init__(self):
        self.player = Player(x=5)
        self.room = Room(WIDTH, HEIGHT)
        self.ui = UI()
        self.renderer = Renderer(WIDTH, HEIGHT)
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