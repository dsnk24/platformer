import pygame, sys
import random
import os

clock = pygame.time.Clock()

from pygame.locals import *
pygame.init()

pygame.display.set_caption('Menu')
screen = pygame.display.set_mode((600, 400),0,32)
 
font = pygame.font.SysFont(None, 30)
 
def draw_text(text, font, color, surface, x, y):
	textobj = font.render(text, 1, color)
	textrect = textobj.get_rect()
	textrect.topleft = (x, y)
	surface.blit(textobj, textrect)
 
click = False
 
def main_menu():
	while True:
 
		screen.fill((0,0,0))
		draw_text('Main Menu', font, (255, 255, 255), screen, 20, 20)
 
		mx, my = pygame.mouse.get_pos()
 
		play_button_rect = pygame.Rect(199,132,202,68)

		if play_button_rect.collidepoint((mx, my)):
			if click:
				game()

		play_button_img = pygame.image.load('textures/play_button.png')
		play_button_img = pygame.transform.scale(play_button_img,(202, 68))
		screen.blit(play_button_img, (199, 132))
 
		click = False
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					pygame.quit()
					sys.exit()
			if event.type == MOUSEBUTTONDOWN:
				if event.button == 1:
					click = True
 
		pygame.display.update()
		clock.tick(60)


def game():
	running = True

	screen.fill((0,0,0))
	
	sprinting_right = False
	sprinting_left = False

	moving_right = False
	moving_left = False
	vertical_momentum = 0
	air_timer = 0
	grass_sound_timer = 0

	true_cam_movement = [0,0]

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

	player_action = 'idle'
	player_frame = 0
	player_img_flip = False

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
	player_rect = pygame.Rect(100,100,5,13)

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

	while running: # game loop
		
		display.fill((146,244,255)) # filling screen with blue so images dont leave trails

		if grass_sound_timer > 0:
			grass_sound_timer -= 1

		true_cam_movement[0] += (player_rect.x-true_cam_movement[0]-152)/20
		true_cam_movement[1] += (player_rect.y-true_cam_movement[1]-106)/20

		cam_movement = true_cam_movement.copy()
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

		player_movement = [0,0]
		
		if moving_right == True:
			player_movement[0] += 2
		
		if moving_left == True:
			player_movement[0] -= 2

		if sprinting_right == True:
			player_movement[0] += 3

		if sprinting_left == True:
			player_movement[0] -= 3
		
		player_movement[1] += vertical_momentum
		vertical_momentum += 0.2
		
		if vertical_momentum > 3:
			vertical_momentum = 3

		if player_movement[0] > 0:
			player_action, player_frame = action_change(player_action, player_frame, 'run')
			player_img_flip = False
		if player_movement[0] == 0:
			player_action, player_frame = action_change(player_action, player_frame, 'idle')
		if player_movement[0] < 0:
			player_action, player_frame = action_change(player_action, player_frame, 'run')
			player_img_flip = True

		player_rect,collisions = move(player_rect,player_movement,tile_rects)

		if collisions['bottom'] == True:
			air_timer = 0
			vertical_momentum = 0

			if player_movement[0] != 0:
				if grass_sound_timer == 0:
					grass_sound_timer = 30
					sound = random.choice(grass_sounds)
					sound.play()
		else:
			air_timer += 1

		player_frame += 1
		if player_frame >= len(animation_db[player_action]):
			player_frame = 0

		player_img_id = animation_db[player_action][player_frame]
		player_img = animation_frames[player_img_id]
		display.blit(pygame.transform.flip(player_img, player_img_flip, False),(player_rect.x-cam_movement[0],player_rect.y-cam_movement[1]))

		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			
			if event.type == KEYDOWN:
				if event.key == K_d:
					moving_right = True
				
				if event.key == K_a:
					moving_left = True
				
				if event.key == K_d and pygame.key.get_mods() & KMOD_SHIFT:
					sprinting_right == True

				if event.key == K_a and pygame.key.get_mods() & KMOD_SHIFT:
					sprinting_left == True

				if event.key == K_w:
					if air_timer < 6:
						jump_sound.play()
						vertical_momentum = -5
				if event.key == K_ESCAPE:
					main_menu()
			
			if event.type == KEYUP:
				if event.key == K_d:
					moving_right = False
				
				if event.key == K_a:
					moving_left = False
			
		screen.blit(pygame.transform.scale(display,WINDOW_SIZE),(0,0))
		pygame.display.update()
		clock.tick(60)

clock = pygame.time.Clock()

pygame.display.set_caption('not sure')

WINDOW_SIZE = (600,400)

screen = pygame.display.set_mode(WINDOW_SIZE,0,32)

display = pygame.Surface((300,200))

CHUNK_SIZE = 8

main_menu()