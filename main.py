import pygame
import os
import random
import csv
import pickle
from pygame import mixer
from button import Button

pygame.init()
mixer.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
ROWS = 16
COLS = 128
TILE_SIZE = SCREEN_HEIGHT // ROWS
SCROLL_LIMIT = 400
MAX_LEVELS = 2

level = 1
start_game = False
start_intro = False

screen_scroll = 0
bg_scroll = 0

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Thiefdom')
clock = pygame.time.Clock()

#player vars
moving_left = False
moving_right = False
shoot = False
attack = False

bomb = False
thrown = False

#images
arrow_img = pygame.image.load('img/arrow.png').convert_alpha()
bomb_base = pygame.image.load('img/bomb.png').convert_alpha()
bomb_img = pygame.transform.scale(bomb_base, (20,22))


#backgroung_img
bg_sky = pygame.image.load("./img/bg/bg_sky.png").convert_alpha()
bg_sky = pygame.transform.scale(bg_sky, (int(SCREEN_WIDTH) * 2, (int(SCREEN_HEIGHT) * 2)))

#background_img
path, dirs, bgs = next(os.walk("./img/bg"))
TILE_TYPES = len(bgs)
bg_list = []
for x in range(TILE_TYPES-1):
    bg = pygame.image.load(f'./img/bg/{x}.png').convert_alpha()
    bg = pygame.transform.scale(bg, (int(SCREEN_WIDTH) * 2, (int(SCREEN_HEIGHT) // 2)))
    bg_list.append(bg)

# menu
start_img = pygame.image.load('./img/menu/NewGame.png').convert_alpha()
exit_img = pygame.image.load('./img/menu/Exit.png').convert_alpha()
load_img = pygame.image.load('./img/menu/LoadGame.png').convert_alpha()

#tiles_img
path, dirs, tiles = next(os.walk("./LevelEditor/tiles"))
TILE_TYPES = len(tiles)
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'./LevelEditor/tiles/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)


#sounds
def launch_music():
    pygame.mixer.music.load('./sounds/forest.mp3')
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1, 0.0, 5000)

jump_fx = pygame.mixer.Sound('./sounds/jump.wav')
jump_fx.set_volume(0.5)
attack_fx = pygame.mixer.Sound('./sounds/attack.wav')
attack_fx.set_volume(0.5)
arrow_fx = pygame.mixer.Sound('./sounds/arrow.wav')
arrow_fx.set_volume(0.5)
bomb_fx = pygame.mixer.Sound('./sounds/bomb.wav')
bomb_fx.set_volume(0.5)
coins_fx = pygame.mixer.Sound('./sounds/coins.wav')
coins_fx.set_volume(0.5)

#game vars
GRAVITY = 0.75

#colors
BG = (140, 200, 120)
MENU = (90, 60, 0)
RED = (255, 0, 0)

font = pygame.font.SysFont('Futura', 30)
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    width = bg_sky.get_width()
    for i in range(5):
        screen.blit(bg_sky, ((i*width) - bg_scroll * 0.5, 0))
        screen.blit(bg_list[1], ((i*width) - bg_scroll * 0.6, SCREEN_HEIGHT - bg_list[1].get_height() - 100))
        screen.blit(bg_list[0], ((i*width) - bg_scroll * 0.7, SCREEN_HEIGHT - bg_list[0].get_height()))
        screen.blit(bg_list[2], ((i*width) - bg_scroll * 0.8, SCREEN_HEIGHT - bg_list[2].get_height() + 100))

def reset_map():
    enemy_group.empty()
    arrow_group.empty()
    bomb_group.empty()
    item_group.empty()
    water_group.empty()
    decoration_group.empty()
    exit_group.empty()
    summon_group.empty()

    # empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS  # -1 repeated x 150
        data.append(r)
    return data

class Character(pygame.sprite.Sprite):
    def __init__(self, type, x, y, scale, speed, ammo, bombs, health, hostile):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.hostile = hostile
        self.type = type
        self.scale = scale
        self.speed = speed
        self.const_speed = self.speed
        self.ammo = ammo
        self.start_ammo = self.ammo
        self.bombs = bombs
        self.start_bombs = self.bombs
        self.shoot_cooldown = 0
        self.attack_cooldown = 0
        self.throw_cooldown = 0
        self.summon_cooldown = 0
        self.health = health
        self.max_health = self.health
        self.direction = 1
        self.flip = False
        self.jump = False
        self.jump_height = 0
        self.in_air = True
        self.sneaking = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        self.block_movement = False
        self.treasure = 0
        self.active = False

        #-------ai----------
        self.move_counter = 0
        self.patrol_distance = 0
        self.idle = False
        self.idle_counter = 0
        self.vision = pygame.Rect(0, 0, 250, 20)
        self.jump_counter = 0

        # load img
        if self.type == "thief":
           animation_types = ['idle', 'walk', 'attack', 'dead',  'shoot', 'sneak', 'sneakwalk', 'jump', 'shoot_low']
        elif self.type == "shadow":
             animation_types = ['idle', 'walk', 'attack', 'dead', 'shoot']
        else:
            animation_types = ['idle', 'walk', 'attack', 'dead']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'img/{self.type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(124*scale), int(124*scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect[2] = int(self.rect[2] // 2)
        self.rect[3] = int(self.rect[3] * 0.8)

        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        #cooldown
        if self.shoot_cooldown > 0:
           self.shoot_cooldown -= 1
        if self.attack_cooldown > 0:
           self.attack_cooldown -= 1
        if self.throw_cooldown > 0:
           self.throw_cooldown -= 1
        if self.summon_cooldown > 0:
           self.summon_cooldown -= 1

        #print(self.rect)

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx = 0
        dy = 0

        if self.block_movement == False:
            if moving_left:
                dx = -self.speed
                self.flip = True
                self.direction = -1
            if moving_right:
                dx = self.speed
                self.flip = False
                self.direction = 1
            if moving_left and self.sneaking == True:
                dx = -self.speed * 0.5
                self.flip = True
                self.direction = -1
            if moving_right and self.sneaking == True:
                dx = self.speed * 0.5
                self.flip = False
                self.direction = 1

        #jump
        if self.jump == True and self.in_air == False:
           self.jump_height = -13
           self.jump = False
           self.in_air = True

        # gravity
        self.jump_height += GRAVITY
        # if self.jump_height > 9:
        #    self.jump_height
        dy += self.jump_height

        # collisions
        for tile in world.obstacle_list: #(img, rect)
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect[2], self.rect[3]):
               dx = 0
               if self.type != 'thief':
                   self.direction *= -1
                   self.move_counter = 0

            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect[2], self.rect[3]):
                if self.jump_height < 0:
                    self.jump_height = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.jump_height >= 0:
                    self.jump_height = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # exit
        map_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            map_complete = True
        # fallinga
        if self.rect.bottom > SCREEN_HEIGHT:
           self.health = 0
        # map edges
        if self.type == 'thief':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #------------------update rect with dx/dy-----------
        self.rect.x += dx
        self.rect.y += dy

        #sroll_update
        if self.type == 'thief':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_LIMIT and bg_scroll < (world.map_length * TILE_SIZE) - SCREEN_WIDTH)\
                    or (self.rect.left < SCROLL_LIMIT//2 and bg_scroll > abs(dx)): #change left threshold
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, map_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
           self.shoot_cooldown = 40
           arrow_fx.play()
           if self.rect.top > player.rect.top and self.hostile:
               arrow = Projectile(self.rect.centerx + (0.8 * self.rect.size[0] * self.direction), self.rect.centery - 20, self.direction, self.flip, 'upper')
           elif player.sneaking and (self.hostile or self.type == 'thief'):
               arrow = Projectile(self.rect.centerx + (0.8 * self.rect.size[0] * self.direction), self.rect.centery + 20, self.direction, self.flip, 'lower')
           else:
               arrow = Projectile(self.rect.centerx + (0.8 * self.rect.size[0] * self.direction), self.rect.centery, self.direction, self.flip, 'middle')

           if self.hostile == False:
              arrow.friendly_fire = True

           arrow_group.add(arrow)
           if self.type == 'thief':
              self.ammo -= 1

    #-------------------AI-------------------
    def ai_jump(self):
        self.jump_counter += 1
        if self.jump_counter == 100:
            if self.direction == 1:
                self.rect.x -= 20
            else:
                self.rect.x += 20
            self.jump_height = -16
            self.jump_counter = 0
        self.jump_height += GRAVITY

    #-------------------AI-------------------
    def ai(self):
        if self.alive and player.alive:
            #draw vision
            #pygame.draw.rect(screen, (255,0,0), self.vision, 2)
            if self.idle == False and random.randint(1, 200) == 1:
                self.idle = True
                self.idle_counter = 50
                self.update_action(0)
            #--------------patrolling--------------
            if self.type == 'crossbowman':
                self.patrol_distance = TILE_SIZE//2
            elif self.type == 'swordsman':
                self.patrol_distance = TILE_SIZE
            #------------vision/move----------------
            if self.vision.colliderect(player):
                #-------------------------------------
                if self.hostile:
                    if self.type == 'crossbowman':
                        self.update_action(2)
                        self.shoot()
                        self.idle = True
                    elif self.type == 'swordsman' and self.rect.colliderect(player):
                        self.attack()
                        self.idle = True
                if player.rect.right - 10 < self.rect.left:
                    ai_moving_left = True
                    ai_moving_right = False
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)
                if player.rect.left + 10 > self.rect.right:
                    ai_moving_right = True
                    ai_moving_left = False
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)
                #--------------jump-------------------
                for tile in world.obstacle_list:
                    if tile[1].right == self.rect.left or tile[1].left == self.rect.right:
                        self.ai_jump()
            #--------------------------------------------------------------------------
            for ally in summon_group:
                if ally.alive and self.vision.colliderect(ally):
                    #-------------------------------------
                    if self.hostile:
                        if self.type == 'crossbowman':
                            self.update_action(2)
                            self.shoot()
                            self.idle = True
                        elif self.type == 'swordsman' and self.rect.colliderect(ally):
                            self.attack()
                            self.idle = True
                    if ally.rect.right - 10 < self.rect.left:
                        ai_moving_left = True
                        ai_moving_right = False
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)
                    if ally.rect.left + 10 > self.rect.right:
                        ai_moving_right = True
                        ai_moving_left = False
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)
                    #--------------jump-------------------
                    for tile in world.obstacle_list:
                        if tile[1].right == self.rect.left or tile[1].left == self.rect.right:
                            self.ai_jump()
            #------------------------------------
            else:
                if self.idle == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)

                    self.move_counter += 1
                    #----------------vision-------------------
                    self.vision.center = (self.rect.centerx + 150 * self.direction, self.rect.centery)
                    #pygame.draw.rect(screen, (255,255,255), self.vision)

                    if self.move_counter > self.patrol_distance:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idle_counter -= 1
                    if self.idle_counter <= 0:
                       self.idle = False
                #--------------------------------------------------------------
        #---------scroll-----------
        self.rect.x += screen_scroll

    #------------------------------------------------------------------------------
    def ally_ai(self):
        #------------------------------------
        if self.alive and player.alive:
            #pygame.draw.rect(screen, (255,0,0), self.vision, 2)
            if self.idle == False and random.randint(1, 200) == 1:
                self.idle = True
                self.idle_counter = 50
                self.update_action(0)

            #--------------patrolling--------------
            if self.hostile == False:
                self.patrol_distance = TILE_SIZE * 2
                self.health -= 0.1
            #------------vision/move----------------
            for enemy in enemy_group:
                if enemy.alive and self.vision.colliderect(enemy):
                    #------------------------------------
                    if self.hostile == False:
                        if not self.rect.colliderect(enemy):
                            self.update_action(4)
                            self.shoot()
                            self.idle = True
                        elif self.rect.colliderect(enemy):
                             self.attack()
                             self.idle = True

                    if enemy.rect.right - 10 < self.rect.left:
                        ai_moving_left = True
                        ai_moving_right = False
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)
                    if enemy.rect.left + 10 > self.rect.right:
                        ai_moving_right = True
                        ai_moving_left = False
                        self.move(ai_moving_left, ai_moving_right)
                        self.update_action(1)
                    #--------------jump-------------------
                    for tile in world.obstacle_list:
                        if tile[1].right == self.rect.left or tile[1].left == self.rect.right:
                            self.ai_jump()
            #------------------------------------
            else:
                if self.idle == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)

                    self.move_counter += 1
                    #----------------vision-------------------
                    self.vision.center = (self.rect.centerx + 150 * self.direction, self.rect.centery)
                    #pygame.draw.rect(screen, (255,255,255), self.vision)

                    if self.move_counter > self.patrol_distance:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idle_counter -= 1
                    if self.idle_counter <= 0:
                        self.idle = False
        #---------scroll-----------
        self.rect.x += screen_scroll

    #--------------------------------------
    def attack(self):
        if self.attack_cooldown == 0:
           self.attack_cooldown = 40

           if self.type == 'thief':
               for enemy in enemy_group:
                   if self.rect.colliderect(enemy):
                      enemy.health -= 35

           elif self.rect.colliderect(player):
               player.health -= 25

           elif self.hostile:
               for ally in summon_group:
                   if self.rect.colliderect(ally):
                       ally.health -= 25

           elif self.hostile == False:
               for enemy in enemy_group:
                   if self.rect.colliderect(enemy):
                       enemy.health -= 25

           attack_fx.play()
           self.update_action(2)

    def summon(self):
        if self.summon_cooldown == 0:
           self.summon_cooldown = 300
           for x in range(2):
               ally = Character('shadow', player.rect.x, player.rect.y, 0.8, 3, 36, 2, 120, False)
               summon_group.add(ally)

    def update_animation(self):
        if self.type == "thief":
            if self.action == 0: #idle
                ANIMATION_COOLDOWN = 600
            elif self.action == 1: #walk
                ANIMATION_COOLDOWN = 150
            elif self.action == 2: #attack
                ANIMATION_COOLDOWN = 200
            elif self.action == 3: #dead
                ANIMATION_COOLDOWN = 200
            elif self.action == 4: #shoot
                ANIMATION_COOLDOWN = 100
            elif self.action == 5: #sneakwalk
                ANIMATION_COOLDOWN = 250
            elif self.action == 6: #sneak
                ANIMATION_COOLDOWN = 300
            elif self.action == 7: #jump
                ANIMATION_COOLDOWN = 100
            else:
                ANIMATION_COOLDOWN = 300
        else:
            if self.action == 0: #idle
                ANIMATION_COOLDOWN = 600
            elif self.action == 1: #walk
                ANIMATION_COOLDOWN = 150
            elif self.action == 2: #attack
                ANIMATION_COOLDOWN = 200
            elif self.action == 3: #dead
                ANIMATION_COOLDOWN = 200
            elif self.action == 4: #shoot
                ANIMATION_COOLDOWN = 200
            else:
                ANIMATION_COOLDOWN = 300

        # changing frames
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
           self.update_time = pygame.time.get_ticks()
           self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
           if self.action == 3:
              self.frame_index = len(self.animation_list[self.action]) - 1
           else:
              self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
           self.action = new_action
           self.frame_index = 0
           self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
           self.health = 0
           self.speed = 0
           self.alive = False
           self.block_movement = True
           self.update_action(3)
           if self.type == 'shadow':
              self.kill()


    def draw(self):
        #pygame.draw.rect(screen, (255,0,0), self.rect, 2)
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x-(28*self.scale), self.rect.y-(26*self.scale)))

        #healthbar
        healthbar = HealthBar(self.rect.x, self.rect.y - 20, self.rect.width, 10, self.health, self.max_health)
        if self.alive == True:
           healthbar.draw(self.health)

#------------------------------------------------------------------
#items
heath_item_img = pygame.image.load('img/items/health.png').convert_alpha()
fireflask_item_img = pygame.image.load('img/items/fireflask.png').convert_alpha()
arrows_item_img = pygame.image.load('img/items/arrows.png').convert_alpha()
coins_item_img = pygame.image.load('img/items/coins.png').convert_alpha()

item_box = {
    'Health': heath_item_img,
    'Arrows': arrows_item_img,
    'FireFlask': fireflask_item_img,
    'Coins': coins_item_img
}

#------------------------------------------------------------------------
class Item(pygame.sprite.Sprite):
    def __init__(self, type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.type = type
        self.image = pygame.transform.scale(item_box[self.type], (48, 48))
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #pygame.draw.rect(screen, (255,0,0), self.rect, 4)
        self.rect.x += screen_scroll

        if pygame.sprite.collide_rect(self, player) and player.sneaking == True:
            if self.type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                   player.health = player.max_health
            elif self.type == 'Arrows':
                player.ammo += 6
            elif self.type == 'FireFlask':
                player.bombs += 3
            elif self.type == 'Coins':
                coins_fx.play()
                player.treasure += 50


            self.kill()
#------------------------------------------------------------------------
class HealthBar():
    def __init__(self, x, y, length, width, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
        self.length = length
        self.width = width

    def draw(self, health):
        self.health = health
        ratio = self.health/self.max_health
        pygame.draw.rect(screen, (225, 225, 0), (self.x - 2, self.y - 2, self.length + 4, self.width + 4))
        pygame.draw.rect(screen, (250, 0, 0), (self.x, self.y, self.length, self.width))
        pygame.draw.rect(screen, (0, 250, 0), (self.x, self.y, self.length*ratio, self.width))

#-------------------------------------------------------------------
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, flip, elevation):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 8
        self.flip = flip
        self.image = arrow_img
        self.image = pygame.transform.flip(self.image, flip, False)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.friendly_fire = False
        self.elevation = elevation

    def update(self):
        self.rect.x += (self.direction * self.speed) + screen_scroll
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # collision_tiles
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # collision
        if pygame.sprite.spritecollide(player, arrow_group, False):
           if player.alive:
               if player.sneaking and self.elevation == 'lower':
                    player.health -= 25
                    self.kill()
               else:
                    player.health -= 25
                    self.kill()

        # collision npc
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, arrow_group, False) and self.friendly_fire:
                if enemy.alive:
                    enemy.health -= 50
                    self.kill()

        for ally in summon_group:
            if pygame.sprite.spritecollide(ally, arrow_group, False):
                if ally.alive:
                    ally.health -= 50
                    self.kill()
#-------------------------------------------------------------------
class Throwable(pygame.sprite.Sprite):
    def __init__(self, x, y, img, direction):
        pygame.sprite.Sprite.__init__(self)
        self.fuze = 100
        self.vel_y = -12
        self.speed = 8
        self.image = pygame.transform.scale(img, (20, 22))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y
        #pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

        #collision_tile
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y + dy, self.rect[2], self.rect[3]):
               self.direction *= -1
               dx = self.direction * self.speed
            # collisions
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect[2], self.rect[3]):
                self.speed = 0
                if self.vel_y < 0: # thrown up
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # if self.rect.bottom + dy > 600:
        #     dy = 600 - self.rect.bottom
        #     self.speed = 0

        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        self.fuze -= 1
        if self.fuze <= 0:
            self.kill()
            bomb_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y)
            explosion.rect.bottom = self.rect.y + 22
            expl_group.add(explosion)
            # collateral damage
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE*3 and \
               abs(self.rect.centery - player.rect.centery) < TILE_SIZE*3:
                    player.health -= 75
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE*3 and \
                   abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE*3:
                   enemy.health -= 100
            for ally in summon_group:
                if abs(self.rect.centerx - ally.rect.centerx) < TILE_SIZE*3 and \
                   abs(self.rect.centery - ally.rect.centery) < TILE_SIZE*3:
                   ally.health -= 100

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(len(os.listdir(f'img/fire'))):
            img = pygame.image.load(f'img/fire/{i}.png').convert_alpha()
            img = pygame.transform.scale(img, (64, 108))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()

        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        self.rect.x += screen_scroll
        #animation
        SPEED = 5
        self.counter += 1
        if self.counter >= SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]
        #pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.map_length = len(data[0]) # cols
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    # collisions / tiles
                    if tile >= 0 and tile <= 1:
                        self.obstacle_list.append(tile_data)
                    elif tile == 2 or tile == 3: #water
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)

                    elif tile == 4: #create thief
                        player = Character('thief', x * TILE_SIZE, y * TILE_SIZE, 0.8, 5, 12, 2, 100, False)
                    elif tile == 5 or tile == 6:
                        enemy_type = {'crossbowman': 100, 'swordsman': 120}
                        if tile == 5: type = list(enemy_type.keys())[1]
                        elif tile == 6: type = list(enemy_type.keys())[0]
                        #type = random.choice(list(enemy_type.keys()))
                        #(list(enemy_type.items())[0][1][1])
                        enemy = Character(type, x * TILE_SIZE, y * TILE_SIZE, 0.8, 3, 24, 0, int(enemy_type[type]), True)
                        enemy_group.add(enemy)
                    elif tile == 7:
                        item = Item('Arrows', x * TILE_SIZE, y * TILE_SIZE)
                        item_group.add(item)
                    elif tile == 8:
                        item = Item('FireFlask', x * TILE_SIZE, y * TILE_SIZE)
                        item_group.add(item)
                    elif tile == 9:
                        item = Item('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_group.add(item)
                    elif tile == 15:
                        item = Item('Coins', x * TILE_SIZE, y * TILE_SIZE)
                        item_group.add(item)

                    elif tile >= 10 and tile <= 13:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 14:
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player

    def draw(self):
            for tile in self.obstacle_list:
                tile[1][0] += screen_scroll
                screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.direction == 2:
           pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete

death_fade = ScreenFade(2, MENU, 5)
start_fade = ScreenFade(1, MENU, 5)

#menu buttons
start_btn = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT  // 2 - 100, start_img, 1)
load_btn = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, load_img, 1)
exit_btn = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, exit_img, 1)


#--------
arrow_group = pygame.sprite.Group()
bomb_group = pygame.sprite.Group()
expl_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
summon_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()


# enemy_type = {'crossbowman': 100, 'swordsman': 120}
# for i in range(3):
#     type = random.choice(list(enemy_type.keys()))
#     enemy = Character(type, random.randint(100,600),550, 0.8, 3, 24, 0, int(enemy_type[type]))
#     enemy_group.add(enemy)
    #print(enemy.type, enemy.health)

#print(list(enemy_type.items())[0][1][1])
#[v2 for v1 in dictTest.values() for v2 in v1]


#-----------loadmap----------
world_data = []
for row in range(ROWS):
    r = [-1] * COLS  # -1 repeated x 150
    world_data.append(r)
#-----------------------
with open(f'./LevelEditor/Locations/map{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
player = world.process_data(world_data)

#print(world_data)
#--------load_data alternative----------
# reader = open(f'./LevelEditor/Locations/map{level}_data.csv', 'rb')
# world_data = pickle.load(reader)

run = True
while run:
    clock.tick(FPS)

    if start_game == False:
       screen.fill(MENU)

       if start_btn.draw(screen):
          start_game = True
          start_intro = True
          launch_music()
       if exit_btn.draw(screen):
          run = False
    else:
        draw_bg()
        # draw world map
        world.draw()
        #----------------


        draw_text(f'Arrows:  ', font, (255,255,255), 10, 10)
        for x in range(player.ammo):
            screen.blit(arrow_img, (100 + (x * 10), 20))
        draw_text(f'Bombs:  ', font, (255,255,255), 10, 40)
        for x in range(player.bombs):
            screen.blit(bomb_img, (100 + (x * 20), 40))

        draw_text(f'Treasure: {player.treasure}', font, (255,255,255), 10, 80)
        draw_text('LSHIFT: Attack; SPACE: Shoot; LCTRL: Throw; C: Summon', font, (255,255,255), 10, 120)

        player.update()
        player.draw()


        for enemy in enemy_group:
            if moving_left or moving_right or player.active == True:
                enemy.ai()
            enemy.update()
            enemy.draw()
        for ally in summon_group:
            if moving_left or moving_right or player.active == True:
                ally.ally_ai()
            ally.update()
            ally.draw()



        # update groups
        arrow_group.update()
        arrow_group.draw(screen)
        #---------------------
        bomb_group.update()
        bomb_group.draw(screen)
        #---------------------
        expl_group.update()
        expl_group.draw(screen)
        #---------------------
        item_group.update()
        item_group.draw(screen)
        #---------------------
        water_group.update()
        water_group.draw(screen)
        #---------------------
        exit_group.update()
        exit_group.draw(screen)
        #---------------------
        decoration_group.update()
        decoration_group.draw(screen)

        # intro
        if start_intro:
            if start_fade.fade():
                start_intro = False
                start_fade.fade_counter = 0

        #actions
        if player.alive:
            if shoot and player.sneaking == False:
               player.shoot()
               player.active = True
               player.update_action(4)
            elif shoot and player.sneaking:
                player.shoot()
                player.active = True
                player.update_action(8)
            elif attack:
                player.active = True
                player.attack()
            elif bomb and thrown == False and player.bombs > 0 and player.throw_cooldown <= 0:
                firebomb = Throwable(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                           player.rect.top + 30, bomb_img, player.direction)
                bomb_group.add(firebomb)
                player.throw_cooldown = 100
                player.bombs -= 1
                thrown = True

            elif player.in_air:
                player.update_action(7)
            elif player.sneaking and moving_left or player.sneaking and moving_right:
                player.update_action(6)
            elif player.sneaking:
                player.update_action(5)
                #print(player.sneaking)
            elif moving_left or moving_right:
                player.update_action(1)
            else:
                player.update_action(0)
                player.active = False
            # screen scrolling and level change
            screen_scroll, map_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #-----------------------------map_completion-----------------------
            if map_complete:
               start_intro = True
               try:
                   level += 1
                   bg_scroll = 0
                   world_data = reset_map()
                   if level <= MAX_LEVELS:
                       with open(f'./LevelEditor/Locations/map{level}_data.csv', newline='') as csvfile:
                           reader = csv.reader(csvfile, delimiter=',')
                           for x, row in enumerate(reader):
                               for y, tile in enumerate(row):
                                   world_data[x][y] = int(tile)
                       world = World()
                       player = world.process_data(world_data)
               except:
                     print('There are no other levels')

        else: #-------------------reset logic----------------
            screen_scroll = 0
            if death_fade.fade():
                if load_btn.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_map()
                    with open(f'./LevelEditor/Locations/map{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)

                    world = World()
                    player = world.process_data(world_data)
    #-----------------------controls---------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        #controls
        if event.type == pygame.KEYDOWN and player.alive == True:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE and player.ammo > 0:
                shoot = True
            if event.key == pygame.K_LSHIFT:
                attack = True
                player.block_movement = True
            if event.key == pygame.K_LCTRL:
                bomb = True
            if event.key == pygame.K_w:
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_s:
                player.sneaking = True
            if event.key == pygame.K_c:
                player.summon()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_s:
                player.sneaking = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_LSHIFT:
                attack = False
                player.block_movement = False
            if event.key == pygame.K_LCTRL:
                bomb = False
                thrown = False



            # misc controls
            if event.key == pygame.K_ESCAPE:
                run = False

    pygame.display.update()

pygame.quit()

