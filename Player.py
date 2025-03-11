from microbit import *
import radio
import random

# Define maze dimensions
MAZE_WIDTH = 5
MAZE_HEIGHT = 5
radio.config(group=23)

# The Block class is used to create obstacles in the maze
class Block:
    # Constructor
    def __init__(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height
        self.BLOCK_START_X = random.randint(0, MAZE_WIDTH - width)
        self.BLOCK_START_Y = random.randint(0, MAZE_HEIGHT - height)
        self.ALLOWED_BLOCK_END = MAZE_WIDTH - width

    # Show the block
    def show(self):
        # Check if the block is allowed to spawn
        self.check_if_spawn()
        # Loop through the block's width and height
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                display.set_pixel(self.BLOCK_START_X + x, self.BLOCK_START_Y + y, 5)

    # Check if the block is allowed to spawn
    def check_if_spawn(self):
        # Check if the block's start position is at the default position of the Player
        done = False
        while not done:
            if self.BLOCK_START_Y == 0 and self.BLOCK_START_X == 0:
                self.BLOCK_START_X = random.randint(0, MAZE_WIDTH - self.WIDTH)
                self.BLOCK_START_Y = random.randint(0, MAZE_HEIGHT - self.HEIGHT)
                self.ALLOWED_BLOCK_END = MAZE_WIDTH - self.WIDTH
            else:
                done = True

# The Portal class is used to create portals in the maze, which the player has to find
class Portal:
    FOUND = False
    # Constructor
    def __init__(self, blocks: 'list[Block]'):
        self.blocks = blocks
        self.X = random.randint(0, MAZE_WIDTH - 1)
        self.Y = random.randint(0, MAZE_HEIGHT - 1)
    # Check if the portal is allowed to spawn
    def check_if_spawn(self):
        done = False
        while not done:
            if (self.X, self.Y) == (0, 0) or self.is_on_block():
                self.X = random.randint(0, MAZE_WIDTH - 1)
                self.Y = random.randint(0, MAZE_HEIGHT - 1)
            else:
                done = True
    # Check if the portal is on a block
    def is_on_block(self):
        for block in self.blocks:
            if (block.BLOCK_START_X <= self.X < block.BLOCK_START_X + block.WIDTH) and \
                    (block.BLOCK_START_Y <= self.Y < block.BLOCK_START_Y + block.HEIGHT):
                return True
        return False
    # Show the portal
    def show(self):
        if not self.FOUND:
            self.check_if_spawn()
            # Display the portal on the LED matrix with brightness 5
            display.set_pixel(self.X, self.Y, 7)
        else:
            del self

    # Hide the portal
    def hide(self):
        self.FOUND = True
        display.set_pixel(self.X, self.Y, 0)

# The Player class is used to create the player object
class Player:
    X = 0
    Y = 0
    # Constructor
    def __init__(self, slowness: int, portals: 'list[Portal]', blocks: 'list[Block]'):
        self.SLOW = slowness
        self.PORTALS = portals
        self.BLOCKS = blocks

    # Check if the player is on a portal
    def check_for_portal(self):
        for p in self.PORTALS:
            if p.X == self.X and p.Y == self.Y:
                p.hide()
                # remove the portal from the list
                self.PORTALS.remove(p)
                return True

    # Check if the player is on a block
    def is_on_block(self):
        for block in self.BLOCKS:
            if (block.BLOCK_START_X <= self.X < block.BLOCK_START_X + block.WIDTH) and \
                    (block.BLOCK_START_Y <= self.Y < block.BLOCK_START_Y + block.HEIGHT):
                return True
        return False

    # Move the player
    def move(self):
        display.set_pixel(self.X, self.Y, 9)  # Display player
        sleep(self.SLOW)
        x, y, z = accelerometer.get_values()
        if x < -300 and self.X > 0:
            display.set_pixel(self.X, self.Y, 0)
            self.X -= 1  # Move left
        elif x > 300 and self.X < MAZE_WIDTH - 1:
            display.set_pixel(self.X, self.Y, 0)
            self.X += 1  # Move right
        elif y < -300 and self.Y > 0:
            display.set_pixel(self.X, self.Y, 0)
            self.Y -= 1  # Move up
        elif y > 300 and self.Y < MAZE_HEIGHT - 1:
            display.set_pixel(self.X, self.Y, 0)
            self.Y += 1  # Move down

# The Level class is used to create the levels of the game
class Level:
    # Constructor
    def __init__(self, player_slowness: int, number_of_portals: int, *planned_blocks: 'list[tuple[int, int]]'):
        self.blocks = []
        self.portals = []
        # Create the blocks, there could be an infinite amount of blocks because of the * in *planned_blocks
        for b in planned_blocks:
            self.blocks.append(Block(b[0], b[1]))

        # Create the portals
        i = 0
        while i < number_of_portals:
            self.portals.append(Portal(self.blocks))
            i += 1

        self.player = Player(player_slowness, self.portals, self.blocks)

# Main Game class
class Game:
    # Constructor
    def __init__(self, level: Level):
        self.GAME_OVER = False
        self.CURRENT_LEVEL = 0
        self.RESTARTS = 0
        self.DEATHS = 0
        self.END_TIME = 0
        self.LEVEL = level
        self.START_TIME = running_time()
        self.PORTALS_LEFT = len(self.LEVEL.portals)
        radio.on()
        radio.send("clr")
        radio.send("lvl;" + str(self.CURRENT_LEVEL + 1))
        radio.send("rst;" + str(self.RESTARTS))
        radio.send("dth;" + str(self.DEATHS))
        radio.send("lvlt;" + str(0))
        radio.off()
        self.ENDTIMESET = False

    # Main game loop
    def play(self):
        if not self.GAME_OVER:
            # Restart the game manually
            if button_a.is_pressed():
                self.RESTARTS += 1
                radio.on()
                radio.send("rst;" + str(self.RESTARTS))
                radio.off()
                self.restart()
            # Show blocks
            for b in self.LEVEL.blocks:
                b.show()
            # Show portals
            for p in self.LEVEL.portals:
                p.show()
            self.LEVEL.player.move()
            # Check if player is on a portal
            if self.LEVEL.player.check_for_portal():
                self.PORTALS_LEFT -= 1
                if self.PORTALS_LEFT == 0:
                    self.end()
            # Check if player is on a block
            if self.LEVEL.player.is_on_block():
                self.DEATHS += 1
                radio.on()
                radio.send("dth;" + str(self.DEATHS))
                radio.off()
                display.show(Image.SAD)
                sleep(500)
                self.restart()

        else:
            if not self.ENDTIMESET:
                self.END_TIME = running_time()-self.START_TIME
                self.ENDTIMESET = True
            display.show(Image.HEART)

    # Ending
    def end(self):
        display.clear()
        radio.on()
        TIME = running_time() - self.START_TIME
        TIME_in_seconds = TIME / 1000
        formatted_TIME = "{:.1f}".format(TIME_in_seconds)
        radio.send("lvlt;" + formatted_TIME)
        radio.send("lvl;" + str(self.CURRENT_LEVEL + 1))
        radio.send("rst;" + str(self.RESTARTS))
        radio.send("dth;" + str(self.DEATHS))
        radio.off()

        self.CURRENT_LEVEL += 1
        self.restart()

    # Restarting the Level, when for example the level is not possible or the player dies
    def restart(self):
        # End the game, when all levels have been played
        if self.CURRENT_LEVEL > len(Levels) - 1:
            self.end_game()
            return
        else:
            self.LEVEL = Level(*Levels[self.CURRENT_LEVEL])
            self.LEVEL.player.X = 0
            self.LEVEL.player.Y = 0
            self.PORTALS_LEFT = len(self.LEVEL.portals)
            for p in self.LEVEL.portals:
                p.FOUND = False
            display.clear()

    def end_game(self):
        display.clear()
        display.show(Image.HEART)
        self.GAME_OVER = True

Levels = [
    [150, 2, [2, 2], [2, 2]],
    [130, 2, [2, 2], [2, 2]],
    [100, 2, [2, 2], [2, 2]],
    [100, 3, [2, 2], [2, 2]],
    [100, 4, [2, 2], [2, 2]],
    [150, 2, [2, 2], [2, 2], [1, 1]],
    [150, 2, [3, 2], [2, 2], [1, 1]],
    [130, 2, [3, 2], [2, 2], [1, 1]],
    [100, 2, [3, 2], [2, 2], [1, 1]],
    [150, 2, [3, 2], [2, 3], [1, 1]],
    [100, 2, [2, 2], [2, 2], [2, 1]],
    [130, 2, [2, 2], [2, 2], [2, 2]],
    [100, 2, [2, 2], [2, 2], [2, 2]],
    [100, 2, [2, 2], [2, 2], [3, 1]],
]

game = Game(Level(*Levels[0]))
# play game forever
radio.on()
radio.send("rgstr;Aron")
radio.off()
while True:
    game.play()
