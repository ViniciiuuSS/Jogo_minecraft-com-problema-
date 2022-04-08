from __future__ import division
import sys 
import random
import time
from collections import deque
import pyglet
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse
import math


setor = 16
tick_rate = 60

velocidade_andar = 5
fly_speed = 15
jump = 1.0
gravidade = 20.0

velocidade_jump = math.sqrt(2 * gravidade * jump)
Terminal_velocidade = 50
altura_jogador = 2

if sys.version_info[0] >= 3:
    xrange = range

def cube_vertices(x,y,z,n):
    return[x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,
            x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,
            x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,
            x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,
            x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,
            x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,]

def tex_coord(x,y, n =4):
    m = 1.0 / n
    dx = x*m
    dy = y*m
    return dx, dy, dx+m, dy, dx+m, dy+m, dx, dy+m 
def tex_coords(top, buttom, side):
    top = tex_coord(*top)
    buttom = tex_coord(*buttom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(buttom)
    result.extend(side * 4)
    return result
textura = "texturas.png"

terra = tex_coords((1,0), (0,1), (0,0))
madeira = tex_coords((1,1), (1,1), (1,1))   
pedra = tex_coords((2,0), (2,0), (2,0))
tijolo = tex_coords((2,1), (2,1), (2,1))

faces = [
        (0, 1, 0),
        (0, -1, 0),
        (-1, 0, 0),
        (1, 0, 0),
        (0, 0, 1),
        (0, 0, -1)
]

def normalize(position):
    x,y,z = position
    x,y,z = (int(round(x)), int(round(y)),int(round(z)))
    return(x,y,z)

def sectorize(position):
    x,y,z = normalize(position)
    x,y,z = x // setor, y // setor, z // setor
    return(x,0,z)

class Model(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.group = TextureGroup(image.load(textura).get_texture())
        self.wold = {}

        self.shown = {}
        self._shown = {}
        self.sectors = {}

        self.queue = deque()
        self._initialize()
    def _initialize(self):
        n = 80
        s = 1
        y = 0
        for x in xrange(-n, n+1, s):
            for z in xrange(-n, n+1, s):
                self.add_block((x,y-2,z),terra, immediate = False) 
                self.add_block((x,y-3,z), pedra, immediate = False) 
                if x in (-n, n) or z in (-n,n):
                    for dy in xrange(-2,3):
                        self.add_block((x,y+dy,z), pedra, immediate=False)
        
        o = n - 10
        for _in in xrange(120):
            a = random.randint(-o, o)
            b = random.randint(-o, o)
            c = -1
            h = random.randint(1, 6)
            s = random.randint(4, 8)
            d = 1
            t = random.choice([terra, pedra, tijolo])
            for y in xrange(c, c+h):
                for x in xrange(a-s, a+s+1):
                    for z in xrange(b- s , b+s+1):
                        if (x-a)**2+(z-b)**2 > (s+1)**2:
                            continue
                        if (x-0)**2+(z-0)**2 < 5**2:
                            continue
                        self.add_block((x,y,z), t, immediate=False)
                s -=d

    def hit_test(self,position,vector,max_ditance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previus = None
        for _ in xrange(max_ditance * m):
            key = normalize((x,y,z))
            if key != previus and key in self.wold:
                return key, previus
            previus = key 
            x,y,z = x + dx/ m, y + dy / m, z + dz / m
        return None, None
    def exposed(self, position):
        x,y,z = position
        for dx, dy, dz in faces:
            if (x+dx, y+dy, z+dz) not in self.wold:
                return True
            return False
    
    def add_block(self,position, texture, immediate=True):
        if position in self.wold:
            self.remove_block(position, immediate)
        self.wold[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
                self.check_neighbors(position)

    def remove_block(self,position, immediate=True):
        del self.wold[position ]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
       
    def check_neighbors(self,position):
        x,y,z = position
        for dx, dy, dz in faces:
            key = (x+dx, y+dy, z+dz) 
            if key not in self.wold:
                continue
            if self.exposed(key):
                if key not in self.show:
                    self.show_block(key)
            else:
                if key in self.show:
                    self.hide_block(key)
    def show_block(self,position, immediate=True):
        texture = sefl.wold(position)
        self.show[position] = texture
        if immediate:
            self.show_block(position,texture)
        else:
            self._enqueue(self.show_block, position, texture)

    def _show_block(self,position, texture):
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        self.show[position] = self.batch.add(24, GL_QUADS, self.group, ('v3f/static', vertex_data), ('t2f/static'), texture_data)

    def hide_block(self,position, immediate=True):
        self.show.pop(position)
        if immediate:
            self.hide_block(position)
        else:
            self._enqueue(self.hide_block, position)

    def _hide_block(self,position):
        self.show.pop(position).delete()

    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.show and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.show :
                self.hide_block(position, False)
    
    def change_sectors(self,before, after):
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad+1):
            for dy in [0]:
                for dz in xrange(-pad, pad+1):
                    if dx**dy**2 + dz**2> (pad + 1) **2:
                        continue
                    if before:
                        x, y ,z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y ,z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.show_sector(sector)
    
    def _enqueue(self, func, *args):
        self.enqueue.append((func, args))
    def _dequeue(self):
        func, args = self.queue.popleft() 
        func(*args)
    def process_queue(self):
        start = time.clock(0)
        while self.queue and time.clock() - start < 1.0 / tick_rate:
            self._dequeue()
    def process_entire_queue(self):
        while self.queue:
            self.deque()

class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = False
        self.strafe = [0,0]
        self.position = (0,0,0)
        self.rotation = (0,0)
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.inventory = [terra, pedra, madeira, tijolo]
        self.block = self.inventory[0]
        self.num_keys = [
            key._1,key._2,key._3,key._4,key._5,key._6,key._7
        ]
        self.model = Model()
        self.label = pyglet.text.Label('', font_name = 'arial', font_size=18, x=10, y=self.height, anchor_x='left', anchor_y='top', color=(0,0,0,255))
        pyglet.clock.schedule_interval(self.update,1.0 / tick_rate)
    
    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

        x,y = self.rotation
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90))
        dz = math.sin(math.radians(x - 90 )) 
        return(dx,dy,dz)
    def _get_motion_vector(self):
        if any(self.strate):
            x,y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x+ strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                    dx = math.cos(x_angle) * m
                    dz = math.cos(x_angle) * m
            else:
                dy = 0
                dx = math.cos(x_angle) * m
                dz = math.cos(x_angle) * m
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return(dx,dy,dz)
    def update(self, dt):
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self.update(dt/m)
    
    def _update(self, dt):
        speed = fly_speed if self.flying else velocidade_andar
        d = dt * speed
        dx, dy, dz  = self._get_motion_vector()
        dx, dy,dz = dx* d, dy * d, dz*d
        if not self.flying:
            self.dy -= dt * gravidade
            self.dy = max(self.dy - Terminal_velocidade)
            dy += self.dy * dt
        x,y,z = self.position
        x,y,z = self.collide((x+dx, y+dy,z+dz), altura_jogador)
        self.position = (x,y,z)

    def collide(self,position,height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in faces:
            for i in xrange(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height):
                    op = list(np)
                    op[1] -=dyop[i] 
                    op[i] += face[i]
                    if tuple(op) not in self.model.wold:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0,-1,0) or face== (0,1,0):
                        self.dy = 0
                        break
                    return tuple(p)
    def on_mouse_press(self,x,y,buttom,modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previus = self.model.hit_test(self.position, vector)
            if (buttom == mouse.RIGHT) or ((buttom == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                if previus:
                    self.model.add_block(previus, self.block)
            elif buttom == pyglet.window.mouse.LEFT and block:
                texture = self.model.wold[block]
                if texture != pedra:
                    self.model.remove_block(block)
        else:
            self.set_exclusive_mouse(True)
    def on_mouse_motion(self,x,y,dx,dy):
        if self.exclusive:
            m = 0.15
            x,y = self.rotation
            x,y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x,y)
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[0] += 1
        elif symbol == key.D:
            self.strafe[0] -= 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = velocidade_jump
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
    def on_key_release(self,symbol,modifiers):
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
    def on_resize(self, width, height):
        self.label.y = height - 10
        if self.reticle:
            self.reticle.delete()
        x,y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,'v2i',(x,-n, y, x + n, y, x, y - n, x, y +n))
    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0,0,max(1, viewport[0],), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0,max(1,width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0,0,max(1, viewport[0],), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotaref(x,0,1,0)
        glRotaref(-y, math.cos(math.radians(x)), 0 , math.sin(math.radians(x)))
        x, y,z = self.position
        glTranslatef(-x,-y,-z)
    def on_draw(self):
        self.clear()
        self.set_3d()
        glColor3d(1,1,1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticule()
    def draw_focused_block(self):
        vector = self.get_sight_vector
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x,y,z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0,0,0)
            glPolygonMode(GL_FRONT_AND_BAKC, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BAKC, GL_FILL)
    def draw_label(self):
        x,y,z = self.position
        self.label.text = '%02d (%.2f,%.2f,%.2f,) %d / %d' % (pyglet.clock.get_fps(), x,y,z, len(self.model._shown), len(self.model.wold))
        self.label.draw()
    def draw_reticule(self):
        glColor3d(0,0,0)
        self.reticle.draw(GL_LINES)
def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (glfloat*4)(0.5,0.69,1.0,1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)
def setup():
    glClearColor(0.5,0.69,1.0,1)
    glEnable(GL_CULL_FACE)
    glTextParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTextParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
def main():
    window = Window(width=800, height=600, caption="pyglet", resizable=True)
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()
if __name__== '__main__':
    main()

