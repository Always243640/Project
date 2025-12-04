import time
from dataclasses import dataclass, field
from typing import Optional


ROUND_LIMIT = 15
SELECTION_TIME = 5

HP_MAX = 100
MP_MAX = 50
RAGE_MAX = 30


@dataclass
class PlayerState:
    name: str
    is_left: bool
    hp: int = HP_MAX
    mp: int = MP_MAX
    rage: int = 0
    shield: int = 0
    shield_turns: int = 0
    debuff_attack: int = 0
    pending_debuff_attack: int = 0
    heal_cooldown: int = 0
    last_skill: Optional[int] = None
    pending_damage: int = 0

    def apply_damage(self, dmg: int):
        if self.shield > 0:
            absorbed = min(self.shield, dmg)
            self.shield -= absorbed
            dmg -= absorbed
        self.hp = max(0, self.hp - dmg)
        if dmg > 0:
            self.rage = min(RAGE_MAX, self.rage + (dmg // 5))

    def restore_mana(self, amount: int):
        self.mp = min(MP_MAX, self.mp + amount)

    def use_mana(self, amount: int) -> bool:
        if self.mp >= amount:
            self.mp -= amount
            return True
        return False

    def heal(self, amount: int):
        self.hp = min(HP_MAX, self.hp + amount)


@dataclass
class RoundState:
    round_index: int = 1
    phase: str = "select"  # select -> execute_left -> execute_right -> announce
    selection_start: float = field(default_factory=time.time)
    left_choice: Optional[int] = None
    right_choice: Optional[int] = None
    phase_time: float = 0.0
    left_resolved: bool = False
    right_resolved: bool = False

    def reset_for_selection(self):
        self.left_choice = None
        self.right_choice = None
        self.left_resolved = False
        self.right_resolved = False
        self.phase = "select"
        self.selection_start = time.time()


@dataclass
class GestureResult:
    gesture: Optional[int]
    is_ok: bool
    handedness: str
    side: str


def skill_name(skill_id: Optional[int]) -> str:
    mapping = {1: "普攻", 2: "回血", 3: "火焰", 4: "屏障", 5: "大招"}
    return mapping.get(skill_id, "未选择")


def execute_skill(skill_id: int, actor: PlayerState, target: PlayerState):
    dmg_pending = 0
    if skill_id == 1:
        damage = 10
        if actor.debuff_attack > 0:
            damage = max(0, damage - actor.debuff_attack)
            actor.debuff_attack = 0
        dmg_pending = damage
        actor.restore_mana(4)
    elif skill_id == 2:
        if actor.heal_cooldown == 0:
            actor.heal(15)
            actor.heal_cooldown = 2
        else:
            actor.last_skill = None
    elif skill_id == 3:
        if actor.use_mana(25):
            damage = 40
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            target.pending_debuff_attack = 8
        else:
            actor.last_skill = None
    elif skill_id == 4:
        if actor.use_mana(20):
            actor.shield = 20
            actor.shield_turns = 1
        else:
            actor.last_skill = None
    elif skill_id == 5:
        if actor.rage >= 20 and actor.use_mana(40):
            damage = 90
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            actor.heal(20)
            actor.rage = 0
        else:
            actor.last_skill = None

    target.pending_damage += dmg_pending


def apply_round_damage(player: PlayerState, decrement_cooldown: bool = True):
    if player.pending_damage > 0:
        player.apply_damage(player.pending_damage)
        player.pending_damage = 0
    if decrement_cooldown:
        if player.heal_cooldown > 0:
            player.heal_cooldown -= 1
        if player.shield_turns > 0:
            player.shield_turns -= 1
            if player.shield_turns == 0:
                player.shield = 0
        if player.pending_debuff_attack > 0:
            player.debuff_attack = player.pending_debuff_attack
            player.pending_debuff_attack = 0
