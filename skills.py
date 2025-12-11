import math
import os
import random
from typing import List, Tuple
import pygame
from PIL import Image, ImageFilter
import io

# 初始化Pygame混合模式
pygame.init()

ASSET_DIR = os.path.dirname(__file__)


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

    _claw_sprite: pygame.Surface | None = None

    @classmethod
    def _load_claw(cls) -> pygame.Surface:
        if cls._claw_sprite is None:
            sprite = pygame.image.load("claw.png").convert_alpha()
            # 抓痕缩小为原先的35%，避免遮挡角色
            cls._claw_sprite = pygame.transform.smoothscale(
                sprite, (int(sprite.get_width() * 0.35), int(sprite.get_height() * 0.35))
            )
        return cls._claw_sprite

    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, is_player1: bool = True):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.current_pos = list(self.start_pos)
        self.color = (240, 200, 120) if is_player1 else (120, 210, 240)
        self.timer = 0
        self.slash_frames = 30   # 击中后的显示时间与淡出
        self.claw_marks: List[dict] = []
        self.hit = True
        self.damage_timer = 0
        self.claw_sprite = self._load_claw()
        self._create_claw()

    def _create_claw(self):
        base_angle = math.atan2(self.target_pos[1] - self.start_pos[1], self.target_pos[0] - self.start_pos[0])
        for i in range(3):
            scale = 0.95 + i * 0.08
            sprite = pygame.transform.rotozoom(self.claw_sprite, 0, scale)
            # 以平行于攻击方向的角度旋转
            angle = base_angle + random.uniform(-0.18, 0.18)
            blur_scale = 1.25
            blurred = pygame.transform.smoothscale(
                sprite,
                (
                    int(sprite.get_width() * blur_scale),
                    int(sprite.get_height() * blur_scale),
                ),
            )
            # 模拟高斯模糊：缩放后降低透明度、再轻微缩小叠加
            blurred = pygame.transform.smoothscale(
                blurred, (int(blurred.get_width() * 0.95), int(blurred.get_height() * 0.95))
            )
            blurred.set_alpha(140)
            rotated = pygame.transform.rotate(sprite, -math.degrees(angle))
            rotated_blur = pygame.transform.rotate(blurred, -math.degrees(angle))
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            rect = rotated.get_rect(center=(self.target_pos[0] + offset_x, self.target_pos[1] + offset_y))
            rect_blur = rotated_blur.get_rect(center=rect.center)
            self.claw_marks.append(
                {
                    "sharp": rotated,
                    "blur": rotated_blur,
                    "rect": rect,
                    "blur_rect": rect_blur,
                    "alpha": 255,
                    "life": self.slash_frames,
                }
            )

        self.damage_timer = self.slash_frames

    def update(self):
        self.timer += 1
        for mark in self.claw_marks[:]:
            mark["life"] -= 1
            mark["alpha"] = int(255 * (mark["life"] / self.slash_frames))
            if mark["life"] <= 0:
                self.claw_marks.remove(mark)
        if self.damage_timer > 0:
            self.damage_timer -= 1

    def draw(self, surface: pygame.Surface):
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
        return self.hit and not self.claw_marks and self.damage_timer <= 0


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
        self.glow_radius = 32 + math.sin(self.timer * 0.15) * 7
        if self.timer < self.duration:
            # 冒泡加号
            if self.timer % 2 == 0:
                self.pluses.append({
                    "x": self.x + random.uniform(-18, 18),
                    "y": self.y - random.uniform(0, 12),
                    "size": random.uniform(16, 28),
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
            font = pygame.font.Font(None, 38)
            text = font.render("+10", True, (100, 240, 140))
            text.set_alpha(max(0, 255 - int(self.timer * 3)))
            surface.blit(text, (self.x - 16, self.y - 50 - self.timer * 0.4))

    def is_done(self) -> bool:
        return self.timer >= self.duration and not self.pluses


class FlameAttackEffect:
    """火焰攻击：火焰弹飞向目标，命中后逐渐消散（使用Pillow增强模糊效果）"""

    _left_sprite: pygame.Surface | None = None
    _right_sprite: pygame.Surface | None = None
    _left_blurred_cache: pygame.Surface | None = None
    _right_blurred_cache: pygame.Surface | None = None

    @classmethod
    def _load_sprite(cls, is_left: bool) -> pygame.Surface:
        """加载并预处理火焰精灵"""
        if is_left:
            if cls._left_sprite is None:
                sprite = pygame.image.load(os.path.join(ASSET_DIR, "fire.png")).convert_alpha()
                original_sprite = pygame.transform.smoothscale(
                    sprite, (int(sprite.get_width() * 0.6), int(sprite.get_height() * 0.6))
                )

                cls._left_sprite = original_sprite
                cls._left_blurred_cache = cls._create_advanced_blur(original_sprite)

            return cls._left_sprite
        else:
            if cls._right_sprite is None:
                sprite = pygame.image.load(os.path.join(ASSET_DIR, "fire.png")).convert_alpha()
                original_sprite = pygame.transform.smoothscale(
                    sprite, (int(sprite.get_width() * 0.6), int(sprite.get_height() * 0.6))
                )

                cls._right_sprite = original_sprite
                cls._right_blurred_cache = cls._create_advanced_blur(original_sprite)

            return cls._right_sprite

    @staticmethod
    def _create_advanced_blur(surface: pygame.Surface) -> pygame.Surface:
        """使用Pillow创建高级模糊效果"""
        size = surface.get_size()
        data = pygame.image.tostring(surface, 'RGBA')
        pil_image = Image.frombytes('RGBA', size, data)

        # 基础高斯模糊
        gaussian_blur = pil_image.filter(ImageFilter.GaussianBlur(radius=3))

        # 转换为pygame Surface
        return pygame.image.fromstring(gaussian_blur.tobytes(), size, 'RGBA')

    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float):
        self.start_pos = (start_x, start_y)
        self.target_pos = (target_x, target_y)
        self.is_left = start_x < target_x
        self.sprite = self._load_sprite(self.is_left)

        # 使用缓存的模糊精灵
        if self.is_left:
            self.blurred_sprite = FlameAttackEffect._left_blurred_cache
        else:
            self.blurred_sprite = FlameAttackEffect._right_blurred_cache

        self.progress = 0
        self.speed = 0.06
        self.hit = False
        self.timer = 0
        self.elapsed = 0
        self.smoke: List[Particle] = []
        self.burst_particles: List[Particle] = []
        self.max_travel_frames = int(1 / self.speed)
        self.dissipate_frames = 45
        self.fade_portion = 0.18
        self.wave_phase = random.uniform(0, math.pi * 2)

        # 轨迹效果
        self.trail_positions = []
        self.trail_max_length = 5
        self.trail_alphas = [255, 200, 150, 100, 50]

    def update(self):
        if not self.hit:
            self.elapsed += 1
            self.progress += self.speed
            self.progress = min(1, self.progress)

            # 计算当前位置
            cx = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * self.progress
            cy = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * self.progress

            # 添加轨迹点
            self.trail_positions.insert(0, (cx, cy))
            if len(self.trail_positions) > self.trail_max_length:
                self.trail_positions.pop()

            if self.progress >= 1:
                self.hit = True
                self.timer = self.dissipate_frames
                self._create_impact_effects()
        else:
            self.timer -= 1
            for p in self.smoke[:]:
                if not p.update():
                    self.smoke.remove(p)
            for p in self.burst_particles[:]:
                if not p.update():
                    self.burst_particles.remove(p)

    def _create_impact_effects(self):
        """创建冲击效果"""
        # 烟雾粒子（使用RGB三元组）
        for _ in range(32):
            smoke = Particle(
                self.target_pos[0], self.target_pos[1],
                random.choice([(120, 90, 90), (160, 110, 110)])  # 只传递RGB
            )
            smoke.size = random.uniform(5, 10)
            smoke.speed_x *= 1.6
            smoke.speed_y *= 1.6
            smoke.gravity = -0.02
            smoke.life = random.randint(30, 50)
            smoke.max_life = smoke.life
            self.smoke.append(smoke)

        # 余烬粒子（使用RGB三元组）
        for _ in range(22):
            ember = Particle(
                self.target_pos[0], self.target_pos[1],
                random.choice([(255, 120, 120), (255, 180, 160), (255, 90, 90)])  # 只传递RGB
            )
            ember.size = random.uniform(3, 5)
            ember.speed_x *= 2.5
            ember.speed_y *= 2.5
            ember.gravity = -0.03
            ember.life = random.randint(20, 35)
            ember.max_life = ember.life
            self.burst_particles.append(ember)

    def draw(self, surface: pygame.Surface):
        if not self.hit:
            cx = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * self.progress
            cy = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * self.progress

            # 添加摆动效果
            wobble = math.sin((self.elapsed + self.wave_phase) * 0.4) * 6 + random.uniform(-1.5, 1.5)
            cy += wobble

            # 计算角度和透明度
            angle = -math.degrees(math.atan2(
                self.target_pos[1] - self.start_pos[1],
                self.target_pos[0] - self.start_pos[0]
            ))

            fade_in = min(1.0, self.progress / self.fade_portion)
            fade_out = min(1.0, (1 - self.progress) / self.fade_portion)
            alpha_factor = min(fade_in, fade_out)

            # 旋转精灵
            sprite = pygame.transform.rotozoom(self.sprite, angle, 1.0)
            blur = pygame.transform.rotozoom(self.blurred_sprite, angle, 1.0)

            # 设置透明度
            base_alpha = int(255 * alpha_factor)
            sprite.set_alpha(base_alpha)
            blur.set_alpha(int(200 * alpha_factor * 0.7))

            # 获取矩形
            rect_blur = blur.get_rect(center=(int(cx), int(cy)))
            rect_sprite = sprite.get_rect(center=(int(cx), int(cy)))

            # 绘制轨迹
            for i, (trail_x, trail_y) in enumerate(self.trail_positions[1:], 1):
                if i < len(self.trail_alphas):
                    trail_alpha = self.trail_alphas[i]
                    trail_scale = 1.0 - (i * 0.15)

                    trail_sprite = pygame.transform.rotozoom(self.sprite, angle, trail_scale)
                    trail_sprite.set_alpha(trail_alpha)
                    trail_rect = trail_sprite.get_rect(center=(int(trail_x), int(trail_y)))
                    surface.blit(trail_sprite, trail_rect)

            # 绘制效果
            surface.blit(blur, rect_blur)
            surface.blit(sprite, rect_sprite)
        else:
            # 绘制粒子
            for p in self.smoke:
                p.draw(surface)
            for p in self.burst_particles:
                p.draw(surface)

            # 绘制消散光环
            if self.timer > 0:
                self._draw_dissipating_halo(surface)

    def _draw_dissipating_halo(self, surface: pygame.Surface):
        """绘制消散时的光环效果"""
        alpha = int(230 * (self.timer / self.dissipate_frames))
        radius = 48 - (self.timer / self.dissipate_frames) * 26

        # 简化版光环
        temp = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(temp, (255, 100, 100, alpha),
                           (int(radius), int(radius)), int(radius), 4)
        pygame.draw.circle(temp, (255, 170, 170, max(30, alpha - 30)),
                           (int(radius), int(radius)), int(radius * 0.6))

        surface.blit(temp, (int(self.target_pos[0] - radius),
                            int(self.target_pos[1] - radius)))

    def is_done(self) -> bool:
        return self.hit and self.timer <= 0 and not self.smoke and not self.burst_particles
class ShieldEffect:
    """防御屏障：盾牌图片下降到角色侧面，维持一回合后淡出"""

    _left_sprite: pygame.Surface | None = None
    _right_sprite: pygame.Surface | None = None

    @classmethod
    def _load_sprite(cls, is_left: bool) -> pygame.Surface:
        if is_left and cls._left_sprite is None:
            sprite = pygame.image.load("left_shield.png").convert_alpha()
            target_height = int(320 * 2 / 3)  # 盾牌高度约为人物高度的2/3
            scale_ratio = target_height / sprite.get_height()
            cls._left_sprite = pygame.transform.smoothscale(
                sprite, (int(sprite.get_width() * scale_ratio), target_height)
            )
        if not is_left and cls._right_sprite is None:
            sprite = pygame.image.load("right_shield.png").convert_alpha()
            target_height = int(320 * 2 / 3)
            scale_ratio = target_height / sprite.get_height()
            cls._right_sprite = pygame.transform.smoothscale(
                sprite, (int(sprite.get_width() * scale_ratio), target_height)
            )
        return cls._left_sprite if is_left else cls._right_sprite

    def __init__(self, x: float, y: float, is_left: bool = True):
        self.base_x = x + 70 if is_left else x - 70
        self.final_y = y - 30
        self.current_y = self.final_y - 220
        self.state = "drop"  # drop -> hold -> fade
        self.timer = 0
        self.hold_frames = 70  # 约一回合显示
        self.fade_frames = 30
        self.sprite = self._load_sprite(is_left)
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

        sprite = self.sprite.copy()
        sprite.set_alpha(alpha)
        angle = -10 if self.is_left else 10
        rotated = pygame.transform.rotate(sprite, angle)
        rect = rotated.get_rect(center=(self.base_x, self.current_y))
        surface.blit(rotated, rect)

    def is_done(self) -> bool:
        return self.state == "fade" and self.timer <= 0


class UltimateEffect:
    """大招：蓄力后对敌方位置产生爆炸"""

    _boom_frames: List[pygame.Surface] | None = None

    @classmethod
    def _load_boom_frames(cls) -> List[pygame.Surface]:
        if cls._boom_frames is None:
            gif_path = os.path.join(ASSET_DIR, "boom.gif")
            frames: List[pygame.Surface] = []
            try:
                with Image.open(gif_path) as img:
                    pil_frames: List[Image.Image] = []
                    for frame_idx in range(img.n_frames):
                        img.seek(frame_idx)
                        rgba_frame = img.convert("RGBA")
                        # 将纯黑背景转换为透明，避免叠加时出现黑边
                        transparent_ready = []
                        for r, g, b, a in rgba_frame.getdata():
                            if r < 10 and g < 10 and b < 10:
                                transparent_ready.append((r, g, b, 0))
                            else:
                                transparent_ready.append((r, g, b, a))
                        rgba_frame.putdata(transparent_ready)
                        pil_frames.append(rgba_frame.copy())
                    # 增加帧数：为相邻帧插入插值帧，使爆炸更加顺滑
                    expanded_frames: List[Image.Image] = []
                    for idx, frame in enumerate(pil_frames):
                        expanded_frames.append(frame)
                        if idx < len(pil_frames) - 1:
                            next_frame = pil_frames[idx + 1]
                            blended = Image.blend(frame, next_frame, 0.5)
                            expanded_frames.append(blended)
                    for frame in expanded_frames:
                        surface = pygame.image.fromstring(
                            frame.tobytes(), frame.size, "RGBA"
                        ).convert_alpha()
                        frames.append(surface)
            except Exception:
                fallback = pygame.image.load(gif_path).convert_alpha()
                fallback.set_colorkey((0, 0, 0))
                frames.append(fallback)
            cls._boom_frames = frames
        return cls._boom_frames

    def __init__(self, x: float, y: float, is_player1: bool = True, target_x: float | None = None, target_y: float | None = None):
        self.start_pos = (x, y)
        self.target_pos = (target_x if target_x is not None else x, target_y if target_y is not None else y)
        self.is_player1 = is_player1
        self.charge_frames = 18
        self.flight_frames = 14
        self.explosion_frames = 78
        self.stage = 0  # 0:charge,1:flight,2:explode
        self.timer = 0
        self.projectile_pos = list(self.start_pos)
        self.charge_particles: List[Particle] = []
        self.explosion_particles: List[Particle] = []
        self.main_color = (255, 130, 130) if is_player1 else (120, 140, 255)
        self.boom_frames = self._load_boom_frames()

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
            progress = min(1.0, self.timer / self.explosion_frames)
            eased = progress ** 0.7
            radius = 36 + eased * 64
            alpha = int(255 * (1 - eased))
            ring = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            highlight_color = tuple(min(255, c + 60) for c in self.main_color)
            pygame.draw.circle(ring, (*highlight_color, min(255, alpha + 40)), (int(radius), int(radius)), int(radius), 8)
            pygame.draw.circle(ring, (*self.main_color, alpha), (int(radius), int(radius)), int(radius * 0.62))
            surface.blit(ring, (int(self.target_pos[0] - radius), int(self.target_pos[1] - radius)))
            # 爆炸贴图加戏：扩大并逐渐淡出
            if self.boom_frames:
                frame_progress = min(1.0, self.timer / self.explosion_frames)
                frame_index = min(len(self.boom_frames) - 1, int(frame_progress * (len(self.boom_frames) - 1)))
                boom_frame = self.boom_frames[frame_index]
                target_visual_size = max(120, boom_frame.get_width(), boom_frame.get_height())
                boom_size = target_visual_size
                boom = pygame.transform.smoothscale(boom_frame, (int(boom_size), int(boom_size)))
                boom.set_alpha(max(0, int(255 * (1 - eased))))
                boom_rect = boom.get_rect(center=(int(self.target_pos[0]), int(self.target_pos[1] - 10)))
                surface.blit(boom, boom_rect)
            for p in self.explosion_particles:
                p.draw(surface)
            if progress < 0.6:
                font = pygame.font.Font(None, 36)
                text = font.render("-90", True, highlight_color)
                surface.blit(text, (self.target_pos[0] - 20, self.target_pos[1] - 60))

    def is_done(self) -> bool:
        if self.stage < 2:
            return False
        return self.timer >= self.explosion_frames and not self.explosion_particles
