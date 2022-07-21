#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses, sys, os, csv

stdscr = curses.initscr()

map_dir="bristol-centre-c360map/"
map_file = open(map_dir+"map.brf", "r")
MAP = map_file.readlines()

KEY_QUIT = ord('q')
DIRECTIONS = {
	curses.KEY_UP: (0, -1),
	curses.KEY_RIGHT: (1, 0),
	curses.KEY_DOWN: (0, 1),
	curses.KEY_LEFT: (-1, 0),
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
		x, y = self.x + dx, self.y + dy
		# Let player be next to road
		if MAP[top_row + y][left_col + x] == ' ':
			if (MAP[top_row + y][left_col + x-1] == ' ' and 
				MAP[top_row + y][left_col + x+1] == ' '):
				raise BlockedMovement()
		self.x, self.y = x, y
		for highway_row in highway_csv:
			if (int(highway_row[1])-1 == int(left_col+self.x) and
				int(highway_row[0])-1 == int(top_row+self.y)):
				self.add_message('You are on '+highway_row[2])

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
		prevdirection = [0,0]
		while key != KEY_QUIT:
			self.screen.addstr(self.y, self.x, '=')
			# Hack to move cursor out the way
			self.screen.addstr(8, 39	, '')
			stdscr.timeout(2000)
			key = self.screen.getch()
			prevdirection = direction
			try:
				direction = DIRECTIONS[key]
			except KeyError:
				direction = prevdirection
			self.screen.addstr(self.y, self.x, ' ')
			try:
				self.move_player(direction, map_left_col, map_top_row, highway_csv)
			except BlockedMovement:
				pass
			if direction[0] != 0:
				if self.x < 2:
					map_left_col = map_left_col-38
					if map_left_col < 0:
						map_left_col = 0
					else:
						self.move_player((+38, 0), map_left_col, map_top_row, highway_csv)
				if self.x > 38:
					map_left_col = map_left_col+38
					self.move_player((-38,0), map_left_col, map_top_row, highway_csv)
			if direction[1] != 0:
				if self.y < 2:
					map_top_row = map_top_row-6
					if map_top_row < 0:
						map_top_row = 0
					else:
						self.move_player((0, +6), map_left_col, map_top_row, highway_csv)
				if self.y > 6:
					map_top_row = map_top_row+6
					self.move_player((0, -6), map_left_col, map_top_row, highway_csv)
			self.draw_map([map_left_col, map_top_row])
		self.screen.nodelay(False)

if __name__ == '__main__':
	curses.wrapper(lambda screen: Game(screen).main())

