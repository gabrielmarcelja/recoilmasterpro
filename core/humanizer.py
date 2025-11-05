
"""
Sistema de humanização avançado
Torna movimento indistinguível de humano
"""

import random
import time
import math

class Humanizer:
    """Adiciona características humanas ao movimento"""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.fatigue_level = 0.0  # Simula cansaço
        self.consistency = random.uniform(0.85, 0.95)  # Consistência individual
        
    def jitter(self, value, amount=1):
        """Micro-jitter natural das mãos"""
        if not self.enabled:
            return value
        
        # Jitter aumenta com fadiga
        effective_amount = amount * (1 + self.fatigue_level * 0.5)
        
        # Distribuição mais natural (não uniforme)
        jitter = random.gauss(0, effective_amount / 2)
        jitter = max(-effective_amount, min(effective_amount, jitter))
        
        return value + int(jitter)
    
    def timing_variance(self, base_ms):
        """Variação de timing (reaction time)"""
        if not self.enabled:
            return base_ms / 1000
        
        # Humanos têm variação de 5-15ms
        variance = random.gauss(0, 5)  # Média 0, desvio 5ms
        
        # Fadiga aumenta variação
        variance *= (1 + self.fatigue_level * 0.3)
        
        # Consistência pessoal
        variance *= (2 - self.consistency)
        
        return (base_ms + variance) / 1000
    
    def micro_correction(self, probability=0.1):
        """Micro-correções aleatórias (ajustes naturais)"""
        if not self.enabled or random.random() > probability:
            return 0, 0
        
        # Correções pequenas, mais frequentes que grandes
        if random.random() < 0.7:
            # Pequena correção
            return random.randint(-1, 1), random.randint(-1, 1)
        else:
            # Correção média
            return random.randint(-2, 2), random.randint(-2, 2)
    
    def smoothing_curve(self, start, end, progress):
        """Curva de movimento suave (ease-out)"""
        if not self.enabled:
            return end
        
        # Ease-out cubic
        t = progress
        t = 1 - pow(1 - t, 3)
        
        return start + (end - start) * t
    
    def add_fatigue(self, amount=0.001):
        """Simula cansaço ao longo do tempo"""
        self.fatigue_level = min(1.0, self.fatigue_level + amount)
    
    def reset_fatigue(self):
        """Reset de fadiga (pause/break)"""
        self.fatigue_level = max(0.0, self.fatigue_level - 0.1)
    
    def mouse_path(self, start_x, start_y, end_x, end_y, steps=10):
        """Gera caminho natural de mouse (Bezier-like)"""
        if not self.enabled:
            return [(end_x, end_y)]
        
        path = []
        
        # Ponto de controle aleatório (dá "curva" natural)
        mid_x = (start_x + end_x) / 2 + random.randint(-5, 5)
        mid_y = (start_y + end_y) / 2 + random.randint(-5, 5)
        
        for i in range(steps + 1):
            t = i / steps
            
            # Quadratic Bezier
            x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y
            
            # Adicionar jitter
            x = self.jitter(x, 1)
            y = self.jitter(y, 1)
            
            path.append((int(x), int(y)))
        
        return path
    
    def overshoot_correction(self, target, overshoot_chance=0.15):
        """Simula overshoot (passar do alvo e corrigir)"""
        if not self.enabled or random.random() > overshoot_chance:
            return target, False
        
        # Passar um pouco do alvo
        overshoot = random.randint(1, 3)
        return target + overshoot, True

# ========== EXEMPLO DE USO ==========
if __name__ == "__main__":
    h = Humanizer()
    
    # Teste jitter
    print("Jitter test:")
    for i in range(10):
        print(f"  Original: 20 → Humanizado: {h.jitter(20, 2)}")
    
    # Teste timing
    print("\nTiming variance test:")
    base = 133  # ms
    for i in range(10):
        print(f"  Base: {base}ms → Humanizado: {h.timing_variance(base)*1000:.1f}ms")
    
    # Teste path
    print("\nMouse path test (0,0 → 100,100):")
    path = h.mouse_path(0, 0, 100, 100, steps=5)
    for point in path:
        print(f"  {point}")