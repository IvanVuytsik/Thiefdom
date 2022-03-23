import pygame
import os, os.path
import csv
import pickle

pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
LOWER_MARGIN = 0
SIDE_MARGIN = 300
WINDOW_SIZE = (1280, 720)

screen = pygame.display.set_mode((WINDOW_SIZE[0] + SIDE_MARGIN, WINDOW_SIZE[1] + LOWER_MARGIN))
display = pygame.Surface((1280, 720))

pygame.display.set_caption('Level Editor')
FPS = 60
clock = pygame.time.Clock()
run = True

ROWS = 16
MAX_COLS = 128
TILE_SIZE = SCREEN_HEIGHT // ROWS

path, dirs, files = next(os.walk("./LevelEditor/tiles"))
file_count = len(files)
TILE_TYPES = file_count

scroll_left = False
scroll_right = False
scroll_up = False
scroll_down = False

mouse_scroll_up = False
mouse_scroll_down = False

scroll = [0, 0]
mouse_scroll = [0,0]
scroll_speed = 1
current_tile = 0

map = 0
layer = 0


bg_sky = pygame.image.load("./img/bg/bg_sky.png").convert_alpha()
bg_sky = pygame.transform.scale(bg_sky, (int(SCREEN_WIDTH) * 2, (int(SCREEN_HEIGHT) * 2)))
bg_mountains = pygame.image.load("./img/bg/1.png").convert_alpha()
bg_mountains = pygame.transform.scale(bg_mountains, (int(SCREEN_WIDTH * 2), (int(SCREEN_HEIGHT))))
bg_forest = pygame.image.load("./img/bg/0.png").convert_alpha()
bg_forest = pygame.transform.scale(bg_forest, (int(SCREEN_WIDTH * 2), (int(SCREEN_HEIGHT / 2))))

save_img = pygame.image.load("./LevelEditor/save.png").convert_alpha()
save_img = pygame.transform.scale(save_img, (40, 40))
load_img = pygame.image.load("./LevelEditor/load.png").convert_alpha()
load_img = pygame.transform.scale(load_img, (40, 40))

class WorldButton():
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        action = False
        # get mouse position
        pos = pygame.mouse.get_pos()
        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        # draw button
        surface.blit(self.image, (self.rect.x, self.rect.y +mouse_scroll[1]))
        return action

# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'./LevelEditor/tiles/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

green = (144, 201, 120)
white = (255, 255, 255)
red = (200, 25, 25)
blue = (135, 206, 250)
font = pygame.font.SysFont('Futura', 30)

# world_list
world_data = []

for row in range(ROWS):
    r = [-1] * MAX_COLS  # -1 repeated x 150
    world_data.append(r)


#create with tiles
for tile in range(0,MAX_COLS):
    world_data[ROWS-1][tile] = 0     #[ROWS-1][tile] = last row = 0 tile
#print(world_data)

def draw_text(surface, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    surface.blit(img, (x, y))

def draw_bg():
    display.fill(blue)
    width = bg_sky.get_width()
    for x in range(4):
        display.blit(bg_sky, ((x * width) - scroll[0] * 0.5, 0))
        display.blit(bg_mountains, ((x * width) - scroll[0] * 0.6, SCREEN_HEIGHT - bg_mountains.get_height()+150))
        display.blit(bg_forest, ((x * width) - scroll[0] * 0.7, SCREEN_HEIGHT - bg_forest.get_height()+100))

def draw_grid():
    for c in range(MAX_COLS + 1):
        pygame.draw.line(display, white, (c * TILE_SIZE - scroll[0], 0 - scroll[1]),
                         (c * TILE_SIZE - scroll[0], SCREEN_HEIGHT * 4 - scroll[1]))
    for c in range(ROWS + 1):
        pygame.draw.line(display, white, (0 - scroll[0], c * TILE_SIZE - scroll[1]),
                         (SCREEN_WIDTH * 14 - scroll[0], c * TILE_SIZE - scroll[1]))

def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                display.blit(img_list[tile], (x * TILE_SIZE - scroll[0], y * TILE_SIZE - scroll[1]))

def draw_surface(world, images):
    for y, row in enumerate(world):
        for x, tile in enumerate(row):
            if tile >= 0:
                display.blit(images[tile], (x * TILE_SIZE - scroll[0], y * TILE_SIZE - scroll[1]))

button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
    tile_button = WorldButton(SCREEN_WIDTH + (60 * button_col) + 30, 50 * button_row + 20, img_list[i], 0.8)
    button_list.append(tile_button)
    button_col += 1
    if button_col == 4:
        button_row += 1
        button_col = 0

constructs_button_list = []
button_col = 0
button_row = 0



while run:
    clock.tick(FPS)
    # display.fill((146,244,255))
    draw_bg()
    draw_grid()
    draw_world()

    save_button = WorldButton(1290, 680 -mouse_scroll[1], save_img, 1)
    load_button = WorldButton(1530, 680 -mouse_scroll[1], load_img, 1)

#-----------------------------------------Panel---------------------------------------
    pygame.draw.rect(screen, '#2c2d47', (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))
    # choosing tiles
    if layer == 0:
        button_count = 0
        for button_count, i in enumerate(button_list):
            if i.draw(screen):
                current_tile = button_count
            pygame.draw.rect(screen, red, button_list[current_tile].rect, 3)
            # highlight selected tile

    #--------------------------------textsrender------------------------------
    draw_text(screen, f'Map: {map}', font, (255, 225, 100), SCREEN_WIDTH + 5, SCREEN_HEIGHT - 70)
    draw_text(screen, 'W/S switch', font, (255, 225, 100), SCREEN_WIDTH + 5, SCREEN_HEIGHT - 90)
    draw_text(screen, f'Layer: {layer}', font, (255, 225, 100), SCREEN_WIDTH + 215, SCREEN_HEIGHT - 70)
    draw_text(screen, 'A/D switch', font, (255, 225, 100), SCREEN_WIDTH + 185, SCREEN_HEIGHT - 90)
    # -----------------------------Save/Load------------------------------

    if save_button.draw(screen):
        # pickle_out = open(f'./LevelEditor/Locations/map{map}_data.csv', 'wb')
        # pickle.dump(world_data, pickle_out)
        # pickle_out.close()

        with open(f'./LevelEditor/Locations/map{map}_data.csv', 'w', newline ='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            for row in world_data:
                writer.writerow(row)

    try:
        if load_button.draw(screen):
            scroll[0] = 0
            scroll[1] = 0
            with open(f'./LevelEditor/Locations/map{map}_data.csv', newline ='') as csvfile:
                reader = csv.reader(csvfile, delimiter = ',')
                for row in world_data:
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)

            #world_data = []
            # pickle_in = open(f'./LevelEditor/Locations/map{map}_data.csv', 'rb')
            # world_data = pickle.load(pickle_in)
            # print(world_data)

    except:
        print("No such files!")


    if scroll_left == True and scroll[0] > 0:
        scroll[0] -= 5 * scroll_speed
    if scroll_right == True and scroll[0] < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH:
        scroll[0] += 5 * scroll_speed
    if scroll_up == True and scroll[1] > 0:
        scroll[1] -= 5 * scroll_speed
    if scroll_down == True and scroll[1] < (ROWS * TILE_SIZE) - SCREEN_HEIGHT:
        scroll[1] += 5 * scroll_speed

    # ------------------newtiles-------------------
    pos = pygame.mouse.get_pos()
    x = (pos[0] + scroll[0]) // TILE_SIZE
    y = (pos[1] + scroll[1]) // TILE_SIZE

    # check that coordinates are within the tile grid
    try:
        if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
            if layer == 0:
                if pygame.mouse.get_pressed()[0] == 1:
                    if world_data[y][x] != current_tile:
                        world_data[y][x] = current_tile
                if pygame.mouse.get_pressed()[2] == 1:
                    world_data[y][x] = -1

    except:
        print('No such files!')
    # print(x)
    # print(y)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                map += 1
            if event.key == pygame.K_s and map > 0:
                map -= 1
            if event.key == pygame.K_d:
                layer += 1
            if event.key == pygame.K_a and layer > 0:
                layer -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_UP:
                scroll_up = True
            if event.key == pygame.K_DOWN:
                scroll_down = True
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 5

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_UP:
                scroll_up = False
            if event.key == pygame.K_DOWN:
                scroll_down = False
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 and mouse_scroll[1] < 0:
                mouse_scroll[1] +=15*scroll_speed
            if event.button == 5:
                mouse_scroll[1] -=15*scroll_speed

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    pygame.display.update()
    # clock.tick(60)

pygame.quit()
