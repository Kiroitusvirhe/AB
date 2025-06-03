import os
import time
import shutil
import msvcrt
import random

# --- Game Constants ---
WIDTH = 60   # Width of the game area (number of columns)
HEIGHT = 16  # Height of the game area (number of rows)

# --- Entity Classes ---
class Entity:
    """Base class for all entities (player, enemies)."""
    def __init__(self, x, char):
        self.x = x              # X position of the entity in the game area
        self.char = char        # Character used to represent the entity on screen
        # Offensive stats
        self.attack = 1         # Attack power
        self.attack_speed = 1.0 # How fast the entity attacks (attacks per second)
        self.crit_chance = 0.05 # Chance to land a critical hit (5%)
        self.crit_damage = 2.0  # Damage multiplier for critical hits
        # Defensive stats
        self.hp = 10            # Current health points
        self.max_hp = 10        # Maximum health points
        self.defence = 0        # Defense value (reduces incoming damage)
        self.health_regen = 0   # Health regenerated per turn
        self.thorn_damage = 0   # Damage dealt back to attackers
        self.lifesteal = 0.0    # Percentage of damage healed on attack
        self.dodge_chance = 0.0 # Chance to dodge an incoming attack (0-1)

class Player(Entity):
    """Player character."""
    def __init__(self, x):
        super().__init__(x, '@')  # Player is represented by '@'

    def update(self):
        pass  # Placeholder for player update logic (e.g., movement, actions)

class Enemy(Entity):
    """Enemy character with different types."""
    def __init__(self, x, enemy_type='basic'):
        # Different enemy types have different stats and characters
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
            self.dodge_chance = 0.05
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
            self.dodge_chance = 0.15
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
            self.dodge_chance = 0.02
        else:
            char = '?'
            super().__init__(x, char)

# --- Room and UI Classes ---
class Room:
    """Represents the game area (the 'room' the player is in)."""
    def __init__(self, width, height):
        self.width = width      # Width of the room
        self.height = height    # Height of the room

    def get_landscape_line(self, y):
        # Returns a blank line for the game area (can be expanded for obstacles, etc.)
        return [' '] * self.width

class UI:
    """Handles UI elements and stat formatting (prepares data, does not print)."""
    def __init__(self):
        self.title = "ASCII Roguelike Demo"  # Title shown at the top

    def get_title_line(self, pad_left, width):
        # Returns the title line as a string, centered above the game area
        return ' ' * pad_left + self.title.center(width + 2)

    def get_player_stats_lines(self, player, game_height):
        # Prepares a list of strings for the player's stats, one per line
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
            f"DODGE%: {int(player.dodge_chance * 100)}",
        ]
        # Pad with empty lines so the stats box is as tall as the game area
        stats += [''] * (game_height - len(stats))
        return stats

    def get_enemy_stats_lines(self, enemy, game_height):
        # Prepares a list of strings for the enemy's stats, one per line
        if enemy is None:
            stats = [''] * game_height
        else:
            stats = [
                f"ENEMY: {enemy.char}",
                f"HP: {enemy.hp}/{enemy.max_hp}",
                f"ATK: {enemy.attack}",
                f"ATK SPD: {enemy.attack_speed}",
                f"CRIT%: {int(enemy.crit_chance * 100)}",
                f"CRIT DMG: {enemy.crit_damage}",
                f"DEF: {enemy.defence}",
                f"REGEN: {enemy.health_regen}",
                f"THORN: {enemy.thorn_damage}",
                f"LIFESTEAL: {enemy.lifesteal}",
                f"DODGE%: {int(enemy.dodge_chance * 100)}",
            ]
            stats += [''] * (game_height - len(stats))
        return stats

class Renderer:
    """Handles all drawing to the terminal (prints the UI and game area)."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.enemy = None  # Track current enemy for rendering

    def clear(self):
        # Move cursor to top-left instead of clearing the whole screen (reduces flicker)
        print('\033[H', end='')

    def render(self, player, room, ui, boss_info_lines=None, battle_log_lines=None, intro_message=None):
        stats_col_width = 16
        boss_col_width = 16
        term_size = shutil.get_terminal_size((80, 24))
        pad_left = (term_size.columns - (self.width + 2 + stats_col_width + boss_col_width)) // 2

        stats_lines = ui.get_player_stats_lines(player, self.height)
        if boss_info_lines is None:
            boss_info_lines = [''] * self.height
        else:
            boss_info_lines += [''] * (self.height - len(boss_info_lines))

        # Print the title and top frame of the UI
        print(ui.get_title_line(pad_left + stats_col_width, self.width))
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        # Print each row of the game area (including player and stats)
        for y in range(self.height):
            print(' ' * pad_left + '|' + stats_lines[y].ljust(stats_col_width), end='')
            line = room.get_landscape_line(y)
            # Draw player character on the bottom row of the game area
            if y == self.height - 1:
                if 0 <= player.x < self.width:
                    line[player.x] = player.char
            # Draw enemy character on the bottom row, more to the center (not at the edge)
            if self.enemy is not None and y == self.height - 1:
                if 0 <= self.enemy.x < self.width:
                    line[self.enemy.x] = self.enemy.char
            # If intro_message is set, print it centered in the game area (centered vertically and horizontally)
            if intro_message and y == self.height // 2:
                lines = intro_message.split('\n')
                for idx, msg in enumerate(lines):
                    if y + idx < self.height:
                        print('|' + msg.center(self.width) + '|', end='')
                        print(boss_info_lines[y + idx].ljust(boss_col_width) + '|')
                        break
            else:
                print('|' + ''.join(line) + '|', end='')
                print(boss_info_lines[y].ljust(boss_col_width) + '|')

        # Print the bottom frame of the game area (also top of battle log)
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        # Print the battle log area (6 lines, can be changed)
        battle_log_height = 6
        if battle_log_lines is None:
            battle_log_lines = []
        for i in range(battle_log_height):
            log = battle_log_lines[i] if i < len(battle_log_lines) else ''
            print(' ' * pad_left + '|' + ' ' * stats_col_width + '|' + log.ljust(self.width) + '|' + ' ' * boss_col_width + '|')

        # Print the bottom frame of the UI/battle log
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

# --- Input Handler ---
class InputHandler:
    """Handles keyboard input (ESC to quit, SPACE to start)."""
    def __init__(self):
        self.quit = False
        self.space_pressed = False

    def poll(self):
        # Check if a key has been pressed
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC key
                self.quit = True
            elif key == b' ':
                self.space_pressed = True

# --- Announcements Class ---
class Announcements:
    """Handles displaying announcements and intro messages."""
    def __init__(self, renderer, ui, room, player, input_handler):
        self.renderer = renderer
        self.ui = ui
        self.room = room
        self.player = player
        self.input_handler = input_handler

    def wait_for_space(self, message, enemy=None, show_player=True):
        """Show a message and wait for spacebar, centered, with optional enemy stats and player visibility."""
        self.input_handler.space_pressed = False
        # Set enemy for renderer
        self.renderer.enemy = enemy
        # Save original player x to restore after announcement if needed
        original_player_x = self.player.x
        while not self.input_handler.space_pressed:
            # Only hide player if explicitly told to (for lose screen only)
            if not show_player:
                self.player.x = -1
            else:
                # Always restore player position if show_player is True
                if original_player_x < 0:
                    self.player.x = 5  # Default position if lost
                else:
                    self.player.x = original_player_x
            self.renderer.clear()
            boss_info_lines = self.ui.get_enemy_stats_lines(enemy, self.room.height) if enemy else [''] * self.room.height
            self.renderer.render(
                self.player, self.room, self.ui,
                boss_info_lines=boss_info_lines,
                intro_message=message
            )
            self.input_handler.poll()
            time.sleep(0.05)
        # Restore player position after announcement
        if show_player:
            if original_player_x < 0:
                self.player.x = 5
            else:
                self.player.x = original_player_x
        # After announcement, clear enemy from renderer if not in pre-battle
        if enemy is None:
            self.renderer.enemy = None

    def intro(self):
        """Show intro message and wait for spacebar."""
        self.wait_for_space("Press spacebar to start", show_player=True)

    def battle_start(self, enemy):
        """Show battle start message and wait for spacebar."""
        self.wait_for_space("Press spacebar to start the battle", enemy=enemy, show_player=True)

    def win(self):
        """Show win message and wait for spacebar."""
        self.wait_for_space("You win!\nPress spacebar to enter the next room", enemy=None, show_player=True)

    def lose(self, enemy):
        """Show lose message and wait for spacebar. Player is hidden, enemy remains visible."""
        self.wait_for_space("You lose!\nPress spacebar to restart", enemy=enemy, show_player=False)

# --- Animations Class ---
class Animations:
    """Handles all game animations (player slide, attacks, etc)."""
    def __init__(self, renderer, room, ui, player):
        self.renderer = renderer
        self.room = room
        self.ui = ui
        self.player = player

    def player_slide_and_disappear(self):
        """Animate the player sliding to the right edge and disappearing."""
        for x in range(self.player.x, WIDTH):
            self.player.x = x
            self.renderer.clear()
            self.renderer.render(self.player, self.room, self.ui)
            time.sleep(0.02)
        # Hide the player after sliding out
        self.player.x = -1
        self.renderer.clear()
        self.renderer.render(self.player, self.room, self.ui)
        time.sleep(0.3)

# --- Battle System Class ---
class Battle:
    """Handles the battle logic between two entities, using all stats."""
    def __init__(self, renderer, ui, room):
        self.renderer = renderer
        self.ui = ui
        self.room = room

    def attack(self, attacker, defender):
        """
        Handles a single attack from attacker to defender, applying all stats.
        Returns a string describing the attack for the battle log.
        """
        import random

        # Dodge check
        if random.random() < defender.dodge_chance:
            return f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"

        # Calculate base damage
        damage = max(1, attacker.attack - defender.defence)

        # Critical hit check
        crit = False
        if random.random() < attacker.crit_chance:
            damage = int(damage * attacker.crit_damage)
            crit = True

        # Apply lifesteal (heal attacker)
        if attacker.lifesteal > 0:
            heal = int(damage * attacker.lifesteal)
            attacker.hp = min(attacker.max_hp, attacker.hp + heal)

        # Apply damage to defender
        defender.hp -= damage

        # Apply thorn damage (defender reflects damage back)
        thorn_msg = ""
        if defender.thorn_damage > 0:
            attacker.hp -= defender.thorn_damage
            thorn_msg = f" {attacker.char} takes {defender.thorn_damage} thorn damage!"

        # Compose log message
        msg = f"{attacker.char} hits {defender.char} for {damage} damage"
        if crit:
            msg += " (CRIT!)"
        msg += "!" + thorn_msg

        return msg

    def battle(self, player, enemy, running_flag):
        """
        Runs the autobattle between player and enemy using all stats.
        Returns "win" if player wins, "lose" if enemy wins.
        """
        battle_log = []
        player_next_attack = 0.0
        enemy_next_attack = 0.0
        clock = 0.0
        time_step = 0.05  # seconds per simulation step

        # Main battle loop
        while player.hp > 0 and enemy.hp > 0 and running_flag():
            acted = False
            # Player attacks if it's time
            if clock >= player_next_attack:
                msg = self.attack(player, enemy)
                battle_log.append(msg)
                player_next_attack += 1.0 / player.attack_speed
                acted = True
            # Enemy attacks if it's time
            if clock >= enemy_next_attack and enemy.hp > 0:
                msg = self.attack(enemy, player)
                battle_log.append(msg)
                enemy_next_attack += 1.0 / enemy.attack_speed
                acted = True
            # Regeneration for both entities (if any)
            if player.health_regen > 0 and int(clock * 10) % 10 == 0:
                player.hp = min(player.max_hp, player.hp + player.health_regen)
            if enemy.health_regen > 0 and int(clock * 10) % 10 == 0:
                enemy.hp = min(enemy.max_hp, enemy.hp + enemy.health_regen)
            # Render only if something happened or every so often
            if acted or int(clock * 10) % 2 == 0:
                self.renderer.clear()
                self.renderer.render(
                    player, self.room, self.ui,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:]
                )
            if enemy.hp <= 0:
                self.renderer.enemy = None  # Remove enemy from renderer after battle
                return "win"
            if player.hp <= 0:
                # Player disappears, enemy stays visible
                player.x = -1
                self.renderer.clear()
                self.renderer.render(
                    player, self.room, self.ui,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:]
                )
                return "lose"
            time.sleep(time_step)
            clock += time_step

# --- Main Game Loop ---
class Game:
    """Main game class. Manages game state and runs the main loop."""
    def __init__(self):
        self.player = Player(x=5)                # Create the player at position 5
        self.room = Room(WIDTH, HEIGHT)          # Create the game room
        self.ui = UI()                           # Create the UI handler
        self.renderer = Renderer(WIDTH, HEIGHT)  # Create the renderer
        self.input_handler = InputHandler()      # Create the input handler
        self.announcements = Announcements(self.renderer, self.ui, self.room, self.player, self.input_handler)
        self.animations = Animations(self.renderer, self.room, self.ui, self.player)
        self.battle_system = Battle(self.renderer, self.ui, self.room)
        self.enemy = None                        # Current enemy in the room
        self.running = True                      # Game running flag

    def spawn_enemy(self):
        """Spawn a random enemy more to the center (not at the edge)."""
        enemy_type = random.choice(['basic', 'speedy', 'tough'])
        # Place enemy at 3/4 of the width (rounded down)
        self.enemy = Enemy(x=(WIDTH * 3) // 4, enemy_type=enemy_type)
        self.renderer.enemy = self.enemy

    def update(self):
        # Update game state (player, input, etc.)
        self.player.update()
        self.input_handler.poll()
        if self.input_handler.quit:
            self.running = False

    def reset_player(self):
        """Reset player stats and position for a new game."""
        self.player = Player(x=5)

    def hard_reset(self):
        """Completely reset the game state as if starting for the first time."""
        self.reset_player()
        self.enemy = None
        self.renderer.enemy = None
        self.input_handler.space_pressed = False
        self.player.x = 5  # Ensure player is visible at start

    def run(self):
        while self.running:
            # --- Hard reset at the start of the game or after a loss ---
            self.hard_reset()
            # --- Intro ---
            self.announcements.intro()
            if self.input_handler.quit:
                return
            # --- Animation ---
            self.animations.player_slide_and_disappear()
            # --- Enter first room and battle loop ---
            while self.running:
                # Reset player position if needed
                self.player.x = 5
                # Spawn enemy
                self.spawn_enemy()
                # Show enemy stats and wait for battle start
                self.announcements.battle_start(self.enemy)
                if self.input_handler.quit:
                    return
                # Battle!
                result = self.battle_system.battle(self.player, self.enemy, lambda: self.running)
                if result == "win":
                    self.announcements.win()
                    # Slide animation to next room after win
                    self.animations.player_slide_and_disappear()
                else:
                    self.announcements.lose(self.enemy)
                    # Hard reset for a full restart
                    break  # Go back to intro loop
                if self.input_handler.quit:
                    return

if __name__ == "__main__":
    print('\033[?25l', end='')  # Hide cursor for a cleaner look
    try:
        game = Game()
        game.run()
    finally:
        print('\033[?25h', end='')  # Show cursor again on exit