import random
import sys
import pygame
import os
import glob

# --- Configurações ---
WIDTH = 480
HEIGHT = 640
FPS = 60
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 6
BLOCK_MIN_SIZE = 20
BLOCK_MAX_SIZE = 80
BLOCK_MIN_SPEED = 3
BLOCK_MAX_SPEED = 8
SPAWN_INTERVAL = 700  # ms
FONT_NAME = None
BACKGROUND_SCROLL_SPEED = 1.8  # pixels por frame base

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 40, 40)
GREEN = (40, 200, 40)
BLUE = (50, 120, 220)
GRAY = (30, 30, 30)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image=None):
        super().__init__()
        # Se foi fornecida uma imagem (Surface), redimensionar e usar
        if image:
            try:
                surf = pygame.transform.smoothscale(image, (PLAYER_WIDTH, PLAYER_HEIGHT))
                self.image = surf.convert_alpha()
            except Exception:
                image = None

        # Se não houver imagem válida, desenhar um triângulo simples (nave)
        if not image:
            self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
            # desenhar triângulo apontando para cima (ou para frente)
            p1 = (PLAYER_WIDTH // 2, 0)
            p2 = (0, PLAYER_HEIGHT)
            p3 = (PLAYER_WIDTH, PLAYER_HEIGHT)
            pygame.draw.polygon(self.image, BLUE, [p1, p2, p3])

        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED

    def update(self, *args):
        # Aceita args opcionais para compatibilidade com Group.update(keys)
        if args and args[0] is not None:
            keys = args[0]
        else:
            keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # Manter dentro da tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH


class Block(pygame.sprite.Sprite):
    def __init__(self, planet_images=None):
        super().__init__()
        w = random.randint(BLOCK_MIN_SIZE, BLOCK_MAX_SIZE)
        h = random.randint(BLOCK_MIN_SIZE, BLOCK_MAX_SIZE)

        # se houver imagens de planetas, escolher uma aleatória e redimensionar preservando alpha
        if planet_images:
            try:
                src = random.choice(planet_images)
                img = pygame.transform.smoothscale(src, (w, h))
                self.image = img.convert_alpha()
            except Exception:
                self.image = pygame.Surface((w, h))
                self.image.fill((random.randint(40, 240), random.randint(40, 240), random.randint(40, 240)))
        else:
            self.image = pygame.Surface((w, h))
            self.image.fill((random.randint(40, 240), random.randint(40, 240), random.randint(40, 240)))

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.speed = random.randint(BLOCK_MIN_SPEED, BLOCK_MAX_SPEED)

    def update(self, *args):
        # aceita args para compatibilidade com Group.update(keys)
        self.rect.y += self.speed
        # se sair da tela, mata o sprite
        if self.rect.top > HEIGHT:
            self.kill()


def draw_text(surf, text, size, x, y, color=WHITE, center=True):
    font = pygame.font.Font(FONT_NAME, size)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surf.blit(text_surf, text_rect)


def load_planet_images():
    """Carrega imagens de planetas em assets cujo nome começa com 'planet' seguido de dígitos.
    Retorna lista de Surfaces (podem estar vazias se nenhum asset encontrado).
    """
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    images = []
    if not os.path.isdir(assets_dir):
        return images

    pattern = os.path.join(assets_dir, '**', 'planet*.png')
    for path in glob.glob(pattern, recursive=True):
        basename = os.path.basename(path)
        name_no_ext = os.path.splitext(basename)[0]
        # aceitar nomes como planet0, planet00, planet01, planet10, etc. (sufixo dígitos)
        if name_no_ext.startswith('planet') and name_no_ext[len('planet'):].isdigit():
            try:
                img = pygame.image.load(path).convert_alpha()
                images.append(img)
            except Exception:
                pass
    return images


def main():
    pygame.init()
    pygame.mixer.init()

    # Carregar música de fundo
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets/sounds')
    bg_music_path = os.path.join(assets_dir, 'background.mp3')
    if os.path.isfile(bg_music_path):
        pygame.mixer.music.load(bg_music_path)
        pygame.mixer.music.set_volume(0.5)  # volume de 0.0 a 1.0
        pygame.mixer.music.play(-1)  # -1 = toca em loop infinito

    gameover_sound = None
    gameover_path = os.path.join(assets_dir, 'game-over.mp3')
    if os.path.isfile(gameover_path):
        gameover_sound = pygame.mixer.Sound(gameover_path)
        gameover_sound.set_volume(0.7)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dodge the Blocks")
    clock = pygame.time.Clock()

    # carregar imagens de planetas (se houver)
    planet_images = load_planet_images()

    # carregar background.jpg (procurar em assets/ e subpastas)
    bg_image = None
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        candidate = os.path.join(assets_dir, 'background.jpg')
        if os.path.isfile(candidate):
            bg_image = pygame.image.load(candidate).convert()
        else:
            for path in glob.glob(os.path.join(assets_dir, '**', 'background.jpg'), recursive=True):
                try:
                    bg_image = pygame.image.load(path).convert()
                    break
                except Exception:
                    bg_image = None
    except Exception:
        bg_image = None

    # se existe imagem de background, redimensionar para o tamanho da tela e preparar scroll
    if bg_image:
        try:
            bg_image = pygame.transform.smoothscale(bg_image, (WIDTH, HEIGHT))
        except Exception:
            bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
        bg_y1 = 0
        bg_y2 = -HEIGHT
    else:
        bg_y1 = bg_y2 = 0

    # carregar imagem da nave ship_K.png (se existir)
    ship_image = None
    try:
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        candidate = os.path.join(assets_dir, 'ship_K.png')
        if os.path.isfile(candidate):
            ship_image = pygame.image.load(candidate).convert_alpha()
        else:
            for path in glob.glob(os.path.join(assets_dir, '**', 'ship_K.png'), recursive=True):
                try:
                    ship_image = pygame.image.load(path).convert_alpha()
                    break
                except Exception:
                    ship_image = None
    except Exception:
        ship_image = None

    # Grupo de sprites
    all_sprites = pygame.sprite.Group()
    blocks = pygame.sprite.Group()

    player = Player(WIDTH // 2, HEIGHT - 50, image=ship_image)
    all_sprites.add(player)

    # score usa float para acumular corretamente com dt
    score = 0.0
    high_score = 0
    # sistema de níveis
    level = 1
    level_up_threshold = 100  # pontos necessários por nível
    level_message = ""
    level_message_timer = 0.0
    running = True
    game_over = False
    paused = False

    SPAWN_EVENT = pygame.USEREVENT + 1
    # usar variável para controlar o intervalo atual de spawn
    spawn_interval = SPAWN_INTERVAL
    pygame.time.set_timer(SPAWN_EVENT, spawn_interval)

    # Timer para aumentar dificuldade aos poucos
    difficulty_timer = 0

    while running:
        dt = clock.tick(FPS)
        difficulty_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == SPAWN_EVENT and not game_over and not paused:
                # cria um bloco
                b = Block(planet_images=planet_images)
                blocks.add(b)
                all_sprites.add(b)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # reinicia o jogo
                        for s in all_sprites:
                            s.kill()
                        all_sprites = pygame.sprite.Group()
                        blocks = pygame.sprite.Group()
                        player = Player(WIDTH // 2, HEIGHT - 50, image=ship_image)
                        all_sprites.add(player)
                        score = 0.0
                        level = 1
                        level_message = ""
                        level_message_timer = 0.0
                        game_over = False
                        spawn_interval = SPAWN_INTERVAL
                        pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
                    else:
                        paused = not paused

        keys = pygame.key.get_pressed()

        if not game_over and not paused:
            all_sprites.update(keys)

            # colisões: player com blocos
            if pygame.sprite.spritecollide(player, blocks, False):
                game_over = True
                if int(score) > high_score:
                    high_score = int(score)
                pygame.time.set_timer(SPAWN_EVENT, 0)

                # tocar som de game over
                if gameover_sound:
                    gameover_sound.play()
                # parar a música de fundo (opcional)
                pygame.mixer.music.stop()

            # incrementa pontuação conforme tempo (usar float para evitar truncamento)
            # usamos dt/100 para ter aproximadamente ~10 pontos por segundo
            score += dt / 100.0

            # aumenta o nível quando atingir threshold
            if int(score) >= level * level_up_threshold:
                level += 1
                level_message = f"Nível {level}!"
                level_message_timer = 1500  # em ms
                # ao subir de nível, aumentar dificuldade
                spawn_interval = max(200, spawn_interval - 60)
                pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
                for b in blocks:
                    b.speed += 1

            # aumentar dificuldade gradualmente: reduzir intervalo e aumentar velocidades (backup por tempo)
            if difficulty_timer > 5000:  # a cada 5s
                difficulty_timer = 0
                # diminuir intervalo de spawn até um mínimo
                spawn_interval = max(200, spawn_interval - 40)
                pygame.time.set_timer(SPAWN_EVENT, spawn_interval)
                # aumentar velocidades das classes Block existentes e futuras
                for b in blocks:
                    b.speed += 1

        # diminuir timers (fora do if para que o HUD mostre countdown mesmo pausado)
        if level_message_timer > 0:
            level_message_timer -= dt
            if level_message_timer <= 0:
                level_message = ""
                level_message_timer = 0

        # Desenho do background infinito
        if bg_image:
            # a velocidade do background aumenta levemente com o nível
            bg_speed = BACKGROUND_SCROLL_SPEED + max(0, (level - 1) * 0.3)
            # mover ambos os fundos
            bg_y1 += bg_speed
            bg_y2 += bg_speed
            # se um saiu totalmente da tela, reposicionar acima do outro
            if bg_y1 >= HEIGHT:
                bg_y1 = bg_y2 - HEIGHT
            if bg_y2 >= HEIGHT:
                bg_y2 = bg_y1 - HEIGHT
            # desenhar
            screen.blit(bg_image, (0, int(bg_y1)))
            screen.blit(bg_image, (0, int(bg_y2)))
        else:
            screen.fill(GRAY)

        all_sprites.draw(screen)

        # HUD
        draw_text(screen, f"Score: {int(score)}", 22, 8, 8, WHITE, center=False)
        draw_text(screen, f"High: {high_score}", 22, WIDTH - 8, 8, WHITE, center=False)
        draw_text(screen, f"Level: {level}", 22, WIDTH // 2, 8, WHITE, center=True)

        # mensagem de level
        if level_message:
            draw_text(screen, level_message, 36, WIDTH // 2, HEIGHT // 2 - 100, GREEN)

        if paused and not game_over:
            draw_text(screen, "PAUSADO", 48, WIDTH // 2, HEIGHT // 2, RED)
            draw_text(screen, "Pressione Espaço para continuar", 20, WIDTH // 2, HEIGHT // 2 + 40, WHITE)

        if game_over:
            draw_text(screen, "GAME OVER", 64, WIDTH // 2, HEIGHT // 2 - 30, RED)
            draw_text(screen, f"Pontuação: {int(score)}", 28, WIDTH // 2, HEIGHT // 2 + 20, WHITE)
            draw_text(screen, "Pressione Espaço para reiniciar", 20, WIDTH // 2, HEIGHT // 2 + 60, WHITE)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
