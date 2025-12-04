import math
import random
from typing import List, Tuple

import pygame

# 初始化Pygame混合模式
pygame.init()


class Particle:
    """轻量级粒子基类，用于各种技能残影与烟雾"""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(2.0, 4.5)
        self.speed_x = random.uniform(-1.5, 1.5)
        self.speed_y = random.uniform(-1.5, 1.5)
        self.life = random.randint(18, 45)
        self.max_life = self.life
        self.gravity = random.uniform(0.02, 0.1)

    def update(self) -> bool:
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size))
        temp = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color, alpha), (size, size), size)
        surface.blit(temp, (int(self.x - size), int(self.y - size)))


class NormalAttackEffect:
    """普攻：爪痕挥砍并显示伤害数字"""

    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, is_player1: bool = True):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.current_pos = list(self.start_pos)
        self.color = (240, 200, 120) if is_player1 else (120, 210, 240)
        self.timer = 0
        self.travel_frames = 14  # 约0.23秒
        self.slash_frames = 26   # 击中后的显示时间
        self.trail: List[dict] = []
        self.claw_marks: List[dict] = []
        self.hit = False
        self.damage_timer = 0

    def _create_claw(self):
        base_angle = math.atan2(self.target_pos[1] - self.start_pos[1], self.target_pos[0] - self.start_pos[0])
        for i in range(3):
            length = 70 + i * 6
            width = 26
            surf = pygame.Surface((length, width), pygame.SRCALPHA)
            points = [(8, width // 2), (length - 10, 4), (length - 4, width // 2), (length - 10, width - 4)]
            pygame.draw.polygon(surf, (*self.color, 220), points)
            # 模拟模糊：扩大后降低透明度叠加
            blurred = pygame.transform.smoothscale(surf, (int(length * 1.35), int(width * 1.55)))
            blurred.set_alpha(120)
            angle = base_angle + random.uniform(-0.18, 0.18)
            rotated = pygame.transform.rotate(surf, -math.degrees(angle))
            rotated_blur = pygame.transform.rotate(blurred, -math.degrees(angle))
            offset_x = random.uniform(-8, 8)
            offset_y = random.uniform(-8, 8)
            rect = rotated.get_rect(center=(self.target_pos[0] + offset_x, self.target_pos[1] + offset_y))
            rect_blur = rotated_blur.get_rect(center=rect.center)
            self.claw_marks.append({
                "sharp": rotated,
                "blur": rotated_blur,
                "rect": rect,
                "blur_rect": rect_blur,
                "alpha": 255,
                "life": self.slash_frames
            })

        self.damage_timer = self.slash_frames

    def update(self):
        self.timer += 1
        if not self.hit:
            progress = min(1, self.timer / self.travel_frames)
            self.current_pos[0] = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * progress
            self.current_pos[1] = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * progress
            self.trail.append({
                "x": self.current_pos[0],
                "y": self.current_pos[1],
                "alpha": 200,
                "life": 12
            })
            if progress >= 1:
                self.hit = True
                self._create_claw()
        else:
            for mark in self.claw_marks[:]:
                mark["life"] -= 1
                mark["alpha"] = int(255 * (mark["life"] / self.slash_frames))
                if mark["life"] <= 0:
                    self.claw_marks.remove(mark)
            if self.damage_timer > 0:
                self.damage_timer -= 1

        for trail in self.trail[:]:
            trail["life"] -= 1
            trail["alpha"] = max(0, trail["alpha"] - 16)
            if trail["life"] <= 0:
                self.trail.remove(trail)

    def draw(self, surface: pygame.Surface):
        # 轨迹模糊
        for trail in self.trail:
            radius = 10
            blur_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(blur_surface, (*self.color, trail["alpha"]), (radius, radius), radius)
            surface.blit(blur_surface, (int(trail["x"] - radius), int(trail["y"] - radius)))

        if not self.hit:
            core = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(core, (255, 255, 255, 230), (9, 9), 9)
            pygame.draw.circle(core, (*self.color, 200), (9, 9), 6)
            surface.blit(core, (int(self.current_pos[0] - 9), int(self.current_pos[1] - 9)))
        else:
            for mark in self.claw_marks:
                mark["blur"].set_alpha(int(mark["alpha"] * 0.6))
                mark["sharp"].set_alpha(mark["alpha"])
                surface.blit(mark["blur"], mark["blur_rect"])
                surface.blit(mark["sharp"], mark["rect"])

            if self.damage_timer > 0:
                font = pygame.font.Font(None, 32)
                alpha = int(255 * (self.damage_timer / self.slash_frames))
                text = font.render("-10", True, (255, 80, 80))
                text.set_alpha(alpha)
                y_offset = (self.slash_frames - self.damage_timer) * 0.6
                surface.blit(text, (self.target_pos[0] - 16, self.target_pos[1] - 40 - y_offset))

    def is_done(self) -> bool:
        return self.hit and not self.trail and not self.claw_marks and self.damage_timer <= 0


class HealEffect:
    """加血：冒泡式加号与绿色数字"""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 70  # 约1.1秒
        self.pluses: List[dict] = []
        self.glow_radius = 0

    def update(self):
        self.timer += 1
        self.glow_radius = 25 + math.sin(self.timer * 0.15) * 6
        if self.timer < self.duration:
            # 冒泡加号
            if self.timer % 2 == 0:
                self.pluses.append({
                    "x": self.x + random.uniform(-18, 18),
                    "y": self.y - random.uniform(0, 12),
                    "size": random.uniform(12, 24),
                    "speed": random.uniform(-1.6, -0.8),
                    "alpha": 255,
                })

        for plus in self.pluses[:]:
            plus["y"] += plus["speed"]
            plus["alpha"] = max(0, plus["alpha"] - 6)
            if plus["alpha"] <= 0:
                self.pluses.remove(plus)

    def draw(self, surface: pygame.Surface):
        if self.timer < self.duration:
            glow_surface = pygame.Surface((int(self.glow_radius * 2), int(self.glow_radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (120, 255, 160, 80), (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
            pygame.draw.circle(glow_surface, (180, 255, 200, 140), (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius / 1.5), 2)
            surface.blit(glow_surface, (int(self.x - self.glow_radius), int(self.y - self.glow_radius)))

        for plus in self.pluses:
            alpha = int(plus["alpha"])
            size = plus["size"]
            plus_surface = pygame.Surface((int(size), int(size)), pygame.SRCALPHA)
            pygame.draw.rect(plus_surface, (120, 255, 160, alpha), (size * 0.4, 0, size * 0.2, size))
            pygame.draw.rect(plus_surface, (120, 255, 160, alpha), (0, size * 0.4, size, size * 0.2))
            surface.blit(plus_surface, (plus["x"] - size / 2, plus["y"] - size / 2))

        if self.timer < self.duration:
            font = pygame.font.Font(None, 32)
            text = font.render("+10", True, (100, 240, 140))
            text.set_alpha(max(0, 255 - int(self.timer * 3)))
            surface.blit(text, (self.x - 16, self.y - 50 - self.timer * 0.4))

    def is_done(self) -> bool:
        return self.timer >= self.duration and not self.pluses


class FlameAttackEffect:
    """火焰攻击：火焰弹飞向目标，命中后逐渐消散"""

    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.progress = 0
        self.speed = 0.08
        self.hit = False
        self.timer = 0
        self.trail: List[Particle] = []
        self.smoke: List[Particle] = []

    def update(self):
        if not self.hit:
            self.progress += self.speed
            self.progress = min(1, self.progress)
            cx = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * self.progress
            cy = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * self.progress
            if random.random() < 0.7:
                p = Particle(cx, cy, random.choice([(255, 120, 40), (255, 180, 60), (255, 80, 20)]))
                p.size = random.uniform(3, 6)
                p.gravity = 0.01
                self.trail.append(p)
            for p in self.trail[:]:
                if not p.update():
                    self.trail.remove(p)
            if self.progress >= 1:
                self.hit = True
                self.timer = 35  # 约0.6秒消散
                for _ in range(24):
                    smoke = Particle(self.target_pos[0], self.target_pos[1], random.choice([(120, 120, 120), (160, 140, 120)]))
                    smoke.size = random.uniform(3, 7)
                    smoke.speed_x *= 1.5
                    smoke.speed_y *= 1.5
                    smoke.gravity = -0.02
                    self.smoke.append(smoke)
        else:
            self.timer -= 1
            for p in self.smoke[:]:
                if not p.update():
                    self.smoke.remove(p)

    def draw(self, surface: pygame.Surface):
        if not self.hit:
            cx = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * self.progress
            cy = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * self.progress
            for p in self.trail:
                p.draw(surface)
            core = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(core, (255, 210, 120, 220), (12, 12), 12)
            pygame.draw.circle(core, (255, 120, 40, 255), (12, 12), 9)
            surface.blit(core, (int(cx - 12), int(cy - 12)))
        else:
            for p in self.smoke:
                p.draw(surface)
            if self.timer > 0:
                alpha = int(200 * (self.timer / 35))
                radius = 40 - (self.timer / 35) * 20
                temp = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(temp, (255, 140, 60, alpha), (int(radius), int(radius)), int(radius), 3)
                surface.blit(temp, (int(self.target_pos[0] - radius), int(self.target_pos[1] - radius)))

    def is_done(self) -> bool:
        return self.hit and self.timer <= 0 and not self.smoke


class ShieldEffect:
    """防御屏障：盾牌图片下降到角色侧面，维持一回合后淡出"""

    _shield_sprite: pygame.Surface | None = None

    @classmethod
    def _load_sprite(cls) -> pygame.Surface:
        if cls._shield_sprite is None:
            # 通过绘制生成盾牌外观，避免依赖外部 png 资源
            width, height = 110, 140
            surf = pygame.Surface((width, height), pygame.SRCALPHA)

            # 背景渐变
            top_color = pygame.Color(130, 200, 255)
            bottom_color = pygame.Color(40, 90, 160)
            for y in range(height):
                ratio = y / height
                color = (
                    int(top_color.r * (1 - ratio) + bottom_color.r * ratio),
                    int(top_color.g * (1 - ratio) + bottom_color.g * ratio),
                    int(top_color.b * (1 - ratio) + bottom_color.b * ratio),
                    210,
                )
                pygame.draw.line(surf, color, (width * 0.2, y), (width * 0.8, y), 2)

            # 外圈轮廓
            outer_points = [
                (width * 0.5, 8),
                (width * 0.85, height * 0.22),
                (width * 0.85, height * 0.7),
                (width * 0.5, height - 8),
                (width * 0.15, height * 0.7),
                (width * 0.15, height * 0.22),
            ]
            pygame.draw.polygon(surf, (90, 150, 210, 230), outer_points)
            pygame.draw.polygon(surf, (255, 255, 255, 200), outer_points, width=3)

            # 中央亮纹
            center_points = [
                (width * 0.5, 16),
                (width * 0.7, height * 0.3),
                (width * 0.7, height * 0.65),
                (width * 0.5, height - 18),
                (width * 0.3, height * 0.65),
                (width * 0.3, height * 0.3),
            ]
            pygame.draw.polygon(surf, (180, 230, 255, 140), center_points)
            pygame.draw.line(
                surf,
                (255, 255, 255, 200),
                (width * 0.5, 20),
                (width * 0.5, height - 20),
                2,
            )

            cls._shield_sprite = surf
        return cls._shield_sprite

    def __init__(self, x: float, y: float, is_left: bool = True):
        self.base_x = x + 60 if is_left else x - 60
        self.final_y = y - 30
        self.current_y = self.final_y - 220
        self.state = "drop"  # drop -> hold -> fade
        self.timer = 0
        self.hold_frames = 60  # 约一回合显示
        self.fade_frames = 25
        self.sprite = self._load_sprite()
        self.is_left = is_left

    def update(self):
        if self.state == "drop":
            self.current_y += 14
            if self.current_y >= self.final_y:
                self.current_y = self.final_y
                self.state = "hold"
                self.timer = self.hold_frames
        elif self.state == "hold":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "fade"
                self.timer = self.fade_frames
        elif self.state == "fade":
            self.timer -= 1

    def draw(self, surface: pygame.Surface):
        alpha = 255
        if self.state == "drop":
            alpha = max(80, int(255 * (1 - (self.final_y - self.current_y) / 220)))
        elif self.state == "fade":
            alpha = max(0, int(255 * (self.timer / self.fade_frames)))

        sprite = self.sprite
        if not self.is_left:
            sprite = pygame.transform.flip(sprite, True, False)
        sprite = sprite.copy()
        sprite.set_alpha(alpha)
        angle = -10 if self.is_left else 10
        rotated = pygame.transform.rotate(sprite, angle)
        rect = rotated.get_rect(center=(self.base_x, self.current_y))
        surface.blit(rotated, rect)

    def is_done(self) -> bool:
        return self.state == "fade" and self.timer <= 0


class UltimateEffect:
    """大招：蓄力后对敌方位置产生爆炸"""

    def __init__(self, x: float, y: float, is_player1: bool = True, target_x: float | None = None, target_y: float | None = None):
        self.start_pos = (x, y)
        self.target_pos = (target_x if target_x is not None else x, target_y if target_y is not None else y)
        self.is_player1 = is_player1
        self.charge_frames = 18
        self.flight_frames = 12
        self.explosion_frames = 45
        self.stage = 0  # 0:charge,1:flight,2:explode
        self.timer = 0
        self.projectile_pos = list(self.start_pos)
        self.charge_particles: List[Particle] = []
        self.explosion_particles: List[Particle] = []
        self.main_color = (255, 130, 130) if is_player1 else (120, 140, 255)

    def update(self):
        self.timer += 1
        if self.stage == 0:
            if random.random() < 0.6:
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(20, 60)
                px = self.start_pos[0] + math.cos(angle) * dist
                py = self.start_pos[1] + math.sin(angle) * dist
                p = Particle(px, py, self.main_color)
                dx, dy = self.start_pos[0] - px, self.start_pos[1] - py
                length = max(0.1, math.hypot(dx, dy))
                p.speed_x = dx / length * 2.2
                p.speed_y = dy / length * 2.2
                self.charge_particles.append(p)
            for p in self.charge_particles[:]:
                if not p.update():
                    self.charge_particles.remove(p)
            if self.timer >= self.charge_frames:
                self.stage = 1
                self.timer = 0
        elif self.stage == 1:
            progress = min(1, self.timer / self.flight_frames)
            self.projectile_pos[0] = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * progress
            self.projectile_pos[1] = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * progress
            if random.random() < 0.5:
                self.charge_particles.append(Particle(self.projectile_pos[0], self.projectile_pos[1], self.main_color))
            for p in self.charge_particles[:]:
                if not p.update():
                    self.charge_particles.remove(p)
            if progress >= 1:
                self.stage = 2
                self.timer = 0
                for _ in range(36):
                    p = Particle(self.target_pos[0], self.target_pos[1], self.main_color)
                    p.speed_x *= 3
                    p.speed_y *= 3
                    p.size = random.uniform(3, 6)
                    self.explosion_particles.append(p)
        elif self.stage == 2:
            for p in self.explosion_particles[:]:
                if not p.update():
                    self.explosion_particles.remove(p)

    def draw(self, surface: pygame.Surface):
        if self.stage == 0:
            radius = 16 + math.sin(self.timer * 0.2) * 4
            temp = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp, (*self.main_color, 180), (int(radius), int(radius)), int(radius))
            pygame.draw.circle(temp, (255, 255, 255, 230), (int(radius), int(radius)), int(radius / 2))
            surface.blit(temp, (int(self.start_pos[0] - radius), int(self.start_pos[1] - radius)))
            for p in self.charge_particles:
                p.draw(surface)
        elif self.stage == 1:
            for p in self.charge_particles:
                p.draw(surface)
            glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 255, 240), (15, 15), 10)
            pygame.draw.circle(glow, (*self.main_color, 200), (15, 15), 7)
            surface.blit(glow, (int(self.projectile_pos[0] - 15), int(self.projectile_pos[1] - 15)))
        elif self.stage == 2:
            progress = min(1, self.timer / self.explosion_frames)
            radius = 30 + progress * 50
            alpha = int(255 * (1 - progress))
            ring = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*self.main_color, alpha), (int(radius), int(radius)), int(radius), 6)
            surface.blit(ring, (int(self.target_pos[0] - radius), int(self.target_pos[1] - radius)))
            for p in self.explosion_particles:
                p.draw(surface)
            if progress < 0.6:
                font = pygame.font.Font(None, 36)
                text = font.render("-90", True, self.main_color)
                surface.blit(text, (self.target_pos[0] - 20, self.target_pos[1] - 60))

    def is_done(self) -> bool:
        if self.stage < 2:
            return False
        return self.timer >= self.explosion_frames and not self.explosion_particles
