import time
from dataclasses import dataclass, field
from typing import Optional


ROUND_LIMIT = 30
SELECTION_TIME = 5


@dataclass
class PlayerState:
    name: str
    is_left: bool
    hp: int = 100
    mp: int = 50
    rage: int = 0
    shield: int = 0
    debuff_attack: int = 0
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
            self.rage = min(100, self.rage + (dmg // 10))

    def restore_mana(self, amount: int):
        self.mp = min(100, self.mp + amount)

    def use_mana(self, amount: int) -> bool:
        if self.mp >= amount:
            self.mp -= amount
            return True
        return False

    def heal(self, amount: int):
        self.hp = min(100, self.hp + amount)


@dataclass
class RoundState:
    round_index: int = 1
    phase: str = "select"  # select -> execute -> post_wait -> announce
    selection_start: float = field(default_factory=time.time)
    left_choice: Optional[int] = None
    right_choice: Optional[int] = None
    execute_time: float = 0.0
    phase_time: float = 0.0

    def reset_for_selection(self):
        self.left_choice = None
        self.right_choice = None
        self.phase = "select"
        self.selection_start = time.time()


@dataclass
class GestureResult:
    gesture: Optional[int]
    is_ok: bool
    handedness: str


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
        actor.restore_mana(5)
    elif skill_id == 2:
        if actor.heal_cooldown == 0:
            actor.heal(20)
            actor.heal_cooldown = 1
            actor.restore_mana(5)
        else:
            actor.last_skill = None
    elif skill_id == 3:
        if actor.use_mana(20):
            damage = 50
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            target.debuff_attack = 10
        else:
            actor.last_skill = None
    elif skill_id == 4:
        if actor.use_mana(15):
            actor.shield = max(actor.shield, 30)
        else:
            actor.last_skill = None
    elif skill_id == 5:
        if actor.rage >= 50 and actor.use_mana(50):
            damage = 100
            if actor.debuff_attack > 0:
                damage = max(0, damage - actor.debuff_attack)
                actor.debuff_attack = 0
            dmg_pending = damage
            actor.heal(30)
            actor.rage = 0
        else:
            actor.last_skill = None

    target.pending_damage += dmg_pending


def apply_round_damage(player: PlayerState):
    if player.pending_damage > 0:
        player.apply_damage(player.pending_damage)
        player.pending_damage = 0
    if player.heal_cooldown > 0:
        player.heal_cooldown -= 1
