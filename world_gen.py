import opensimplex
import curses
import math

# Fixed seeds for elevation and moisture
seed_elevation = 6666
seed_moisture = 9999
noise_elevation = opensimplex.OpenSimplex(seed_elevation)
noise_moisture = opensimplex.OpenSimplex(seed_moisture)

def get_noise(x, y, noise_type='elevation'):
    scale = 0.1
    if noise_type == 'elevation':
        return noise_elevation.noise2(x * scale, y * scale)
    elif noise_type == 'moisture':
        return noise_moisture.noise2(x * scale, y * scale)

def get_biome(elevation, moisture, y, height):
    ice_threshold = height * 0.1  # Top and bottom edges for ice/glaciers.

    if y < ice_threshold or y > height - ice_threshold:
        if elevation > 0.8:
            return 'glaciers'
        elif elevation < -0.05:
            return 'ice'

    # Elevation adjustments for detailed water bodies
    if elevation < -0.1:
        return 'deep_water'
    elif elevation < 0:
        return 'shallow_water'
    elif elevation < 0.1:
        if moisture < -0.1:
            return 'beach'
        else:
            return 'plains'
    elif elevation < 0.3:
        if moisture < -0.2:
            return 'desert'
        elif moisture < 0:
            return 'savannah'
        elif moisture < 0.1:
            return 'grassland'
        else:
            return 'forest'
    elif elevation < 0.5:
        if moisture < 0.2:
            return 'hills'
        else:
            return 'rainforest'
    elif elevation < 0.7:
        if moisture < -0.1:
            return 'canyons'
        elif moisture < 0.1:
            return 'mountains'
        else:
            return 'swamps'
    else:
        if moisture < -0.2:
            return 'lava_fields'
        elif moisture < 0:
            return 'volcano'
        elif moisture < 0.1:
            return 'badlands'
        elif moisture < 0.2:
            return 'tundra'
        else:
            return 'glaciers'  # Glaciers for very high elevations with enough moisture...should probably change this to snow capped mountain?



# Create_atlas function to pass y and height to get_biome
def create_atlas(width, height):
    atlas = [[None for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            elevation = get_noise(x, y, 'elevation')
            base_moisture = get_noise(x, y, 'moisture')
            adjusted_moisture = adjust_moisture_by_latitude(base_moisture, y, height)
            atlas[y][x] = {'type': get_biome(elevation, adjusted_moisture, y, height), 'elevation': elevation, 'moisture': adjusted_moisture}
    return atlas



def adjust_moisture_by_latitude(moisture, y, height):
    # Define latitude as a value between 0 and 1, where 0.5 represents the equator
    latitude = y / height
    
    # Simulate equatorial moisture peak and gradual decrease towards the poles
    # Use a cosine function to simulate the increase in moisture near the equator and decrease towards the poles
    equatorial_moisture_adjustment = (1 + math.cos(math.pi * latitude)) / 2
    
    # Adjust the base moisture level with the equatorial moisture adjustment factor
    # This factor peaks at the equator (latitude = 0.5) and decreases towards the poles (latitude = 0 or 1)
    adjusted_moisture = moisture * equatorial_moisture_adjustment
    
    # I am an imposter and I wish I could code
    return adjusted_moisture

# I spent so much time here trying to get the look right and I'm still not happy
def get_char_and_color(tile):
    tile_mapping = {
    	'shallow_water': ("~", curses.COLOR_CYAN), 
        'deep_water': ("≈", curses.COLOR_BLUE),
        'beach': (":", curses.COLOR_YELLOW),
        'plains': ('"', curses.COLOR_GREEN),
        'desert': (";", curses.COLOR_YELLOW),
        'grassland': ('"', curses.COLOR_GREEN),
        'forest': ('F', curses.COLOR_GREEN),
        'rainforest': ('R', curses.COLOR_GREEN),
        'scorched': ('▪︎', curses.COLOR_RED),
        'bare': ('b', curses.COLOR_WHITE),
        'tundra': ('t', curses.COLOR_CYAN),
        'volcano': ('^', curses.COLOR_RED),
        'fissure': ('|', curses.COLOR_RED),
        'badlands': ('#', curses.COLOR_YELLOW),
        'ice': ('■', curses.COLOR_CYAN),
        'rivers': ('•', curses.COLOR_BLUE), 
        'lakes': ('O', curses.COLOR_BLUE), 
        'mountains': ('^', curses.COLOR_WHITE), 
        'hills': ('n', curses.COLOR_GREEN), 
        'swamps': ('&', curses.COLOR_GREEN), 
        'canyons': ('v', curses.COLOR_RED), 
        'glaciers': ('¤', curses.COLOR_CYAN), 
        'savannah': ('.', curses.COLOR_GREEN), 
        'rocky': ('*', curses.COLOR_WHITE),  
        'cliffs': ('▲', curses.COLOR_WHITE),  
        'lava_fields': ('∼', curses.COLOR_RED),  
        'meadows': ('"', curses.COLOR_GREEN), 
     
    }
    char, color = tile_mapping.get(tile['type'], (' ', curses.COLOR_WHITE))
    return char, color


# What unholy demon invented curses and why is this necessary?
# Why does using ANSI break everything when using curses?
def init_color_pairs():
    curses.start_color()
    curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)

# Wrapping it up and adding an exception seemed to solve the problem of starting out of bounds
def draw_atlas(window, atlas, player_pos):
    max_y, max_x = window.getmaxyx()
    global_width, global_height = len(atlas[0]), len(atlas)  # Get the size of the atlas

    for y in range(max_y):
        for x in range(max_x):
            # Calculate the world coordinates with wrapping
            world_x = (player_pos[0] + x - max_x // 2) % global_width
            world_y = (player_pos[1] + y - max_y // 2) % global_height

            # Get the tile type and corresponding character and color
            tile = atlas[world_y][world_x]
            char, color = get_char_and_color(tile)

            # Draw the tile
            try:
                window.addstr(y, x, char, curses.color_pair(color))
            except curses.error:
                # This handles any attempt to draw outside the window's bounds
                pass

    # Draw the player character at the center of the screen...please?
    try:
        window.addstr(max_y // 2, max_x // 2, '@', curses.color_pair(curses.COLOR_WHITE))
    except curses.error:
        pass

# Need to add 4 more directions
def main(window):
    curses.curs_set(0) 
    init_color_pairs()

    width, height = 200, 200 
    player_pos = [width // 2, height // 2] 
    atlas = create_atlas(width, height) 

    legend_visible = False 

    while True:
        window.clear()
        if legend_visible:
            draw_legend(window)
        else:
            draw_atlas(window, atlas, player_pos)
        
        window.refresh() 

        key = window.getch()  # Wait for user input
        if key in [ord('w'), ord('W')]: 
            player_pos[1] = (player_pos[1] - 1) % height
        elif key in [ord('s'), ord('S')]: 
            player_pos[1] = (player_pos[1] + 1) % height
        elif key in [ord('a'), ord('A')]: 
            player_pos[0] = (player_pos[0] - 1) % width
        elif key in [ord('d'), ord('D')]: 
            player_pos[0] = (player_pos[0] + 1) % width
        elif key in [ord('l'), ord('L')]:  # Toggle legend
            legend_visible = not legend_visible
        elif key == ord('q'):  # Quit
            break  # Exit the loop and end the program

def draw_legend(window):
    legend = [
        ("~", curses.COLOR_CYAN, "Shallow Water"),
        ("≈", curses.COLOR_BLUE, "Deep Water"),
        (":", curses.COLOR_YELLOW, "Beach"),
        ('"', curses.COLOR_GREEN, "Plains"),
        (";", curses.COLOR_YELLOW, "Desert"),
        ('F', curses.COLOR_GREEN, "Forest"),
        ('R', curses.COLOR_GREEN, "Rainforest"),
        ('s', curses.COLOR_RED, "Scorched"),
        ('b', curses.COLOR_WHITE, "Bare"),
        ('t', curses.COLOR_CYAN, "Tundra"),
        ('v', curses.COLOR_RED, "Canyons"),
        ('^', curses.COLOR_WHITE, "Mountains"),
        ('&', curses.COLOR_GREEN, "Swamps"),
        ('∼', curses.COLOR_RED, "Lava Fields"),
        ('"', curses.COLOR_GREEN, "Meadows"),
        ('■', curses.COLOR_CYAN, "Ice"),
      
        
    ]
    start_y, start_x = 2, 0  # Adjust starting position if needed

    for i, (char, color, desc) in enumerate(legend):
        try:
            window.addstr(start_y + i, start_x, f"{char} - {desc}", curses.color_pair(color))
        except curses.error:
            # This handles any attempt to draw outside the window's bounds
            pass


if __name__ == "__main__":
    curses.wrapper(main)
