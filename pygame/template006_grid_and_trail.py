# -*- coding: utf-8 -*-
"""
author: Horst JENS
email: horstjens@gmail.com
contact: see http://spielend-programmieren.at/de:kontakt
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
idea: template to show how to move and rotate pygames Sprites
this example is tested using python 3.4 and pygame
needs: file 'babytux.png' in subfolder 'data'
"""

#TODO: räume, tore in angrenzende Räume, Raumwechsel, Teleporter
#TODO: Pause (state machine)

#the next line is only needed for python2.x and not necessary for python3.x
from __future__ import print_function, division

import pygame 
import math
import random
import os
import sys

GRAD = math.pi / 180 # 2 * pi / 360   # math module needs Radiant instead of Grad


# ------ generic functions ----

def draw_examples(background):
    """painting on the background surface"""
    pygame.draw.line(background, (0,255,0), (10,10), (50,100))
    pygame.draw.rect(background, (0,255,0), (50,50,100,25)) # rect: (x1, y1, width, height)
    pygame.draw.circle(background, (0,200,0), (200,50), 35)
    pygame.draw.polygon(background, (0,180,0), ((250,100),(300,0),(350,50)))
    pygame.draw.arc(background, (0,150,0),(400,10,150,100), 0, 3.14) # radiant instead of grad

def write(background, text, x=50, y=150, color=(0,0,0),
          fontsize=None, center=False):
        """write text on pygame surface. """
        if fontsize is None:
            fontsize = 24
        font = pygame.font.SysFont('mono', fontsize, bold=True)
        fw, fh = font.size(text)
        surface = font.render(text, True, color)
        if center: # center text around x,y
            background.blit(surface, (x-fw//2, y-fh//2))
        else:      # topleft corner is x,y
            background.blit(surface, (x,y))
    
def elastic_collision(sprite1, sprite2):
        """elasitc collision between 2 sprites (calculated as disc's).
           The function alters the dx and dy movement vectors of both sprites.
           The sprites need the property .mass, .radius, .x .y, .dx, dy
           by Leonard Michlmayr"""
        dirx = sprite1.x - sprite2.x
        diry = sprite1.y - sprite2.y
        sumofmasses = sprite1.mass + sprite2.mass
        sx = (sprite1.dx * sprite1.mass + sprite2.dx * sprite2.mass) / sumofmasses
        sy = (sprite1.dy * sprite1.mass + sprite2.dy * sprite2.mass) / sumofmasses
        bdxs = sprite2.dx - sx
        bdys = sprite2.dy - sy
        cbdxs = sprite1.dx - sx
        cbdys = sprite1.dy - sy
        distancesquare = dirx * dirx + diry * diry
        if distancesquare == 0:
            dirx = random.randint(0,11) - 5.5
            diry = random.randint(0,11) - 5.5
            distancesquare = dirx * dirx + diry * diry
        dp = (bdxs * dirx + bdys * diry) # scalar product
        dp /= distancesquare # divide by distance * distance.
        cdp = (cbdxs * dirx + cbdys * diry)
        cdp /= distancesquare
        if dp > 0:
            sprite2.dx -= 2 * dirx * dp 
            sprite2.dy -= 2 * diry * dp
            sprite1.dx -= 2 * dirx * cdp 
            sprite1.dy -= 2 * diry * cdp
            
            
def fill_surface_with_tiles(tile, width, height, leave_border_empty=False):
    """return a width x height surface filled with tiles"""
    bigpicture = pygame.Surface((width, height))
    tilewidth = tile.get_rect().width
    tileheight = tile.get_rect().height
    if leave_border_empty:
        tiles_x = range(width//tilewidth)
        tiles_y = range(height // tileheight)
    else:
        tiles_x = range(width // tilewidth +1)
        tiles_y = range(height // tileheight +1)
    for x in tiles_x:
        for y in tiles_y:
            bigpicture.blit(tile, (x * tilewidth, y * tileheight))
    return bigpicture
    
# --- game Classes --------

class FlyingObject(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygames sprite class"""
    number = 0 # current number for new Sprite
    numbers = {} # {number: Sprite}
  
    
    def __init__(self, radius = 50, color=None, x=320, y=240,
                 dx=0, dy=0, layer=4, friction=1.0, mass=10, speed = 20,
                 hitpoints=100, damage=10, bossnumber = None, imagenr = None, trail=False):
        """create a (black) surface and paint a blue ball on it"""
        self._layer = layer   #self.layer = layer
        pygame.sprite.Sprite.__init__(self, self.groups) #call parent class. NEVER FORGET !
        # self groups is set in PygView.paint()
        self.number = FlyingObject.number # unique number for each sprite
        FlyingObject.number += 1 
        FlyingObject.numbers[self.number] = self
        self.radius = radius
        self.mass = mass
        self.damage = damage
        self.imagenr = imagenr
        self.bossnumber = bossnumber
        self.hitpoints = hitpoints
        self.hitpointsfull = hitpoints
        self.trail = trail
        self.trail_max_length = 50 # max 255 !
        self.width = 2 * self.radius
        self.height = 2 * self.radius
        self.turnspeed = 5   # onnly important for rotating
        self.speed = speed      # only important for ddx and ddy
        self.oldspeed = speed
        self.angle = 0
        self.x = x           # position
        self.y = y
        self.targetx = None
        self.targety = None
        self.target_time = False
        self.old_distances_to_target = []
        self.dx = dx         # movement
        self.dy = dy
        self.ddx = 0 # acceleration and slowing down. set dx and dy to 0 first!
        self.ddy = 0
        self.friction = friction # 1.0 means no friction at all
        if color is None: # create random color if no color is given
            self.color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        else:
            self.color = color
        self.create_image()
        self.rect= self.image.get_rect()
        self.init2()
        if self.trail:
            self.oldposlist = []
            
        
    def init2(self):
        pass # for specific init stuff of subclasses, overwrite init2
        
    def get_speed_from_dxdy(self):
        if self.dx != 0 or self.dy != 0:
           self.speed =  ( self.dx **2 + self.dy **2 ) ** 0.5
        
    def kill(self):
        del self.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)
            
    def create_image(self):
        self.image = pygame.Surface((self.width,self.height))    
        self.image.fill((self.color))
        self.image = self.image.convert()
        
    def turnleft(self):
        self.angle += self.turnspeed
        
    def turnright(self):
        self.angle -= self.turnspeed
        
    def forward(self):
        self.ddx = -math.sin(self.angle*GRAD) 
        self.ddy = -math.cos(self.angle*GRAD) 
        
    def backward(self):
        self.ddx = +math.sin(self.angle*GRAD) 
        self.ddy = +math.cos(self.angle*GRAD)  
        
    def straferight(self):
        self.ddx = +math.cos(self.angle*GRAD)
        self.ddy = -math.sin(self.angle*GRAD)
    
    def strafeleft(self):
        self.ddx = -math.cos(self.angle*GRAD) 
        self.ddy = +math.sin(self.angle*GRAD) 
        
    def turn_to_heading(self):
        """rotate into direction of movement (dx,dy)"""
        self.angle = math.atan2(-self.dx, -self.dy)/math.pi*180.0 
        self.image = pygame.transform.rotozoom(self.image0,self.angle,1.0)
    
    def rotate(self):
          """rotate because changes in self.angle"""
          self.oldcenter = self.rect.center
          self.image = pygame.transform.rotate(self.image0, self.angle)
          self.rect = self.image.get_rect()
          self.rect.center = self.oldcenter
    
    def teleport_to_grid(self, gridx, gridy, stop_moving = True):
        """teleport instantly to the gridtile (gridx, gridy) if it is a valid gridtile"""
        if gridx < 0 or gridx > PygView.gridsx:
            return False
        if gridy < 0 or gridy > PygView.gridsy:
            return False
        if stop_moving:
            self.dx = 0
            self.dy = 0
        self.x, self.y =  PygView.grid_to_xy(gridx,gridy)
        
    def glide_to(self, targetx, targety, rotate=True, end_angle=False, target_time=False):
        """glide to position (x,y) using time of target_time (how many
           seconds in the future) (if given) or using self.speed"""
        self.targetx = targetx
        self.targety = targety
        # calculate distance
        self.target_time = target_time
        self.end_angle = end_angle
        distance = ( (self.targetx - self.x)**2 + (self.targety-self.y)**2 ) ** 0.5
        if not target_time:
            # calculate target_time using self.speed
            target_time = distance / self.speed
        elif target_time <= 0: # teleport
            self.x = targetx
            self.y = targety
            self.dx = 0
            self.dy = 0
            return
        else:
            self.speed = distance / target_time
        # calculate dx, dy using self.speed
        self.dx = ( targetx - self.x) / target_time
        self.dy = ( targety - self.y) / target_time
        if rotate:
            self.turn_to_heading()
        
    
    def glide_to_grid(self, gridx, gridy, rotate=True, end_angle=False, target_time=False):
        """glide with self.speed to gridtile(gridx, gridy).
           if time_in_seconds is given, ajust speed.
           if rotate is True, rotate into  heading"""
        if gridx < 0 or gridx > PygView.gridsx:
            return False
        if gridy < 0 or gridy > PygView.gridsy:
            return False
        # calculate endpoints
        self.targetx, self.targety = PygView.grid_to_xy(gridx,gridy)
        self.glide_to(self.targetx, self.targety, rotate=rotate, end_angle=end_angle, target_time=target_time)
        
        

    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        # --------- alive? ------
        if self.hitpoints < 1:
            self.kill()
        # ---- calculate new  position ----
        self.dx += self.ddx * self.speed
        self.dy += self.ddy * self.speed
        if abs(self.dx) > 0 : 
            self.dx *= self.friction  # make the Sprite slower over time
        if abs(self.dy) > 0 :
            self.dy *= self.friction
        self.x += self.dx * seconds
        self.y += self.dy * seconds
        # --- end of glide ? ---
        if self.target_time:
            self.target_time -= seconds
            if self.target_time <= -0.3:  # 0 makes a visible jump -0.3 seems to work better
                self.x = self.targetx
                self.y = self.targety
                self.dx = 0
                self.dy = 0
                self.targetx = None
                self.targety = None
                self.speed = self.oldspeed
                self.target_time = False
                if self.end_angle:
                    self.angle = self.end_angle
                    self.end_angle = False
                    self.rotate()
        # ---- reflect from screen border -----
        if self.x - self.width //2 < 0:
            self.x = self.width // 2
            self.dx *= -1 
        if self.y - self.height // 2 < 0:
            self.y = self.height // 2
            self.dy *= -1
        if self.x + self.width //2 > PygView.width:
            self.x = PygView.width - self.width //2
            self.dx *= -1
        if self.y + self.height //2 > PygView.height:
            self.y = PygView.height - self.height //2
            self.dy *= -1
        # ----- update sprite rect ----
        self.rect.centerx = round(self.x, 0)
        self.rect.centery = round(self.y, 0)
        # ---- paint trail ----
        if self.trail:
            if len(self.oldposlist) > self.trail_max_length:
                self.oldposlist.pop(0) # remove first item
            self.oldposlist.append((self.x, self.y)) 
        


class Hitpointbar(pygame.sprite.Sprite):
        """shows a bar with the hitpoints of a Boss sprite
        Boss needs a unique number in FlyingObject.numbers,
        self.hitpoints and self.hitpointsfull"""
    
        def __init__(self, bossnumber, height=7, color = (0,255,0), ydistance=10):
            pygame.sprite.Sprite.__init__(self,self.groups)
            self.bossnumber = bossnumber # lookup in Flyingobject.numbers
            self.boss = FlyingObject.numbers[self.bossnumber]
            self.height = height
            self.color = color
            self.ydistance = ydistance
            self.image = pygame.Surface((self.boss.rect.width,self.height))
            self.image.set_colorkey((0,0,0)) # black transparent
            pygame.draw.rect(self.image, self.color, (0,0,self.boss.rect.width,self.height),1)
            self.rect = self.image.get_rect()
            self.oldpercent = 0
            
            
        def update(self, time):
            self.rect.centerx = self.boss.rect.centerx
            self.rect.centery = self.boss.rect.centery - self.boss.rect.height //2 - self.ydistance
            self.percent = self.boss.hitpoints / self.boss.hitpointsfull * 1.0
            if self.percent != self.oldpercent:
                pygame.draw.rect(self.image, (0,0,0), (1,1,self.boss.rect.width-2,self.height-2)) # fill black
                pygame.draw.rect(self.image, (0,255,0), (1,1,
                    int(self.boss.rect.width * self.percent),self.height-2),0) # fill green
            self.oldpercent = self.percent
            #check if boss is still alive
            if self.bossnumber not in FlyingObject.numbers:
                self.kill() # kill the hitbar


class Ball(FlyingObject):
    """a big pygame Sprite with high mass"""
        
    def init2(self):
        self.mass = 150
        checked = False
        self.dx = random.random() * 100 - 50
        self.dy = random.random() * 100 - 50
        Hitpointbar(self.number)
        
    def create_image(self):
        self.image = pygame.Surface((self.width,self.height))    
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius) # draw blue filled circle on ball surface
        pygame.draw.circle (self.image, (0,0,200) , (self.radius //2 , self.radius //2), self.radius// 3)         # left blue eye
        pygame.draw.circle (self.image, (255,255,0) , (3 * self.radius //2  , self.radius //2), self.radius// 3)  # right yellow yey
        pygame.draw.arc(self.image, (32,32,32), (self.radius //2, self.radius, self.radius, self.radius//2), math.pi, 2*math.pi, 1) # grey mouth
        self.image.set_colorkey((0,0,0))
        self.image = self.image.convert_alpha() # faster blitting with transparent color
        self.rect= self.image.get_rect()
        
class Bullet(FlyingObject):
    """a small Sprite with mass"""

    def init2(self):
        self.mass = 5
        self.lifetime = 8.5 # seconds

    def update(self, seconds):
        super(Bullet,self).update(seconds)
        self.lifetime -= seconds # aging
        if self.lifetime < 0:
            self.kill() 
        
    def create_image(self):
        self.image = pygame.Surface((self.width,self.height))    
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius) # draw blue filled circle on ball surface
        self.image.set_colorkey((0,0,0))
        self.image = self.image.convert_alpha() # faster blitting with transparent color
        self.rect= self.image.get_rect()
        
class Tux(FlyingObject):
    """player-controlled character with relative movement"""
        
    def init2(self):
        self.friction = 0.992 # slow down self-movement over time
        self.hitpoints = 200
        self.mass = 50
        self.damage = 1
        self.radius = 16 # image is 32x36 pixel
        Hitpointbar(self.number)
        
    def create_image(self):
        self.image = PygView.images[self.imagenr]
        self.image0 = PygView.images[self.imagenr]
        self.width = self.image.get_rect().width
        self.height = self.image.get_rect().height
                
    def update(self, seconds):
          super(Tux,self).update(seconds)
          #self.turn_to_heading() # use for non-controlled missles etc.
          self.rotate()        # use for player-controlled objects

            
            
class PygView(object):
    images = []
    
    def __init__(self, width=640, height=400, fps=30, grid=50):
        """Initialize pygame, window, background, font,..."""
        pygame.init()
        pygame.display.set_caption("Press ESC to quit")
        PygView.width = width    # make global readable
        PygView.height = height
        PygView.grid = grid
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.background = pygame.Surface(self.screen.get_size()).convert()  
        self.background.fill((255,255,255)) # fill background white
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.playtime = 0.0
        #self.font = pygame.font.SysFont('mono', 24, bold=True)
        self.loadresources() # loadresources calls paintgrid
        
    def paintgrid(self, centercolor=(255,0,0), bordercolor=(0,255,0)):
        PygView.gridsx = self.width // self.grid   # how many grids exist in x dimension
        PygView.gridsy = self.height // self.grid  # how many grids exist in y dimension
        PygView.restx = int(self.width % self.grid)  # area not filled with grids in the x dimension
        PygView.resty = int(self.height % self.grid) # area not filled with grids in the y dimension
        print("restx, resty", self.restx, self.resty, self.gridsx, self.gridsy)
        # border 
        for x in range(self.restx//2, self.width, self.grid):
            pygame.draw.line(self.background, bordercolor, (x,0), (x, self.height))
        for y in range(self.resty//2, self.height, self.grid):
            pygame.draw.line(self.background, bordercolor, (0,y), (self.width, y))
        # center
        for x in range(self.restx//2 + self.grid//2, self.width, self.grid):
            pygame.draw.line(self.background, centercolor, (x,0), (x, self.height))
        
        for y in range(self.resty//2 + self.grid//2, self.height, self.grid):
            pygame.draw.line(self.background, centercolor, (0,y), (self.width, y))
        
    @staticmethod        
    def grid_to_xy(gridx, gridy):
        """get center (x,y) coordinate of grid tile (gridx, gridy)"""
        return (PygView.restx//2 + PygView.grid//2 + PygView.grid * gridx,
                PygView.resty//2 + PygView.grid//2 + PygView.grid * gridy)
    
    @staticmethod
    def xy_to_grid(x,y):
        """get center coordinate (gridx, gridy) of nearest grid tile if given a point(x,y)
           return False if x,y is outside a valid grid tile """
        if  x < PygView.restx//2 or x > PygView.restx//2 + PygView.gridsx * PygView.grid:
            return False
        if y <  PygView.resty//2 or y > PygView.resty//2 + PygView.gridsy * PygView.grid:
            return False
        return ( (x - PygView.restx//2)% PygView.grid, (y - PygView.resty//2)% PygView.grid )
        
        
    def loadresources(self):
        """painting on the surface (once) and create sprites"""
        # make an interesting background 
        draw_examples(self.background) # background artwork
        try:  # ----------- load sprite images -----------
            tile = pygame.image.load(os.path.join("data", "startile-300px.png"))
            PygView.images.append(pygame.image.load(os.path.join("data", "babytux.png"))) # index 0
            
            # load other resources here
        except:
            print("pygame error:", pygame.get_error())
            print("please make sure there is a subfolder 'data' with the resource files in it")
            pygame.quit()
            sys.exit()
        # fill background with tiles
        self.background = fill_surface_with_tiles(tile, self.width, self.height)
        # write text
        # -------  write text over everything  -----------------
        write(self.background, "Press b to add another ball", x=self.width//2, y=250, center=True)
        write(self.background, "Press c to add another bullet", x=self.width//2, y=275, center=True)
        write(self.background, "Press w,a,s,d and q,e to steer tux", x=self.width//2, y=300, center=True)
        write(self.background, "Press space to fire from tux", x=self.width//2, y=325, center=True)
            
        self.paintgrid()
        # -------  create (pygame) Sprites Groups and Sprites -------------
        self.allgroup =  pygame.sprite.LayeredUpdates() # for drawing
        self.ballgroup = pygame.sprite.Group()          # for collision detection etc.
        self.hitpointbargroup = pygame.sprite.Group()
        self.bulletgroup = pygame.sprite.Group()
        self.tuxgroup = pygame.sprite.Group()
        # ----- assign Sprite class to sprite Groups ------- 
        Tux.groups = self.allgroup, self.tuxgroup
        Hitpointbar.groups = self.hitpointbargroup
        Ball.groups = self.allgroup, self.ballgroup # each Ball object belong to those groups
        Bullet.groups = self.allgroup, self.bulletgroup
        self.ball1 = Ball(x=100, y=100, radius = 10, trail=True) # creating a Ball Sprite
        self.ball2 = Ball(x=200, y=100, radius = 20, trail=True) # create another Ball Sprite
        self.tux1 = Tux(x=400, y=200, dx=0, dy=0, layer=5, imagenr = 0, trail=True) # over balls layer
        

    def run(self):
        """The mainloop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False 
                elif event.type == pygame.KEYDOWN: 
                    # ------- press and release key handler -------
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_b:
                        Ball(x=random.randint(0,PygView.width-100)) # add big balls!
                    if event.key == pygame.K_c:
                        Bullet(radius=5, x=0,y=0, dx=200, dy=200, color=(255,0,0))
                    if event.key == pygame.K_RIGHT:
                        self.tux1.glide_to_grid(9,2, target_time=1.5)
                        
                    if event.key == pygame.K_SPACE: # fire forward from tux1 with 300 speed
                        Bullet(radius=5, x=self.tux1.x, y=self.tux1.y,
                               dx=-math.sin(self.tux1.angle*GRAD)*300,
                               dy=-math.cos(self.tux1.angle*GRAD)*300,
                               bossnumber=self.tux1.number,
                               color = (0,0,255))         
                    if event.key == pygame.K_RETURN:
                        self.tux1.dx = 0
                        self.tux1.dy = 0
            # ------ pressed keys key handler ------------
            pressedkeys = pygame.key.get_pressed()
            self.tux1.ddx = 0 # reset movement
            self.tux1.ddy = 0 
            if pressedkeys[pygame.K_w]: # forward
                 self.tux1.forward()
            if pressedkeys[pygame.K_s]: # backward
                 self.tux1.backward()
            if pressedkeys[pygame.K_a]: # turn left
                self.tux1.turnleft()
            if pressedkeys[pygame.K_d]: # turn right
                self.tux1.turnright()
            if pressedkeys[pygame.K_e]: # strafe right
                self.tux1.straferight()
            if pressedkeys[pygame.K_q]: # strafe left
                self.tux1.strafeleft()
            # ------ clock ----------
            milliseconds = self.clock.tick(self.fps) 
            seconds = milliseconds / 1000
            self.playtime += seconds
            self.screen.blit(self.background, (0, 0))  # clear screen
            # write text below sprites
            write(self.screen, "FPS: {:6.3}  PLAYTIME: {:6.3} SECONDS".format(
                           self.clock.get_fps(), self.playtime))
            # write in window title
            pygame.display.set_caption("tux1: x {:.2f} y {:.2f} dx {:.2f} dy {:.2f} ddx {:.2f} ddy {:.2f} ".format(self.tux1.x, self.tux1.y, self.tux1.dx, self.tux1.dy, self.tux1.ddx, self.tux1.ddy))
            # -------- collision detection ---------
            # you can use: pygame.sprite.collide_rect, pygame.sprite.collide_circle, pygame.sprite.collide_mask
            # the False means the colliding sprite is not killed
            # ---------- collision detection between ball and bullet sprites ---------
            for ball in self.ballgroup:
               crashgroup = pygame.sprite.spritecollide(ball, self.bulletgroup, False, pygame.sprite.collide_circle)
               for bullet in crashgroup:
                   elastic_collision(ball, bullet) # change dx and dy of both sprites
                   ball.hitpoints -= bullet.damage
                   ball.target_time = False
                   ball.speed = ball.oldspeed
            # --------- collision detection between ball and other balls
            for ball in self.ballgroup:
                crashgroup = pygame.sprite.spritecollide(ball, self.ballgroup, False, pygame.sprite.collide_circle)
                for otherball in crashgroup:
                    if ball.number > otherball.number:     # make sure no self-collision or calculating collision twice
                        elastic_collision(ball, otherball) # change dx and dy of both sprites
                        ball.target_time = False
                        ball.speed = ball.oldspeed
            # ---------- collision detection between bullet and other bullets
            for bullet in self.bulletgroup:
                crashgroup = pygame.sprite.spritecollide(bullet, self.bulletgroup, False, pygame.sprite.collide_circle)
                for otherbullet in crashgroup:
                    if bullet.number > otherbullet.number:
                         elastic_collision(bullet, otherball) # change dx and dy of both sprites
            # --------- collision detection between Tux and balls
            for tux in self.tuxgroup:
                crashgroup = pygame.sprite.spritecollide(tux, self.ballgroup, False, pygame.sprite.collide_circle)
                for otherball in crashgroup:
                    elastic_collision(tux, otherball)
                    tux.hitpoints -= otherball.damage
                    otherball.hitpoints -= tux.damage
                    otherball.target_time = False
                    otherball.speed = otherball.oldspeed
                    tux.target_time = False
                    tux.speed = tux.oldspeed
            # ------------ collision detection between Tux and bullets
            for tux in self.tuxgroup:
                crashgroup = pygame.sprite.spritecollide(tux, self.bulletgroup, False, pygame.sprite.collide_circle)
                for otherbullet in crashgroup:
                    # tux is not damaged by his own bullets
                    if otherbullet.bossnumber != tux.number:
                        elastic_collision(tux, otherbullet)
                        tux.hitpoints -= otherbullet.damage
                        tux.target_time = False
                        tux.speed = tux.oldspeed
                        otherbullet.kill()                        
            # ----------- paint trails ----------
            for thing in self.allgroup:
                if thing.trail:
                    e = enumerate(thing.oldposlist) # ( number, (pos))
                    for epos in e:
                        if epos[0] > 0:
                            pygame.draw.line(self.screen,
                                             (thing.color[0], thing.color[1], int(epos[0] * 255/thing.trail_max_length)),
                                             oldpos, epos[1], epos[0]//100+4) # TODO trailwidth dependent from trail_start_width
                        oldpos = epos[1]
            # ----------- clear, draw , update, flip -----------------  
            #self.allgroup.clear(screen, background)
            self.allgroup.update(seconds) # would also work with ballgroup
            self.hitpointbargroup.update(seconds) # to avoid "bouncing" hitpointbars
            self.allgroup.draw(self.screen)      
            self.hitpointbargroup.draw(self.screen)     
            
            # --------- next frame ---------------
            pygame.display.flip()
        pygame.quit()

if __name__ == '__main__':
    # try PygView(800,600).run()
    PygView().run() 
