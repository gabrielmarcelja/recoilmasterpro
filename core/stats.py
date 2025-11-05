"""
Sistema de estatísticas e tracking
"""

import time
import json
from pathlib import Path
from datetime import datetime, timedelta

class StatsTracker:
    """Rastreia estatísticas de uso"""
    
    def __init__(self, stats_file='stats.json'):
        self.file = Path(stats_file)
        self.session_start = time.time()
        self.load()
    
    def load(self):
        """Carregar stats de arquivo"""
        if self.file.exists():
            with open(self.file, 'r') as f:
                data = json.load(f)
                self.total_shots = data.get('total_shots', 0)
                self.total_sprays = data.get('total_sprays', 0)
                self.total_sessions = data.get('total_sessions', 0)
                self.total_time = data.get('total_time', 0)
                self.weapon_stats = data.get('weapon_stats', {})
                self.history = data.get('history', [])
        else:
            self.reset()
    
    def save(self):
        """Salvar stats"""
        data = {
            'total_shots': self.total_shots,
            'total_sprays': self.total_sprays,
            'total_sessions': self.total_sessions,
            'total_time': self.total_time,
            'weapon_stats': self.weapon_stats,
            'history': self.history[-100:]  # Últimas 100 sessões
        }
        
        with open(self.file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset(self):
        """Reset stats"""
        self.total_shots = 0
        self.total_sprays = 0
        self.total_sessions = 0
        self.total_time = 0
        self.weapon_stats = {}
        self.history = []
        self.save()
    
    def record_shot(self, weapon):
        """Registrar tiro"""
        self.total_shots += 1
        
        if weapon not in self.weapon_stats:
            self.weapon_stats[weapon] = {'shots': 0, 'sprays': 0}
        
        self.weapon_stats[weapon]['shots'] += 1
    
    def record_spray(self, weapon, shots_in_spray):
        """Registrar spray completo"""
        if shots_in_spray < 5:  # Mínimo para contar como spray
            return
        
        self.total_sprays += 1
        
        if weapon not in self.weapon_stats:
            self.weapon_stats[weapon] = {'shots': 0, 'sprays': 0}
        
        self.weapon_stats[weapon]['sprays'] += 1
    
    def start_session(self):
        """Iniciar nova sessão"""
        self.session_start = time.time()
        self.total_sessions += 1
    
    def end_session(self):
        """Finalizar sessão"""
        duration = time.time() - self.session_start
        self.total_time += duration
        
        # Adicionar ao histórico
        self.history.append({
            'date': datetime.now().isoformat(),
            'duration': duration,
            'shots': self.total_shots,
            'sprays': self.total_sprays
        })
        
        self.save()
    
    def get_session_stats(self):
        """Stats da sessão atual"""
        duration = time.time() - self.session_start
        
        return {
            'duration': duration,
            'duration_formatted': str(timedelta(seconds=int(duration))),
            'shots': self.total_shots,
            'sprays': self.total_sprays
        }
    
    def get_summary(self):
        """Resumo completo"""
        return {
            'total': {
                'shots': self.total_shots,
                'sprays': self.total_sprays,
                'sessions': self.total_sessions,
                'time': self.total_time,
                'time_formatted': str(timedelta(seconds=int(self.total_time)))
            },
            'weapons': self.weapon_stats,
            'averages': {
                'shots_per_session': self.total_shots / max(1, self.total_sessions),
                'sprays_per_session': self.total_sprays / max(1, self.total_sessions),
                'shots_per_spray': self.total_shots / max(1, self.total_sprays)
            }
        }
    
    def print_summary(self):
        """Imprimir resumo formatado"""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("  📊 ESTATÍSTICAS")
        print("="*50)
        
        print("\n[TOTAIS]")
        print(f"  Tiros: {summary['total']['shots']:,}")
        print(f"  Sprays: {summary['total']['sprays']:,}")
        print(f"  Sessões: {summary['total']['sessions']}")
        print(f"  Tempo total: {summary['total']['time_formatted']}")
        
        print("\n[MÉDIAS]")
        print(f"  Tiros/sessão: {summary['averages']['shots_per_session']:.1f}")
        print(f"  Sprays/sessão: {summary['averages']['sprays_per_session']:.1f}")
        print(f"  Tiros/spray: {summary['averages']['shots_per_spray']:.1f}")
        
        if summary['weapons']:
            print("\n[POR ARMA]")
            for weapon, stats in summary['weapons'].items():
                print(f"  {weapon}: {stats['shots']} tiros, {stats['sprays']} sprays")
        
        print("\n" + "="*50 + "\n")