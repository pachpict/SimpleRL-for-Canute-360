#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses, sys, os, csv
from os import system, name

stdscr = curses.initscr()

map_dir="bristol-centre-c360map/"
map_file = open(map_dir+"map.brf", "r")
MAP = map_file.readlines()

KEY_QUIT = ord('q')
KEY_BREAK = ord(' ')
DIRECTIONS = {
	curses.KEY_UP: (0, -1),
	curses.KEY_RIGHT: (1, 0),
	curses.KEY_DOWN: (0, 1),
	curses.KEY_LEFT: (-1, 0),
	curses.KEY_ENTER: (0, 0)
}

def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

class BlockedMovement(Exception):
	pass


class Game(object):
	def __init__(self, screen):
		self.screen = screen

	def add_message(self, message):
		self.screen.addstr(8, 0, "                                       ")
		self.screen.addstr(8, 0, message[0:38])

	def break_movement(self):
		self.momentum[0] = 0
		self.momentum[1] = 0
		self.transport = 'parked'

	def move_player(self, (dx, dy), map_change):

		blocked = False

		pos=[self.map_pos[0] + self.x,self.map_pos[1] + self.y]
		neighbours = [
			MAP[pos[1]-1][pos[0]],
			MAP[pos[1]-1][pos[0]+1],
			MAP[pos[1]][pos[0]+1],
			MAP[pos[1]+1][pos[0]+1],
			MAP[pos[1]+1][pos[0]],
			MAP[pos[1]+1][pos[0]-1],
			MAP[pos[1]][pos[0]-1],
			MAP[pos[1]-1][pos[0]-1]
		]
		# 7 0 1
		# 6 x 2
		# 5 4 3
		if self.map_pos[0] == 0 and self.x < 2:
			neighbours[5], neighbours[6], neighbours[7] = ' '
		if self.map_pos[0] == len(MAP[0]) and self.x > 38:
			neighbours[1], neighbours[2], neighbours[3] = ' '

		if self.map_pos[1] == 0 and self.y < 2:
			neighbours[7], neighbours[0], neighbours[1] = ' '
		if self.map_pos[1] == len(MAP) and self.x > 6:
			neighbours[5], neighbours[4], neighbours[3] = ' '

		# Need to change momentum if change direction of travel
		if dx > 1 or dx < -1 or dy > 1 or dy < -1:
			self.x, self.y = self.x + dx, self.y + dy
		elif dx == 0 and dy == -1:
			if neighbours[0] != ' ': self.y = self.y - 1
			elif neighbours[1] != ' ': self.x, self.y = self.x + 1, self.y - 1
			elif neighbours[7] != ' ': self.x, self.y = self.x - 1, self.y - 1
			else: blocked = True
		elif dx == 1 and dy == -1:
			if neighbours[1] != ' ': self.x, self.y = self.x + 1, self.y - 1
			elif neighbours[2] != ' ': self.x = self.x + 1
			elif neighbours[0] != ' ': self.y = self.y - 1
			else: blocked = True
		elif dx == 1 and dy == 0:
			if neighbours[2] != ' ': self.x = self.x + 1
			elif neighbours[3] != ' ': self.x, self.y = self.x + 1, self.y + 1
			elif neighbours[1] != ' ': self.x, self.y = self.x + 1, self.y - 1
			else: blocked = True
		elif dx == 1 and dy == 1:
			if neighbours[3] != ' ': self.x, self.y = self.x + 1, self.y + 1
			elif neighbours[2] != ' ': self.x = self.x + 1
			elif neighbours[4] != ' ': self.y = self.y + 1
			else: blocked = True
		elif dx == 0 and dy == 1:
			if neighbours[4] != ' ': self.y = self.y + 1
			elif neighbours[3] != ' ': self.x, self.y = self.x + 1, self.y + 1
			elif neighbours[5] != ' ': self.x, self.y = self.x - 1, self.y + 1
			else: blocked = True
		if dx == -1 and dy == 1:
			if neighbours[5] != ' ': self.x, self.y = self.x - 1, self.y + 1
			elif neighbours[6] != ' ': self.x = self.x - 1
			elif neighbours[4] != ' ': self.y = self.y + 1
			else: blocked = True
		elif dx == -1 and dy == 0:
			if neighbours[6] != ' ': self.x = self.x - 1
			elif neighbours[5] != ' ': self.x, self.y = self.x - 1, self.y + 1
			elif neighbours[7] != ' ': self.x, self.y = self.x - 1, self.y - 1
			else: blocked = True
		elif dx == -1 and dy == -1:
			if neighbours[7] != ' ': self.x, self.y = self.x - 1, self.y - 1
			elif neighbours[6] != ' ': self.x = self.x - 1
			elif neighbours[0] != ' ': self.y = self.y + 1
			else: blocked = True

		if blocked == True: 
			self.transport = 'parked'
			raise BlockedMovement()
		else: self.transport = 'driving'

		for highway_row in self.ways:
			if (int(highway_row[1])-1 == int(self.map_pos[0]+self.x) and
				int(highway_row[0])-1 == int(self.map_pos[1]+self.y)):
				self.location = highway_row[2]
		if map_change == False:
			for story_row in self.story_csv:
				# First cell is whether it is unlocked by default or has
				# to be triggered by another event (1/0)
				if (int(story_row[1])-1 == int(self.map_pos[0]+self.x) and
					int(story_row[2])-1 == int(self.map_pos[1]+self.y)):
					self.story(story_row[3])

	def draw_map(self):
		for row in range(8):
			self.screen.addstr(row, 0, MAP[self.map_pos[1] + row][self.map_pos[0]:self.map_pos[0]+40])

	def story(self, story_page):
		# If the story location is two cells from top it triggers three times...
		f = open(map_dir+'story/'+story_page,'r')
		storylines = f.readlines()
		# Mark story page as read
		# Look for related story pages on same csv row and unmark them as usable
		# That way a basic story telling multiple choice game engine.
		clear()
		for row in range(8):
			self.screen.addstr(row, 0, storylines[row][0:39])
			stdscr.timeout(self.speed)
			self.screen.getch()
		self.break_movement()
		stdscr.timeout(720000)
		self.screen.getch()

	def main(self):
		with open(map_dir+'map-start.csv', mode='r') as map_start_file:
			map_start_csv = list(csv.reader(map_start_file))
		self.map_pos = [
			int(map_start_csv[1][0]),
			int(map_start_csv[1][1])
		]
		self.location = map_start_csv[1][2]
		self.x, self.y = int(map_start_csv[0][0]), int(map_start_csv[0][1])
		with open(map_dir+'highway-locations.csv', mode='r') as highway_locations_file:
			self.ways = list(csv.reader(highway_locations_file))
		self.transport = 'parked'
		self.momentum = [0,0]
		self.speed = 3500
		with open(map_dir+'story.csv', mode='r') as story_file:
			self.story_csv = list(csv.reader(story_file))
		self.story(self.story_csv[0][3])
		direction = [0,0]
		map_change = False
		key = None
		while key != KEY_QUIT:
			if map_change == True: stdscr.timeout(10000+self.speed)
			else: stdscr.timeout(self.speed)
			key = self.screen.getch()
			try: self.direction = DIRECTIONS[key]
			except KeyError: self.direction = [0,0]
			if self.direction[0] != 0 or self.direction[1] != 0: 
				self.momentum[0] = self.direction[0]
				self.momentum[1] = self.direction[1]
			if key == KEY_BREAK: self.break_movement()
			self.screen.addstr(self.y, self.x, ' ')
			if self.momentum[0] != 0 or self.momentum[1] != 0:
				map_change = False
				try:
					self.move_player(self.momentum, map_change)
				except BlockedMovement: self.break_movement()
				pass
				if self.x < 2 and self.momentum[0] < 0:
					self.map_pos[0] = self.map_pos[0]-38
					if self.map_pos[0] < 0: self.map_pos[0] = 0
					else:
						map_change = True
						self.move_player((+38, 0), map_change)
				elif self.x > 38 and self.momentum[0] > 0:
					self.map_pos[0] = self.map_pos[0]+38
					map_change = True
					self.move_player((-38,0), map_change)
				if self.y < 2 and self.momentum[1] < 0:
					self.map_pos[1] = self.map_pos[1]-6
					if self.map_pos[1] < 0: self.map_pos[1] = 0
					else:
						map_change = True
						self.move_player((0, +6), map_change)
				elif self.y > 6 and self.momentum[1] > 0:
					self.map_pos[1] = self.map_pos[1]+6
					map_change = True
					self.move_player((0, -6), map_change)
			self.draw_map()
			self.add_message('You are '+self.transport+' on '+self.location)
			self.screen.addstr(self.y, self.x, '=')
			# Hack to move cursor out the way
			self.screen.addstr(8, 39, '')
		self.screen.nodelay(False)

if __name__ == '__main__':
	curses.wrapper(lambda screen: Game(screen).main())

