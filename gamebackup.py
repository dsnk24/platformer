import pygame, sys
from pygame.locals import *
import os
import random

clock = pygame.time.Clock()

from pygame.locals import *
pygame.init()

pygame.display.set_caption('not sure')

WINDOW_SIZE = (600,400)
CHUNK_SIZE = 8

screen = pygame.display.set_mode(WINDOW_SIZE,0,32)
display = pygame.Surface((300,200))
font = pygame.font.SysFont(None, 30)

class Player:
	def __init__(self, moving_right, moving_left, vertical_momentum, height, width, player_movement):
		self.moving_right = moving_right #false
		self.moving_left = moving_left #false
		self.vertical_momentum = vertical_momentum #0
		self.air_timer = 0
		self.grass_sound_timer = 0
		self.true_cam_movement = [0,0]
		self.player_action = 'idle'
		self.player_frame = 0
		self.player_img_flip = False
		self.player_rect = pygame.Rect(100,100,5,13)
		self.player_height = height
		self.player_width = width
		self.player_movement = player_movement #[0,0]


def render_text(text, font, color, surface, x, y):
	text_obj = font.render(text, 1, color)
	text_rect = text_obj.get_rect()
	text_rect.topleft = (x, y)
	surface.blit(text_obj, text_rect)

def gen_chunks(x,y):
	chunk_data = []

	for y_pos in range(CHUNK_SIZE):
		for x_pos in range(CHUNK_SIZE):
			target_x = x * CHUNK_SIZE + x_pos
			target_y = y * CHUNK_SIZE + y_pos

			tile_type = 0 # air

			if target_y > 10:
				tile_type = 1 # dirt
			elif target_y == 10:
				tile_type = 2 # grass
			elif target_y == 9:
				if random.randint(1, 5) == 1:
					tile_type = 3 # grass plant thingy
			if tile_type != 0:
				chunk_data.append([[target_x, target_y], tile_type])

	return chunk_data

global animation_frames
animation_frames = {}

def load_animation(path, frame_durations):
	
	global animation_frames
	
	animation_name = path.split('/')[-1]
	
	animation_frame_data = []
	
	n = 0
	
	for frame in frame_durations:
		
		animation_frame_id = animation_name + '_' + str(n)
		img_location = path + '/' + animation_frame_id + '.png'
		
		animation_img = pygame.image.load(img_location).convert()
		animation_img.set_colorkey((255,255,255))
		
		animation_frames[animation_frame_id] = animation_img.copy()

		for i in range(frame):
			animation_frame_data.append(animation_frame_id)

		n += 1

	return animation_frame_data

def action_change(action, frame, new_action):
	if action != new_action:
		action = new_action
		frame = 0

	return action, frame

animation_db = {}

animation_db['run'] = load_animation('player images/run', [7,7])
animation_db['idle'] = load_animation('player images/idle', [7,7,40])

# chunks dict
game_map = {}

grass_img = pygame.image.load('textures/grass.png')
dirt_img = pygame.image.load('textures/dirt.png')
grass_img_2 = pygame.image.load('textures/plant.png').convert()
grass_img_2.set_colorkey((255,255,255))

font_img = pygame.image.load('textures/font.png')

tile_index = {1:dirt_img, 2:grass_img, 3:grass_img_2}

# pygame mixer settings
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

# sound for jumping
jump_sound = pygame.mixer.Sound('sfx/jump.wav')
jump_sound.set_volume(0.2)

#sounds for moving on grass
grass_sounds = [pygame.mixer.Sound('sfx/grass_0.wav'), pygame.mixer.Sound('sfx/grass_1.wav')]
grass_sounds[0].set_volume(0.2)
grass_sounds[1].set_volume(0.2)

# music
pygame.mixer.music.load('sfx/music.wav')
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1)

# player's rect

# parallax objects
background_objects = [[0.25, [120,10,70,400]], [0.25, [280,30,40,400]], [0.5, [30,40,40,400]], [0.5, [130,90,100,400]], [0.5, [300,80,120,400]]]

def collision_test(rect,tiles): # collisions function
	hit_list = []
	
	for tile in tiles:
		if rect.colliderect(tile):
			hit_list.append(tile)
	
	return hit_list

def move(rect,movement,tiles): # movement function
	
	collision_types = {'top':False,'bottom':False,'right':False,'left':False}
	
	rect.x += movement[0]
	hit_list = collision_test(rect,tiles)
	for tile in hit_list:
		if movement[0] > 0:
			rect.right = tile.left
			collision_types['right'] = True
		
		elif movement[0] < 0:
			rect.left = tile.right
			collision_types['left'] = True
	
	rect.y += movement[1]
	hit_list = collision_test(rect,tiles)
	for tile in hit_list:
		if movement[1] > 0:
			rect.bottom = tile.top
			collision_types['bottom'] = True
		
		elif movement[1] < 0:
			rect.top = tile.bottom
			collision_types['top'] = True
	
	return rect, collision_types

player_char = Player(False, False, 0, 13, 5, [0,0])

while True: # game loop
	
	display.fill((146,244,255)) # filling screen with blue so images dont leave trails

	if player_char.grass_sound_timer > 0:
		player_char.grass_sound_timer -= 1

	player_char.true_cam_movement[0] += (player_char.player_rect.x-player_char.true_cam_movement[0]-152)/20
	player_char.true_cam_movement[1] += (player_char.player_rect.y-player_char.true_cam_movement[1]-106)/20

	cam_movement = player_char.true_cam_movement.copy()
	cam_movement[0] = int(cam_movement[0])
	cam_movement[1] = int(cam_movement[1])

	pygame.draw.rect(display, (7,80,75), pygame.Rect(0,120,300,80))

	for background_object in background_objects*2: # iterating through all parallax obj
		
		obj_rect = pygame.Rect(background_object[1][0]-cam_movement[0]*background_object[0],background_object[1][1]-cam_movement[1]*background_object[0],background_object[1][2],background_object[1][3])

		if background_object[0] == 0.5:
			pygame.draw.rect(display, (14,222,150), obj_rect)
		else:
			pygame.draw.rect(display, (9,91,85), obj_rect)

	tile_rects = [] # tile rendering

	for y in range(3):
		for x in range(4):
			target_x = x - 1 + int(round(cam_movement[0]/(CHUNK_SIZE*16)))
			target_y = y - 1 + int(round(cam_movement[1]/(CHUNK_SIZE*16)))

			target_chunk = str(target_x) + ';' + str(target_y)

			if target_chunk not in game_map:
				game_map[target_chunk] = gen_chunks(target_x, target_y)

			for tile in game_map[target_chunk]:
				display.blit(tile_index[tile[1]], (tile[0][0]*16-cam_movement[0], tile[0][1]*16-cam_movement[1]))

				if tile[1] in [1, 2]:
					tile_rects.append(pygame.Rect(tile[0][0]*16, tile[0][1]*16, 16, 16))

	if player_char.moving_right == True:
		player_char.player_movement[0] += 2
	
	if player_char.moving_left == True:
		player_char.player_movement[0] -= 2
	
	player_char.player_movement[1] += player_char.vertical_momentum
	player_char.vertical_momentum += 0.2
	
	if player_char.vertical_momentum > 3:
		player_char.vertical_momentum = 3

	if player_char.player_movement[0] > 0:
		player_char.player_action, player_char.player_frame = action_change(player_char.player_action, player_char.player_frame, 'run')
		player_char.player_img_flip = False
	if player_char.player_movement[0] == 0:
		player_char.player_action, player_char.player_frame = action_change(player_char.player_action, player_char.player_frame, 'idle')
	if player_char.player_movement[0] < 0:
		player_char.player_action, player_char.player_frame = action_change(player_char.player_action, player_char.player_frame, 'run')
		player_char.player_img_flip = True

	player_char.player_rect,collisions = move(player_char.player_rect,player_char.player_movement,tile_rects)

	if collisions['bottom'] == True:
		player_char.air_timer = 0
		player_char.vertical_momentum = 0

		if player_char.player_movement[0] != 0:
			if player_char.grass_sound_timer == 0:
				player_char.grass_sound_timer = 30
				sound = random.choice(grass_sounds)
				sound.play()
	else:
		player_char.air_timer += 1

	player_char.player_frame += 1
	if player_char.player_frame >= len(animation_db[player_char.player_action]):
		player_char.player_frame = 0

	player_char.player_img_id = animation_db[player_char.player_action][player_char.player_frame]
	player_char.player_img = animation_frames[player_char.player_img_id]
	display.blit(pygame.transform.flip(player_char.player_img, player_char.player_img_flip, False),(player_char.player_rect.x-cam_movement[0],player_char.player_rect.y-cam_movement[1]))

	for event in pygame.event.get():
		if event.type == QUIT:
			pygame.quit()
			sys.exit()
		
		if event.type == KEYDOWN:
			if event.key == K_d:
				player_char.moving_right = True
			
			if event.key == K_a:
				player_char.moving_left = True
			
			if event.key == K_w:
				if player_char.air_timer < 6:
					jump_sound.play()
					player_char.vertical_momentum = -5
			if event.key == K_ESCAPE:
				pygame.quit()
				sys.exit()
		if event.type == KEYUP:
			if event.key == K_d:
				player_char.moving_right = False
			
			if event.key == K_a:
				player_char.moving_left = False
		
	screen.blit(pygame.transform.scale(display,WINDOW_SIZE),(0,0))
	pygame.display.update()
	clock.tick(60)
