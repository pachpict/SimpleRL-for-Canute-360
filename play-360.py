#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses, sys, os, csv

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

class BlockedMovement(Exception):
	pass


class Game(object):
	def __init__(self, screen):
		self.screen = screen

	def add_message(self, message):
		self.screen.addstr(8, 0, "                                       ")
		self.screen.addstr(8, 0, message[0:38])

	def move_player(self, (dx, dy), left_col, top_row, highway_csv):

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

		if blocked == True: raise BlockedMovement()

		for highway_row in highway_csv:
			if (int(highway_row[1])-1 == int(left_col+self.x) and
				int(highway_row[0])-1 == int(top_row+self.y)):
				self.add_message('You are '+transport+' on '+highway_row[2])

	def draw_map(self, (left_col, top_row)):
		for row in range(8):
			self.screen.addstr(row, 0, MAP[top_row + row][left_col:left_col+40])
		
	def main(self):
		key = None
		with open(map_dir+'map-start.csv', mode='r') as map_start_file:
			map_start_csv = list(csv.reader(map_start_file))
		with open(map_dir+'highway-locations.csv', mode='r') as highway_locations_file:
			highway_csv = list(csv.reader(highway_locations_file))
		self.x, self.y = int(map_start_csv[0][0]), int(map_start_csv[0][1])
		map_left_col = int(map_start_csv[1][0])
		map_top_row = int(map_start_csv[1][1])
		self.draw_map([map_left_col, map_top_row])
		self.add_message('You, =, have started at '+map_start_csv[1][2])
		direction = [0,0]
		momentum = [0,0]
		while key != KEY_QUIT:
			self.screen.addstr(self.y, self.x, '=')
			# Hack to move cursor out the way
			self.screen.addstr(8, 39	, '')
			stdscr.timeout(2000)
			key = self.screen.getch()
			try: direction = DIRECTIONS[key]
			except KeyError: direction = [0,0]
			if direction[0] != 0: momentum[0] = direction[0]
			if direction[1] != 0: momentum[1] = direction[1]
			if key == KEY_BREAK:
				momentum[0] = 0
				momentum[1] = 0
			self.screen.addstr(self.y, self.x, ' ')
			if momentum[0] != 0 or momentum[1] != 0:
				try:
					self.move_player(momentum, map_left_col, map_top_row, highway_csv)
				except BlockedMovement:
					momentum[0] = 0
					momentum[1] = 0
					pass
				if momentum[0] != 0:
					if self.x < 2:
						map_left_col = map_left_col-38
						if map_left_col < 0: map_left_col = 0
						else:
							self.move_player((+38, 0), map_left_col, map_top_row, highway_csv)
					if self.x > 38:
						map_left_col = map_left_col+38
						self.move_player((-38,0), map_left_col, map_top_row, highway_csv)
				if momentum[1] != 0:
					if self.y < 2:
						map_top_row = map_top_row-6
						if map_top_row < 0: map_top_row = 0
						else:
							self.move_player((0, +6), map_left_col, map_top_row, highway_csv)
					if self.y > 6:
						map_top_row = map_top_row+6
						self.move_player((0, -6), map_left_col, map_top_row, highway_csv)
				self.draw_map([map_left_col, map_top_row])
		self.screen.nodelay(False)

if __name__ == '__main__':
	curses.wrapper(lambda screen: Game(screen).main())

