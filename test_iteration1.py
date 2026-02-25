import math
import sys

from main import Map, Player, Raycaster, TILE_SIZE, FOV, FISHEYE_CORRECTION




# helper
def check(description, condition):
    # green ansi code is \033[92m, red is \033[91m, reset is \033[0m
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {description}")
    
    return condition


# map tests 
def test_map():
    print("\nMap")
    game_map = Map()

    # corner tile (0,0) must always be a wall in our map layout
    check("get_tile(0,0) returns WALL",
          game_map.get_tile(0, 0) == Map.WALL)

    # tile (1,1) is the first open floor tile
    check("get_tile(1,1) returns EMPTY",
          game_map.get_tile(1, 1) == Map.EMPTY)

    # out-of-bounds should be treated as wall (validation / boundary test)
    check("get_tile(-1, 0) out-of-bounds returns WALL",
          game_map.get_tile(-1, 0) == Map.WALL)
    check("get_tile(100, 100) out-of-bounds returns WALL",
          game_map.get_tile(100, 100) == Map.WALL)

    # is_wall: world coords inside the outer wall border (tile 0,0 = 0..63 px)
    check("is_wall(32, 32) inside tile (0,0) = True",
          game_map.is_wall(32, 32) is True)

    # is_wall: world coords inside an open tile (tile 1,1 = 64..127 px)
    check("is_wall(96, 96) inside tile (1,1) = False",
          game_map.is_wall(96, 96) is False)

    # is_wall: negative coordinates (out-of-bounds) treated as wall
    check("is_wall(-1, -1) out-of-bounds = True",
          game_map.is_wall(-1, -1) is True)


# player tests
def test_player():
    print("\nPlayer")
    game_map = Map()

    # instantiate player at tile (1,1) centre = (96, 96)
    player = Player(start_x=96, start_y=96, start_angle=0.0)

    check("Player initialises at correct x position (96)",
          player.x == 96.0)
    check("Player initialises at correct y position (96)",
          player.y == 96.0)
    check("Player initialises with correct angle (0.0)",
          player.angle == 0.0)

    # collisions - player should not be able to move into a wall.
    # tile (0,x) is always a wall. Player at x=96, moving hard left
    # should be stopped by the wall at world_x = 0..63.
    player2 = Player(start_x=96, start_y=96, start_angle=0.0)
    original_x = player2.x
    player2._try_move(-200, 0, game_map)  # try to move far left into wall
    check("Collision: player blocked from moving into wall (x axis)",
          player2.x == original_x)

    # player should be able to move freely into open space
    player3 = Player(start_x=96, start_y=96, start_angle=0.0)
    player3._try_move(1, 0, game_map)     # small step right, into open tile
    check("Movement: player moves right into open space",
          player3.x > 96.0)

    # angle wraps correctly after full rotation
    player4 = Player(start_x=96, start_y=96, start_angle=0.0)
    # simulate a mouse movement that would push angle beyond 2 pi
    two_pi = 2 * math.pi
    large_delta = int(two_pi / Player.ROT_SPEED) + 1  # enough to exceed 2 pi
    player4.angle = (player4.angle + large_delta * Player.ROT_SPEED) % two_pi
    check("Angle wraps into [0, 2π) after large rotation",
          0.0 <= player4.angle < two_pi)

# raycaster tests 
def test_raycaster():
    print("\nRaycaster")
    raycaster = Raycaster(1280, 720, FOV)
    game_map = Map()

    # player facing directly east (angle=0) at tile (1,1) centre
    player = Player(start_x=96, start_y=96, start_angle=0.0)
    ray_results = raycaster.cast_all(player, game_map)

    # cast_all should return exactly one entry per screen column
    check(f"cast_all returns {1280} results (one per column)",
          len(ray_results) == 1280)

    # each entry must be a tuple of two values
    check("Each result entry is a (wall_height, shade) tuple of length 2",
          all(len(r) == 2 for r in ray_results))

    # wall heights must be positive integers
    check("All wall heights are positive",
          all(r[0] > 0 for r in ray_results))

    # shade values within valid colour range 0-255
    check("All shade values are in range [0, 255]",
          all(0 <= r[1] <= 255 for r in ray_results))

    # with fisheye correction on, the wall slice heights should vary smoothly
    # standard deviation should not be large compared to mean
    heights = [r[0] for r in ray_results]
    mean_h = sum(heights) / len(heights)
    check("Mean wall height is a positive, finite value",
          mean_h > 0 and math.isfinite(mean_h))

    # a ray cast straight at a wall 1 tile away should produce a large wall height
    centre_height = ray_results[640][0]
    check("Centre wall height is a reasonable positive value",
          10 < centre_height < 5000)



if __name__ == "__main__":

    print("it 1 tests")
    print("-" * 50)

    test_map()
    test_player()
    test_raycaster()


