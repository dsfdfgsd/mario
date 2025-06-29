import pygame
from .. import setup, tools
from .. import constants as C
from .powerup import create_powerup


class Box(pygame.sprite.Sprite):
    def __init__(self, x, y, box_type, group, name='box'):
        pygame.sprite.Sprite.__init__(self)  # 初始化父类
        self.x = x  # 水平坐标
        self.y = y  # 垂直坐标
        self.box_type = box_type  # 盒子类型标识
        self.group = group
        self.name = name

        # 定义4种帧的矩形区域参数 (x位置, y位置, 宽度, 高度)
        self.frame_rects = [
            (384, 0, 16, 16),
            (400, 0, 16, 16),
            (416, 0, 16, 16),
            (432, 0, 16, 16)
        ]

        # 加载图像帧
        self.frames = []
        for frame_rect in self.frame_rects:
            # 从tile_set图集中提取指定区域的图像
            self.frames.append(
                tools.get_image(
                    setup.GRAPHICS['tile_set'],  # 图集资源
                    *frame_rect,  # 解包矩形参数
                    (0, 0, 0),  # 透明色（黑色）
                    C.BRICK_MULTI  # 缩放倍数
                )
            )

        # 初始化显示状态
        self.frame_index = 0  # 当前帧索引
        self.image = self.frames[self.frame_index]  # 当前显示图像
        self.rect = self.image.get_rect()  # 获取碰撞矩形
        self.rect.x = self.x  # 设置实际显示位置
        self.rect.y = self.y
        self.gravity = C.GRAVITY

        self.state = 'rest'
        self.timer = 0

    def update(self):
        self.current_time = pygame.time.get_ticks()
        self.handle_states()

    def handle_states(self):
        if self.state == 'rest':
            self.rest()
        elif self.state == 'bumped':
            self.bumped()
        elif self.state == 'open':
            self.open()

    def rest(self):
        frame_durations = [400, 100, 100, 50]
        if self.current_time - self.timer > frame_durations[self.frame_index]:
            self.frame_index = (self.frame_index + 1) % 4
            self.timer = self.current_time
        self.image = self.frames[self.frame_index]

    def go_bumped(self):
        self.y_vel = -7
        self.state = 'bumped'

    def bumped(self):
        self.rect.y += self.y_vel
        self.y_vel += self.gravity
        self.frame_index = 3
        self.image = self.frames[self.frame_index]

        if self.rect.y > self.y + 5:
            self.rect.y = self.y
            self.state = 'open'

            # box_type 0, 1, 2, 3 对应 空,金币,星星,蘑菇
            if self.box_type == 1:
                pass
            else:
                self.group.add(create_powerup(self.rect.centerx,
                                              self.rect.centery, self.box_type))

    def open(self):
        pass


