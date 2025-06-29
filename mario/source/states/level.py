import os
import json

from ..components import info, player, stuff, brick, box, enemy
import pygame
from .. import tools, setup
from .. import constants as C


class Level:
    def start(self, game_info):
        self.game_info = game_info
        self.finished = False
        self.next = 'game_over'
        self.info = info.Info('level', self.game_info)
        self.load_map_data()
        self.setup_background()
        self.setup_start_positions()
        self.setup_player()
        self.setup_ground_items()
        self.setup_bricks_and_boxes()
        self.setup_enemies()
        self.setup_checkpoints()

    def load_map_data(self):
        file_name = 'level_1.json'
        file_path = os.path.join('source/data/maps', file_name)
        with open(file_path) as f:
            self.map_data = json.load(f)

    def setup_background(self):
        self.image_name = self.map_data['image_name']
        self.background = setup.GRAPHICS[self.image_name]
        rect = self.background.get_rect()
        self.background = pygame.transform.scale(self.background, (int(rect.width * C.BG_MULTI),
                                                                   int(rect.height * C.BG_MULTI)))
        self.background_rect = self.background.get_rect()
        self.game_window = setup.SCREEN.get_rect()
        self.game_ground = pygame.Surface((self.background_rect.width, self.background_rect.height))

    def setup_start_positions(self):
        self.positions = []
        for data in self.map_data['maps']:
            self.positions.append((data['start_x'], data['end_x'], data['player_x'], data['player_y']))
        self.start_x, self.end_x, self.player_x, self.player_y = self.positions[0]

    def setup_player(self):
        self.player = player.Player('mario')
        self.player.rect.x = self.game_window.x + self.player_x
        self.player.rect.bottom = self.player_y

    def setup_ground_items(self):
        self.ground_items_group = pygame.sprite.Group()

        for name in ['ground', 'pipe', 'step']:
            for item in self.map_data[name]:
                self.ground_items_group.add(stuff.Item(item['x'], item['y'],
                                                       item['width'], item['height'], name))


    def setup_bricks_and_boxes(self):
        """初始化砖块和箱子的精灵组"""
        self.brick_group = pygame.sprite.Group()  # 砖块容器
        self.box_group = pygame.sprite.Group()  # 箱子容器
        self.coin_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()


        # 处理砖块数据
        if 'brick' in self.map_data:
            for brick_data in self.map_data['brick']:
                x, y = brick_data['x'], brick_data['y']
                brick_type = brick_data['type']

                if brick_type == 0:
                    if 'brick_num' in brick_data:
                        # TODO batch bricks
                        pass
                    else:
                        self.brick_group.add(brick.Brick(x, y, brick_type, None))
                elif brick_type == 1:
                    self.brick_group.add(brick.Brick(x, y, brick_type, self.coin_group))
                else:
                    self.brick_group.add(brick.Brick(x, y, brick_type, self.powerup_group))




        # 处理箱子数据（注：原代码存在笔误，应为box_group）
        if 'box' in self.map_data:
            for box_data in self.map_data['box']:
                x, y = box_data['x'], box_data['y']
                box_type = box_data['type']
                if box_type == 1:
                    self.box_group.add(box.Box(x, y, box_type, self.coin_group))
                else:
                    self.box_group.add(box.Box(x, y, box_type, self.powerup_group))


    def setup_enemies(self):
        self.dying_group = pygame.sprite.Group()
        self.shell_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.enemy_group_dict = {}  # 创建敌人分组字典

        # 遍历地图数据中的敌人配置
        for enemy_group_data in self.map_data['enemy']:
            group = pygame.sprite.Group()  # 创建新精灵组

            # 解构敌人组数据
            for enemy_group_id, enemy_list in enemy_group_data.items():
                # 批量生成敌人
                for enemy_data in enemy_list:
                    group.add(enemy.create_enemy(enemy_data))

                # 登记分组到字典
                self.enemy_group_dict[enemy_group_id] = group

    def setup_checkpoints(self):
        self.checkpoint_group = pygame.sprite.Group()
        for item in self.map_data['checkpoint']:
            x, y, w, h = item['x'], item['y'], item['width'], item['height']
            checkpoint_type = item['type']
            enemy_groupid = item.get('enemy_groupid')
            self.checkpoint_group.add(stuff.Checkpoint(x, y, w, h, checkpoint_type, enemy_groupid))



    def update(self, surface, keys):
        # 获取当前游戏时间（毫秒）
        self.current_time = pygame.time.get_ticks()

        # 更新玩家状态
        self.player.update(keys, self)

        # 死亡状态处理
        if self.player.dead:
            # 死亡3秒后结束游戏
            if self.current_time - self.player.death_timer > 3000:
                self.finished = True
                self.update_game_info()

        elif self.is_frozen():
            pass
        else:

            self.update_player_position()  # 更新玩家坐标
            self.check_checkpoints()
            self.check_if_go_die()  # 检测死亡条件
            self.update_game_window()  # 更新游戏视口
            self.info.update()
            self.brick_group.update()
            self.box_group.update()
            self.enemy_group.update(self)
            self.dying_group.update(self)
            self.shell_group.update(self)
            self.coin_group.update()
            self.powerup_group.update(self)


        # 画面绘制（参数surface应为屏幕Surface对象）
        self.draw(surface)

    def is_frozen(self):
        return self.player.state in ['small2big', 'big2small',
                                     'big2fire', 'fire2small']




    def update_player_position(self):
        self.player.rect.x += self.player.x_vel
        if self.player.rect.x < self.start_x:
            self.player.rect.x = self.start_x
        elif self.player.rect.right > self.end_x:
            self.player.rect.right = self.end_x

        self.check_x_collisions()

        # y
        if not self.player.dead:
            self.player.rect.y += self.player.y_vel
            self.check_y_collisions()



    def check_x_collisions(self):
        check_group = pygame.sprite.Group(self.ground_items_group, self.brick_group, self.box_group)
        collided_sprite = pygame.sprite.spritecollideany(self.player, check_group)
        if collided_sprite:
            self.adjust_player_x(collided_sprite)

        if self.player.hurt_immune:
            return

        enemy = pygame.sprite.spritecollideany(self.player, self.enemy_group)
        if enemy:
            if self.player.big:
                self.player.state = 'big2small'
                self.player.hurt_immune = True
            else:
                self.player.go_die()



        shell = pygame.sprite.spritecollideany(self.player, self.shell_group)

        if shell:
            if shell.state == 'slide':
                self.player.go_die()
            else:
                if self.player.rect.x < shell.rect.x:
                    shell.x_vel = 10
                    shell.rect.x += 40
                    shell.direction = 1
                else:
                    shell.x_vel = -10
                    shell.rect.x -= 40
                    shell.direction = 0
                shell.state = 'slide'

        powerup = pygame.sprite.spritecollideany(self.player, self.powerup_group)

        if powerup:
            if powerup.name == 'fireballr':
                pass
            if powerup.name == 'fireflower':
                self.player.state = 'big2fire'
                powerup.kill()

        # if powerup:
        #     powerup.kill()
        #     # if powerup.name == 'mushroom':
        #     #     self.player.state = 'small2big'
        #     if powerup.name == 'fireflower':
        #         self.player.state = 'big2fire'

    def check_y_collisions(self):

        ground_item = pygame.sprite.spritecollideany(self.player, self.ground_items_group)
        brick = pygame.sprite.spritecollideany(self.player, self.brick_group)
        box = pygame.sprite.spritecollideany(self.player, self.box_group)
        enemy = pygame.sprite.spritecollideany(self.player, self.enemy_group)

        if brick and box:
            to_brick = abs(self.player.rect.centerx - brick.rect.centerx)
            to_box = abs(self.player.rect.centerx - box.rect.centerx)

            if to_brick > to_box:
                brick = None
            else:
                box = None

        if ground_item:
            self.adjust_player_y(ground_item)
        elif brick:
            self.adjust_player_y(brick)
        elif box:
            self.adjust_player_y(box)
        elif enemy:

            if self.player.hurt_immune:
                return

            self.adjust_player_y(enemy)
            if enemy.name == 'koopa':
                self.shell_group.add(enemy)
            else:
                self.dying_group.add(enemy)

            if self.player.y_vel < 0:
                how = 'bumped'
            else:
                how = 'trampled'
                self.player.state = 'jump'
                self.player.rect.bottom = enemy.rect.top
                self.player.y_vel = self.player.jump_vel * 0.8
            enemy.go_die(how, 1 if self.player.face_right else -1)

        self.check_will_fall(self.player)




    # def check_y_collisions(self):
    #     check_group = pygame.sprite.Group(self.ground_items_group, self.brick_group, self.box_group)
    #     collided_sprite = pygame.sprite.spritecollideany(self.player, check_group)
    #     if collided_sprite:
    #         self.adjust_player_y(collided_sprite)
    #
    #     enemy = pygame.sprite.spritecollideany(self.player, self.enemy_group)
    #     if enemy:
    #         self.enemy_group.remove(enemy)
    #         if enemy.name == 'koopa':
    #             self.shell_group.add(enemy)
    #         else:
    #             self.dying_group.add(enemy)
    #
    #         if self.player.y_vel < 0:
    #             how = 'bumped'
    #         else:
    #             how = 'trampled'
    #             self.player.state = 'jump'
    #             self.player.rect.bottom = enemy.rect.top
    #             self.player.y_vel = self.player.jump_vel * 0.8
    #         enemy.go_die(how)
    #
    #
    #     self.check_will_fall(self.player)



    def adjust_player_x(self, sprite):
        if self.player.rect.x < sprite.rect.x:
            self.player.rect.right = sprite.rect.left
        else:
            self.player.rect.left = sprite.rect.right
        self.player.x_vel = 0

    def adjust_player_y(self, sprite):
        # downwards
        if self.player.rect.bottom < sprite.rect.bottom:
            self.player.y_vel = 0
            self.player.rect.bottom = sprite.rect.top
            self.player.state = 'walk'
        # upwards
        else:
            self.player.y_vel = 7
            self.player.rect.top = sprite.rect.bottom
            self.player.state = 'fall'

            self.is_enemy_on(sprite)

            if sprite.name == 'box':
                if sprite.state == 'rest':
                    sprite.go_bumped()

            if sprite.name == 'brick':  # 判断精灵是否为砖块
                if self.player.big and sprite.brick_type == 0:  # 当Mario处于变大状态且砖块内无物品
                    sprite.smashed(self.dying_group)  # 击碎砖块（砖块消失）
                else:
                    sprite.go_bumped()  # 砖块被顶起（但未被击碎）

    def is_enemy_on(self, sprite):
        """检测敌人是否位于精灵上方并触发击杀逻辑"""
        sprite.rect.y -= 1  # 临时上移精灵位置1像素
        enemy = pygame.sprite.spritecollideany(sprite, self.enemy_group)

        if enemy:  # 如果检测到碰撞
            self.enemy_group.remove(enemy)  # 从敌人组移除
            self.dying_group.add(enemy)  # 加入死亡动画组
            if sprite.rect.centerx > enemy.rect.centerx:
                enemy.go_die('bumped', -1)
            else:
                enemy.go_die('bumped')


        sprite.rect.y += 1  # 恢复精灵原始位置

    def check_will_fall(self, sprite):
        sprite.rect.y += 1
        check_group = pygame.sprite.Group(self.ground_items_group, self.brick_group, self.box_group)
        collided_sprite = pygame.sprite.spritecollideany(sprite, check_group)
        if not collided_sprite and sprite.state != 'jump' and not self.is_frozen():
            sprite.state = 'fall'
        sprite.rect.y -= 1

    def update_game_window(self):
        third = self.game_window.x + self.game_window.width / 3
        if (self.player.x_vel > 0
                and self.player.rect.centerx > third
                and self.game_window.right < self.end_x):
            self.game_window.x += self.player.x_vel
            self.start_x = self.game_window.x


    # def update_player_position(self):
    #     self.player.rect.x += self.player.x_vel
    #     if self.player.rect.x < 0:
    #         self.player.rect.x = 0
    #     if self.player.rect.x > C.SCREEN_W - 16 * C.PLAYER_MULTI:
    #         self.player.rect.x = C.SCREEN_W - 16 * C.PLAYER_MULTI
    #     self.player.rect.y += self.player.y_vel

    def update_game_window(self):
        third = self.game_window.x + self.game_window.width / 3
        if self.player.x_vel > 0 and self.player.rect.centerx > third:
            self.game_window.x += self.player.x_vel

    def draw(self, surface):
        self.game_ground.blit(self.background, self.game_window, self.game_window)
        self.game_ground.blit(self.player.image, self.player.rect)
        self.powerup_group.draw(self.game_ground)
        self.brick_group.draw(self.game_ground)
        self.box_group.draw(self.game_ground)
        self.enemy_group.draw(self.game_ground)
        self.dying_group.draw(self.game_ground)
        self.shell_group.draw(self.game_ground)
        self.coin_group.draw(self.game_ground)


        surface.blit(self.game_ground, (0, 0), self.game_window)
        self.info.draw(surface)

    def check_checkpoints(self):
        checkpoint = pygame.sprite.spritecollideany(self.player, self.checkpoint_group)
        if checkpoint:
            if checkpoint.checkpoint_type == 0:  # checkpoint for enemy appearance
                self.enemy_group.add(self.enemy_group_dict[str(checkpoint.enemy_groupid)])
            checkpoint.kill()

    def check_if_go_die(self):
        if self.player.rect.y > C.SCREEN_H:  # 检测玩家Y坐标是否超出屏幕高度
            self.player.go_die()  # 触发死亡逻辑

    def update_game_info(self):
        """更新游戏状态信息"""
        if self.player.dead:  # 检测玩家死亡状态
            self.game_info['lives'] -= 1  # 生命值减1

        # 判断游戏结束条件
        if self.game_info['lives'] == 0:  # 生命值耗尽
            self.next = 'game_over'  # 跳转游戏结束场景
        else:  # 还有剩余生命
            self.next = 'load_screen'  # 跳转加载场景

