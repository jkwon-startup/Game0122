"""
🍔 먹방 게임 (Mukbang Game) - Pygame 버전
==========================================

실행 방법:
1. Python 3.x 설치 확인
2. pygame 설치: pip install pygame
3. 실행: python mukbang_game_pygame.py

조작법:
- ← → 방향키 또는 A, D 키로 이동
- 스페이스바로 게임 시작/재시작
"""

import pygame
import random
import sys

# ============================================
# 🎮 게임 설정 상수
# ============================================

# 화면 설정
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# 플레이어 설정
PLAYER_SIZE = 50
PLAYER_SPEED = 8

# 아이템 설정
ITEM_SIZE = 40
SPAWN_INTERVAL = 800  # ms (0.8초)
GAME_TIME = 60  # 초

# 색상 설정 (RGB)
COLORS = {
    'background': (26, 26, 46),
    'ground': (22, 33, 62),
    'text': (255, 255, 255),
    'score': (255, 215, 0),
    'life': (255, 107, 107),
    'time': (78, 205, 196),
    'button': (100, 100, 200),
    'button_border': (150, 150, 255)
}

# 아이템 정의 (이모지 대신 텍스트와 색상 사용)
ITEM_TYPES = {
    'pizza':   {'symbol': 'P', 'color': (255, 200, 100), 'score': 10,  'probability': 40, 'speed': 3},
    'burger':  {'symbol': 'B', 'color': (200, 150, 100), 'score': 20,  'probability': 30, 'speed': 4},
    'chicken': {'symbol': 'C', 'color': (255, 180, 120), 'score': 30,  'probability': 20, 'speed': 5},
    'star':    {'symbol': '★', 'color': (255, 255, 0),   'score': 100, 'probability': 5,  'speed': 6},
    'bomb':    {'symbol': 'X', 'color': (100, 100, 100), 'score': -1,  'probability': 5,  'speed': 4}
}

# 등급 시스템
GRADES = [
    {'min': 500, 'grade': '👑', 'title': '전설의 대식가', 'message': '먹방의 신이 강림했다!'},
    {'min': 300, 'grade': '🥇', 'title': '먹방 스타', 'message': '대단해!'},
    {'min': 100, 'grade': '🥈', 'title': '먹방 유망주', 'message': '제법인데?'},
    {'min': 0,   'grade': '🥉', 'title': '배고픈 초보', 'message': '더 열심히 먹어보자!'}
]


# ============================================
# 🎮 게임 클래스
# ============================================

class Player:
    """플레이어 클래스"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
    
    def move(self, direction):
        """플레이어 이동"""
        self.x += direction * self.speed
        # 화면 경계 처리
        self.x = max(self.size // 2, min(SCREEN_WIDTH - self.size // 2, self.x))
    
    def draw(self, screen, font):
        """플레이어 그리기"""
        # 캐릭터 (원형 얼굴)
        pygame.draw.circle(screen, (255, 220, 150), (self.x, self.y), self.size // 2)
        pygame.draw.circle(screen, (0, 0, 0), (self.x, self.y), self.size // 2, 2)
        
        # 눈
        pygame.draw.circle(screen, (0, 0, 0), (self.x - 10, self.y - 5), 5)
        pygame.draw.circle(screen, (0, 0, 0), (self.x + 10, self.y - 5), 5)
        
        # 입 (웃는 모양)
        pygame.draw.arc(screen, (0, 0, 0), 
                       (self.x - 15, self.y - 5, 30, 25), 
                       3.14, 0, 3)
        
        # 플랫폼
        pygame.draw.rect(screen, (100, 100, 150), 
                        (self.x - 30, self.y + self.size // 2, 60, 10),
                        border_radius=5)
    
    def get_rect(self):
        """충돌 감지용 사각형"""
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size
        )


class Item:
    """떨어지는 아이템 클래스"""
    def __init__(self, x, item_type):
        self.x = x
        self.y = -ITEM_SIZE
        self.size = ITEM_SIZE
        self.type = item_type
        self.data = ITEM_TYPES[item_type]
        self.speed = self.data['speed']
    
    def update(self):
        """아이템 위치 업데이트"""
        self.y += self.speed
    
    def draw(self, screen, font):
        """아이템 그리기"""
        color = self.data['color']
        symbol = self.data['symbol']
        
        # 아이템 배경 (원)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size // 2)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size // 2, 2)
        
        # 심볼 텍스트
        text = font.render(symbol, True, (50, 50, 50))
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)
    
    def get_rect(self):
        """충돌 감지용 사각형"""
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size
        )
    
    def is_off_screen(self):
        """화면 밖으로 나갔는지 확인"""
        return self.y > SCREEN_HEIGHT + self.size


class Game:
    """메인 게임 클래스"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('🍔 먹방 게임 - Pygame')
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # 폰트 설정
        try:
            # 시스템 폰트 사용 시도
            self.font_large = pygame.font.SysFont('malgungothic', 48)
            self.font_medium = pygame.font.SysFont('malgungothic', 24)
            self.font_small = pygame.font.SysFont('malgungothic', 18)
            self.font_symbol = pygame.font.SysFont('segoeuisymbol', 24)
        except:
            # 기본 폰트
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
            self.font_symbol = pygame.font.Font(None, 24)
        
        self.reset_game()
    
    def reset_game(self):
        """게임 초기화"""
        self.state = 'start'  # 'start', 'playing', 'gameover'
        self.score = 0
        self.life = 3
        self.time_left = GAME_TIME
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        self.items = []
        self.last_spawn_time = pygame.time.get_ticks()
        self.last_second_time = pygame.time.get_ticks()
    
    def get_random_item_type(self):
        """확률 기반 랜덤 아이템 타입 반환"""
        rand = random.randint(1, 100)
        cumulative = 0
        
        for item_type, data in ITEM_TYPES.items():
            cumulative += data['probability']
            if rand <= cumulative:
                return item_type
        
        return 'pizza'
    
    def spawn_item(self):
        """새 아이템 생성"""
        item_type = self.get_random_item_type()
        x = random.randint(ITEM_SIZE, SCREEN_WIDTH - ITEM_SIZE)
        self.items.append(Item(x, item_type))
    
    def get_grade(self):
        """점수에 따른 등급 반환"""
        for grade in GRADES:
            if self.score >= grade['min']:
                return grade
        return GRADES[-1]
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state in ['start', 'gameover']:
                        self.reset_game()
                        self.state = 'playing'
                
                if event.key == pygame.K_ESCAPE:
                    return False
        
        return True
    
    def update(self):
        """게임 상태 업데이트"""
        if self.state != 'playing':
            return
        
        # 키보드 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-1)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(1)
        
        current_time = pygame.time.get_ticks()
        
        # 타이머 업데이트
        if current_time - self.last_second_time >= 1000:
            self.time_left -= 1
            self.last_second_time = current_time
            if self.time_left <= 0:
                self.state = 'gameover'
                return
        
        # 아이템 생성
        if current_time - self.last_spawn_time >= SPAWN_INTERVAL:
            self.spawn_item()
            self.last_spawn_time = current_time
        
        # 아이템 업데이트 및 충돌 감지
        player_rect = self.player.get_rect()
        
        for item in self.items[:]:
            item.update()
            
            # 충돌 감지
            if player_rect.colliderect(item.get_rect()):
                if item.type == 'bomb':
                    self.life -= 1
                    if self.life <= 0:
                        self.state = 'gameover'
                        return
                else:
                    self.score += item.data['score']
                self.items.remove(item)
                continue
            
            # 화면 밖 아이템 삭제
            if item.is_off_screen():
                self.items.remove(item)
    
    def draw_start_screen(self):
        """시작 화면 그리기"""
        self.screen.fill(COLORS['background'])
        
        # 타이틀
        title = self.font_large.render('먹방 게임', True, COLORS['score'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # 부제목
        subtitle = self.font_small.render('음식을 먹고 폭탄을 피해라!', True, COLORS['text'])
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 50))
        self.screen.blit(subtitle, subtitle_rect)
        
        # 시작 버튼
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT // 2, 180, 50)
        pygame.draw.rect(self.screen, COLORS['button'], btn_rect, border_radius=25)
        pygame.draw.rect(self.screen, COLORS['button_border'], btn_rect, 3, border_radius=25)
        
        btn_text = self.font_medium.render('SPACE로 시작', True, COLORS['text'])
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)
        
        # 조작법
        control = self.font_small.render('조작: 방향키 또는 A, D', True, (150, 150, 150))
        control_rect = control.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(control, control_rect)
        
        # 아이템 설명
        items_info = self.font_small.render('P:+10  B:+20  C:+30  ★:+100  X:목숨-1', True, (150, 150, 150))
        items_rect = items_info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(items_info, items_rect)
    
    def draw_game(self):
        """게임 화면 그리기"""
        self.screen.fill(COLORS['background'])
        
        # 바닥
        pygame.draw.rect(self.screen, COLORS['ground'], 
                        (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        
        # 아이템 그리기
        for item in self.items:
            item.draw(self.screen, self.font_symbol)
        
        # 플레이어 그리기
        self.player.draw(self.screen, self.font_medium)
        
        # HUD 그리기
        self.draw_hud()
    
    def draw_hud(self):
        """HUD 그리기"""
        # HUD 배경
        hud_surface = pygame.Surface((SCREEN_WIDTH, 50))
        hud_surface.set_alpha(200)
        hud_surface.fill((0, 0, 0))
        self.screen.blit(hud_surface, (0, 0))
        
        # 시간
        time_text = self.font_small.render(f'Time: {self.time_left}s', True, COLORS['time'])
        self.screen.blit(time_text, (15, 15))
        
        # 점수
        score_text = self.font_small.render(f'Score: {self.score}', True, COLORS['score'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 25))
        self.screen.blit(score_text, score_rect)
        
        # 목숨
        life_text = '♥' * self.life + '♡' * (3 - self.life)
        life_render = self.font_small.render(f'Life: {life_text}', True, COLORS['life'])
        life_rect = life_render.get_rect(right=SCREEN_WIDTH - 15, centery=25)
        self.screen.blit(life_render, life_rect)
    
    def draw_gameover_screen(self):
        """게임 오버 화면 그리기"""
        # 기존 게임 화면 위에 오버레이
        self.draw_game()
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        grade = self.get_grade()
        
        # GAME OVER
        gameover_text = self.font_large.render('GAME OVER', True, (255, 100, 100))
        gameover_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.screen.blit(gameover_text, gameover_rect)
        
        # 등급 칭호
        title_text = self.font_medium.render(grade['title'], True, COLORS['score'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(title_text, title_rect)
        
        # 점수
        score_text = self.font_medium.render(f'최종 점수: {self.score}점', True, COLORS['text'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(score_text, score_rect)
        
        # 메시지
        msg_text = self.font_small.render(f'"{grade["message"]}"', True, (200, 200, 200))
        msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(msg_text, msg_rect)
        
        # 재시작 버튼
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 140, 180, 50)
        pygame.draw.rect(self.screen, COLORS['button'], btn_rect, border_radius=25)
        pygame.draw.rect(self.screen, COLORS['button_border'], btn_rect, 3, border_radius=25)
        
        btn_text = self.font_medium.render('SPACE로 재시작', True, COLORS['text'])
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)
    
    def draw(self):
        """화면 그리기"""
        if self.state == 'start':
            self.draw_start_screen()
        elif self.state == 'playing':
            self.draw_game()
        elif self.state == 'gameover':
            self.draw_gameover_screen()
        
        pygame.display.flip()
    
    def run(self):
        """게임 메인 루프"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


# ============================================
# 🚀 메인 실행
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🍔 먹방 게임 (Mukbang Game) - Pygame 버전")
    print("=" * 50)
    print("\n조작법:")
    print("  - ← → 방향키 또는 A, D: 이동")
    print("  - SPACE: 게임 시작/재시작")
    print("  - ESC: 종료")
    print("\n아이템:")
    print("  - P(피자): +10점")
    print("  - B(버거): +20점")
    print("  - C(치킨): +30점")
    print("  - ★(스타): +100점")
    print("  - X(폭탄): 목숨 -1")
    print("\n" + "=" * 50)
    print("게임을 시작합니다...")
    print("=" * 50 + "\n")
    
    game = Game()
    game.run()
