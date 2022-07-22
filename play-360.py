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

	def move_player(self, (dx, dy), left_col, top_row, highway_csv, look_for_story):

		blocked = False

		pos=[left_col + self.x,top_row + self.y]
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

		for highway_row in highway_csv:
			if (int(highway_row[1])-1 == int(left_col+self.x) and
				int(highway_row[0])-1 == int(top_row+self.y)):
				self.location = highway_row[2]
		if look_for_story == True:
			for story_row in self.story_csv:
				# First cell is whether it is unlocked by default or has
				# to be triggered by another event (1/0)
				if (int(story_row[1])-1 == int(left_col+self.x) and
					int(story_row[2])-1 == int(top_row+self.y)):
					self.story(story_row[3])

	def draw_map(self, (left_col, top_row)):
		for row in range(8):
			self.screen.addstr(row, 0, MAP[top_row + row][left_col:left_col+40])

	def story(self, story_page):
		# If the story location is two cells from top it triggers three times...
		f = open(map_dir+'story/'+story_page,'r')
		storylines = f.readlines()
		# Mark story page as read
		# Look for related story pages on same csv row and unmark them as usable
		# That way a basic story telling multiple choice game engine.
#		clear()
		for row in range(8):
			self.screen.addstr(row, 0, storylines[row])
			stdscr.timeout(2000)
			self.screen.getch()
		self.break_movement()
		stdscr.timeout(720000)
		self.screen.getch()

	def main(self):
		key = None
		with open(map_dir+'map-start.csv', mode='r') as map_start_file:
			map_start_csv = list(csv.reader(map_start_file))
		with open(map_dir+'highway-locations.csv', mode='r') as highway_locations_file:
			highway_csv = list(csv.reader(highway_locations_file))
		with open(map_dir+'story.csv', mode='r') as story_file:
			self.story_csv = list(csv.reader(story_file))
		self.x, self.y = int(map_start_csv[0][0]), int(map_start_csv[0][1])
		self.transport = 'parked'
		self.location = map_start_csv[1][2]
		map_left_col = int(map_start_csv[1][0])
		map_top_row = int(map_start_csv[1][1])
		self.direction = [0,0]
		self.momentum = [0,0]
		self.story(self.story_csv[0][3])
		while key != KEY_QUIT:
			stdscr.timeout(2000)
			key = self.screen.getch()
			try: self.direction = DIRECTIONS[key]
			except KeyError: self.direction = [0,0]
			if self.direction[0] != 0 or self.direction[1] != 0: 
				self.momentum[0] = self.direction[0]
				self.momentum[1] = self.direction[1]
			if key == KEY_BREAK: self.break_movement()
			self.screen.addstr(self.y, self.x, ' ')
			if self.momentum[0] != 0 or self.momentum[1] != 0:
				try:
					self.move_player(self.momentum, map_left_col, map_top_row, highway_csv, True)
				except BlockedMovement: self.break_movement()
				pass
				if self.x < 2:
					map_left_col = map_left_col-38
					if map_left_col < 0: map_left_col = 0
					else:
						self.move_player((+38, 0), map_left_col, map_top_row, highway_csv, False)
				if self.x > 38:
					map_left_col = map_left_col+38
					self.move_player((-38,0), map_left_col, map_top_row, highway_csv, False)
				if self.y < 2:
					map_top_row = map_top_row-6
					if map_top_row < 0: map_top_row = 0
					else:
						self.move_player((0, +6), map_left_col, map_top_row, highway_csv, False)
				if self.y > 6:
					map_top_row = map_top_row+6
					self.move_player((0, -6), map_left_col, map_top_row, highway_csv, False)
			self.draw_map([map_left_col, map_top_row])
			self.add_message('You are '+self.transport+' on '+self.location)
			self.screen.addstr(self.y, self.x, '=')
			# Hack to move cursor out the way
			self.screen.addstr(8, 39, '')
		self.screen.nodelay(False)

if __name__ == '__main__':
	curses.wrapper(lambda screen: Game(screen).main())

