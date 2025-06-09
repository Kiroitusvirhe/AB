import time
import shutil
import msvcrt
import random

# --- Game Constants ---
WIDTH = 60
HEIGHT = 17  # Increased by 1 for even bottom boxes
PLAYER_START_X = WIDTH * 1 // 4  # Player starts at 1/4th of the width, mirroring enemy at 3/4th

class Skill:
    """Base class for all skills."""
    char = '?'
    def __init__(self, name, description, cooldown):
        self.name = name
        self.description = description
        self.cooldown = cooldown
        self.cooldown_timer = 0.0

    def use(self, player, *args, **kwargs):
        """Override in subclasses. Should return a log string or None."""
        return None

class BigSlashSkill(Skill):
    char = 'S'
    def __init__(self):
        super().__init__("Big Slash", "Deal double damage to all enemies.", cooldown=8.0)

    def use(self, player, enemies):
        if player.can_use_skill():
            log = []
            for enemy in enemies:
                damage = max(0, player.attack * 2 - enemy.defence)
                enemy.hp -= damage
                log.append(f"{enemy.char}: {damage:.0f} damage!")
            player.skill_cooldown_timer = 0.0
            return f"BIG SLASH! " + ", ".join(log)
        return None

class DoubleAttackSkill(Skill):
    char = 'D'
    def __init__(self):
        super().__init__("Double Attack", "Attack twice with bonus crit chance.", cooldown=6.0)

    def use(self, player, enemy):
        if player.can_use_skill():
            results = []
            orig_crit = player.crit_chance
            player.crit_chance = min(1.0, player.crit_chance + 0.10)
            for _ in range(2):
                damage = max(1, player.attack - enemy.defence)
                crit = False
                if random.random() < player.crit_chance:
                    damage = int(damage * player.crit_damage)
                    crit = True
                enemy.hp -= damage
                results.append(f"{damage:.0f}{' (CRIT!)' if crit else ''} damage!")
            player.crit_chance = orig_crit
            player.skill_cooldown_timer = 0.0
            return f"DOUBLE ATTACK: {' + '.join(results)}"
        return None

class BlessingLightSkill(Skill):
    char = 'L'
    def __init__(self):
        super().__init__("Blessing Light", "Heal 10% of max HP.", cooldown=12.0)

    def use(self, player):
        if player.can_use_skill():
            heal = max(1, int(player.max_hp * 0.10))
            player.hp = min(player.max_hp, player.hp + heal)
            player.skill_cooldown_timer = 0.0
            return f"Paladin uses BLESSING LIGHT! (+{heal:.0f} HP)"
        return None
    
class ThornBurstSkill(Skill):
    char = 'T'
    def __init__(self):
        super().__init__("Thorn Burst", "Deal your thorn damage to all enemies.", cooldown=7.0)
    def use(self, player, enemies):
        for enemy in enemies:
            enemy.hp -= player.thorn_damage
        self.cooldown_timer = 0.0
        return f"THORN BURST! {player.thorn_damage:.0f} dmg to all!"

class LuckyStrikeSkill(Skill):
    char = '$'
    def __init__(self):
        super().__init__("Lucky Strike", "Deal bonus damage equal to your luck.", cooldown=6.0)
    def use(self, player, enemy):
        damage = max(1, player.attack - enemy.defence) + player.luck
        enemy.hp -= damage
        self.cooldown_timer = 0.0
        return f"LUCKY STRIKE! {enemy.char} takes {damage:.0f} dmg!"

class RegenWaveSkill(Skill):
    char = 'R'
    def __init__(self):
        super().__init__("Regen Wave", "Heal for 2x your regen.", cooldown=8.0)
    def use(self, player):
        heal = max(1, player.health_regen * 2)
        player.hp = min(player.max_hp, player.hp + heal)
        self.cooldown_timer = 0.0
        return f"REGEN WAVE! Heal {heal:.0f} HP!"

class CritShieldSkill(Skill):
    char = '#'
    def __init__(self):
        super().__init__("Shield Wall", "Shield: 3x your defence for 3s.", cooldown=10.0)
    def use(self, player):
        if "crit_shield" not in player.timed_effects:
            shield = max(1, player.defence * 3)
            player.timed_effects["crit_shield"] = {"value": shield, "timer": 3.0}
            self.cooldown_timer = 0.0
            return f"SHIELD WALL! Shield {shield:.0f} HP (3s)!"
        else:
            return "SHIELD WALL is active!"

class LifestealNovaSkill(Skill):
    char = 'N'
    def __init__(self):
        super().__init__("Lifesteal Nova", "Hit all enemies, heal for total dealt.", cooldown=9.0)
    def use(self, player, enemies):
        if not enemies:
            self.cooldown_timer = 0.0
            return "LIFESTEAL NOVA! No enemies to hit."
        total = 0
        for enemy in enemies:
            damage = max(1, player.attack - enemy.defence)
            enemy.hp -= damage
            total += damage
        player.hp = min(player.max_hp, player.hp + total)
        self.cooldown_timer = 0.0
        return f"LIFESTEAL NOVA! {player.attack:.0f} dmg to all, heal {total:.0f}!"

class CounterDodgeSkill(Skill):
    char = 'C'
    def __init__(self):
        super().__init__("Counter Dodge", "Dodging has a 50% chance to counterattack.", cooldown=0.0)
    def use(self, player):
        # This skill is passive, so nothing to do on use
        return None

class GoldRushSkill(Skill):
    char = 'G'
    def __init__(self):
        super().__init__("Gold Rush", "Gain 2 gold every 8s.", cooldown=8.0)
    def use(self, player):
        player.gold += 2
        self.cooldown_timer = 0.0
        return f"GOLD RUSH! You gain 2 gold!"

class GuaranteedCritSkill(Skill):
    char = '!'
    def __init__(self):
        super().__init__("Sure Crit", "Next attack is a guaranteed crit.", cooldown=7.0)
    def use(self, player, enemy):
        damage = int(max(1, player.attack - enemy.defence) * player.crit_damage)
        enemy.hp -= damage
        self.cooldown_timer = 0.0
        return f"SURE CRIT! {enemy.char} takes {damage:.0f} CRIT dmg!"

class AdrenalineRushSkill(Skill):
    char = 'A'
    def __init__(self):
        super().__init__("Adrenaline Rush", "+50% attack speed for 3s.", cooldown=10.0)
    def use(self, player):
        if "adrenaline" not in player.timed_effects:
            boost = player.attack_speed * 0.5
            player.timed_effects["adrenaline"] = {"value": boost, "timer": 3.0}
            player.attack_speed += boost
            self.cooldown_timer = 0.0
            return "ADRENALINE RUSH! Atk speed up!"
        else:
            return "ADRENALINE already active!"

class JackpotSkill(Skill):
    char = 'J'
    def __init__(self):
        super().__init__("Jackpot", "Gain gold equal to your luck.", cooldown=10.0)
    def use(self, player):
        gold = player.luck
        player.gold += gold
        self.cooldown_timer = 0.0
        return f"JACKPOT! You gain {gold} gold!"

class GambleSkill(Skill):
    char = '?'
    def __init__(self):
        super().__init__("Gamble", "", cooldown=7.0)  # Leave description blank

    def get_description(self, player):
        win_chance = min(0.5 + 0.03 * player.luck, 0.8)
        lose_chance = 1.0 - win_chance
        return f"{int(win_chance*100)}%: gain 10 gold, {int(lose_chance*100)}%: lose 5 HP."

    def use(self, player):
        win_chance = min(0.5 + 0.03 * player.luck, 0.8)
        lose_chance = 1.0 - win_chance
        self.description = self.get_description(player)
        if random.random() < win_chance:
            player.gold += 10
            result = "win 10 gold!"
        else:
            player.hp = max(1, player.hp - 5)
            result = "lose 5 HP!"
        self.cooldown_timer = 0.0
        return f"GAMBLE! You {result}"

class GlassCannonSkill(Skill):
    char = 'g'
    def __init__(self):
        super().__init__("Glass Cannon", "+3 atk, -10 max HP (permanent).", cooldown=0.0)
    def use(self, player):
        if "GlassCannonSkill" in player.permanent_skills_used:
            return None
        player.attack += 3
        player.max_hp = max(1, player.max_hp - 10)
        player.hp = min(player.hp, player.max_hp)
        player.permanent_skills_used.add("GlassCannonSkill")
        self.cooldown_timer = 0.0
        return "GLASS CANNON! +3 atk, -10 max HP!"

class ClumsySwingSkill(Skill):
    char = 'Z'
    def __init__(self):
        super().__init__("Clumsy Swing", "2x dmg, 30% chance to miss.", cooldown=8.0)
    def use(self, player, enemy):
        if random.random() < 0.7:
            self.cooldown_timer = 0.0
            return "CLUMSY SWING! You miss!"
        damage = int(max(1, player.attack * 2 - enemy.defence))
        enemy.hp -= damage
        self.cooldown_timer = 0.0
        return f"CLUMSY SWING! {enemy.char} takes {damage:.0f} dmg!"

class UnstablePowerSkill(Skill):
    char = 'U'
    def __init__(self):
        super().__init__("Unstable Power", "2x atk (1 turn), then 0.5x atk (2 turns).", cooldown=10.0)
    def use(self, player):
        if "unstable_power" not in player.timed_effects:
            player.attack *= 2
            player.timed_effects["unstable_power"] = {"stage": 1, "timer": 1.0}
            self.cooldown_timer = 0.0
            return "UNSTABLE POWER! 2x atk!"
        else:
            return "UNSTABLE POWER already active!"

class InvincibleSkill(Skill):
    char = 'I'
    def __init__(self):
        super().__init__("Invincible", "No damage taken for 2s.", cooldown=12.0)
    def use(self, player):
        if "invincible" not in player.timed_effects:
            player.timed_effects["invincible"] = {"timer": 2.0}
            self.cooldown_timer = 0.0
            return "INVINCIBLE! No damage for 2s!"
        else:
            return "INVINCIBLE already active!"

class IronWillSkill(Skill):
    char = 'W'
    def __init__(self):
        super().__init__("Iron Will", "+10 max HP (permanent).", cooldown=0.0)
    def use(self, player):
        if "IronWillSkill" in player.permanent_skills_used:
            return None
        player.max_hp += 10
        player.hp += 10
        player.permanent_skills_used.add("IronWillSkill")
        self.cooldown_timer = 0.0
        return "IRON WILL! +10 max HP!"

class SharpenedMindSkill(Skill):
    char = 'M'
    def __init__(self):
        super().__init__("Sharpened Mind", "+1 attack (permanent).", cooldown=0.0)
    def use(self, player):
        if "SharpenedMindSkill" in player.permanent_skills_used:
            return None
        player.attack += 1  # Directly increase attack, not via stat_boosts
        player.permanent_skills_used.add("SharpenedMindSkill")
        self.cooldown_timer = 0.0
        return "SHARPENED MIND! +1 attack!"

class CowardsGraceSkill(Skill):
    char = 'V'
    def __init__(self):
        super().__init__("Coward's Grace", "+10% dodge, -5 max HP (permanent).", cooldown=0.0)
    def use(self, player):
        if "CowardsGraceSkill" in player.permanent_skills_used:
            return None
        player.dodge_chance = min(0.7, player.dodge_chance + 0.10)
        player.max_hp = max(1, player.max_hp - 5)
        player.hp = min(player.hp, player.max_hp)
        player.permanent_skills_used.add("CowardsGraceSkill")
        self.cooldown_timer = 0.0
        return "COWARD'S GRACE! +10% dodge, -5 max HP!"

class LeadFeetSkill(Skill):
    char = 'F'
    def __init__(self):
        super().__init__("Lead Feet", "+5 defence, -10% dodge (permanent).", cooldown=0.0)
    def use(self, player):
        if "LeadFeetSkill" in player.permanent_skills_used:
            return None
        player.defence += 5
        player.dodge_chance = max(0.0, player.dodge_chance - 0.10)
        player.permanent_skills_used.add("LeadFeetSkill")
        self.cooldown_timer = 0.0
        return "LEAD FEET! +5 def, -10% dodge!"

class BloodPactSkill(Skill):
    char = 'P'
    def __init__(self):
        super().__init__("Blood Pact", "2x attack speed, -15 max HP (permanent).", cooldown=0.0)
    def use(self, player):
        if "BloodPactSkill" in player.permanent_skills_used:
            return None
        player.attack_speed *= 2  # Double the attack speed
        player.max_hp = max(1, player.max_hp - 15)
        player.hp = min(player.hp, player.max_hp)
        player.permanent_skills_used.add("BloodPactSkill")
        self.cooldown_timer = 0.0
        return "BLOOD PACT! 2x atk spd, -15 max HP!"
    
class BlindingFlashSkill(Skill):
    char = 'B'
    def __init__(self):
        super().__init__("Blinding Flash", "All enemies skip their next attack.", cooldown=10.0)
    def use(self, player, enemies):
        for enemy in enemies:
            if not hasattr(enemy, "skip_turns"):
                enemy.skip_turns = 0
            enemy.skip_turns += 1
        self.cooldown_timer = 0.0
        return "BLINDING FLASH! All enemies are stunned for 1 turn!"

class ScholarSkill(Skill):
    char = 'S'
    def __init__(self):
        super().__init__("Scholar", "+30% XP gain (permanent).", cooldown=0.0)
    def use(self, player):
        if "ScholarSkill" in player.permanent_skills_used:
            return None
        player.xp_gain_multiplier = getattr(player, "xp_gain_multiplier", 1.0) * 1.3
        player.permanent_skills_used.add("ScholarSkill")
        self.cooldown_timer = 0.0
        return "SCHOLAR! +30% XP gain!"

class QuickStepSkill(Skill):
    char = 'Q'
    def __init__(self):
        super().__init__("Quick Step", "+10% dodge for first 5s of each battle.", cooldown=0.0)
    def use(self, player):
        if "QuickStepSkill" in player.permanent_skills_used:
            return None
        player.permanent_skills_used.add("QuickStepSkill")
        # Passive, handled in battle logic
        return "QUICK STEP! +10% dodge for first 5s of each battle!"

class SteadyHandsSkill(Skill):
    char = 'H'
    def __init__(self):
        super().__init__("Steady Hands", "-10% crit chance, +2 defence (permanent).", cooldown=0.0)
    def use(self, player):
        if "SteadyHandsSkill" in player.permanent_skills_used:
            return None
        player.crit_chance = max(0.0, player.crit_chance - 0.10)
        player.defence += 2
        player.permanent_skills_used.add("SteadyHandsSkill")
        return "STEADY HANDS! -10% crit, +2 defence!"

class HeavyHitterSkill(Skill):
    char = 'Y'
    def __init__(self):
        super().__init__("Heavy Hitter", "First attack in each battle deals double damage.", cooldown=0.0)
    def use(self, player):
        if "HeavyHitterSkill" in player.permanent_skills_used:
            return None
        player.permanent_skills_used.add("HeavyHitterSkill")
        # Passive, handled in battle logic
        return "HEAVY HITTER! First attack in each battle deals double damage!"
    
class TreasureHunterSkill(Skill):
    char = 'T'
    def __init__(self):
        super().__init__("Treasure Hunter", "+15% chance to find loot after battles (passive).", cooldown=0.0)
    def use(self, player):
        if "TreasureHunterSkill" in player.permanent_skills_used:
            return None
        player.loot_chance_bonus = getattr(player, "loot_chance_bonus", 0.0) + 0.15
        player.permanent_skills_used.add("TreasureHunterSkill")
        return "TREASURE HUNTER! +15% loot chance!"


SKILL_POOL = [
    ThornBurstSkill,
    LuckyStrikeSkill,
    RegenWaveSkill,
    CritShieldSkill,
    LifestealNovaSkill,
    CounterDodgeSkill,
    GoldRushSkill,
    GuaranteedCritSkill,
    AdrenalineRushSkill,
    JackpotSkill,
    GambleSkill,
    GlassCannonSkill,
    ClumsySwingSkill,
    UnstablePowerSkill,
    InvincibleSkill,
    IronWillSkill,
    SharpenedMindSkill,
    CowardsGraceSkill,
    LeadFeetSkill,
    BloodPactSkill,
    BlindingFlashSkill,
    ScholarSkill,
    QuickStepSkill,   
    SteadyHandsSkill,  
    HeavyHitterSkill,
    TreasureHunterSkill,

]  
    
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
        self.luck = 0  # <--- Add this line

class Player(Entity):
    """Player character."""
    def __init__(self, x):
        super().__init__(x, '@')
        self.xp = 0
        self.level = 1
        self.xp_to_next = 10  # Start with 10 XP for level 2
        self.regen_timer = 0.0
        self.skill_cooldown = 10.0  # Default, override in subclasses
        self.skill_cooldown_timer = 0.0
        self.potions = [None, None, None, None]  # 4 potion slots
        self.equipment_items = [None, None, None, None]  # 4 equipment slots
        self.luck = 0  # <--- Add this line
        self.lifesteal_pool = 0.0  # <--- Add this line for cumulative lifesteal
        self.gold = 0
        self.skills = []
        self.timed_effects = {}  # e.g. {"crit_shield": {"value": 10, "timer": 3.0}}
        self.permanent_skills_used = set()
        self.boss_xp_bonus = 1.0

    def gain_xp(self, amount):
        leveled_up = False
        skill_mult = getattr(self, "xp_gain_multiplier", 1.0)
        boss_mult = getattr(self, "boss_xp_bonus", 1.0)
        self.xp += int(amount * skill_mult * boss_mult)
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            leveled_up = True
        return leveled_up

    def upgrade_stat(self, stat):
        if stat == "attack":
            self.attack += 1.2
        elif stat == "attack_speed":
            self.attack_speed += 0.12
        elif stat == "crit_chance":
            self.crit_chance = min(1.0, self.crit_chance + 0.05)
        elif stat == "crit_damage":
            self.crit_damage += 0.2
        elif stat == "defence":
            self.defence += 1
        elif stat == "health_regen":
            self.health_regen += 2
        elif stat == "thorn_damage":
            self.thorn_damage += 1
        elif stat == "lifesteal":
            self.lifesteal = min(1.0, self.lifesteal + 0.05)
        elif stat == "dodge_chance":
            self.dodge_chance = min(0.7, self.dodge_chance + 0.05)
        elif stat == "max_hp":
            self.max_hp += 6
            self.hp += 6
        elif stat == "luck":
            self.luck = min(10, self.luck + 1)

    def reset_regen_timer(self):
        self.regen_timer = 0.0

    def can_use_skill(self):
        return self.skill_cooldown_timer >= self.skill_cooldown

    def use_skill(self, *args, **kwargs):
        return None  # To be overridden

    def update_skill_timer(self, dt):
        self.skill_cooldown_timer += dt

    def equip(self, item):
        stat_map = {
            Sword: "attack",
            Shield: "defence",
            Armor: "max_hp",
            Fangs: "lifesteal",
            Boots: "dodge_chance",
            Amulet: "crit_chance",
            Gem: "crit_damage",
            Thorns: "thorn_damage",
            Ring: "health_regen",
            Gloves: "attack_speed",
        }
        for cls, stat in stat_map.items():
            if isinstance(item, cls):
                for _ in range(item.level):
                    self.upgrade_stat(stat)
                # Apply tier bonus stats
                if hasattr(item, "bonus_stats"):
                    if not hasattr(self, "_equipment_bonus_applied"):
                        self._equipment_bonus_applied = {}
                    for bonus_stat, bonus in item.bonus_stats.items():
                        # Save original value if not already saved
                        if (id(item), bonus_stat) not in self._equipment_bonus_applied:
                            self._equipment_bonus_applied[(id(item), bonus_stat)] = getattr(self, bonus_stat)
                        # Apply bonus multiplicatively
                        setattr(self, bonus_stat, getattr(self, bonus_stat) * (1 + bonus))
                if not hasattr(self, 'equipment'):
                    self.equipment = {}
                self.equipment[stat] = item
                break

    def downgrade_stat(self, stat):
        # This should reverse the effect of upgrade_stat
        if stat == "attack":
            self.attack = max(1, self.attack - 1)
        elif stat == "attack_speed":
            self.attack_speed = max(0.1, self.attack_speed - 0.1)
        elif stat == "crit_chance":
            self.crit_chance = max(0.0, self.crit_chance - 0.05)
        elif stat == "crit_damage":
            self.crit_damage = max(1.0, self.crit_damage - 0.2)
        elif stat == "defence":
            self.defence = max(0, self.defence - 1)
        elif stat == "health_regen":
            self.health_regen = max(0, self.health_regen - 1)
        elif stat == "thorn_damage":
            self.thorn_damage = max(0, self.thorn_damage - 1)
        elif stat == "lifesteal":
            self.lifesteal = max(0.0, self.lifesteal - 0.05)
        elif stat == "dodge_chance":
            self.dodge_chance = max(0.0, self.dodge_chance - 0.05)
            self.dodge_chance = min(self.dodge_chance, 0.7)  # Ensure cap after downgrade
        elif stat == "max_hp":
            self.max_hp = max(1, self.max_hp - 5)
            self.hp = min(self.hp, self.max_hp)
        elif stat == "luck":
            self.luck = max(0, self.luck - 1)  # <--- Add this line

    def unequip(self, item):
        stat_map = {
            Sword: "attack",
            Shield: "defence",
            Armor: "max_hp",
            Fangs: "lifesteal",
            Boots: "dodge_chance",
            Amulet: "crit_chance",
            Gem: "crit_damage",
            Thorns: "thorn_damage",
            Ring: "health_regen",
            Gloves: "attack_speed",
        }
        for cls, stat in stat_map.items():
            if isinstance(item, cls):
                for _ in range(item.level):
                    self.downgrade_stat(stat)
                # Remove tier bonus stats
                if hasattr(item, "bonus_stats") and hasattr(self, "_equipment_bonus_applied"):
                    for bonus_stat, bonus in item.bonus_stats.items():
                        key = (id(item), bonus_stat)
                        if key in self._equipment_bonus_applied:
                            # Restore original value
                            setattr(self, bonus_stat, self._equipment_bonus_applied[key])
                            del self._equipment_bonus_applied[key]
                if hasattr(self, 'equipment') and stat in self.equipment:
                    self.equipment[stat] = None
                break

# --- Player Job Classes ---
class Fighter(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("attack")
        self.skill_cooldown = 8.0  # seconds
        # Give starting sword
        sword = Sword(level=1, tier="Good")
        self.equipment_items[0] = sword
        self.equip(sword)
        self.skills = [BigSlashSkill()]

class Assassin(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("crit_chance")
        self.upgrade_stat("attack_speed")
        self.upgrade_stat("attack_speed")  # +2 levels to attack speed
        self.upgrade_stat("dodge_chance")
        self.skill_cooldown = 6.0  # seconds
        # Give starting boots
        boots = Boots(level=1, tier="Good")
        self.equipment_items[0] = boots
        self.equip(boots)
        self.skills = [DoubleAttackSkill()]

class Paladin(Player):
    def __init__(self, x):
        super().__init__(x)
        self.upgrade_stat("defence")
        self.upgrade_stat("max_hp")  # +5 HP
        self.skill_cooldown = 12.0  # seconds
        # Give starting shield
        shield = Shield(level=1, tier="Good")
        self.equipment_items[0] = shield
        self.equip(shield)
        self.skills = [BlessingLightSkill()]

# --- Enemy Classes ---
class Enemy(Entity):
    """Enemy character with different types."""
    def __init__(self, x, enemy_type='basic', room_number=1):
        # Scaling factors
        hp_scale = 1 + 0.02 * (room_number - 1)
        atk_scale = 1 + 0.015 * (room_number - 1)
        spd_scale = 1 + 0.01 * (room_number - 1)
        def_scale = 1 + 0.01 * (room_number - 1)
        dodge_scale = 1 + 0.01 * (room_number - 1)

        if enemy_type == 'basic':
            char = 'E'
            super().__init__(x, char)
            self.dead = False
            self.hp = int(8 * hp_scale)
            self.max_hp = self.hp
            self.attack = int(2 * atk_scale)
            self.attack_speed = 1.0 * spd_scale
            self.crit_chance = 0.1
            self.crit_damage = 2.0
            self.defence = int(0 * def_scale)
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
            self.dodge_chance = min(0.05 * dodge_scale, 0.7)
        elif enemy_type == 'speedy':
            char = 'S'
            super().__init__(x, char)
            self.hp = int(5 * (1 + 0.07 * (room_number - 1)))
            self.max_hp = self.hp
            self.attack = int(1 * (1 + 0.07 * (room_number - 1)))
            self.attack_speed = 1.1 * spd_scale  # Speed scales more
            self.crit_chance = 0.1
            self.crit_damage = 2.0
            self.defence = int(0 * def_scale)
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
            self.dodge_chance = min(0.12 * dodge_scale, 0.7)  # Dodge scales more
        elif enemy_type == 'tough':
            char = 'O'
            super().__init__(x, char)
            self.hp = int(13 * hp_scale * 1.12)  # HP scales more
            self.max_hp = self.hp
            self.attack = int(1 * atk_scale)
            self.attack_speed = 0.5 * (1 + 0.03 * (room_number - 1))  # Speed scales less
            self.crit_chance = 0.05
            self.crit_damage = 2.0
            self.defence = int(0 + (room_number // 8))  # Defence increases every 2 rooms
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
            self.dodge_chance = min(0.02 * dodge_scale, 0.7)
        elif enemy_type == 'brute':
            char = 'B'
            super().__init__(x, char)
            self.hp = int(10 * (1 + 0.03 * (room_number - 1)))
            self.max_hp = self.hp
            self.attack = int(2 * (1 + 0.04 * (room_number - 1)))  # High damage
            self.attack_speed = 0.5 * (1 + 0.01 * (room_number - 1))  # Slow attack speed
            self.crit_chance = 0.08
            self.crit_damage = 2.0
            self.defence = int(0 * def_scale)
            self.health_regen = 0
            self.thorn_damage = 0
            self.lifesteal = 0.0
            self.dodge_chance = min(0.03 * dodge_scale, 0.7)
        else:
            char = '?'
            super().__init__(x, char)

class BossEnemy(Enemy):
    """Base class for all boss enemies."""
    def __init__(self, x, name="Boss", room_number=1):
        super().__init__(x, enemy_type='boss', room_number=room_number)
        self.name = name
        self.char = 'B'  # Default boss character

class RegenBoss(BossEnemy):
    """Boss with high health regeneration."""
    def __init__(self, x, room_number=1):
        super().__init__(x, name="Regen Boss", room_number=room_number)
        self.char = 'R'
        self.hp = int(30 + 3 * room_number)  # Lowered HP scaling
        self.max_hp = self.hp
        self.attack = 2 + room_number // 12   # Lowered attack
        self.attack_speed = 0.8
        self.crit_chance = 0.12
        self.crit_damage = 2.0
        self.defence = 2 + room_number // 16
        self.health_regen = 2 + room_number // 8
        self.thorn_damage = 0
        self.lifesteal = 0.0
        self.dodge_chance = 0.07

class LifestealBoss(BossEnemy):
    """Boss with high lifesteal."""
    def __init__(self, x, room_number=1):
        super().__init__(x, name="Lifesteal Boss", room_number=room_number)
        self.char = 'L'
        self.hp = int(35 + 3 * room_number)  # Lowered HP scaling
        self.max_hp = self.hp
        self.attack = 2 + room_number // 10   # Lowered attack
        self.attack_speed = 0.9
        self.crit_chance = 0.10
        self.crit_damage = 2.0
        self.defence = 1 + room_number // 18
        self.health_regen = 1
        self.thorn_damage = 0
        self.lifesteal = 0.18
        self.dodge_chance = 0.08

class FinalBoss(BossEnemy):
    """Balanced final boss that can summon minions."""
    def __init__(self, x, room_number=1):
        super().__init__(x, name="??? FINAL BOSS ???", room_number=room_number)
        self.char = 'F'
        self.hp = int(120 + 10 * room_number)
        self.max_hp = self.hp
        self.attack = 8 + room_number // 2
        self.attack_speed = 1.2
        self.crit_chance = 0.25
        self.crit_damage = 2.5
        self.defence = 8 + room_number // 8
        self.health_regen = 3 + room_number // 10
        self.thorn_damage = 3
        self.lifesteal = 0.15
        self.dodge_chance = 0.15
        self.summon_cooldown = 8.0  # seconds
        self.summon_timer = 0.0

    def update(self, dt, enemies, room_number):
        # Summon minions every summon_cooldown seconds, up to 2 at a time
        self.summon_timer += dt
        if self.summon_timer >= self.summon_cooldown:
            self.summon_timer = 0.0
            minions = []
            for _ in range(2):
                minion_type = random.choice(['basic', 'speedy', 'tough', 'brute'])
                minion = Enemy(x=random.randint(10, 50), enemy_type=minion_type, room_number=max(1, room_number - 5))
                minion.hp = max(1, int(minion.hp * 0.5))
                minion.max_hp = minion.hp
                minion.attack = max(1, int(minion.attack * 0.6))
                minions.append(minion)
            enemies.extend(minions)
            return f"{self.name} summons reinforcements!"
        return None
        
# --- Item Classes ---
class Item:
    """Base class for all items."""
    def __init__(self, name):
        self.name = name

class Potion(Item):
    """Base class for all potions."""
    def __init__(self, name):
        super().__init__(name)

    def use(self, player):
        pass  # To be overridden

class HealingPotion(Potion):
    heal_percent = 0.0  # Override in subclasses
    potion_classes = []  # Will be filled after all subclasses are defined

    def __init__(self, name=None):
        if name is None:
            name = self.__class__.__name__
        super().__init__(name)

    def use(self, player):
        heal_amount = max(1, int(player.max_hp * self.heal_percent))
        player.hp = min(player.max_hp, player.hp + heal_amount)
        return f"{player.char} uses {self.name} and heals {heal_amount} HP!"

class SmallHealingPotion(HealingPotion):
    char = '!'
    heal_percent = 0.25
    def __init__(self):
        super().__init__("a small health potion")

class MediumHealingPotion(HealingPotion):
    char = '%'
    heal_percent = 0.5
    def __init__(self):
        super().__init__("a medium health potion")

class MaxHealingPotion(HealingPotion):
    char = '&'
    heal_percent = 1.0
    def __init__(self):
        super().__init__("a max health potion")

class StatPotion(Potion):
    def __init__(self, name, stat):
        super().__init__(name)
        self.stat = stat

    def use(self, player):
        # Mark the stat to be boosted for the next battle
        if not hasattr(player, 'stat_boosts'):
            player.stat_boosts = {}
        stat_value = getattr(player, self.stat)
        if stat_value == 0:
            player.stat_boosts[self.stat] = "+1"
            stat_name = self.stat.replace('_', ' ').title()
            return f"{player.char} uses {self.name}! {stat_name} +1 next battle!"
        else:
            player.stat_boosts[self.stat] = "double"
            stat_name = self.stat.replace('_', ' ').title()
            return f"{player.char} uses {self.name}! {stat_name} x2 next battle!"

class AttackPotion(StatPotion):
    char = 'A'
    def __init__(self):
        super().__init__("an attack potion", "attack")

class DefencePotion(StatPotion):
    char = 'D'
    def __init__(self):
        super().__init__("a defence potion", "defence")

class AttackSpeedPotion(StatPotion):
    char = 'S'
    def __init__(self):
        super().__init__("an attack speed potion", "attack_speed")

class CritChancePotion(StatPotion):
    char = 'C'
    def __init__(self):
        super().__init__("a crit chance potion", "crit_chance")

class CritDamagePotion(StatPotion):
    char = 'G'
    def __init__(self):
        super().__init__("a crit damage potion", "crit_damage")

class ThornPotion(StatPotion):
    char = 'T'
    def __init__(self):
        super().__init__("a thorn potion", "thorn_damage")

class LifestealPotion(StatPotion):
    char = 'L'
    def __init__(self):
        super().__init__("a lifesteal potion", "lifesteal")

class DodgePotion(StatPotion):
    char = 'V'
    def __init__(self):
        super().__init__("a dodge potion", "dodge_chance")

class RegenPotion(StatPotion):
    char = 'R'
    def __init__(self):
        super().__init__("a regen potion", "health_regen")

# Register potion classes after all are defined
HealingPotion.potion_classes = [
    SmallHealingPotion, MediumHealingPotion, MaxHealingPotion,
    AttackPotion, DefencePotion, AttackSpeedPotion,
    CritChancePotion, CritDamagePotion, ThornPotion,
    LifestealPotion, DodgePotion, RegenPotion,
]

# --- Equipment Tiers ---
EQUIPMENT_TIERS = ["Basic", "Good", "Rare", "Awesome", "Legendary"]

def random_tier(luck=0):
    """
    Returns a random equipment tier, weighted by player's luck.
    At luck 0: Only Basic, Good, and rarely Rare.
    Luck unlocks higher tiers and shifts weights.
    Legendary is always extremely rare.
    """
    # Tiers:        0      1      2      3        4
    #            Basic   Good   Rare  Awesome  Legendary
    # Weights for each luck level 0-10:
    tier_weights_by_luck = [
        [0.80, 0.18, 0.02, 0.00, 0.00],  # luck 0
        [0.70, 0.22, 0.07, 0.01, 0.00],  # luck 1
        [0.60, 0.25, 0.12, 0.03, 0.00],  # luck 2
        [0.50, 0.28, 0.17, 0.05, 0.00],  # luck 3
        [0.40, 0.30, 0.20, 0.09, 0.01],  # luck 4
        [0.32, 0.32, 0.22, 0.13, 0.01],  # luck 5
        [0.25, 0.32, 0.24, 0.17, 0.02],  # luck 6
        [0.18, 0.32, 0.25, 0.22, 0.03],  # luck 7
        [0.12, 0.30, 0.26, 0.27, 0.05],  # luck 8
        [0.07, 0.25, 0.27, 0.34, 0.07],  # luck 9
        [0.03, 0.18, 0.28, 0.41, 0.10],  # luck 10
    ]
    idx = min(max(int(luck), 0), 10)
    weights = tier_weights_by_luck[idx]
    return random.choices(EQUIPMENT_TIERS, weights)[0]

# --- Equipment Classes ---
class Equipment(Item):
    """Base class for all equipment items."""
    # List of stats that can be boosted (excluding luck)
    BONUS_STATS = [
        "attack", "attack_speed", "crit_chance", "crit_damage", "defence",
        "health_regen", "thorn_damage", "lifesteal", "dodge_chance", "max_hp"
    ]
    # Short names for display
    STAT_SHORT = {
        "attack": "atk",
        "attack_speed": "spd",
        "crit_chance": "crit%",
        "crit_damage": "critdmg",
        "defence": "def",
        "health_regen": "regen",
        "thorn_damage": "thorn",
        "lifesteal": "lifesteal",
        "dodge_chance": "dodge",
        "max_hp": "hp",
    }
    # Tier: (number of stats to boost, percent boost)
    TIER_BONUSES = {
        "Basic": (0, 0.0),
        "Good": (1, 0.10),
        "Rare": (1, 0.20),
        "Awesome": (1, 0.35),
        "Legendary": (2, 0.50),
    }

    def __init__(self, name, level=1, tier="Basic"):
        super().__init__(name)
        self.level = level
        self.tier = tier
        self.bonus_stats = {}  # e.g. {"attack": 0.1}
        num_stats, bonus = self.TIER_BONUSES.get(tier, (0, 0.0))
        if num_stats > 0:
            stats = random.sample(self.BONUS_STATS, num_stats)
            for stat in stats:
                self.bonus_stats[stat] = bonus

    def display_name(self):
        # Show level, tier, name, and bonus stat(s) if any
        bonus = ""
        if self.bonus_stats:
            # e.g. (+atk) or (+atk) (+spd)
            bonus = " " + " ".join(
                f"(+{self.STAT_SHORT.get(stat, stat)})" for stat in self.bonus_stats
            )
        return f"lvl.{self.level} {self.tier.lower()} {self.name}{bonus}"

# Equipment subclasses for each stat

class Sword(Equipment):
    char = '/'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("sword", level, tier)  # Attack

class Shield(Equipment):
    char = ']'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("shield", level, tier)  # Defence

class Armor(Equipment):
    char = 'U'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("armor", level, tier)  # Max HP

class Fangs(Equipment):
    char = 'f'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("fangs", level, tier)  # Lifesteal

class Boots(Equipment):
    char = 'b'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("boots", level, tier)  # Dodge chance

class Amulet(Equipment):
    char = 'a'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("amulet", level, tier)  # Crit chance

class Gem(Equipment):
    char = '*'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("gem", level, tier)  # Crit damage

class Thorns(Equipment):
    char = 't'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("thorns", level, tier)  # Thorn damage

class Ring(Equipment):
    char = 'r'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("ring", level, tier)  # Health regen

class Gloves(Equipment):
    char = 'g'
    def __init__(self, level=1, tier="Basic"):
        super().__init__("gloves", level, tier)  # Attack speed

Equipment.equipment_classes = [
    Sword, Shield, Armor, Fangs, Boots, Amulet, Gem, Thorns, Ring, Gloves
]
# Add more as needed for other stats

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
            f"HP: {int(player.hp):.0f}/{player.max_hp:.0f}",
            f"ATK: {player.attack:.0f}",
            f"ATK SPD: {player.attack_speed:.1f}",
            f"CRIT%: {int(round(player.crit_chance * 100))}",
            f"CRIT DMG: {player.crit_damage:.1f}",
            f"DEF: {player.defence:.0f}",
            f"REGEN: {player.health_regen:.0f}",
            f"THORN: {player.thorn_damage:.0f}",
            f"LIFESTEAL: {player.lifesteal:.2f}",
            f"DODGE%: {int(round(player.dodge_chance * 100))}",
            f"LUCK: {player.luck}",
            f"GOLD: {player.gold}",
        ]
        stats += [''] * (game_height - len(stats))
        return stats

    def get_enemy_stats_lines(self, enemy, game_height):
        if enemy is None:
            stats = [''] * game_height
        else:
            stats = [
                f"ENEMY: {enemy.char}",
                f"HP: {enemy.hp:.0f}/{enemy.max_hp:.0f}",
                f"ATK: {enemy.attack}",
                f"ATK SPD: {enemy.attack_speed:.1f}",
                f"CRIT%: {int(round(enemy.crit_chance * 100))}",
                f"CRIT DMG: {enemy.crit_damage:.1f}",
                f"DEF: {enemy.defence}",
                f"REGEN: {enemy.health_regen}",
                f"THORN: {enemy.thorn_damage}",
                f"LIFESTEAL: {enemy.lifesteal:.1f}",
                f"DODGE%: {int(round(enemy.dodge_chance * 100))}",
            ]
            # Calculate how many blank lines to add so the boss chance is at the bottom
            lines_needed = game_height - len(stats) - 2
            if lines_needed > 0:
                stats += [''] * lines_needed
            # Add a separator and the boss chance at the very bottom
            stats.append('-' * 14)
            # Try to get boss_probability from the game instance
            boss_chance = 0.0
            try:
                import __main__
                if hasattr(__main__, 'game'):
                    boss_chance = getattr(__main__.game, 'boss_probability', 0.0)
            except Exception:
                pass
            stats.append(f"BOSS CHANCE: {boss_chance*100:.0f}%")
            # If stats is now longer than game_height, trim it (shouldn't happen)
            stats = stats[:game_height]
        return stats

    def get_room_counter_line(self, room_number):
        return f"ROOM: {room_number}"

    def get_inventory_box(self, height=7, width=16):
        """
        Draws a cross (no extra borders) dividing the box into 4 slots.
        """
        lines = []
        mid_row = height // 2
        mid_col = width // 2

        for row in range(height):
            if row == mid_row:
                # Horizontal line
                lines.append(" " * width)
                lines[-1] = lines[-1][:1] + "-" * (width - 2) + lines[-1][-1:]
            else:
                # Vertical line
                line = [" "] * width
                line[mid_col] = "|"
                lines.append("".join(line))
        return lines

    def get_equipment_box(self, height=7, width=16):
        """
        Draws a cross (no extra borders) dividing the box into 4 slots for equipment.
        """
        lines = []
        mid_row = height // 2
        mid_col = width // 2

        for row in range(height):
            if row == mid_row:
                # Horizontal line
                lines.append(" " * width)
                lines[-1] = lines[-1][:1] + "-" * (width - 2) + lines[-1][-1:]
            else:
                # Vertical line
                line = [" "] * width
                line[mid_col] = "|"
                lines.append("".join(line))
        return lines

class Renderer:
    """Handles all drawing to the terminal."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.enemy = None

    def clear(self):
        print('\033[H', end='')

    def render(self, player, room, ui, boss_info_lines=None, battle_log_lines=None, intro_message=None, room_number=None, enemies=None):
        self.clear()
        stats_col_width = 16
        boss_col_width = 16
        term_size = shutil.get_terminal_size((80, 24))
        pad_left = (term_size.columns - (self.width + 2 + stats_col_width + boss_col_width)) // 2

        # --- Skill icons rendering ---
        stats_lines = ui.get_player_stats_lines(player, self.height)
        if boss_info_lines is None:
            boss_info_lines = [''] * self.height
        else:
            boss_info_lines += [''] * (self.height - len(boss_info_lines))

        print(ui.get_title_line(pad_left + stats_col_width, self.width))
        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        for y in range(self.height):
            print(' ' * pad_left + '|' + stats_lines[y].ljust(stats_col_width), end='')
            if y == 0:
                # Always draw skill icons on the first line
                skill_chars = [getattr(skill, 'char', '?') for skill in getattr(player, 'skills', [])]
                icons_per_row = self.width
                skill_line = ''.join(skill_chars[:icons_per_row]).ljust(self.width)
                print('|' + skill_line + '|', end='')
                print(boss_info_lines[y].ljust(boss_col_width) + '|')
            else:
                # Draw the normal game area line
                line = room.get_landscape_line(y)
                # Draw player and enemies on the correct line
                if y == self.height - 1:
                    if 0 <= player.x < self.width:
                        line[player.x] = player.char
                    if enemies is None:
                        enemies = [self.enemy] if self.enemy else []
                    for enemy in enemies:
                        if getattr(enemy, "dead", False):
                            continue
                        if 0 <= enemy.x < self.width:
                            line[enemy.x] = enemy.char
                # Overlay message if intro_message is present and this is a message line
                if intro_message is not None:
                    message_lines = intro_message.split('\n')
                    msg_start = (self.height - len(message_lines)) // 2
                    if msg_start <= y < msg_start + len(message_lines):
                        msg = message_lines[y - msg_start].center(self.width)
                        # Overlay the message on top of the line
                        for i, ch in enumerate(msg):
                            if ch != ' ':
                                line[i] = ch
                print('|' + ''.join(line) + '|', end='')
                print(boss_info_lines[y].ljust(boss_col_width) + '|')

        print(' ' * pad_left + '+' + '-' * stats_col_width + '+' + '-' * self.width + '+' + '-' * boss_col_width + '+')

        battle_log_height = 7  # Increased by 1 for even bottom row
        if battle_log_lines is None:
            battle_log_lines = []

        room_num = room_number
        if room_num is None:
            room_num = getattr(room, 'current_room', 1)
        room_line = ui.get_room_counter_line(room_num)
        if len(battle_log_lines) == 0:
            battle_log_lines = [room_line]
        elif len(battle_log_lines) < battle_log_height:
            battle_log_lines = [room_line] + battle_log_lines

        inventory_box = ui.get_inventory_box(height=battle_log_height, width=stats_col_width)
        equipment_box = ui.get_equipment_box(height=battle_log_height, width=boss_col_width)
        # Inventory slot positions (row, col) for 4 slots in the cross
        slot_positions = [
            (1, stats_col_width // 4),           # Top-left
            (1, 3 * stats_col_width // 4),       # Top-right
            (battle_log_height - 2, stats_col_width // 4),     # Bottom-left
            (battle_log_height - 2, 3 * stats_col_width // 4), # Bottom-right
        ]
        # Copy inventory_box to a mutable list of lists
        inv_box = [list(row) for row in inventory_box]
        for idx, potion in enumerate(getattr(player, "potions", [])):
            if potion:
                row, col = slot_positions[idx]
                inv_box[row][col] = getattr(potion, "char", "?")
        # Convert back to strings
        inventory_box = ["".join(row) for row in inv_box]

        # --- Equipment rendering logic ---
        eq_box = [list(row) for row in equipment_box]
        for idx, eq in enumerate(getattr(player, "equipment_items", [])):
            if eq:
                row, col = slot_positions[idx]
                eq_box[row][col] = getattr(eq, "char", "?")
        equipment_box = ["".join(row) for row in eq_box]

        for i in range(battle_log_height):
            inv = inventory_box[i] if i < len(inventory_box) else ''
            log = battle_log_lines[i] if i < len(battle_log_lines) else ''
            eq = equipment_box[i] if i < len(equipment_box) else ''
            print(' ' * pad_left + '|' + inv + '|' + log.ljust(self.width) + '|' + eq + '|')

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

    def wait_for_space(self, message, enemy=None, show_player=True, room_number=None, battle_log_lines=None, enemies=None):
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
                room_number=room_number if room_number is not None else getattr(self, 'current_room', 1),
                battle_log_lines=battle_log_lines,
                enemies=enemies,
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

    def win(self, battle_log_lines=None):
        self.wait_for_space(
            "You win!\nPress spacebar to enter the next room",
            enemy=None,
            show_player=True,
            room_number=self.current_room,
            battle_log_lines=battle_log_lines
        )

    def lose(self, enemy):
        self.wait_for_space("You lose!\nPress spacebar to restart", enemy=enemy, show_player=False, room_number=self.current_room)

    def level_up_screen(self, player, battle_log_lines=None):
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
        # Add luck if not maxed
        if getattr(player, "luck", 0) < 10:
            stat_options.append(("luck", "Luck +1"))
        choices = random.sample(stat_options, 3)
        selected = 0

        while True:
            lines = ["LVL UP!", "", "Choose a stat to upgrade:"]
            for i, (stat, desc) in enumerate(choices):
                prefix = "-> " if i == selected else "   "
                lines.append(f"{prefix}{i+1}. {desc}")
            message = "\n".join(lines)
            self.renderer.render(self.player, self.room, self.ui, intro_message=message, room_number=self.current_room, battle_log_lines=battle_log_lines)
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

    def pre_battle_item_use(self, player, enemy, enemies=None):
        while any(player.potions):
            # Show inventory and ask if the player wants to use a potion
            lines = ["Use a potion before battle?"]
            for idx, potion in enumerate(player.potions):
                if potion:
                    lines.append(f"{idx+1}. {potion.name}")
                else:
                    lines.append(f"{idx+1}. (empty)")
            lines.append("[Press 1-4 to use, or space to start battle]")
            message = "\n".join(lines)
            self.renderer.render(player, self.room, self.ui, intro_message=message, room_number=self.current_room, enemies=enemies)
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3', b'4']:
                    slot = int(key) - 1
                    if player.potions[slot]:
                        log = player.potions[slot].use(player)
                        player.potions[slot] = None
                        # Show heal message, pass the enemy!
                        self.wait_for_space(log, enemy=enemy, show_player=True, room_number=self.current_room, enemies=enemies)
                elif key == b' ':
                    break
            time.sleep(0.08)

    def loot_screen(self, found_items, battle_log_lines=None):
        # found_items: list of Item objects
        if not found_items:
            return
        # Use display_name for equipment, name for others
        def item_display(item):
            if isinstance(item, Equipment):
                return item.display_name()
            return item.name
        names = [item_display(item) for item in found_items]
        if len(names) == 1:
            msg = f"You found {names[0]}!"
        else:
            msg = "You found:\n" + "\n".join(f"- {name}" for name in names)
        self.wait_for_space(msg, show_player=True, room_number=self.current_room, battle_log_lines=battle_log_lines)

    def equipment_pickup_prompt(self, player, new_item):
        lines = ["Equipment slots full!"]
        for idx, eq in enumerate(player.equipment_items):
            if eq:
                name = eq.display_name()
            else:
                name = "(empty)"
            lines.append(f"{idx+1}. {name}")
        new_name = new_item.display_name()
        lines.append(f"New: {new_name}")
        lines.append("Press 1-4 to replace, or SPACE to discard new item.")
        message = "\n".join(lines)
        self.renderer.render(player, self.room, self.ui, intro_message=message, room_number=self.current_room)
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3', b'4']:
                    slot = int(key) - 1
                    # Unequip old item if present
                    if player.equipment_items[slot]:
                        player.unequip(player.equipment_items[slot])
                    player.equipment_items[slot] = new_item
                    player.equip(new_item)
                    return
                elif key == b' ':
                    return
            time.sleep(0.08)

    def potion_pickup_prompt(self, player, new_potion):
        lines = ["Potion slots full!"]
        for idx, potion in enumerate(player.potions):
            name = potion.name if potion else "(empty)"
            lines.append(f"{idx+1}. {name}")
        lines.append(f"New: {new_potion.name}")
        lines.append("Press 1-4 to replace, or SPACE to discard new potion.")
        message = "\n".join(lines)
        self.renderer.render(player, self.room, self.ui, intro_message=message, room_number=self.current_room)
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3', b'4']:
                    slot = int(key) - 1
                    player.potions[slot] = new_potion
                    return
                elif key == b' ':
                    return
            time.sleep(0.08)

    def skill_learn_screen(self, player, skill_classes, battle_log_lines=None):
        selected = 0
        while True:
            lines = ["LEVEL UP! Choose a new skill:"]
            for i, skill_cls in enumerate(skill_classes):
                prefix = "-> " if i == selected else "   "
                skill_instance = skill_cls()
                if hasattr(skill_instance, "get_description"):
                    desc = skill_instance.get_description(player)
                else:
                    desc = skill_instance.description
                lines.append(f"{prefix}{i+1}. {skill_instance.name}")
                lines.append(f"      {desc}")
            lines.append("Press 1-3, arrows, Enter or Space to select.")
            message = "\n".join(lines)
            self.renderer.render(
                player, self.room, self.ui,
                intro_message=message,
                room_number=self.current_room,
                battle_log_lines=battle_log_lines  # <-- Add this
            )
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'1', b'2', b'3']:
                    selected = int(key) - 1
                    break
                elif key in [b'H', b'K', b'w']:
                    selected = (selected - 1) % len(skill_classes)
                elif key in [b'P', b'M', b's']:
                    selected = (selected + 1) % len(skill_classes)
                elif key == b'\r' or key == b' ':
                    break
            time.sleep(0.08)
        # Actually add the skill
        new_skill = skill_classes[selected]()
        player.skills.append(new_skill)
        # Call use() for permanent skills (cooldown 0)
        if hasattr(new_skill, "use") and new_skill.cooldown == 0.0:
            new_skill.use(player)
        self.wait_for_space(
            f"You learned {new_skill.name}!",
            show_player=True,
            room_number=self.current_room,
            battle_log_lines=battle_log_lines
        )

# --- Animations Class ---
class Animations:
    """Handles all game animations (player slide, attacks, etc)."""
    def __init__(self, renderer, room, ui, player):
        self.renderer = renderer
        self.room = room
        self.ui = ui
        self.player = player
        self.current_room = 1  # Will be set by Game

    def player_slide_and_disappear(self, enemies=None):
        for x in range(self.player.x, WIDTH):
            self.player.x = x
            self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room, enemies=enemies)
            time.sleep(0.02)
        self.player.x = -1
        self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room, enemies=enemies)
        time.sleep(0.3)

    def death(self, entity, battle_log_lines=None, enemies=None):
        fade_chars = ['*', '.', ' ']
        old_char = entity.char
        for char in fade_chars:
            entity.char = char
            self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room, battle_log_lines=battle_log_lines, enemies=enemies)
            time.sleep(0.12)
        entity.char = old_char
        entity.x = -1
        self.renderer.render(self.player, self.room, self.ui, room_number=self.current_room, battle_log_lines=battle_log_lines, enemies=enemies)
        time.sleep(0.2)

    def crit_effect(self, attacker, boss_info_lines=None, battle_log_lines=None, enemies=None):
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
                room_number=self.current_room,
                enemies=enemies
            )
            time.sleep(0.6)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room,
            enemies=enemies
        )

    def dodge_effect(self, target, boss_info_lines=None, battle_log_lines=None, enemies=None):
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
                room_number=self.current_room,
                enemies=enemies
            )
            time.sleep(0.6)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room,
            enemies=enemies
        )

    def slash(self, attacker, target=None, boss_info_lines=None, battle_log_lines=None, enemies=None):
        y = self.room.height - 1

        if target is not None and attacker.x < target.x:
            frames = ['>', '>>']
            pos = attacker.x + 1
        else:
            frames = ['<<']
            pos = attacker.x - 1

        old_get_landscape_line = self.room.get_landscape_line

        def make_slash_line(frame):
            line = [' '] * self.room.width
            # Draw all enemies at their real positions
            if enemies:
                for enemy in enemies:
                    if getattr(enemy, "dead", False):
                        continue
                    if 0 <= enemy.x < self.room.width:
                        line[enemy.x] = enemy.char
            # Draw attacker at their real position (in case attacker is not in enemies)
            if 0 <= attacker.x < self.room.width:
                line[attacker.x] = attacker.char
            # Draw slash effect at desired position (use a local variable, not attacker.x)
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
                    room_number=self.current_room,
                    enemies=enemies
                )
                time.sleep(0.08)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room,
            enemies=enemies
        )

    def skill_effect(self, skill_name, attacker, boss_info_lines=None, battle_log_lines=None, enemies=None):
        y = self.room.height - 2  # Same as crit_effect: just above the player
        old_get_landscape_line = self.room.get_landscape_line

        def make_skill_line():
            line = [' '] * self.room.width
            word = skill_name
            start = max(0, min(self.room.width - len(word), attacker.x - len(word)//2))
            for i, ch in enumerate(word):
                line[start + i] = ch
            return line

        try:
            def patched_get_landscape_line(row):
                if row == y:
                    return make_skill_line()
                else:
                    return old_get_landscape_line(row)
            self.room.get_landscape_line = patched_get_landscape_line
            self.renderer.render(
                self.player, self.room, self.ui,
                boss_info_lines=boss_info_lines,
                battle_log_lines=battle_log_lines,
                room_number=self.current_room,
                enemies=enemies
            )
            time.sleep(0.6)
        finally:
            self.room.get_landscape_line = old_get_landscape_line
        self.renderer.render(
            self.player, self.room, self.ui,
            boss_info_lines=boss_info_lines,
            battle_log_lines=battle_log_lines,
            room_number=self.current_room,
            enemies=enemies
        )

# --- Battle System Class ---
class Battle:
    """Handles the battle logic between two entities, using all stats."""
    def __init__(self, renderer, ui, room):
        self.renderer = renderer
        self.ui = ui
        self.room = room
        self.current_room = 1  # Will be set by Game

    def attack(self, attacker, defender, boss_info_lines=None, battle_log_lines=None, first_attack=False, enemies=None):
        messages = []
        # --- Heavy Hitter logic ---
        heavy_hitter_active = False
        if first_attack and isinstance(attacker, Player) and "HeavyHitterSkill" in getattr(attacker, "permanent_skills_used", set()):
            heavy_hitter_active = True

        # Play slash/crit/dodge animation if available
        if hasattr(self, 'animations') and self.animations:
            # Dodge check first
            if random.random() < defender.dodge_chance:
                self.animations.dodge_effect(defender, boss_info_lines, battle_log_lines, enemies=enemies,)
                msg = f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"
                # Counter Dodge logic
                if hasattr(defender, "skills") and any(isinstance(skill, CounterDodgeSkill) for skill in defender.skills):
                    if random.random() < 0.5:  # 50% chance to counter
                        counter_damage = max(1, defender.attack - attacker.defence)
                        attacker.hp -= counter_damage
                        msg += f" {defender.char} COUNTERS for {counter_damage:.0f} dmg!"
                return [msg]
            # Crit check
            crit = False
            if random.random() < attacker.crit_chance:
                damage = int(max(1, attacker.attack - defender.defence) * attacker.crit_damage)
                crit = True
                if heavy_hitter_active:
                    damage *= 2
                self.animations.crit_effect(attacker, boss_info_lines, battle_log_lines, enemies=enemies,)
            else:
                damage = max(1, attacker.attack - defender.defence)
                if heavy_hitter_active:
                    damage *= 2
                self.animations.slash(attacker, defender, boss_info_lines, battle_log_lines, enemies=enemies,)
        else:
            # No animations
            if random.random() < defender.dodge_chance:
                return [f"{attacker.char} attacks {defender.char}, but {defender.char} dodges!"]
            crit = False
            if random.random() < attacker.crit_chance:
                damage = int(max(1, attacker.attack - defender.defence) * attacker.crit_damage)
                crit = True
                if heavy_hitter_active:
                    damage *= 2
            else:
                damage = max(1, attacker.attack - defender.defence)
                if heavy_hitter_active:
                    damage *= 2

        # --- Cumulative lifesteal logic ---
        if hasattr(attacker, "lifesteal") and attacker.lifesteal > 0:
            # Only apply to Player, not enemies
            if isinstance(attacker, Player):
                if not hasattr(attacker, "lifesteal_pool"):
                    attacker.lifesteal_pool = 0.0
                attacker.lifesteal_pool += damage * attacker.lifesteal
                healed = 0
                while attacker.lifesteal_pool >= 1.0:
                    if attacker.hp < attacker.max_hp:
                        attacker.hp += 1
                        healed += 1
                        attacker.lifesteal_pool -= 1.0
                    else:
                        break
                if battle_log_lines is not None:
                    if healed > 0:
                        messages.append(f"{attacker.char} lifesteals {healed:.0f} HP!")
                    elif damage * attacker.lifesteal > 0 and attacker.hp >= attacker.max_hp:
                        messages.append(f"{attacker.char} lifesteals but is already at full HP!")
            else:
                # For enemies, keep old logic if needed
                heal = int(damage * attacker.lifesteal)
                attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        # --- Crit Shield logic ---
        if isinstance(defender, Player) and "crit_shield" in defender.timed_effects:
            shield = defender.timed_effects["crit_shield"]["value"]
            if damage <= shield:
                defender.timed_effects["crit_shield"]["value"] -= damage
                damage = 0
            else:
                damage -= shield
                del defender.timed_effects["crit_shield"]
        # --- Invincible logic ---
        if isinstance(defender, Player) and "invincible" in defender.timed_effects:
            messages.append(f"{defender.char} is INVINCIBLE and takes no damage!")
            return messages

        defender.hp -= damage
        thorn_msg = ""
        if defender.thorn_damage > 0:
            attacker.hp -= defender.thorn_damage
            thorn_msg = f" {attacker.char} takes {defender.thorn_damage:.0f} thorn damage!"
        msg = f"{attacker.char} hits {defender.char} for {damage:.0f} damage"
        if 'crit' in locals() and crit:
            msg += " (CRIT!)"
        msg += "!" + thorn_msg
        messages.append(msg)  # The main attack message
        return messages

    def battle(self, player, enemies, running_flag):
        animations = getattr(self, 'animations', None)
        battle_log = []
        player_next_attack = 0.0
        enemy_next_attack = [0.0 for _ in enemies]
        clock = 0.0
        time_step = 0.05
        regen_base_interval = 6.0  # seconds for 1 regen

        # --- Apply stat boosts ---
        original_stats = {}
        if hasattr(player, 'stat_boosts'):
            for stat, boost_type in player.stat_boosts.items():
                original_stats[stat] = getattr(player, stat)
                if boost_type == "double":
                    setattr(player, stat, getattr(player, stat) * 2)
                elif boost_type == "+1":
                    setattr(player, stat, getattr(player, stat) + 1)
            player.stat_boosts.clear()

        # --- Quick Step logic ---
        quick_step_active = False
        quick_step_timer = 0.0
        if "QuickStepSkill" in getattr(player, "permanent_skills_used", set()):
            player.dodge_chance = min(0.7, player.dodge_chance + 0.10)
            quick_step_active = True
            quick_step_timer = 5.0

        first_attack_done = False

        while player.hp > 0 and any(e.hp > 0 for e in enemies) and running_flag():
            acted = False

            # --- SKILL USAGE (automatic) ---
            player.update_skill_timer(time_step)

            for skill in player.skills:
                skill.cooldown_timer += time_step

            # --- Timed effects update (add this here) ---
            to_remove = []
            for effect, data in player.timed_effects.items():
                data["timer"] -= time_step
                if data["timer"] <= 0:
                    to_remove.append(effect)
            for effect in to_remove:
                if effect == "adrenaline":
                    player.attack_speed -= player.timed_effects[effect]["value"]
                del player.timed_effects[effect]

            # --- Quick Step timer update ---
            if quick_step_active:
                quick_step_timer -= time_step
                if quick_step_timer <= 0:
                    player.dodge_chance = max(0.0, player.dodge_chance - 0.10)
                    quick_step_active = False

            # --- Final Boss Summon Skill ---
            for enemy in enemies:
                if isinstance(enemy, FinalBoss):
                    summon_msg = enemy.update(time_step, enemies, self.current_room)
                    if summon_msg:
                        battle_log.append(summon_msg)

            skill_log = None
            skill_name = None
            living_enemies = [e for e in enemies if e.hp > 0]
            for skill in player.skills:
                # Check if the skill is ready
                if skill.cooldown_timer >= skill.cooldown:
                    skill_log = None
                    skill_name = skill.name
                    # Use correct arguments for each skill
                    if isinstance(skill, BigSlashSkill):
                        skill_log = skill.use(player, living_enemies)
                    elif isinstance(skill, DoubleAttackSkill):
                        if living_enemies:
                            skill_log = skill.use(player, random.choice(living_enemies))
                    elif isinstance(skill, BlindingFlashSkill):
                        if living_enemies:
                            skill_log = skill.use(player, living_enemies)
                    elif isinstance(skill, BlessingLightSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, ThornBurstSkill):
                        skill_log = skill.use(player, living_enemies)
                    elif isinstance(skill, LuckyStrikeSkill):
                        if living_enemies:
                            skill_log = skill.use(player, random.choice(living_enemies))
                    elif isinstance(skill, RegenWaveSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, CritShieldSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, LifestealNovaSkill):
                        if living_enemies:
                            skill_log = skill.use(player, living_enemies)
                    elif isinstance(skill, InvincibleSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, GoldRushSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, GuaranteedCritSkill):
                        if living_enemies:
                            skill_log = skill.use(player, random.choice(living_enemies))
                    elif isinstance(skill, AdrenalineRushSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, JackpotSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, GambleSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, GlassCannonSkill):
                        skill_log = skill.use(player)
                    elif isinstance(skill, ClumsySwingSkill):
                        if living_enemies:
                            skill_log = skill.use(player, random.choice(living_enemies))
                    elif isinstance(skill, UnstablePowerSkill):
                        skill_log = skill.use(player)
                    # Add more skills here as needed

                    if skill_log:
                        if hasattr(self, 'animations') and self.animations:
                            anim_name = skill_name.upper() + "!"
                            self.animations.skill_effect(
                                anim_name, player,
                                boss_info_lines=self.ui.get_enemy_stats_lines(living_enemies[0] if living_enemies else None, self.room.height),
                                battle_log_lines=battle_log[-6:],
                                enemies=enemies,
                            )
                        battle_log.append(skill_log)
                        acted = True

            # --- Player attacks a random living enemy ---
            if clock >= player_next_attack and living_enemies:
                target = random.choice(living_enemies)
                is_first_attack = not first_attack_done
                msgs = self.attack(
                    player, target,
                    boss_info_lines=self.ui.get_enemy_stats_lines(target, self.room.height),
                    battle_log_lines=battle_log[-6:],
                    first_attack=is_first_attack,
                    enemies=enemies
                )
                battle_log.extend(msgs)
                player_next_attack += 1.0 / player.attack_speed
                acted = True
                if is_first_attack:
                    first_attack_done = True

            # --- Each enemy attacks independently ---
            for idx, enemy in enumerate(enemies):
                if hasattr(enemy, "skip_turns") and enemy.skip_turns > 0:
                    enemy.skip_turns -= 1
                    continue  # Skip this enemy's attack this turn
                if enemy.hp > 0 and clock >= enemy_next_attack[idx]:
                    msgs = self.attack(
                        enemy, player,
                        boss_info_lines=self.ui.get_enemy_stats_lines(enemy, self.room.height),
                        battle_log_lines=battle_log[-6:],
                        enemies=enemies
                    )
                    battle_log.extend(msgs)
                    enemy_next_attack[idx] += 1.0 / enemy.attack_speed
                    acted = True

            # --- Regen logic ---
            if player.health_regen > 0:
                interval = regen_base_interval * (0.95 ** (player.health_regen - 1))
                player.regen_timer += time_step
                if player.regen_timer >= interval:
                    healed = min(1, player.max_hp - player.hp)
                    if healed > 0:
                        player.hp += healed
                        battle_log.append(f"{player.char} regenerates {healed} HP!")
                    player.regen_timer = 0.0
            for enemy in enemies:
                if enemy.health_regen > 0 and int(clock * 10) % 10 == 0:
                    for enemy in enemies:
                        if not hasattr(enemy, "regen_timer"):
                            enemy.regen_timer = 0.0
                        if enemy.health_regen > 0:
                            interval = regen_base_interval * (0.95 ** (enemy.health_regen - 1))
                            enemy.regen_timer += time_step
                            if enemy.regen_timer >= interval:
                                healed = min(1, enemy.max_hp - enemy.hp)
                                if healed > 0:
                                    enemy.hp += healed
                                    battle_log.append(f"{enemy.char} regenerates {healed} HP!")
                                enemy.regen_timer = 0.0

            # --- Render ---
            if acted or int(clock * 10) % 2 == 0:
                living_enemies = [e for e in enemies if e.hp > 0]
                if living_enemies:
                    main_enemy = max(living_enemies, key=lambda e: (e.max_hp, e.attack))
                else:
                    main_enemy = None
                self.renderer.enemy = main_enemy
                self.renderer.render(
                    player, self.room, self.ui,
                    boss_info_lines=self.ui.get_enemy_stats_lines(main_enemy, self.room.height),
                    battle_log_lines=battle_log[-6:],
                    room_number=self.current_room,
                    enemies=enemies,
                )

            # --- Check for win/lose ---
            if all(e.hp <= 0 for e in enemies):
                if hasattr(self, 'animations') and self.animations:
                    for enemy in enemies:
                        if enemy.hp <= 0 and not getattr(enemy, "dead", False):
                            self.animations.death(enemy, battle_log_lines=battle_log[-6:])
                            enemy.dead = True
                self.renderer.enemy = None
                leveled_up = player.gain_xp(8 + 2 * self.current_room)
                if leveled_up and hasattr(self, 'announcements') and self.announcements:
                    self.announcements.level_up_screen(player, battle_log_lines=battle_log[-6:])
                    # --- Skill roll on level up (after stat upgrade, before loot) ---
                    skill_chance = 0.35 + 0.01 * player.luck  # 35% base +1% per luck
                    if random.random() < skill_chance:
                        owned_types = {type(skill) for skill in player.skills}
                        available_skills = [cls for cls in SKILL_POOL if cls not in owned_types]
                        if available_skills:
                            choices = random.sample(available_skills, min(3, len(available_skills)))
                            self.announcements.skill_learn_screen(player, choices, battle_log_lines=battle_log[-6:])
                if original_stats:
                    for stat, value in original_stats.items():
                        setattr(player, stat, value)
                return "win", battle_log
            if player.hp <= 0:
                if hasattr(self, 'animations') and self.animations:
                    self.animations.death(player)
                return "lose", battle_log
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
        self.shop_probability = 0.0
        self.boss_probability = 0.0
        self.bosses_encountered = set()  # Track which bosses have been fought
        self.bosses_defeated = set()     # Track which bosses have been defeated
        self.boss_classes = [RegenBoss, LifestealBoss]
        
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
    
    def spawn_enemies(self):
        """
        Spawns a main enemy and, for rooms > 10, rolls for additional weaker enemies.
        Each extra enemy has a rising chance (1% per room after 10, capped at 40%).
        Each extra enemy is based on an earlier room (so they're weaker).
        """
        enemies = []
        room = self.current_room
        # Main enemy (always strongest, at current room level)
        main_enemy_type = random.choice(['basic', 'speedy', 'tough', 'brute'])
        main_enemy = Enemy(x=(WIDTH * 3) // 4, enemy_type=main_enemy_type, room_number=room)
        enemies.append(main_enemy)

        # Only add extra enemies for rooms > 10
        if room > 10:
            # Gradually ramp up max extra enemies
            if room < 15:
                max_extra = 1
            elif room < 20:
                max_extra = 2
            elif room < 25:
                max_extra = 3
            else:
                max_extra = 4
            for i in range(1, max_extra + 1):
                chance = min(0.04 * (room - 10), 0.40)  # 4% per room after 10, capped at 40%
                if random.random() < chance:
                    weaker_room = max(1, room - 2 * i)
                    enemy_type = random.choice(['basic', 'speedy', 'tough', 'brute'])
                    x_pos = (WIDTH * 3) // 4 - i * 2
                    extra_enemy = Enemy(x_pos, enemy_type=enemy_type, room_number=weaker_room)
                    extra_enemy.hp = max(1, int(extra_enemy.hp * 0.6))
                    extra_enemy.max_hp = extra_enemy.hp
                    extra_enemy.attack = max(1, int(extra_enemy.attack * 0.7))
                    enemies.append(extra_enemy)
                else:
                    break  # Stop rolling if one fails

        self.enemies = enemies
        self.enemy = enemies[0]  # For compatibility with old code
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
            # Give the player a Small Healing Potion for testing
           
            self.player.potions[0] = SmallHealingPotion()

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

            # Give the player a Small Healing Potion for testing
            self.player.potions[0] = SmallHealingPotion()

            # Update room number and player reference in other classes
            self.announcements.player = self.player
            self.announcements.current_room = self.current_room
            self.animations.player = self.player
            self.animations.current_room = self.current_room
            self.battle_system.current_room = self.current_room
            self.player.announcements = self.announcements  # <-- KEEP THIS LINE

            self.animations.player_slide_and_disappear()

            # --- Track which bosses have been encountered this run ---
            self.bosses_encountered = set()
            self.bosses_defeated = set()
            self.boss_probability = 0.0

            while self.running:
                self.current_room += 1

                # --- SHOP LOGIC: Only after room 5 ---
                if self.current_room > 5:
                    if random.random() < self.shop_probability:
                        self.show_shop()
                        self.shop_probability = 0.0
                    else:
                        self.shop_probability += 0.05

                # --- BOSS LOGIC: Only after room 10 ---
                boss_room = False
                boss_to_spawn = None
                final_boss_ready = False

                if self.current_room >= 10:
                    # If both regular bosses are defeated, spawn the final boss
                    if len(self.bosses_defeated) >= len(self.boss_classes):
                        final_boss_ready = True
                        boss_room = True
                        boss_to_spawn = FinalBoss
                        self.boss_probability = 0.0  # No more boss chance after this
                    # Otherwise, normal boss logic
                    elif len(self.bosses_defeated) < len(self.boss_classes):
                        if random.random() < self.boss_probability:
                            boss_room = True
                            available_bosses = [b for b in self.boss_classes if b not in self.bosses_encountered]
                            if not available_bosses:
                                available_bosses = [b for b in self.boss_classes if b not in self.bosses_defeated]
                            boss_to_spawn = random.choice(available_bosses)
                            self.bosses_encountered.add(boss_to_spawn)
                            self.boss_probability = 0.0  # Only reset here!
                else:
                    self.boss_probability = 0.0
                if self.current_room >= 11 and not boss_room and not final_boss_ready:
                    self.boss_probability += 0.01
                self.reset_player_position()

                # --- Spawn boss or normal enemies ---
                if boss_room and boss_to_spawn:
                    boss = boss_to_spawn(x=(WIDTH * 3) // 4, room_number=self.current_room)
                    self.enemies = [boss]
                    self.enemy = boss
                    self.renderer.enemy = boss
                    if final_boss_ready:
                        self.announcements.wait_for_space(
                            f"!!! FINAL BOSS ROOM !!!\nYou face {boss.name}!",
                            enemy=boss, show_player=True, room_number=self.current_room
                        )
                    else:
                        self.announcements.wait_for_space(
                            f"BOSS ROOM!\nYou face {boss.name}!",
                            enemy=boss, show_player=True, room_number=self.current_room
                        )
                else:
                    self.spawn_enemies()

                self.announcements.current_room = self.current_room
                self.animations.current_room = self.current_room
                self.battle_system.current_room = self.current_room

                # --- Prompt for potion use before battle ---
                used_potion_prompt = any(self.player.potions)
                self.announcements.pre_battle_item_use(self.player, self.enemy, self.enemies)
                if not used_potion_prompt:
                    self.announcements.battle_start(self.enemy)
                
                if self.input_handler.quit:
                    return

                result, battle_log = self.battle_system.battle(self.player, self.enemies, lambda: self.running)

                if result == "win":
                    # --- Mark boss as defeated if this was a boss room ---
                    if boss_room and boss_to_spawn and not final_boss_ready:
                        self.bosses_defeated.add(boss_to_spawn)
                        # Add stacking 30% XP bonus
                        self.player.boss_xp_bonus *= 1.3

                    # --- Luck-based loot chance ---
                    base_chance = 0.20
                    luck_bonus = (self.player.luck // 2) * 0.01  # +1% per 2 luck
                    loot_chance = base_chance + luck_bonus
                    loot_chance += getattr(self.player, "loot_chance_bonus", 0.0)

                    found_items = []
                    if random.random() < loot_chance:
                        potion_class = random.choice(HealingPotion.potion_classes)
                        found_items.append(potion_class())
                    if random.random() < loot_chance:
                        eq_class = random.choice(Equipment.equipment_classes)
                        max_eq_level = 1 + (self.current_room // 10)
                        eq_level = random.randint(1, max_eq_level)
                        eq_tier = random_tier(self.player.luck)
                        found_items.append(eq_class(level=eq_level, tier=eq_tier))
                    
                    # --- Gold reward ---
                    gold_chance = 0.35 + 0.01 * self.player.luck  # 30% base +1% per luck
                    if random.random() < gold_chance:
                        gold_earned = random.randint(1, 3)
                        self.player.gold += gold_earned
                        found_items.append(type("Gold", (), {"name": f"{gold_earned} gold"})())
                    if found_items:
                        self.announcements.loot_screen(found_items, battle_log_lines=battle_log[-6:])
                        for item in found_items:
                            if isinstance(item, Potion):
                                for i in range(4):
                                    if self.player.potions[i] is None:
                                        self.player.potions[i] = item
                                        break
                                else:
                                    # All slots full, prompt
                                    self.announcements.potion_pickup_prompt(self.player, item)
                            elif isinstance(item, Equipment):
                                for i in range(4):
                                    if self.player.equipment_items[i] is None:
                                        self.player.equipment_items[i] = item
                                        self.player.equip(item)
                                        break
                                else:
                                    # All slots full, prompt
                                    self.announcements.equipment_pickup_prompt(self.player, item)
                    self.announcements.current_room = self.current_room
                    self.animations.current_room = self.current_room
                    self.battle_system.current_room = self.current_room
                    self.announcements.win(battle_log_lines=battle_log[-6:])
                    self.animations.player_slide_and_disappear()
                else:
                    self.announcements.lose(self.enemy)
                    break

                if self.input_handler.quit:
                    return

    def show_shop(self):
        healing_potion_cls = random.choice([SmallHealingPotion, MediumHealingPotion, MaxHealingPotion])
        healing_prices = {SmallHealingPotion: 5, MediumHealingPotion: 10, MaxHealingPotion: 15}
        healing_price = healing_prices[healing_potion_cls]
        healing_potion = healing_potion_cls()

        stat_potion_cls = random.choice([
            AttackPotion, DefencePotion, AttackSpeedPotion, CritChancePotion,
            CritDamagePotion, ThornPotion, LifestealPotion, DodgePotion, RegenPotion
        ])
        stat_potion = stat_potion_cls()
        stat_price = 10

        eq_class = random.choice(Equipment.equipment_classes)
        eq_level = max(1, self.current_room // 10)
        eq_tier = random_tier(self.player.luck)
        eq_item = eq_class(level=eq_level, tier=eq_tier)
        tier_index = EQUIPMENT_TIERS.index(eq_tier)
        eq_price = 10 * eq_level * (tier_index + 1)

        golden_sword = Item("Golden Sword")
        golden_price = 999

        shop_items = [
            (healing_potion, healing_price),
            (stat_potion, stat_price),
            (eq_item, eq_price),
            (golden_sword, golden_price),
        ]

        while True:
            lines = ["SHOP", ""]
            for i, (item, price) in enumerate(shop_items):
                name = item.name if not hasattr(item, "display_name") else item.display_name()
                lines.append(f"   {i+1}. {name} ({price} gold)")
            lines.append("")
            lines.append(f"Gold: {self.player.gold}")
            lines.append("Press 1-4 to buy, SPACE to leave shop.")
            message = "\n".join(lines)
            self.renderer.render(self.player, self.room, self.ui, intro_message=message, room_number=self.current_room)
            # --- Input handling ---
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in [b'1', b'2', b'3', b'4']:
                        idx = int(key) - 1
                        item, price = shop_items[idx]
                        if self.player.gold >= price:
                            self.player.gold -= price
                            # Give item to player, using the same logic as loot
                            if isinstance(item, Potion):
                                for i in range(4):
                                    if self.player.potions[i] is None:
                                        self.player.potions[i] = item
                                        break
                            elif isinstance(item, Equipment):
                                for i in range(4):
                                    if self.player.equipment_items[i] is None:
                                        self.player.equipment_items[i] = item
                                        self.player.equip(item)
                                        break
                            else:
                                # All slots full, prompt
                                self.announcements.equipment_pickup_prompt(self.player, item)
                            self.announcements.wait_for_space(f"You bought {item.name}!", show_player=True, room_number=self.current_room)
                        else:
                            self.announcements.wait_for_space("Not enough gold!", show_player=True, room_number=self.current_room)
                        break  # Re-render shop after purchase or error
                    elif key == b' ':
                        return  # Exit shop
                time.sleep(0.08)

if __name__ == "__main__":
    print('\033[?25l', end='')
    try:
        game = Game()
        game.run()
    finally:
        print('\033[?25h', end='')