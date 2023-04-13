#!/usr/bin/env python
# coding: utf-8

# In[22]:


import ctypes, pygame, pymunk
import pygame.gfxdraw
import random
import sys




TITLE_STRING = 'Plinko Ripoff'
FPS = 60

# Maintain resolution regardless of Windows scaling settings
ctypes.windll.user32.SetProcessDPIAware()

WIDTH = 1920
HEIGHT = 1080

# Plinko config
BG_COLOR = (16, 32, 45)
MULTI_HEIGHT = int(HEIGHT / 19) # 56 on 1920x1080
MULTI_COLLISION = HEIGHT - (MULTI_HEIGHT * 2) # 968 on 1920x1080

SCORE_RECT = int(WIDTH / 16) # 120 on 1920x1080

OBSTACLE_COLOR = "White"
OBSTACLE_RAD = int(WIDTH / 240) # 8 on 1920x1080
OBSTACLE_PAD = int(HEIGHT / 19) # 56 on 1920x1080
OBSTACLE_START = (int((WIDTH / 2) - OBSTACLE_PAD), int((HEIGHT - (HEIGHT * .9)))) # (904, 108) on 1920x1080
segmentA_2 = OBSTACLE_START

BALL_RAD = 16

# Dictionary to keep track of scores
multipliers = {
    "1000": 0,
    "130": 0,
    "26": 0,
    "9": 0,
    "4": 0,
    "2": 0,
    "0.2": 0
}

# RGB Values for multipliers
multi_rgb = {
    (0, 1000): (255, 0, 0),
    (1, 130): (255, 30, 0),
    (2, 26): (255, 60, 0),
    (3, 9): (255, 90, 0),
    (4, 4): (255, 120, 0),
    (5, 2): (255, 150, 0),
    (6, 0.2): (255, 180, 0),
    (7, 0.2): (255, 210, 0),
    (8, 0.2): (255, 240, 0),
    (9, 0.2): (255, 210, 0),
    (10, 0.2): (255, 180, 0),
    (11, 2): (255, 150, 0),
    (12, 4): (255, 120, 0),
    (13, 9): (255, 90, 0),
    (14, 26): (255, 60, 0),
    (15, 130): (255, 30, 0),
    (16, 1000): (255, 0, 0),
}

# Number of multipliers shown underneath obstacles
NUM_MULTIS = 17

# Pymunk settings (prevent same class collisions)
BALL_CATEGORY = 1
OBSTACLE_CATEGORY = 2
BALL_MASK = pymunk.ShapeFilter.ALL_MASKS() ^ BALL_CATEGORY
OBSTACLE_MASK = pymunk.ShapeFilter.ALL_MASKS()

# Audio stuff
pygame.mixer.init()
click = pygame.mixer.Sound("click.mp3")
sound01 = pygame.mixer.Sound("001.mp3")
sound01.set_volume(0.2)
sound02 = pygame.mixer.Sound("002.mp3")
sound02.set_volume(0.3)
sound03 = pygame.mixer.Sound("003.mp3")
sound03.set_volume(0.4)
sound04 = pygame.mixer.Sound("004.mp3")
sound04.set_volume(0.5)
sound05 = pygame.mixer.Sound("005.mp3")
sound05.set_volume(0.6)
sound06 = pygame.mixer.Sound("006.mp3")
sound06.set_volume(0.7)
sound07 = pygame.mixer.Sound("007.mp3")
sound07.set_volume(0.8)




# Sprite for multipliers beneath obstacles
multi_group = pygame.sprite.Group()
clock = pygame.time.Clock()
delta_time = clock.tick(FPS) / 1000.0

class Multi(pygame.sprite.Sprite):
    def __init__(self, position, color, multi_amt):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.SysFont(None, 26)
        self.color = color
        self.border_radius = 10
        self.position = position
        self.rect_width, self.rect_height = OBSTACLE_PAD - (OBSTACLE_PAD / 14), MULTI_HEIGHT
        self.image = pygame.Surface((self.rect_width, self.rect_height), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, self.image.get_rect(), border_radius=self.border_radius)
        self.rect = self.image.get_rect(center=position)
        self.multi_amt = multi_amt
        self.prev_multi = int(WIDTH / 21.3)

        # Animation stuff; framerate independent
        self.animated_frames = 0
        self.animation_frames = int(0.25 / delta_time)
        self.is_animating = False

        # Draw multiplier amount on rectangle
        self.render_multi()

    def animate(self, color, amount):
        if self.animated_frames < self.animation_frames // 2:
            self.rect.bottom += 2
        else:
            self.rect.bottom -= 2
        self.animated_frames += 1
        if self.animated_frames == (self.animation_frames // 2) * 2:
            self.is_animating = False
            self.animated_frames = 0

    def render_multi(self):
        text_surface = self.font.render(f"{self.multi_amt}x", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.image.get_rect().center)
        self.image.blit(text_surface, text_rect)

    def hit_sound(self):
        if str(self.multi_amt) == "0.2":
            sound01.play()
        elif str(self.multi_amt) == "2":
            sound02.play()
        elif str(self.multi_amt) == "4":
            sound03.play()
        elif str(self.multi_amt) == "9":
            sound04.play()
        elif str(self.multi_amt) == "26":
            sound05.play()
        elif str(self.multi_amt) == "130":
            sound06.play()
        elif str(self.multi_amt) == "1000":
            sound07.play()

    def update(self):
        if self.is_animating:
            self.animate(self.color, self.multi_amt)

# Class for previous multiplier display on right side of screen
class PrevMulti(pygame.sprite.Sprite):
    def __init__(self, multi_amt, rgb_tuple):
        super().__init__()
        self.display_surface = pygame.display.get_surface()

        # Rectangle stuff
        self.multi_amt = multi_amt
        self.font = pygame.font.SysFont(None, 36)
        self.rect_width = SCORE_RECT
        self.rect_height = SCORE_RECT
        self.prev_surf = pygame.Surface((self.rect_width, self.rect_height), pygame.SRCALPHA)
        self.rgb = rgb_tuple
        pygame.draw.rect(self.prev_surf, self.rgb, (0, 0, self.rect_width, self.rect_height))
        self.prev_rect = self.prev_surf.get_rect(midbottom=(int(WIDTH * .85), (HEIGHT / 2) - (SCORE_RECT * 2)))

        # Animation
        self.y_traverse = 0
        self.traveled = 0

        self.render_multi()

    def render_multi(self):
        text_surface = self.font.render(f"{self.multi_amt}x", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.prev_surf.get_rect().center)
        self.prev_surf.blit(text_surface, text_rect)

    def update(self):
        if self.prev_rect.bottom > (HEIGHT - (SCORE_RECT * 2)): # 864 at 1080
            self.kill()

        else:
            if self.traveled < self.y_traverse:
                total_distance = SCORE_RECT
                distance_per_second = 1800
                distance_per_frame = distance_per_second * delta_time # 28 at dt = .016
                divisor = int(SCORE_RECT / distance_per_frame)
                distance_per_frame = SCORE_RECT / divisor
                self.prev_rect.bottom += int(distance_per_frame)
                self.traveled += int(distance_per_frame)
            self.display_surface.blit(self.prev_surf, self.prev_rect)

class PrevMultiGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        pass

    def update(self):
        super().update()

        # Maintain four previous multis at a maximum; animate
        if len(self) > 5:
            self.remove(self.sprites().pop(0))        
        if len(self) == 1:
            self.sprites()[0].y_traverse = SCORE_RECT
        elif len(self) == 2:
            self.sprites()[0].y_traverse, self.sprites()[1].y_traverse = SCORE_RECT * 2, SCORE_RECT
        elif len(self) == 3:
            self.sprites()[0].y_traverse, self.sprites()[1].y_traverse, self.sprites()[2].y_traverse = SCORE_RECT * 3, SCORE_RECT * 2, SCORE_RECT
        elif len(self) == 4:
            self.sprites()[0].y_traverse, self.sprites()[1].y_traverse, self.sprites()[2].y_traverse, self.sprites()[3].y_traverse = SCORE_RECT * 4, SCORE_RECT * 3, SCORE_RECT * 2, SCORE_RECT
        elif len(self) == 5:
            self.sprites()[0].y_traverse, self.sprites()[1].y_traverse, self.sprites()[2].y_traverse, self.sprites()[3].y_traverse, self.sprites()[4].y_traverse = SCORE_RECT * 5, SCORE_RECT * 4, SCORE_RECT * 3, SCORE_RECT * 2, SCORE_RECT

prev_multi_group = PrevMultiGroup()



animation_group = pygame.sprite.Group()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.color = OBSTACLE_COLOR
        self.radius = OBSTACLE_RAD
        self.pos_x, self.pos_y = x, y
        self.image = pygame.Surface((BALL_RAD * 2, BALL_RAD * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))

class AnimatedObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, color, delta_time):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.x, self.y = x, y
        self.coords = (self.x, self.y)
        self.radius = radius
        self.color = color
        self.delta_time = delta_time
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

        # Calculate alpha value to decrement each frame
        self.alpha = 125
        self.fade_speed_second = 250
        self.fade_speed_frame = self.fade_speed_second * self.delta_time
        self.divisor = int(self.fade_speed_second / self.fade_speed_frame)
        self.fade_speed_frame = self.alpha / self.divisor

        # Calculate radius value to decrement each frame
        self.radius_dec_second = 32
        self.radius_dec_frame = self.radius_dec_second * self.delta_time
        self.divisor_rad = int(self.radius_dec_second / self.radius_dec_frame)
        self.radius_dec_frame = self.radius_dec_second / self.divisor_rad

    def fade(self, delta_time):
        self.alpha -= int(self.fade_speed_frame)
        if self.radius > 0:
            self.radius -= self.radius_dec_frame
        if self.alpha < 50 or self.radius < 2:
            self.kill()

    def update(self):
        self.fade(self.delta_time)
        self.draw(self.display_surface)

    def draw(self, surface):
        self.circle_surface = pygame.Surface((self.radius, self.radius), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(self.display_surface, self.x, self.y, int(self.radius), (255, 255, 255, self.alpha))
        self.display_surface.blit(self.circle_surface, (0, 0))


class Board():
    def __init__(self, space):
        self.space = space
        self.display_surface = pygame.display.get_surface()

        # Obstacles
        self.curr_row_count = 3
        self.final_row_count = 18
        self.obstacles_list = []
        self.obstacle_sprites = pygame.sprite.Group()
        self.updated_coords = OBSTACLE_START

        # Play button
        self.play_up = pygame.image.load("play01.png").convert_alpha()
        self.play_down = pygame.image.load("play02.png").convert_alpha()
        self.pressing_play = False
        self.play_orig_width = self.play_up.get_width()
        self.play_orig_height = self.play_up.get_height()

        # Scale the play image by 50%
        self.play_scaled_width = self.play_orig_width // 2
        self.play_scaled_height = self.play_orig_height // 2
        self.scaled_play_up = pygame.transform.scale(self.play_up, (self.play_scaled_width, self.play_scaled_height))
        self.scaled_play_down = pygame.transform.scale(self.play_down, (self.play_scaled_width, self.play_scaled_height))
        self.play_rect = self.scaled_play_up.get_rect(center=(WIDTH / 6, HEIGHT / 2))

        # Get second point for segmentA
        self.segmentA_2 = OBSTACLE_START
        while self.curr_row_count <= self.final_row_count:
            for i in range(self.curr_row_count):
                # Get first point for segmentB
                if self.curr_row_count == 3 and self.updated_coords[0] > OBSTACLE_START[0] + OBSTACLE_PAD:
                    self.segmentB_1 = self.updated_coords
                # Get first point for segmentA
                elif self.curr_row_count == self.final_row_count and i == 0:
                    self.segmentA_1 = self.updated_coords
                # Get second point for segmentB
                elif self.curr_row_count == self.final_row_count and i == self.curr_row_count - 1:
                    self.segmentB_2 = self.updated_coords
                self.obstacles_list.append(self.spawn_obstacle(self.updated_coords, self.space))
                self.updated_coords = (int(self.updated_coords[0] + OBSTACLE_PAD), self.updated_coords[1])
            self.updated_coords = (int(WIDTH - self.updated_coords[0] + (.5 * OBSTACLE_PAD)), int(self.updated_coords[1] + OBSTACLE_PAD))
            self.curr_row_count += 1
        self.multi_x, self.multi_y = self.updated_coords[0] + OBSTACLE_PAD, self.updated_coords[1]

        # Segments (boundaries on side of obstacles)
        self.spawn_segments(self.segmentA_1, self.segmentA_2, self.space)
        self.spawn_segments(self.segmentB_1, self.segmentB_2, self.space)
        # Segments at top of obstacles
        self.spawn_segments((self.segmentA_2[0], 0), self.segmentA_2, self.space)
        self.spawn_segments(self.segmentB_1, (self.segmentB_1[0], 0), self.space)

        # Spawn multis
        self.spawn_multis()

    def draw_obstacles(self, obstacles):
        for obstacle in obstacles:
            pos_x, pos_y = int(obstacle.body.position.x), int(obstacle.body.position.y)
            pygame.draw.circle(self.display_surface, (255, 255, 255), (pos_x, pos_y), OBSTACLE_RAD)

    # Used to give a border radius to previous multi display on right side
    def draw_prev_multi_mask(self):
        multi_mask_surface = pygame.Surface((WIDTH / 4, HEIGHT), pygame.SRCALPHA)
        multi_mask_surface.fill(BG_COLOR)
        right_side_of_board = (WIDTH / 16) * 13
        right_side_pad = right_side_of_board / 130
        mask_y = (HEIGHT / 4) + ((HEIGHT / 4) / 9)
        pygame.draw.rect(multi_mask_surface, (0, 0, 0, 0), (right_side_pad, mask_y, SCORE_RECT, SCORE_RECT * 4), border_radius=30)
        self.display_surface.blit(multi_mask_surface, (right_side_of_board, 0))

    def spawn_multis(self):
        self.multi_amounts = [val[1] for val in multi_rgb.keys()]
        self.rgb_vals = [val for val in multi_rgb.values()]
        for i in range(NUM_MULTIS):
            multi = Multi((self.multi_x, self.multi_y), self.rgb_vals[i], self.multi_amounts[i])
            multi_group.add(multi)
            self.multi_x += OBSTACLE_PAD

    def spawn_obstacle(self, pos, space):
        body = pymunk.Body(body_type = pymunk.Body.STATIC)
        body.position = pos
        body.friction = 0.6
        shape = pymunk.Circle(body, OBSTACLE_RAD)
        shape.elasticity = 0.4
        shape.filter = pymunk.ShapeFilter(categories=OBSTACLE_CATEGORY, mask=OBSTACLE_MASK)
        self.space.add(body, shape)
        obstacle = Obstacle(body.position.x, body.position.y)
        self.obstacle_sprites.add(obstacle)
        return shape

    def spawn_segments(self, pointA, pointB, space):
        segment_body = pymunk.Body(body_type = pymunk.Body.STATIC)
        segment_shape = pymunk.Segment(segment_body, pointA, pointB, 5) # radius = 5
        self.space.add(segment_body, segment_shape)

    def update(self):
        self.draw_obstacles(self.obstacles_list)
        multi_group.draw(self.display_surface)
        multi_group.update()
        if len(list(prev_multi_group)) > 0:
            prev_multi_group.update()
        if len(list(animation_group)) > 0:
            animation_group.update()
        self.draw_prev_multi_mask()
        if self.pressing_play:
            self.display_surface.blit(self.scaled_play_down, (WIDTH // 16, HEIGHT // 3))
        else:
            self.display_surface.blit(self.scaled_play_up, (WIDTH // 16, HEIGHT // 3))

class Ball(pygame.sprite.Sprite):
    def __init__(self, pos, space, board, delta_time):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.space = space
        self.board = board
        self.delta_time = delta_time
        self.body = pymunk.Body(body_type = pymunk.Body.DYNAMIC)
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, BALL_RAD)
        self.shape.elasticity = 0.9
        self.shape.density = 10000
        self.shape.mass = 1000
        self.shape.filter = pymunk.ShapeFilter(categories=BALL_CATEGORY, mask=BALL_MASK)
        self.space.add(self.body, self.shape)
        self.image = pygame.Surface((BALL_RAD * 2, BALL_RAD * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(self.body.position.x, self.body.position.y))

    def update(self):
        pos_x, pos_y = int(self.body.position.x), int(self.body.position.y)
        self.rect.centerx = pos_x
        self.rect.centery = pos_y

        # Check to see if ball hits obstacle
        for obstacle in self.board.obstacle_sprites:
            if pygame.sprite.collide_rect(self, obstacle):
                # Create animation and add to animation_group
                obstacle_centerx, obstacle_centery = obstacle.rect.centerx, obstacle.rect.centery
                obstacle_pos = (obstacle_centerx, obstacle_centery)

                for animating_obstacle in animation_group:
                    if obstacle_pos == animating_obstacle.coords:
                        animating_obstacle.kill()

                # Instantiate obstacle animation: params -> x, y, radius, color, delta_time
                obs_anim = AnimatedObstacle(obstacle_centerx, obstacle_centery, 16, (255, 255, 255), self.delta_time)
                animation_group.add(obs_anim)

        # Check to see if ball hits multi
        for multi in multi_group:
            if pygame.sprite.collide_rect(self, multi):
                multi.hit_sound()
                multipliers[str(multi.multi_amt)] += 1
                print(f"Total plays: {sum([val for val in multipliers.values()])} | {multipliers}")
                multi.animate(multi.color, multi.multi_amt)
                multi.is_animating = True

                # Display previous multi on right side of screen
                prev_rgb = multi.color
                prev_multi = PrevMulti(str(multi.multi_amt), prev_rgb)
                prev_multi_group.add(prev_multi)
                self.kill()
        
        # Draw red ball
        pygame.draw.circle(self.display_surface, (255, 0, 0), (pos_x, pos_y), BALL_RAD)

# Maintain resolution regardless of Windows scaling settings
ctypes.windll.user32.SetProcessDPIAware()

class Game:
    def __init__(self):
        # General setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE_STRING)
        self.clock = pygame.time.Clock()
        self.delta_time = 0

        # Pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, 1800)

        # Plinko setup
        self.ball_group = pygame.sprite.Group()
        self.board = Board(self.space)

        # Debugging
        self.balls_played = 0

    def run(self):
        self.start_time = pygame.time.get_ticks()

        while True:
            # Handle quit operation
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Get the position of the mouse click
                    mouse_pos = pygame.mouse.get_pos()

                    # Check if the mouse click position collides with the image rectangle
                    if self.board.play_rect.collidepoint(mouse_pos):
                        self.board.pressing_play = True
                    else:
                        self.board.pressing_play = False
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.board.pressing_play:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.board.play_rect.collidepoint(mouse_pos):
                        random_x = WIDTH//2 + random.choice([random.randint(-20, -1), random.randint(1, 20)])
                        click.play()
                        self.ball = Ball((random_x, 20), self.space, self.board, self.delta_time)
                        self.ball_group.add(self.ball)
                        self.board.pressing_play = False
                    else:
                        self.board.pressing_play = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        pygame.quit()
                        sys.exit()

            self.screen.fill(BG_COLOR)

            # Time variables
            self.delta_time = self.clock.tick(FPS) / 1000.0

            # Pymunk
            self.space.step(self.delta_time)
            self.board.update()
            self.ball_group.update()

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()


# In[ ]:




