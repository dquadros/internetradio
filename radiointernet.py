#!/usr/bin/python
# -*- coding: utf-8 -*-

from gpiozero import Button
from pathlib import Path
import shlex, subprocess
import lcdi2c
import time

tocando = False;

# Inicia o display
lcd = lcdi2c.lcd_pcf8574()
lcd.init()
lcd.backlightOn()

# Inicia a lista de estacoes
estacoes = []
path = Path('./estacoes.txt')
if path.is_file():
    f = open(str(path), "r")
    estacoes = [url.rstrip() for url in f]
    f.close()
if len(estacoes) == 0:
    estacoes = ['http://stream.radioparadise.com/rock-128']
estacao = len(estacoes)
nome = ' '*16

# Inicia volume
volumes = (30, 50, 70, 85, 100)
volume = 0

# Classe para tratar botão com debounce
class Botao:
    # construtor
    def __init__(self,pino):
        self.button = Button(pino)
        self.atual = self.button.is_pressed
        self.estado = False
        self.contagem = 0

    # testa se botao foi apertado e soltado
    def soltou(self):
        # atualiza estado
        novo = self.button.is_pressed
        if self.atual != novo:
            # mudou, reinicia debounce
            self.atual = novo
            self.contagem = 3
        elif self.contagem > 0:
            # permanece o mesmo
            self.contagem = self.contagem - 1
            if (self.contagem == 0) and (self.atual != self.estado):
                # mudança confirmada
                self.estado = self.atual
                if not self.estado:
                    return True
        return False

# Trunca/complenta string
def fixed_length(str, length):
  return ('{:<%d}' % length).format(str[:length])

# Executa comando e retorna resposta
def command(cmd):
  result = subprocess.check_output(
    shlex.split(cmd), stderr=subprocess.STDOUT, text=True
  )
  result = result.rstrip().split('\n')
  print (cmd, '-->', result)
  return result

# Trata botão Play/Stop
def doPlay():
  global tocando
  
  if tocando:
    tocando = False
    command('mpc stop')
  else:
    tocando = True
    command('mpc play')

# Passa para próxima estação
def doNextStation():
    global estacao
    estacao = estacao+1
    if estacao >= len(estacoes):
        estacao = 0
    command('mpc clear')
    command('mpc add '+estacoes[estacao])
    command('mpc play')

# Passa para a estação anterior
def doPrevStation():
    global estacao
    if estacao == 0:
        estacao = len(estacoes)
    estacao = estacao-1
    command('mpc clear')
    command('mpc add '+estacoes[estacao])
    command('mpc play')

# Aumenta o bolume
def doNextVol():
    global volume
    if volume < (len(volumes)-1):
      volume = volume+1
    command('mpc volume {}'.format(volumes[volume]))

# Diminui o volume
def doPrevVol():
    global volume
    if volume > 0:
        volume = volume-1
    command('mpc volume {}'.format(volumes[volume]))

# Atualiza o display
def atlStatus():
  global tocando, nome
  result = command('mpc')
  tocando = (len(result) > 1) and (result[1].find('[playing]') != -1)
  if tocando:
    if result[0].startswith('http'):
        # Não tem o nome da estacao
        parts = result[0].split('//')
        nome = fixed_length(parts[1],16)
        lcd.displayWrite(1, 0, ' '*16)
    else:
        parts = result[0].split(':')
        nome = fixed_length(parts[0],16)
        lcd.displayWrite(1, 0, fixed_length(parts[1].strip(),16))
  else:
    lcd.displayWrite(1, 0, ' '*16)
  lcd.displayWrite(0, 0, nome)

# Define os botoes
bPlay = Botao(24)
bNextStation = Botao(22)
bPrevStation = Botao(23)
bNextVol = Botao(17)
bPrevVol = Botao(27)

# Começa a tocar a primeira estacao
doNextVol()
doNextStation()

# Laco Principal
nextAtl = time.time()
while True:
    if bPlay.soltou():
        doPlay()
    if bNextStation.soltou():
        doNextStation()
    if bPrevStation.soltou():
        doNextStation()
    if bNextVol.soltou():
        doNextVol()
    if bPrevVol.soltou():
        doPrevVol()
    if time.time() >= nextAtl:
        atlStatus()
        nextAtl = time.time() + 2
    time.sleep(.05)
