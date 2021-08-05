import pygame, sys, math, random, time

from pygame import Vector2, sprite
from pygame import mixer
from pygame.draw import rect

global dt

pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Buckshot")
favicon = pygame.image.load("data/images/Player.png")
pygame.display.set_icon(favicon)

is_menu = True

class Explosion():
    global dt
    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.width = 20

    def draw(self, screen):
        pygame.draw.circle(screen, (220, 0, 0), self.position, self.width)
        pygame.draw.circle(screen, (255, 153, 51), self.position, self.width - (self.width / 2))
    
    def scale_down(self):
        if(self.width > 0):
            self.width -= dt * 50


class Gun():
    def __init__(self):
        self.gun_sprite = None
        self.position = Vector2()
        self.is_flipped = False
        self.bullet_count = 3
        pygame.font.init()
        self.font = pygame.font.Font("data/fonts/Montserrat-ExtraBold.ttf", 300)
        self.position = pygame.Vector2()
        self.refresh_sprite()
        self.explosions = []

    def render_current_ammo(self, screen):
        text = self.font.render(str(self.bullet_count), False, (200,200,200))
        screen.blit(text, (300,200))
    
    def shoot(self):
        if(self.bullet_count > 0):
            sound = mixer.Sound("data/audio/Gunshot.wav")
            sound.set_volume(0.02)
            sound.play()
            exp_pos = Vector2()
            exp_pos.x = self.position.x
            exp_pos.y = self.position.y
            mouse_x, mouse_y = pygame.mouse.get_pos()
            rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
            mag = Vector2(rel_x, rel_y).magnitude()
            exp_pos.x += (rel_x / mag) * 100
            exp_pos.y += (rel_y / mag) * 100
            explosion = Explosion(exp_pos)
            self.explosions.append(explosion)
            self.bullet_count -= 1
        else:
            sound = mixer.Sound("data/audio/CantShoot.wav")
            sound.set_volume(0.08)
            sound.play()

    def explode(self, screen):
        for i in range(len(self.explosions)):
            if(self.explosions[i].width <= 1):
                self.explosions.remove(self.explosions[i])
                break
            self.explosions[i].scale_down()
            self.explosions[i].draw(screen)

    def refresh_sprite(self):
        self.gun_sprite = pygame.image.load('data/images/Gun.png').convert_alpha()
        self.gun_sprite = pygame.transform.scale(self.gun_sprite, (200, 200))

    def draw(self, screen):
        screen.blit(self.gun_sprite, self.blit_position())
        self.explode(screen)

    def set_position(self, position):
        self.position = position
    
    def set_rotation(self, degrees):
        self.refresh_sprite()
        self.gun_sprite = pygame.transform.rotate(self.gun_sprite, degrees)
          
    def blit_position(self):
        return self.position.x - (self.gun_sprite.get_width() / 2), self.position.y - (self.gun_sprite.get_height() / 2)

class Player():
    global dt
    def __init__(self):
        self.is_dead = False
        self.score = 0
        self.position = pygame.Vector2()
        w, h = pygame.display.get_surface().get_size()
        self.position.xy = w / 2, h / 5
        self.velocity = pygame.Vector2()
        self.rotation = pygame.Vector2()
        self.offset = pygame.Vector2()
        self.gun = Gun()
        self.drag = 100
        self.gravity_scale = 300
        self.player_sprite = pygame.image.load('data/images/Player.png').convert_alpha()
        self.player_sprite = pygame.transform.scale(self.player_sprite, (50, 60))
        self.gun.set_position(self.position)

    def move(self):
        self.gravity()
        self.air_resistance()
        self.wall_detection()
        self.position.x -= self.velocity.x * dt
        self.position.y -= self.velocity.y * dt
    
    def handle_gun(self):
        self.gun.set_position(self.position)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        self.gun.set_rotation(angle)

        if(self.offset.x > 0):
            self.offset.x = rel_x if rel_x < 4 else 4
        else:
            self.offset.x = rel_x if rel_x > -4 else -4
        if(self.offset.y > 0):
            self.offset.y = rel_y if rel_y < 4 else 4
        else:
            self.offset.y = rel_y if rel_y > -4 else -4

    def wall_detection(self):
        if(self.position.x < 0):
            self.position.x = 800
        if(self.position.x > 800):
            self.position.x = 0

    def get_score(self):
        return self.score
        
    def gravity(self):
        self.velocity.y -= self.gravity_scale * dt

    def air_resistance(self):
        if(self.velocity.y > 0):
            self.velocity.y -= self.drag * dt
        if(self.velocity.x > 0):
            self.velocity.x -= (self.drag - 50) * dt
        else:
            self.velocity.x += (self.drag - 50) * dt

    def check_state(self):
        global is_menu
        if(self.is_dead):
            old_highscore_value = open("data/serialisation/highscore.csv", "r").readline()
            try:
                if(self.score > int(old_highscore_value)):
                    highscore_value = open("data/serialisation/highscore.csv", "w")
                    highscore_value.write(str(self.score))
                    highscore_value.close()
            except:
                pass
            is_menu = True

    def collision_detection(self, level_builder):
        for i in range(len(level_builder.refills)):
            other = level_builder.refills[i]
            if(self.get_left() < other.get_right() and self.get_right() > other.get_left() and self.get_top() < other.get_bottom() and self.get_bottom() > other.get_top()):
                self.gun.bullet_count += 1
                level_builder.populate_refill()
                self.score += 1

        for i in range(len(level_builder.enemies)):
            other = level_builder.enemies[i]
            if(self.get_left() < other.get_right() and self.get_right() > other.get_left() and self.get_top() < other.get_bottom() and self.get_bottom() > other.get_top()):
                self.is_dead = True
        if(self.position.y > 850):
            self.is_dead = True
    
    def get_right(self):
        return self.position.x + (self.player_sprite.get_width() / 2)

    def get_left(self):
        return self.position.x - (self.player_sprite.get_width() / 2)
    
    def get_top(self):
        return self.position.y - (self.player_sprite.get_height() / 2)
    
    def get_bottom(self):
        return self.position.y + (self.player_sprite.get_height() / 2)

    def draw(self, screen):
        self.gun.draw(screen)
        screen.blit(self.player_sprite, self.blit_position())
        pygame.draw.circle(screen, (0,0,0), (self.position.x - 14 + self.offset.x, self.position.y - 10 + self.offset.y), 4)
        pygame.draw.circle(screen, (0,0,0), (self.position.x + 4 + self.offset.x , self.position.y - 10 + self.offset.y ), 4)

    def blit_position(self):
        return (self.position.x - (self.player_sprite.get_width() / 2), self.position.y - (self.player_sprite.get_height() / 2))

    def shoot(self):
        if(self.gun.bullet_count <= 0):
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.position.x, mouse_y - self.position.y
        vector = Vector2()
        vector.xy = rel_x, rel_y
        mag = vector.magnitude()
        vector.xy /= mag
        self.velocity.y = 0
        self.velocity.x = 0
        self.add_force(vector, 500);

    def add_force(self, vector, magnitude):
        self.velocity.x += vector.x * magnitude
        self.velocity.y += vector.y * magnitude


class Refill:
    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.gun_sprite = pygame.image.load('data/images/Bullet.png').convert_alpha()
        self.gun_sprite = pygame.transform.scale(self.gun_sprite, (30, 40))

    def draw(self, screen):
        screen.blit(self.gun_sprite, self.position)
    
    def get_right(self):
        return self.position.x + 30

    def get_left(self):
        return self.position.x 
    
    def get_top(self):
        return self.position.y
    
    def get_bottom(self):
        return self.position.y + 40


#Anyone who snoops... Yes I know inheritance exists but I have 2 hours. Let me off.
class Enemy:
    global dt
    def __init__(self, position):
        self.position = Vector2()
        self.position.x = position.x
        self.position.y = position.y
        self.gravity_scale = random.randint(20, 40)

        self.xOffset = 0
        self.yOffset = 0
         
        rand = random.randint(0, 2)
        self.enemy_sprite = None

        if(rand == 0):
            self.enemy_sprite = pygame.image.load('data/images/Shell.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (40, 40))
            self.xOffset = 40
            self.yOffset = 40
        elif(rand == 1):
            self.enemy_sprite = pygame.image.load('data/images/Fish.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (30, 50))
            self.xOffset = 30
            self.yOffset = 50
        else:
            self.enemy_sprite = pygame.image.load('data/images/Bone.png').convert_alpha()
            self.enemy_sprite = pygame.transform.scale(self.enemy_sprite, (30, 50))
            self.xOffset = 30
            self.yOffset = 50
        

    def draw(self, screen):
        screen.blit(self.enemy_sprite, self.position)
        self.gravity()

    def gravity(self):
        self.position.y += self.gravity_scale * dt
    
    def get_right(self):
        return self.position.x + self.xOffset

    def get_left(self):
        return self.position.x - self.xOffset
    
    def get_top(self):
        return self.position.y - self.yOffset
    
    def get_bottom(self):
        return self.position.y + self.yOffset



class LevelBuilder:
    def __init__(self):
        self.refills = []
        self.enemies = []
    def populate_refill(self):
        self.refills = []
        sound = mixer.Sound("data/audio/Reload.wav")
        sound.set_volume(0.02)
        sound.play()
        for i in range(2):
            pos = Vector2()
            pos.x = random.randint(100, 700)
            pos.y = random.randint(100, 500)
            refill = Refill(pos)
            self.refills.append(refill)

    def spawn_enemies(self):
        rand = random.randint(0, 3)
        sound = mixer.Sound("data/audio/Spawn.wav")
        sound.set_volume(0.05)
        sound.play()
        for i in range(rand):
            random_pos = random.randint(0, 760)
            position = Vector2()
            position.x = random_pos
            position.y = -30
            enemy = Enemy(position)
            self.enemies.append(enemy)
        
            
    def draw(self, screen):
        for i in range(len(self.refills)):
            self.refills[i].draw(screen) 
        for i in range(len(self.enemies)):
            self.enemies[i].draw(screen)    
            if(self.enemies[i].position.y > 850):
                self.enemies.remove(self.enemies[i])

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.size = None
        self.width = None
        self.height = None
        self.background_color = 240, 240, 240
        self.player = Player()
        self.level_builder = LevelBuilder()
        self.clock = pygame.time.Clock()
        self.score = 0

        self.update()

    def update(self):
        global is_menu
        self.level_builder.populate_refill()
        next_time = time.time()
        elapsed_time = time.time()
        min_time = 5
        max_time = 10
        enemiy_iteration = 0
        while not is_menu:
            self.handle_dt()
            self.clear_screen()

            self.player.gun.render_current_ammo(screen)
            
            self.level_builder.draw(screen)
            self.level_builder.draw(screen)
            self.player.move()
            self.player.handle_gun()
            self.player.collision_detection(self.level_builder)
            self.player.check_state()
            self.player.draw(self.screen)

            self.score = self.player.get_score()

            pygame.display.flip()
            self.handle_events()


            elapsed_time = time.time()
            if(elapsed_time > next_time):
                next_time = elapsed_time + random.randint(min_time, max_time)
                self.level_builder.spawn_enemies()
                enemiy_iteration += 1
                if(enemiy_iteration > 5 and min_time > 1):
                    min_time -= 1
                    max_time -= 1
                    enemiy_iteration = 0

            
    def handle_events(self):
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.shoot()      
                    self.player.gun.shoot()        

    def clear_screen(self):
        self.screen.fill(self.background_color)

    def handle_dt(self):
        global dt
        dt = self.clock.tick() / 1000


class Menu():
    def __init__(self, screen):
        self.background_color = 240, 240, 240
        self.screen = screen
        self.update()

    def update(self):
        global is_menu
        pygame.font.init()
    
        sound = mixer.Sound("data/audio/Error.wav")
        sound.set_volume(0.05)
        sound.play()

        while is_menu:
            self.clear_screen()

            logo = pygame.image.load('data/images/Logo.png').convert_alpha()
            logo = pygame.transform.scale(logo, (100, 120))
            screen.blit(logo, (350, 60))

            self.font = pygame.font.Font("data/fonts/Montserrat-ExtraBold.ttf", 70)
            text = self.font.render("BuckShot", False, (100,100,100))
            screen.blit(text, (220, 180))

            self.font = pygame.font.Font("data/fonts/Montserrat-ExtraBold.ttf", 50)
            text = self.font.render("Click To Play", False, (200,200,200))
            screen.blit(text, (230,340 + (math.sin(time.time() * 10) * 5)))


            self.font = pygame.font.Font("data/fonts/Montserrat-ExtraBold.ttf", 30)
            highscore_value = open("data/serialisation/highscore.csv", "r").readline()
            highscore = self.font.render("Highscore: " + str(highscore_value), False, (180,180,180))
            screen.blit(highscore, (300,400 + (math.sin(time.time() * 10) * 5)))
            pygame.display.flip()
            self.handle_events()

    def clear_screen(self):
        self.screen.fill(self.background_color)
            
    def handle_events(self):
        global is_menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                is_menu = False
                

instance = None

mixer.init()
mixer.music.load("data/audio/music.mp3")
mixer.music.set_volume(0.01)
mixer.music.play(-1)

while(True):
    if(is_menu):
        instance = Menu(screen)
    else:
        instance = Game(screen)
    print(is_menu)
