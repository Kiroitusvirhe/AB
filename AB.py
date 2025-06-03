import time
import shutil
import msvcrt
import random

# --- Game Constants ---
WIDTH = 60
HEIGHT = 16

# --- Entity Classes ---
class Entity:
    """Base class for all entities (player, enemies)."""
    def __init__(self, x, char):
        self.x = x
        self.char = char
        self.attack = 1
        self.attack_speed = 1.0
        self.crit_chance = 0.05
        self.crit_damage = 2.0
        self.hp = 10
        self.max_hp = 10
        self.defence = 0
        self.health_regen = 0
        self.thorn_damage = 0
        self.lifesteal = 0.0
        self.dodge_chance = 0.0

class Player(Entity):
    """Player character."""
    def __init__(self, x):
        super().__init__(x, '@')

    def update(self):
        pass

class Enemy(Entity):
    """Enemy character with different types."""
    def __init__(self, x, enemy_type='basic'):
        # --- Updated enemy stats ---
        if enemy_type == 'basic':
            char = 'E'
            super().__init__(x, char)
            self.hp = 8
            self.max_hp = 8
            self.attack = 1
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
            self.crit_chance = 0.1
            self.crit_damage = 2.0
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
            self.attack_speed = 0.5
            self.crit_chance = 0.05
            self.crit_damage = 2.0
            self.defence = 0
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
            self.dodge_chance = 0.02
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
        return [' '] * self.width

class UI:
    """Handles UI elements and stat formatting."""
    def __init__(self):
        self.title = "ASCII Roguelike Demo"

    def get_title_line(self, pad_left, width):
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
            f"DODGE%: {int(player.dodge_chance * 100)}",
        ]
        stats += [''] * (game_height - len(stats))
        return stats

    def get_enemy_stats_lines(self, enemy, game_height):
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
    """Handles all drawing to the terminal."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.enemy = None

    def clear(self):
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

        print(ui.get_title_line(pad_left + stats_col_width, self.width))
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        for y in range(self.height):
            print(' ' * pad_left + '|' + stats_lines[y].ljust(stats_col_width), end='')
            line = room.get_landscape_line(y)
            if y == self.height - 1:
                if 0 <= player.x < self.width:
                    line[player.x] = player.char
            if self.enemy is not None and y == self.height - 1:
                if 0 <= self.enemy.x < self.width:
                    line[self.enemy.x] = self.enemy.char
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

        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        battle_log_height = 6
        if battle_log_lines is None:
            battle_log_lines = []
        for i in range(battle_log_height):
            log = battle_log_lines[i] if i < len(battle_log_lines) else ''
            print(' ' * pad_left + '|' + ' ' * stats_col_width + '|' + log.ljust(self.width) + '|' + ' ' * boss_col_width + '|')

        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

# --- Input Handler ---
class InputHandler:
    """Handles keyboard input (ESC to quit, SPACE to start)."""
    def __init__(self):
        self.quit = False
        self.space_pressed = False

    def poll(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':
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
        self.input_handler.space_pressed = False
        self.renderer.enemy = enemy
        # Always restore player position for announcements unless explicitly hiding
        visible_x = 5  # Default visible position
        original_player_x = self.player.x if self.player.x >= 0 else visible_x
        while not self.input_handler.space_pressed:
            if not show_player:
                self.player.x = -1
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
        # Restore player position after announcement if showing player
        if show_player:
            self.player.x = original_player_x
        if enemy is None:
            self.renderer.enemy = None

    def intro(self):
        self.wait_for_space("Press spacebar to start", show_player=True)

    def battle_start(self, enemy):
        self.wait_for_space("Press spacebar to start the battle", enemy=enemy, show_player=True)

    def win(self):
        self.wait_for_space("You win!\nPress spacebar to enter the next room", enemy=None, show_player=True)

    def lose(self, enemy):
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
        for x in range(self.player.x, WIDTH):
            self.player.x = x
            self.renderer.clear()
            self.renderer.render(self.player, self.room, self.ui)
            time.sleep(0.02)
        self.player.x = -1
        self.renderer.clear()
        self.renderer.render(self.player, self.room, self.ui)
        time.sleep(0.3)

    def death(self, entity):
        """Animate an entity fading out."""
        fade_chars = ['*', '.', ' ']
        old_char = entity.char
        for char in fade_chars:
            entity.char = char
            self.renderer.clear()
            self.renderer.render(self.player, self.room, self.ui)
            time.sleep(0.12)
        entity.char = old_char
        entity.x = -1  # Hide after fade
        self.renderer.clear()
        self.renderer.render(self.player, self.room, self.ui)
        time.sleep(0.2)

    def slash(self, attacker, target=None, boss_info_lines=None, battle_log_lines=None):
        """Show a directional slash effect next to the attacker, facing the target, using the main renderer."""
        y = self.room.height - 1

        if target is not None and attacker.x < target.x:
            frames = ['>', '>>']
            pos = attacker.x + 1
        else:
            frames = ['<', '<<']
            pos = attacker.x - 1

        old_get_landscape_line = self.room.get_landscape_line

        def make_slash_line(frame):
            line = [' '] * self.room.width
            if 0 <= attacker.x < self.room.width:
                line[attacker.x] = attacker.char
            if 0 <= pos < self.room.width:
                for i, ch in enumerate(frame):
                    if 0 <= pos + i < self.room.width:
                        line[pos + i] = ch
            return line

        try:
            for frame in frames:
                def patched_get_landscape_line(row):
                    if row == y:
                        return make_slash_line(frame)
                    else:
                        return old_get_landscape_line(row)
                self.room.get_landscape_line = patched_get_landscape_line
                self.renderer.clear()
                self.renderer.render(
                    self.player, self.room, self.ui,
                    boss_info_lines=boss_info_lines,
                    battle_log_lines=battle_log_lines
                )
                time.sleep(0.08)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.clear()
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines
        )

# --- Battle System Class ---
class Battle:
    """Handles the battle logic between two entities, using all stats."""
    def __init__(self, renderer, ui, room):
        self.renderer = renderer
        self.ui = ui
        self.room = room

    def attack(self, attacker, defender, boss_info_lines=None, battle_log_lines=None):
        # Play slash animation if available
        if hasattr(self, 'animations') and self.animations:
            self.animations.slash(attacker, defender, boss_info_lines, battle_log_lines)
        if random.random() < defender.dodge_chance:
            return f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"
        damage = max(1, attacker.attack - defender.defence)
        crit = False
        if random.random() < attacker.crit_chance:
            damage = int(damage * attacker.crit_damage)
            crit = True
        if attacker.lifesteal > 0:
            heal = int(damage * attacker.lifesteal)
            attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        defender.hp -= damage
        thorn_msg = ""
        if defender.thorn_damage > 0:
            attacker.hp -= defender.thorn_damage
            thorn_msg = f" {attacker.char} takes {defender.thorn_damage} thorn damage!"
        msg = f"{attacker.char} hits {defender.char} for {damage} damage"
        if crit:
            msg += " (CRIT!)"
        msg += "!" + thorn_msg
        return msg

    def battle(self, player, enemy, running_flag):
        # Find the Animations instance if available
        animations = getattr(self, 'animations', None)
        battle_log = []
        player_next_attack = 0.0
        enemy_next_attack = 0.0
        clock = 0.0
        time_step = 0.05
        while player.hp > 0 and enemy.hp > 0 and running_flag():
            acted = False
            if clock >= player_next_attack:
                msg = self.attack(
                    player, enemy,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:]
                )
                battle_log.append(msg)
                player_next_attack += 1.0 / player.attack_speed
                acted = True
            if clock >= enemy_next_attack and enemy.hp > 0:
                msg = self.attack(
                    enemy, player,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:]
                )
                battle_log.append(msg)
                enemy_next_attack += 1.0 / enemy.attack_speed
                acted = True
            if player.health_regen > 0 and int(clock * 10) % 10 == 0:
                player.hp = min(player.max_hp, player.hp + player.health_regen)
            if enemy.health_regen > 0 and int(clock * 10) % 10 == 0:
                enemy.hp = min(enemy.max_hp, enemy.hp + enemy.health_regen)
            if acted or int(clock * 10) % 2 == 0:
                self.renderer.clear()
                self.renderer.render(
                    player, self.room, self.ui,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:]
                )
            if enemy.hp <= 0:
                if hasattr(self, 'animations') and self.animations:
                    self.animations.death(enemy)
                self.renderer.enemy = None
                return "win"
            if player.hp <= 0:
                if hasattr(self, 'animations') and self.animations:
                    self.animations.death(player)
                return "lose"
            time.sleep(time_step)
            clock += time_step

# --- Main Game Loop ---
class Game:
    """Main game class. Manages game state and runs the main loop."""
    def __init__(self):
        self.player = Player(x=5)  # Initialize once, stats persist
        self.room = Room(WIDTH, HEIGHT)
        self.ui = UI()
        self.renderer = Renderer(WIDTH, HEIGHT)
        self.input_handler = InputHandler()
        self.announcements = Announcements(self.renderer, self.ui, self.room, self.player, self.input_handler)
        self.animations = Animations(self.renderer, self.room, self.ui, self.player)
        self.battle_system = Battle(self.renderer, self.ui, self.room)
        self.battle_system.animations = self.animations
        self.enemy = None
        self.running = True

    # --- Reset Methods ---
    def reset_player_stats(self):
        """Reset player stats and position for a new game."""
        # Re-initialize the player object in-place to preserve references
        self.player.__init__(x=5)

    def reset_player_position(self):
        """Only resets position, not stats."""
        self.player.x = 5

    # --- Game Logic ---
    def spawn_enemy(self):
        enemy_type = random.choice(['basic', 'speedy', 'tough'])
        self.enemy = Enemy(x=(WIDTH * 3) // 4, enemy_type=enemy_type)
        self.renderer.enemy = self.enemy

    def update(self):
        self.player.update()
        self.input_handler.poll()
        if self.input_handler.quit:
            self.running = False

    def run(self):
        while self.running:
            # Reset player stats and position at the start of a new game
            self.reset_player_stats()
            self.reset_player_position()
            self.announcements.intro()

            if self.input_handler.quit:
                return

            self.animations.player_slide_and_disappear()

            while self.running:
                self.reset_player_position()  # Reset position only
                self.spawn_enemy()
                self.announcements.battle_start(self.enemy)

                if self.input_handler.quit:
                    return

                result = self.battle_system.battle(self.player, self.enemy, lambda: self.running)

                if result == "win":
                    self.announcements.win()
                    self.animations.player_slide_and_disappear()
                else:
                    self.announcements.lose(self.enemy)
                    break  # Exit battle loop (game over)

                if self.input_handler.quit:
                    return

if __name__ == "__main__":
    print('\033[?25l', end='')
    try:
        game = Game()
        game.run()
    finally:
        print('\033[?25h', end='')