import time
import shutil
import msvcrt
import random

# --- Game Constants ---
WIDTH = 60
HEIGHT = 16
PLAYER_START_X = WIDTH * 1 // 4  # Player starts at 1/4th of the width, mirroring enemy at 3/4th

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
        self.hp = 30
        self.max_hp = 30
        self.defence = 0
        self.health_regen = 0
        self.thorn_damage = 0
        self.lifesteal = 0.0
        self.dodge_chance = 0.05

class Player(Entity):
    """Player character."""
    def __init__(self, x):
        super().__init__(x, '@')
        self.xp = 0
        self.level = 1
        self.xp_to_next = 10  # Start with 10 XP for level 2
        self.regen_timer = 0.0  # Add this line

    def gain_xp(self, amount):
        leveled_up = False
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)  # XP needed increases each level
            leveled_up = True
        return leveled_up

    def upgrade_stat(self, stat):
        if stat == "attack":
            self.attack += 1
        elif stat == "attack_speed":
            self.attack_speed += 0.1
        elif stat == "crit_chance":
            self.crit_chance = min(1.0, self.crit_chance + 0.05)
        elif stat == "crit_damage":
            self.crit_damage += 0.2
        elif stat == "defence":
            self.defence += 1
        elif stat == "health_regen":
            self.health_regen += 1
        elif stat == "thorn_damage":
            self.thorn_damage += 1
        elif stat == "lifesteal":
            self.lifesteal = min(1.0, self.lifesteal + 0.05)
        elif stat == "dodge_chance":
            self.dodge_chance = min(1.0, self.dodge_chance + 0.05)
        elif stat == "max_hp":
            self.max_hp += 5
            self.hp += 5

    def reset_regen_timer(self):
        self.regen_timer = 0.0

# --- Player Job Classes ---
class Fighter(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("attack")

class Assassin(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("crit_chance")
        self.upgrade_stat("attack_speed")
        self.upgrade_stat("attack_speed")  # +2 levels to attack speed
        self.upgrade_stat("dodge_chance")

class Paladin(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("defence")
        self.upgrade_stat("max_hp")  # +5 HP

class Enemy(Entity):
    """Enemy character with different types."""
    def __init__(self, x, enemy_type='basic'):
        # --- Updated enemy stats ---
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
            self.attack_speed = 1.5
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
            f"LVL: {player.level}",
            f"XP: {player.xp}/{player.xp_to_next}",
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

    def get_room_counter_line(self, room_number):
        return f"ROOM: {room_number}"

class Renderer:
    """Handles all drawing to the terminal."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.enemy = None

    def clear(self):
        print('\033[H', end='')

    def render(self, player, room, ui, boss_info_lines=None, battle_log_lines=None, intro_message=None, room_number=None):
        self.clear()  # <-- Always clear at the start of render
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
            # --- PATCH START ---
            # Show multi-line intro_message centered vertically
            if intro_message and (self.height // 2 - 2) <= y < (self.height // 2 - 2) + len(intro_message.split('\n')):
                lines = intro_message.split('\n')
                idx = y - (self.height // 2 - 2)
                msg = lines[idx] if idx < len(lines) else ''
                print('|' + msg.center(self.width) + '|', end='')
                print(boss_info_lines[y].ljust(boss_col_width) + '|')
            else:
                if y == self.height - 1:
                    if 0 <= player.x < self.width:
                        line[player.x] = player.char
                    if self.enemy is not None and 0 <= self.enemy.x < self.width:
                        line[self.enemy.x] = self.enemy.char
                print('|' + ''.join(line) + '|', end='')
                print(boss_info_lines[y].ljust(boss_col_width) + '|')
            # --- PATCH END ---

        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        battle_log_height = 6
        if battle_log_lines is None:
            battle_log_lines = []

        # Add room counter to the first line of battle log
        room_num = room_number
        if room_num is None:
            room_num = getattr(room, 'current_room', 1)
        room_line = ui.get_room_counter_line(room_num)
        if len(battle_log_lines) == 0:
            battle_log_lines = [room_line]
        elif len(battle_log_lines) < battle_log_height:
            battle_log_lines = [room_line] + battle_log_lines

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
        self.current_room = 1  # Will be set by Game

    def wait_for_space(self, message, enemy=None, show_player=True, room_number=None):
        self.input_handler.space_pressed = False
        self.renderer.enemy = enemy
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
                intro_message=message,
                room_number=room_number if room_number is not None else getattr(self, 'current_room', 1)
            )
            self.input_handler.poll()
            time.sleep(0.05)
        if show_player:
            self.player.x = original_player_x
        if enemy is None:
            self.renderer.enemy = None

    def intro(self):
        self.wait_for_space("Press spacebar to start", show_player=True, room_number=self.current_room)

    def battle_start(self, enemy):
        self.wait_for_space("Press spacebar to start the battle", enemy=enemy, show_player=True, room_number=self.current_room)

    def win(self):
        self.wait_for_space("You win!\nPress spacebar to enter the next room", enemy=None, show_player=True, room_number=self.current_room)

    def lose(self, enemy):
        self.wait_for_space("You lose!\nPress spacebar to restart", enemy=enemy, show_player=False, room_number=self.current_room)

    def level_up_screen(self, player):
        # List of upgradable stats and their display names
        stat_options = [
            ("attack", "Attack +1"),
            ("attack_speed", "Attack Speed +0.1"),
            ("crit_chance", "Crit Chance +5%"),
            ("crit_damage", "Crit Damage +0.2"),
            ("defence", "Defence +1"),
            ("health_regen", "Regen +1"),
            ("thorn_damage", "Thorn +1"),
            ("lifesteal", "Lifesteal +5%"),
            ("dodge_chance", "Dodge +5%"),
            ("max_hp", "Max HP +5"),
        ]
        choices = random.sample(stat_options, 3)
        selected = 0

        while True:
            lines = ["LVL UP!", "", "Choose a stat to upgrade:"]
            for i, (stat, desc) in enumerate(choices):
                prefix = "-> " if i == selected else "   "
                lines.append(f"{prefix}{i+1}. {desc}")
            message = "\n".join(lines)
            self.renderer.render(self.player, self.room, self.ui, intro_message=message, room_number=self.current_room)
            # Keyboard navigation: arrows or 1/2/3
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3']:
                    selected = int(key) - 1
                    break
                elif key in [b'H', b'K', b'w']:  # Up arrow or W
                    selected = (selected - 1) % 3
                elif key in [b'P', b'M', b's']:  # Down arrow or S
                    selected = (selected + 1) % 3
                elif key == b'\r' or key == b' ':  # Enter or Space
                    break
            time.sleep(0.08)
        player.upgrade_stat(choices[selected][0])

    def job_select_screen(self):
        jobs = [
            "Fighter",
            "Assassin",
            "Paladin"
        ]
        selected = 0
        while True:
            lines = ["CHOOSE YOUR CLASS:"]
            for i, name in enumerate(jobs):
                prefix = "-> " if i == selected else "   "
                lines.append(f"{prefix}{i+1}. {name}")
            message = "\n".join(lines)
            self.renderer.render(self.player, self.room, self.ui, intro_message=message, room_number=self.current_room)
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3']:
                    selected = int(key) - 1
                    break
                elif key in [b'H', b'K', b'w']:
                    selected = (selected - 1) % 3
                elif key in [b'P', b'M', b's']:
                    selected = (selected + 1) % 3
                elif key == b'\r' or key == b' ':
                    break
            time.sleep(0.08)
        return selected

# --- Animations Class ---
class Animations:
    """Handles all game animations (player slide, attacks, etc)."""
    def __init__(self, renderer, room, ui, player):
        self.renderer = renderer
        self.room = room
        self.ui = ui
        self.player = player
        self.current_room = 1  # Will be set by Game

    def player_slide_and_disappear(self):
        for x in range(self.player.x, WIDTH):
            self.player.x = x
            self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room)
            time.sleep(0.02)
        self.player.x = -1
        self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room)
        time.sleep(0.3)

    def death(self, entity):
        fade_chars = ['*', '.', ' ']
        old_char = entity.char
        for char in fade_chars:
            entity.char = char
            self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room)
            time.sleep(0.12)
        entity.char = old_char
        entity.x = -1
        self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room)
        time.sleep(0.2)

    def crit_effect(self, attacker, boss_info_lines=None, battle_log_lines=None):
        y = self.room.height - 2
        old_get_landscape_line = self.room.get_landscape_line

        def make_crit_line():
            line = [' '] * self.room.width
            word = 'CRIT!'
            start = max(0, min(self.room.width - len(word), attacker.x - len(word)//2))
            for i, ch in enumerate(word):
                line[start + i] = ch
            return line

        try:
            def patched_get_landscape_line(row):
                if row == y:
                    return make_crit_line()
                else:
                    return old_get_landscape_line(row)
            self.room.get_landscape_line = patched_get_landscape_line
            self.renderer.render(
                self.player, self.room, self.ui,
                boss_info_lines=boss_info_lines,
                battle_log_lines=battle_log_lines,
                room_number=self.current_room
            )
            time.sleep(0.8)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room
        )

    def dodge_effect(self, target, boss_info_lines=None, battle_log_lines=None):
        y = self.room.height - 2
        old_get_landscape_line = self.room.get_landscape_line

        def make_dodge_line():
            line = [' '] * self.room.width
            word = 'DODGED!'
            start = max(0, min(self.room.width - len(word), target.x - len(word)//2))
            for i, ch in enumerate(word):
                line[start + i] = ch
            return line

        try:
            def patched_get_landscape_line(row):
                if row == y:
                    return make_dodge_line()
                else:
                    return old_get_landscape_line(row)
            self.room.get_landscape_line = patched_get_landscape_line
            self.renderer.render(
                self.player, self.room, self.ui,
                boss_info_lines=boss_info_lines,
                battle_log_lines=battle_log_lines,
                room_number=self.current_room
            )
            time.sleep(0.8)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room
        )

    def slash(self, attacker, target=None, boss_info_lines=None, battle_log_lines=None):
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
                self.renderer.render(
                    self.player, self.room, self.ui,
                    boss_info_lines=boss_info_lines,
                    battle_log_lines=battle_log_lines,
                    room_number=self.current_room
                )
                time.sleep(0.08)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room
        )

# --- Battle System Class ---
class Battle:
    """Handles the battle logic between two entities, using all stats."""
    def __init__(self, renderer, ui, room):
        self.renderer = renderer
        self.ui = ui
        self.room = room
        self.current_room = 1  # Will be set by Game

    def attack(self, attacker, defender, boss_info_lines=None, battle_log_lines=None):
        # Play slash/crit/dodge animation if available
        if hasattr(self, 'animations') and self.animations:
            # Dodge check first
            if random.random() < defender.dodge_chance:
                self.animations.dodge_effect(defender, boss_info_lines, battle_log_lines)
                return f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"
            # Crit check
            crit = False
            if random.random() < attacker.crit_chance:
                damage = int(max(1, attacker.attack - defender.defence) * attacker.crit_damage)
                crit = True
                self.animations.crit_effect(attacker, boss_info_lines, battle_log_lines)
            else:
                damage = max(1, attacker.attack - defender.defence)
                self.animations.slash(attacker, defender, boss_info_lines, battle_log_lines)
        else:
            # No animations
            if random.random() < defender.dodge_chance:
                return f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"
            crit = False
            if random.random() < attacker.crit_chance:
                damage = int(max(1, attacker.attack - defender.defence) * attacker.crit_damage)
                crit = True
            else:
                damage = max(1, attacker.attack - defender.defence)

        if attacker.lifesteal > 0:
            heal = int(damage * attacker.lifesteal)
            attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        defender.hp -= damage
        thorn_msg = ""
        if defender.thorn_damage > 0:
            attacker.hp -= defender.thorn_damage
            thorn_msg = f" {attacker.char} takes {defender.thorn_damage} thorn damage!"
        msg = f"{attacker.char} hits {defender.char} for {damage} damage"
        if 'crit' in locals() and crit:
            msg += " (CRIT!)"
        msg += "!" + thorn_msg
        return msg

    def battle(self, player, enemy, running_flag):
        animations = getattr(self, 'animations', None)
        battle_log = []
        player_next_attack = 0.0
        enemy_next_attack = 0.0
        clock = 0.0
        time_step = 0.05
        leveled_up_this_battle = False
        prev_level = player.level
        regen_base_interval = 6.0  # seconds for 1 regen
        player.regen_timer = 0.0  # Reset at start
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
            # --- Regen logic with exponential scaling, no minimum interval ---
            if player.health_regen > 0:
                interval = regen_base_interval * (0.95 ** (player.health_regen - 1))
                player.regen_timer += time_step
                if player.regen_timer >= interval:
                    healed = min(1, player.max_hp - player.hp)
                    if healed > 0:
                        player.hp += healed
                        battle_log.append(f"{player.char} regenerates {healed} HP!")
                    player.regen_timer = 0.0
            if enemy.health_regen > 0 and int(clock * 10) % 10 == 0:
                healed = min(enemy.health_regen, enemy.max_hp - enemy.hp)
                if healed > 0:
                    enemy.hp += healed
                    battle_log.append(f"{enemy.char} regenerates {healed} HP!")
            if acted or int(clock * 10) % 2 == 0:
                self.renderer.render(
                    player, self.room, self.ui,
                    boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                    battle_log_lines=battle_log[-6:],
                    room_number=self.current_room
                )
            if enemy.hp <= 0:
                if hasattr(self, 'animations') and self.animations:
                    self.animations.death(enemy)
                self.renderer.enemy = None
                # --- Level up logic here ---
                leveled_up = player.gain_xp(6)
                if leveled_up and hasattr(self, 'announcements') and self.announcements:
                    self.announcements.level_up_screen(player)
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
        self.player = Player(x=PLAYER_START_X)
        self.room = Room(WIDTH, HEIGHT)
        self.ui = UI()
        self.renderer = Renderer(WIDTH, HEIGHT)
        self.input_handler = InputHandler()
        self.announcements = Announcements(self.renderer, self.ui, self.room, self.player, self.input_handler)
        self.animations = Animations(self.renderer, self.room, self.ui, self.player)
        self.battle_system = Battle(self.renderer, self.ui, self.room)
        self.battle_system.animations = self.animations
        self.battle_system.announcements = self.announcements  # <-- Add this line
        self.enemy = None
        self.running = True
        self.current_room = 1  # Add this line to track room number

        # Link room number to other classes
        self.announcements.current_room = self.current_room
        self.animations.current_room = self.current_room
        self.battle_system.current_room = self.current_room

    # --- Reset Methods ---
    def reset_player_stats(self):
        """Reset player stats and position for a new game."""
        # This will be handled by job selection now
        pass

    def reset_player_position(self):
        """Only resets position, not stats."""
        self.player.x = PLAYER_START_X  # Use new constant

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
            # --- Job selection ---
            self.announcements.intro()
            if self.input_handler.quit:
                return
            # --- Reset player to base Player for intro screen (UI box reset) ---
            self.player = Player(x=PLAYER_START_X)
            self.announcements.player = self.player
            self.animations.player = self.player
            # --- Job selection continues ---
            job_idx = self.announcements.job_select_screen()
            if job_idx == 0:
                self.player = Fighter(x=PLAYER_START_X)
            elif job_idx == 1:
                self.player = Assassin(x=PLAYER_START_X)
            else:
                self.player = Paladin(x=PLAYER_START_X)
            self.reset_player_position()
            self.current_room = 1  # Reset room counter on new game

            # Update room number and player reference in other classes
            self.announcements.player = self.player
            self.announcements.current_room = self.current_room
            self.animations.player = self.player
            self.animations.current_room = self.current_room
            self.battle_system.current_room = self.current_room

            self.animations.player_slide_and_disappear()

            while self.running:
                self.reset_player_position()
                self.spawn_enemy()
                self.announcements.current_room = self.current_room
                self.animations.current_room = self.current_room
                self.battle_system.current_room = self.current_room
                self.announcements.battle_start(self.enemy)

                if self.input_handler.quit:
                    return

                result = self.battle_system.battle(self.player, self.enemy, lambda: self.running)

                if result == "win":
                    self.current_room += 1  # Increment room counter
                    self.announcements.current_room = self.current_room
                    self.animations.current_room = self.current_room
                    self.battle_system.current_room = self.current_room
                    self.announcements.win()
                    self.animations.player_slide_and_disappear()
                else:
                    self.announcements.lose(self.enemy)
                    break

                if self.input_handler.quit:
                    return

if __name__ == "__main__":
    print('\033[?25l', end='')
    try:
        game = Game()
        game.run()
    finally:
        print('\033[?25h', end='')