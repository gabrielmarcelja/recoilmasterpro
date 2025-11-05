"""
Backend Interception completo
Motor principal do sistema
"""

import ctypes
from ctypes import *
import time
import threading
from pathlib import Path

from config.patterns import get_pattern
from core.humanizer import Humanizer
from core.stats import StatsTracker

# ========== STRUCTS ==========
class MouseStroke(Structure):
    _fields_ = [
        ("state", c_ushort),
        ("flags", c_ushort),
        ("rolling", c_short),
        ("x", c_int),
        ("y", c_int),
        ("information", c_uint)
    ]

# ========== CONSTANTES ==========
INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001
INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002
INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000

# ========== ENGINE ==========
class RecoilEngine:
    """Motor principal de controle de recoil"""
    
    def __init__(self, dll_path="interception.dll"):
        self.dll_path = dll_path
        self.context = None
        self.running = False
        self.active = False
        self.shooting = False
        self.current_shot = 0
        
        # Configurações
        self.sensitivity = 1.0
        self.current_weapon = 'rust_ak47'
        
        # Sistemas
        self.humanizer = Humanizer(enabled=True)
        self.stats = StatsTracker()
        
        # Timing
        self.last_shot_time = 0
        
        # Carregar DLL
        self.load_dll()
    
    def load_dll(self):
        """Carregar DLL do Interception"""
        try:
            self.dll = CDLL(self.dll_path)
            print(f"[✓] DLL carregada: {self.dll_path}")
            self.setup_functions()
            return True
        except Exception as e:
            print(f"[✗] Erro ao carregar DLL: {e}")
            return False
    
    def setup_functions(self):
        """Configurar funções da DLL"""
        # Create context
        self.dll.interception_create_context.restype = c_void_p
        
        # Destroy context
        self.dll.interception_destroy_context.argtypes = [c_void_p]
        
        # Set filter
        self.dll.interception_set_filter.argtypes = [c_void_p, c_void_p, c_ushort]
        
        # Wait
        self.dll.interception_wait.argtypes = [c_void_p]
        self.dll.interception_wait.restype = c_int
        
        # Receive
        self.dll.interception_receive.argtypes = [c_void_p, c_int, c_void_p, c_uint]
        self.dll.interception_receive.restype = c_int
        
        # Send
        self.dll.interception_send.argtypes = [c_void_p, c_int, c_void_p, c_uint]
        
        # Is mouse
        self.dll.interception_is_mouse.argtypes = [c_int]
        self.dll.interception_is_mouse.restype = c_int
    
    def initialize(self):
        """Inicializar contexto"""
        self.context = self.dll.interception_create_context()
        
        if not self.context:
            print("[✗] Falha ao criar contexto")
            return False
        
        print("[✓] Contexto criado")
        
        # Filtro: capturar todo input de mouse
        FILTER_MOUSE_ALL = 0xFFFF
        self.dll.interception_set_filter(
            self.context,
            self.dll.interception_is_mouse,
            FILTER_MOUSE_ALL
        )
        
        print("[✓] Filtro configurado")
        return True
    
    def apply_recoil(self):
        """Aplicar compensação de recoil"""
        pattern = get_pattern(self.current_weapon)['pattern']
        
        if self.current_shot >= len(pattern):
            return
        
        # Pegar offset do pattern
        x, y, delay = pattern[self.current_shot]
        
        # Humanização
        x = self.humanizer.jitter(x, 1)
        y = self.humanizer.jitter(y, 1)
        
        # Micro-correções aleatórias
        mx, my = self.humanizer.micro_correction(probability=0.12)
        x += mx
        y += my
        
        # Aplicar sensitivity
        move_x = int(x * self.sensitivity)
        move_y = int(y * self.sensitivity)
        
        # Criar stroke
        stroke = MouseStroke()
        stroke.state = INTERCEPTION_MOUSE_MOVE_RELATIVE
        stroke.flags = 0
        stroke.rolling = 0
        stroke.x = move_x
        stroke.y = move_y
        stroke.information = 0
        
        # Enviar
        self.dll.interception_send(self.context, 11, byref(stroke), 1)
        
        # Stats
        self.current_shot += 1
        self.stats.record_shot(self.current_weapon)
        
        # Fadiga
        self.humanizer.add_fatigue(0.0005)
    
    def run(self):
        """Loop principal"""
        if not self.initialize():
            return
        
        self.running = True
        self.stats.start_session()
        
        print("[✓] Engine rodando...\n")
        
        stroke = MouseStroke()
        shots_in_current_spray = 0
        
        try:
            while self.running:
                # Esperar input
                device = self.dll.interception_wait(self.context)
                
                if device <= 0:
                    continue
                
                # Receber stroke
                if self.dll.interception_receive(self.context, device, byref(stroke), 1) > 0:
                    
                    # Detectar início do spray
                    if stroke.state & INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN:
                        self.shooting = True
                        self.current_shot = 0
                        self.last_shot_time = time.time()
                        shots_in_current_spray = 0
                    
                    # Detectar fim do spray
                    if stroke.state & INTERCEPTION_MOUSE_LEFT_BUTTON_UP:
                        was_shooting = self.shooting
                        self.shooting = False
                        self.current_shot = 0
                        
                        # Registrar spray
                        if was_shooting and shots_in_current_spray > 0:
                            self.stats.record_spray(self.current_weapon, shots_in_current_spray)
                            shots_in_current_spray = 0
                        
                        # Reset fadiga (pequeno)
                        self.humanizer.reset_fatigue()
                    
                    # Aplicar recoil
                    if self.active and self.shooting:
                        current_time = time.time()
                        pattern = get_pattern(self.current_weapon)['pattern']
                        
                        if self.current_shot < len(pattern):
                            delay = pattern[self.current_shot][2]
                            time_since_last = (current_time - self.last_shot_time) * 1000
                            
                            # Usar timing humanizado
                            required_delay = self.humanizer.timing_variance(delay) * 1000
                            
                            if time_since_last >= required_delay:
                                self.apply_recoil()
                                self.last_shot_time = current_time
                                shots_in_current_spray += 1
                    
                    # Sempre reenviar input original
                    self.dll.interception_send(self.context, device, byref(stroke), 1)
        
        except KeyboardInterrupt:
            print("\n[i] Encerrando...")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpeza"""
        self.running = False
        
        if self.context:
            self.dll.interception_destroy_context(self.context)
            print("[✓] Contexto destruído")
        
        self.stats.end_session()
        print("[✓] Stats salvos")
    
    def toggle(self):
        """Ativar/desativar"""
        self.active = not self.active
        return self.active
    
    def set_sensitivity(self, value):
        """Ajustar sensitivity"""
        self.sensitivity = max(0.1, min(2.0, value))
    
    def set_weapon(self, weapon_id):
        """Trocar arma"""
        self.current_weapon = weapon_id
    
    def set_humanization(self, enabled):
        """Ativar/desativar humanização"""
        self.humanizer.enabled = enabled
    
    def get_status(self):
        """Status atual"""
        return {
            'active': self.active,
            'shooting': self.shooting,
            'sensitivity': self.sensitivity,
            'weapon': self.current_weapon,
            'humanization': self.humanizer.enabled,
            'current_shot': self.current_shot,
            'stats': self.stats.get_session_stats()
        }