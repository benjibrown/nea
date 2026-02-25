import pygame
import math
import sys


# CONSTANTS 
SCREEN_WIDTH = 1280            
SCREEN_HEIGHT = 720         
FPS = 60              

FOV = math.pi / 3        # fild of view - pi/3 rads
NUM_RAYS = SCREEN_WIDTH        # one ray per screen col
TILE_SIZE = 64                  # each map tile is 64x64 pixels 


# Toggle to demo the fisheye distortion bug 
# Will be explained in the Raycaster section below
FISHEYE_CORRECTION = True


class Map:
    # stores game world as 2D grid of integers 
    # 1 = wall, 0 = empty space. The outer border is all 1s to ensure the player cannot escape the map.

    # tile type constants - for reference
    WALL  = 1
    EMPTY = 0

    def __init__(self):
        # The map layout. Each inner list is one row (top to bottom).
        # The outer border is all 1s to ensure the player cannot escape the map.
        self.grid = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
            [1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        self.num_rows = len(self.grid)
        self.num_cols = len(self.grid[0])

    def get_tile(self, col, row):
        # return the tile value at (col, row) if within bounds, else return WALL 
        # prevents index errors and treats out-of-bounds as solid walls
        if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
            return self.grid[row][col]
        return self.WALL  # boundary is always a wall

    def is_wall(self, world_x, world_y):
        # check if world coordinates (pixels) are inside a wall tile 
        # converts world coordinates to grid coordinates by dividing by TILE_SIZE 
        grid_col = int(world_x // TILE_SIZE)
        grid_row = int(world_y // TILE_SIZE)
        return self.get_tile(grid_col, grid_row) == self.WALL



class Player:
    # represents the player's position, viewing angle, and movement logic.
    
    MOVE_SPEED = 1.5    # world-space pixels moved per frame
    ROT_SPEED = 0.0003  # rads rotated per pixel of horizontal mouse movement

    MARGIN = 10     # collision buffer in pixels - the player is treated as a circle with this radius for collision purposes

    def __init__(self, start_x, start_y, start_angle=0.0):
        self.x = float(start_x)    # world x position (pixels)
        self.y = float(start_y)    # world y position (pixels)
        self.angle = float(start_angle) # viewing direction in rads 

    def handle_input(self, keys, game_map, mouse_dx):
        # handle player movement and rotation based on input.

        # update angle: mouse_dx (+ve is right) * sensitivity 
        # modulo keeps angle within 0,2pi for trig functions
        self.angle = (self.angle + mouse_dx * self.ROT_SPEED) % (2 * math.pi)

        # fwd vector scaled by movement speed    
        forward_dx = math.cos(self.angle) * self.MOVE_SPEED
        forward_dy = math.sin(self.angle) * self.MOVE_SPEED

        if keys[pygame.K_w]:
            self._try_move( forward_dx,  forward_dy, game_map)
        if keys[pygame.K_s]:
            self._try_move(-forward_dx, -forward_dy, game_map)
        if keys[pygame.K_a]:  # move left: perpendicular vector
            self._try_move( forward_dy, -forward_dx, game_map)
        if keys[pygame.K_d]:  # move right: perpendicular vector
            self._try_move(-forward_dy,  forward_dx, game_map)

    def _try_move(self, delta_x, delta_y, game_map):

        # try to make by (delta_x, delta_y) but check for wall collisions first.
        # checking axes separately allows sliding along walls instead of stopping fully when touching one.
        m = self.MARGIN

        # test x movement - check two points at +- margin on y axis
        x_clear = (not game_map.is_wall(self.x + delta_x, self.y - m) and
                   not game_map.is_wall(self.x + delta_x, self.y + m))
        if x_clear:
            self.x += delta_x

        # same for y movement - check two points at +- margin on x axis
        y_clear = (not game_map.is_wall(self.x - m, self.y + delta_y) and
                   not game_map.is_wall(self.x + m, self.y + delta_y))
        if y_clear:
            self.y += delta_y



class Raycaster:
    # converts 2D grid map into 3D view w/ DDA 
    # DDA: for each screen col, a ray is stepped (tile by tile) through the grid - advancing whichever x or y boundary is closer.

    MAX_DEPTH = 20  # maximum ray travel in tiles before giving up 

    def __init__(self, screen_width, screen_height, fov):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.half_height = screen_height // 2 # precompute to prevent unnecessary division in the main loop
        self.fov = fov
        self.half_fov = fov / 2 # same as half height

    def cast_all(self, player, game_map):
        # cast one ray per screen col and returns list of tuples for each col
        # index corresponds to screen column, value is (wall_height, shade) for that column's ray 

        ray_results = []
        angle_step = self.fov / self.screen_width
        # ray starts at left edge of FOV and increments across the screen to the right edge 
        start_angle = player.angle - self.half_fov

        for col in range(self.screen_width):
            ray_angle = start_angle + col * angle_step
            wall_height, shade, hit_side = self._cast_ray(ray_angle, player.angle, player, game_map)

            # darken walls hit on n/s faces for depth 
            if hit_side == 1:
               shade = int(shade * 0.75)

            ray_results.append((wall_height, shade))

        return ray_results
    
    def _cast_ray(self, ray_angle, player_angle, player, game_map):
        # cast a single ray using dda and return (wall_height, shade, hit_side).
        # calculates step distances:
        # delta_x/y: how far ray travels between vert/horiz grid lines 
        # side_dist_x/y: initial distance to first grid line in each axis 
        # hit_side: 0 = east/west wall face, 1 = north/south wall face

        ray_dx = math.cos(ray_angle)
        ray_dy = math.sin(ray_angle)

        # grid tile the player occupies
        map_col = int(player.x // TILE_SIZE)
        map_row = int(player.y // TILE_SIZE)

        # distance along the ray to next vert and horiz grid lines 
        # prevent divison by zero for rays aligned with axes
        delta_dist_x = abs(1 / ray_dx) if ray_dx != 0 else float('inf')
        delta_dist_y = abs(1 / ray_dy) if ray_dy != 0 else float('inf')

        # determine step direction and initial side dist 
        if ray_dx < 0:
            step_x = -1
            side_dist_x = (player.x / TILE_SIZE - map_col) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_col + 1.0 - player.x / TILE_SIZE) * delta_dist_x

        if ray_dy < 0:
            step_y = -1
            side_dist_y = (player.y / TILE_SIZE - map_row) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_row + 1.0 - player.y / TILE_SIZE) * delta_dist_y

        # main dda loop
        wall_hit = False
        hit_side = 0
        depth = 0
        while not wall_hit and depth < self.MAX_DEPTH:
            # step along whichever axis has nearer crossing
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_col += step_x
                hit_side = 0  # e/w face
            else:
                side_dist_y += delta_dist_y
                map_row += step_y
                hit_side = 1  # n/s face

            if game_map.get_tile(map_col, map_row) == Map.WALL:
                wall_hit = True
            depth += 1

        # perp wall dist - the distance from player to wall along the ray, corrected for fisheye.
        if hit_side == 0:
            perp_dist = (side_dist_x - delta_dist_x) * TILE_SIZE
        else:
            perp_dist = (side_dist_y - delta_dist_y) * TILE_SIZE

        # clamp to avoid division by zero
        perp_dist = max(perp_dist, 0.0001)
        

        # TODO - remove fisheye toggle once written section
        if FISHEYE_CORRECTION:
            # dda already calculates this correctly 
            distance = perp_dist
        else:
            # demo of fisheye bug - using euclidean (straight line) distance instead of perp dist causes distortion 
            angle_diff = ray_angle - player_angle
            distance = perp_dist / math.cos(angle_diff)

        wall_height = int((TILE_SIZE / distance) * self.screen_height)

        # shade based on distance, configure for atmoshphere
        tile_dist = distance / TILE_SIZE
        shade = max(40, min(255, 255 - int(tile_dist * 18)))

        return wall_height, shade, hit_side



class Renderer:
    
    # handles all pygame drawing 

    CEILING_COLOUR = (10,  10,  10)  # dark ceiling
    FLOOR_COLOUR = (40,  40,  40)  # grey floor

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.half_height = self.height // 2
        self.hud_font = pygame.font.SysFont(None, 28)

    def draw_background(self):
        # draw ceiling and floor as solid rectangles
        # walls to be draw on top of this
        pygame.draw.rect(self.screen, self.CEILING_COLOUR,
                         (0, 0, self.width, self.half_height))
        pygame.draw.rect(self.screen, self.FLOOR_COLOUR,
                         (0, self.half_height, self.width, self.half_height))

    def draw_walls(self, ray_results):
        # draw one vertical line per screen col using ray data 
        # wall height and shade already calculated by raycast object

        for screen_x, (wall_height, shade) in enumerate(ray_results):
            wall_colour = (shade, shade, shade)  # grey scaled by distance
            wall_top = self.half_height - wall_height // 2
            wall_bottom = self.half_height + wall_height // 2
            pygame.draw.line(self.screen, wall_colour,
                             (screen_x, wall_top), (screen_x, wall_bottom))

    def draw_hud(self, current_fps):

        # minimal HUD for basic use 
        
        # FPS counter (top-left) - will add toggle in later iterations
        fps_surface = self.hud_font.render(f"FPS: {int(current_fps)}", True, (220, 220, 0))
        self.screen.blit(fps_surface, (10, 10))

        # simple crosshair at screen centre - for dev purposes
        cx = self.width  // 2
        cy = self.height // 2
        pygame.draw.line(self.screen, (255, 255, 255), (cx - 12, cy), (cx + 12, cy), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (cx, cy - 12), (cx, cy + 12), 1)

        # control hints - will probably remove in later iterations for a dedicated menu screen, but useful for now
        hint_surface = self.hud_font.render(
            "WASD: move   Mouse: look   ESC: quit", True, (140, 140, 140))
        self.screen.blit(hint_surface, (10, self.height - 30))



class Game:

    # main game class - initializes pygame, creates subsystems, and contains the main loop.

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NEA - Iteration 1: Raycasting Engine")
        self.clock = pygame.time.Clock()

        # instantiate each subsystem
        self.game_map = Map()
        self.player = Player(start_x=TILE_SIZE * 1.5, start_y=TILE_SIZE * 1.5, start_angle=0.3)
        self.raycaster = Raycaster(SCREEN_WIDTH, SCREEN_HEIGHT, FOV)
        self.renderer = Renderer(self.screen)

        # capture mouse         
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def _handle_events(self):
        # process all pending events
        total_mouse_dx = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._quit()
            if event.type == pygame.MOUSEMOTION:
                # accumulate mouse change in x direction  
                total_mouse_dx += event.rel[0]
        return total_mouse_dx

    def run(self):
        # collect inputs 
        # update player state based on inputs 
        # cast rays to generate column data 
        # draw background, walls, then HUD 
        # flip display and cap framerate

        while True:
            mouse_dx = self._handle_events()
            keys     = pygame.key.get_pressed()

            self.player.handle_input(keys, self.game_map, mouse_dx)
            ray_results = self.raycaster.cast_all(self.player, self.game_map)

            self.renderer.draw_background()
            self.renderer.draw_walls(ray_results)
            self.renderer.draw_hud(self.clock.get_fps())

            pygame.display.flip()       # swap back buffer to screen
            self.clock.tick(FPS)        # cap framerate

    def _quit(self):
        pygame.quit()
        sys.exit()



if __name__ == "__main__":
    game = Game()
    game.run()

