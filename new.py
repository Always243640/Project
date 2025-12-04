import pygame
import sys

# 初始化 pygame
pygame.init()

# 设置窗口大小
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('双人PK游戏')

# 加载背景图片并调整大小
bg = pygame.image.load('bg.png')  # 加载背景图片
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))  # 将背景图调整为适应窗口大小

# 加载人物贴图
left_player = pygame.image.load('left.png')  # 左侧人物
right_player = pygame.image.load('right.png')  # 右侧人物

# 设置人物贴图大小
PLAYER_WIDTH = 160  # 可以根据实际需要调整宽度
PLAYER_HEIGHT = 240  # 可以根据实际需要调整高度

# 调整人物图片大小
left_player = pygame.transform.scale(left_player, (PLAYER_WIDTH, PLAYER_HEIGHT))
right_player = pygame.transform.scale(right_player, (PLAYER_WIDTH, PLAYER_HEIGHT))

# 获取人物图片尺寸
left_player_rect = left_player.get_rect()
right_player_rect = right_player.get_rect()

# 设置人物底部位置
player_height = left_player_rect.height+100
ground_level = HEIGHT - player_height  # 底部对齐水平线

# 设置人物初始位置
left_player_rect.topleft = (100, ground_level)  # 左侧人物位置
right_player_rect.topright = (WIDTH - 150, ground_level)  # 右侧人物位置

# 主循环
running = True
while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 绘制背景
    screen.blit(bg, (0, 0))

    # 绘制人物
    screen.blit(left_player, left_player_rect)
    screen.blit(right_player, right_player_rect)

    # 刷新屏幕
    pygame.display.flip()

# 退出 pygame
pygame.quit()
sys.exit()
