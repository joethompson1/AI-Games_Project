import socket
from random import choice
from time import sleep
import time
import math
import sys
import os
import random
from operator import itemgetter
currentdir = os.getcwd()
currentdir = currentdir + '/src'

# the mock-0.3.1 dir contains testcase.py, testutils.py & mock.py
sys.path.append(currentdir)
from Tile import Tile

INF = 9999

class NaiveAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    def __init__(self, board_size=11):
        self.s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )

        self.s.connect((self.HOST, self.PORT))

        self.board_size = board_size
        self.board = []
        self.colour = ""
        self.turn_count = 0
        self.invalid_swaps = []
        self.all_moves_made = []
        self.blueStartPosition = (int(board_size/2) ,0)
        self.blueEndPosition = (int(board_size/2),board_size-1)
        self.redStartPosition = (0,int(board_size/2))
        self.redEndPosition = (board_size-1,int(board_size/2))
        self._choices_copy = []
        self.pruned = 0
        self.firstPos = (0, 0)
        self.shortest_path = []
        self.opp_shortest_path = []
        # self.current_best_shortest_path = []
        self.startingColour = "R"


        self.left_x_displacement =  [-5,-4,-3,-2,-1,0,1,2,3,4,5]
        self.left_y_displacement =  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.top_x_displacement =  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.top_y_displacement = [-5,-4,-3,-2,-1,0,1,2,3,4,5]
        self.bottom_x_displacement = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        self.bottom_y_displacement = [-5,-4,-3,-2,-1,0,1,2,3,4,5]
        self.right_x_displacement = [-5,-4,-3,-2,-1,0,1,2,3,4,5]
        self.right_y_displacement = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]

        self.leftOuterMostNode = (5, -1)
        self.rightOuterMostNode = (5, 11)
        self.topOuterMostNode = (-1, 5)
        self.bottomOuterMostNode = (11, 5)
        self.blueStartPosition = self.leftOuterMostNode
        self.blueEndPosition = self.rightOuterMostNode
        self.redStartPosition = self.topOuterMostNode
        self.redEndPosition = self.bottomOuterMostNode

        self._tiles = []
        for i in range(board_size):
            new_line = []
            for j in range(board_size):
                new_line.append(Tile(i, j))
            self._tiles.append(new_line)

        self.choices = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.choices.append((i, j))
        
        self._create_moves()



    def do_invalid_swaps(self):
        x=0
        y=0
        while (x < self.board_size and y < self.board_size):
            new_position = (x,y)

            if (x <= 1 or y <= 1 or x >= self.board_size-2 or y >= self.board_size-2):
                self.invalid_swaps.append(new_position)
            
            y+=1

            if (y==self.board_size):
                x+=1
                y=0



    def starting_move(self):
        choices_set = set(self.choices)
        outside_set = set(self.invalid_swaps)
        difference = choices_set.difference(outside_set)
        difference = list(difference)
        return difference


    # Need to make it so that if opponent switches moves then firstPos needs to change to the next players move
    def get_bridge_move(self, turn_count):
        # depends if we are moving top to bottom or left to right
        # top to bottom: x + 2 = bridge below
        x_n = self.firstPos[0]
        y_n = self.firstPos[1]

        self.choices = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] == 0:
                    self.choices.append((i, j))

        if self.colour == "R":
            if turn_count == 2:
                x_n += 2
                y_n -= 1

            else:
                x_n -= 2
                y_n += 1

        else:
            if turn_count == 2:
                y_n += 2
                x_n -= 1

            else:
                y_n -= 2
                x_n += 1

        pos = (x_n, y_n)

        # Makes sure move is valid else choose random from options
        if not(pos in self.choices):
            choices_set = set(self.choices)
            outside_set = set(self.invalid_swaps)
            inside_set = choices_set.difference(outside_set)
            choices_inside_set = list(inside_set)
            pos = choice(choices_inside_set)

        return pos


    def find_shortest_path_in_dic(self, visited, colour):
        (start_node, end_node , start_x_displacement, start_y_displacement) = self.startFinishPosition(colour)

        lowest_cost = 100000
        final_node = (0,0)

        # Loops through visited array from the last node to the first node and finds the path with the lowest cost
        for i in range(self.board_size):
            if end_node == (11,5):
                end_node_temp = (end_node[0]+self.bottom_x_displacement[i], end_node[1]+self.bottom_y_displacement[i])
                current_end_node = visited.get(end_node_temp)

                # Finds the end node which is within the board (not outer most nodes)
                if (current_end_node[0] < lowest_cost):
                    final_node = end_node_temp
                    lowest_cost = current_end_node[0]

            else:
                end_node_temp = (end_node[0]+self.right_x_displacement[i], end_node[1]+self.right_y_displacement[i])
                current_end_node = visited.get(end_node_temp)

                if (current_end_node[0] < lowest_cost):
                    final_node = end_node_temp
                    lowest_cost = current_end_node[0]

        return final_node, lowest_cost, start_node



    def run(self):
        """Reads data until it receives an END message or the socket closes."""

        while True:
            data = self.s.recv(1024)
            if not data:
                break
            if (self.interpret_data(data)):
                break


    def interpret_data(self, data):
        """Checks the type of message and responds accordingly. Returns True
        if the game ended, False otherwise.
        """

        messages = data.decode("utf-8").strip().split("\n")
        messages = [x.split(";") for x in messages]
        for s in messages:
            if s[0] == "START":
                self.board_size = int(s[1])
                self.colour = s[2]
                self.board = [
                    [0]*self.board_size for i in range(self.board_size)]

                if self.colour == "R":
                    self.make_move()

            elif s[0] == "END":
                return True

            elif s[0] == "CHANGE":
                if s[3] == "END":
                    return True

                elif s[1] == "SWAP":
                    self.colour = self.opp_colour()
                    if s[3] == self.colour:
                        self.make_move()

                elif s[3] == self.colour:
                    action = [int(x) for x in s[1].split(",")]
                    self.board[action[0]][action[1]] = self.opp_colour()
                    action_removal_service = tuple(action)
                    if action_removal_service in self.choices:
                        print("removal service")
                        self.choices.remove(action_removal_service)
                    self.make_move()

        return False

    def make_move(self):
        """Makes a random move from the available pool of choices. If it can
        swap, chooses to do so 50% of the time.
        """

        if self.colour == "B" and self.turn_count == 0:
            opp_move = (0,0)
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if self.board[i][j] == self.opp_colour():
                        opp_move = (i,j)
            if opp_move in self.starting_move():
                self.s.sendall(bytes("SWAP\n", "utf-8"))
            else:
                # same as below
                pos = choice(self.starting_move())
                # pos = choice(self.choices)
                if pos in self.choices:
                    self.choices.remove(pos)
                if pos in self._choices_copy:
                    self._choices_copy.remove(pos)

                
                self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
                self.board[pos[0]][pos[1]] = self.colour

        elif self.turn_count == 0:
            self.do_invalid_swaps()
            pos = choice(self.starting_move())
            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)

            self.firstPos = pos
            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour

        elif self.turn_count < 3:
            if self.startingColour == self.colour:
                pos = self.get_bridge_move(self.turn_count)

            else:
                pos = choice(self.starting_move())
                self.firstPos = pos
                self.turn_count -= 1
                self.startingColour = self.colour

            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)

            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour


        else:
            choices_set = set(self.choices)
            self.no_nodes_searched = 0
            # best_val, pos = self._alpha_beta(self.colour, -INF, INF)
            visited = {}
            opp_visited = {}
            visited = self.dijkstra(self.colour)
            opp_visited = self.dijkstra(self.opp_colour())

            final_node, lowest_cost, start_node = self.find_shortest_path_in_dic(visited, self.colour)
            opp_final_node, opp_lowest_cost, opp_start_node = self.find_shortest_path_in_dic(opp_visited, self.opp_colour())

            current_node = final_node
            self.shortest_path = []

            while not(current_node == start_node):
                # previous_node = current_node
                self.shortest_path.append(current_node)
                current_node = visited[current_node][1] # sets current node as predecessor node

            opp_current_node = opp_final_node
            self.opp_shortest_path = []

            while not(opp_current_node == opp_start_node):
                # previous_node = opp_current_node
                self.opp_shortest_path.append(opp_current_node)
                opp_current_node = opp_visited[opp_current_node][1] # sets current node as predecessor node

            #  This chooses first to last position in shortest_path
            # pos = self.shortest_path[len(self.shortest_path)-1]
            # del self.shortest_path[len(self.shortest_path)-1]

            self.shortest_path_middle = self.shortest_path.copy()
            self.shortest_path_middle = self.shortest_path_middle[3:len(self.shortest_path)-3]

            matches = set(self.shortest_path) & set(self.opp_shortest_path)
            matches = list(matches)

            if (matches):
                pos = matches[len(matches)-1]
                matches.remove(pos)

                while (not self.board[pos[0]][pos[1]] == 0):
                    if not matches:
                        pos = self.shortest_path[len(self.shortest_path)-1]
                        del self.shortest_path[len(self.shortest_path)-1]

                    else:
                        pos = matches[len(matches)-1]
                        matches.remove(pos)

            else:
                pos = random.choice(self.shortest_path[3:len(self.shortest_path)-3])
                self.shortest_path_middle.remove(pos)


                while (not self.board[pos[0]][pos[1]] == 0): 
                    if not self.shortest_path_middle:
                        pos = self.shortest_path[len(self.shortest_path)-1]
                        del self.shortest_path[len(self.shortest_path)-1]

                    else:           
                        pos = self.shortest_path_middle[0]
                        self.shortest_path.remove(pos)
                        self.shortest_path_middle.remove(pos)


            

            # while (not self.board[pos[0]][pos[1]] == 0):
            #     pos = self.shortest_path[len(self.shortest_path)-1]
            #     del self.shortest_path[len(self.shortest_path)-1]



            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)

            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour

        self.turn_count += 1

# Game doesn't include own bridging tiles in shortest path if they are on the start nodes (edge of the game board)

# try to fill in ones around bridging first
        # bonus try and split the board into 4 quadrants and pick move from shortest_path based on the ones which are in the same quadrant which has most moves already played


    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        if self.colour == "R":
            return "B"
        elif self.colour == "B":
            return "R"
        else:
            return "None"

    def opp_of_this_colour(self, colour):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        if colour == "R":
            return "B"
        elif colour == "B":
            return "R"
        else:
            return "None"



    # move = [x, y]
    def getHeuristicScore(self, colour):
        # Evaluates computers and players score against each other to determine effectiveness of player move
        heuristicScore = self.getShortestPathScore(colour) - self.getShortestPathScore(self.opp_of_this_colour(colour))
        return heuristicScore


    def getShortestPathScore(self, colour):
        # Set the start node to be leftOuterMostNode (assuming we are moving left to right)
        # Pass the starting node to the dijkstra's algorithm
        visited = self.dijkstra(colour)
        (startPosition, endPosition , _, _) = self.startFinishPosition(colour)
        endNode = visited.get(endPosition)
        totalScore = endNode[0]
        return totalScore


    def startFinishPosition(self, playerColour):
        if playerColour == "R":
            playerStartPosition = self.redStartPosition
            playerEndPosition = self.redEndPosition
            start_x_displacement = self.top_x_displacement
            start_y_displacement = self.top_y_displacement


        else:
            playerStartPosition = self.blueStartPosition
            playerEndPosition = self.blueEndPosition
            start_x_displacement = self.left_x_displacement
            start_y_displacement = self.left_y_displacement

        return (playerStartPosition, playerEndPosition, 
                start_x_displacement, start_y_displacement)




    def dijkstra(self, playerColour):
        INF = 9999
        # Initialise visited and unvisited lists

        if playerColour == "R":
            opp_colour = "B"

        else:
            opp_colour = "R"

        unvisited  = {} # Declare unvisted list as empty dictionary
        visited = {} # Declare visited list as empty dictionary

        # Add every node to the unvisited list
        for x in range(self.board_size):
            for y in range(self.board_size):
                unvisited[(x,y)] = [INF, None] # [costFromStart, previousNodeCoordinates]

        
        (playerStartPosition, playerEndPosition, 
        start_x_displacement, start_y_displacement) = self.startFinishPosition(playerColour)
        
        unvisited[playerStartPosition] = [0, None]
        unvisited[playerEndPosition] = [INF, None]

        # Set the cost of the start node to 0
        # unvisited[playerStartPosition][0] = 0 # set costFromStart to 0

        # Repeat the following steps until unvisted list is empty
        finished = False
        while not (finished):
            if not (unvisited): # If unvisted dictionary is empty then
                finished = True

            else:
                # Gets unvisited node with lowest cost as current node
                current_node = min(unvisited, key=unvisited.get)

                x = current_node[0]
                y = current_node[1]
                neighbour_count = 0

                # If at the starting node (outer most node)
                if (current_node == playerStartPosition):
                    neighbour_count = 11
                    x_displacement = start_x_displacement
                    y_displacement = start_y_displacement

                elif (playerEndPosition == self.redEndPosition and x == self.board_size-1):
                    neighbour_count = 7
                    # Keep neighbour displacement the same
                    x_displacement = Tile.I_DISPLACEMENTS
                    # But add an extra displacement for the 7th neighbour (outermost node)
                    x_displacement.append(1) 
                    y_displacement = Tile.J_DISPLACEMENTS
                    # Add the displacement to get to the outerMostNode based on current node y value
                    y_displacement.append(playerEndPosition[1] - y)

                elif (playerEndPosition == self.blueEndPosition and y == self.board_size-1):
                    neighbour_count = 7
                    x_displacement = Tile.I_DISPLACEMENTS
                    x_displacement.append(playerEndPosition[0] - x)
                    y_displacement = Tile.J_DISPLACEMENTS
                    y_displacement.append(1)
                    

                else:
                    neighbour_count = Tile.NEIGHBOUR_COUNT
                    x_displacement = Tile.I_DISPLACEMENTS
                    y_displacement = Tile.J_DISPLACEMENTS


                # Examine neighbours
                for idx in range(neighbour_count): # Loops through each neighbour in turn

                    x_n = x + x_displacement[idx]
                    y_n = y + y_displacement[idx]

                    # Check that x_n & y_n are within the board
                    if (((x_n == playerStartPosition[0] or x_n == playerEndPosition[0]) and (y_n == playerStartPosition[1] or y_n == playerEndPosition[1])) 
                        or (x_n >= 0 and x_n < self.board_size and y_n >= 0 and y_n < self.board_size)): 
                        
                        if not((x_n == playerEndPosition[0] and y_n == playerEndPosition[1]) or (x_n == playerEndPosition[0] and y_n == playerEndPosition[1])):
                            neighbour = self._tiles[x_n][y_n]
                            neighbourTuple = (x_n,y_n)

                        neighbourTuple = (x_n,y_n)
                        if (not (x_n,y_n) in visited): # checks to see what neighbours value is and assigns weight based on value

                            if (neighbourTuple == playerEndPosition):
                                weight = 0

                            elif (self.board[neighbourTuple[0]][neighbourTuple[1]] == opp_colour):
                                weight = INF

                            elif (self.board[neighbourTuple[0]][neighbourTuple[1]] == playerColour):
                                weight = 0 

                            else: # if space is 0 assign weight of 1
                                weight = 1

                            cost = unvisited[current_node][0] + weight


                            if cost < unvisited[neighbourTuple][0]:
                                unvisited[neighbourTuple][0] = cost
                                unvisited[neighbourTuple][1] = current_node

                # Add current node to visited list
                visited[current_node] = unvisited[current_node]
                # Remove from unvisited list
                del unvisited[current_node]

        return visited

        
           

        


    def _alpha_beta(self, colour, alpha, beta, depth=2):
        if colour == 'R':
            opp_colour = 'B'
        else:
            opp_colour = 'R'

        best_move = None
        best_value = -INF

        ## check if at max depth or if game is over

        if depth <= 0:
            best_value = self.getHeuristicScore(colour)
            # print("BEST VALUE", best_value)
            best_move = None
            self._choices_copy = self.choices
            return best_value, best_move
        else:
            self.no_nodes_searched += 1
            moves = self._get_moves()

        for move in moves:

            # self._make_dummy_move(move, colour)
            self.choices.remove(move)

            new_val, _ = self._alpha_beta(opp_colour, -beta, -alpha, depth-1)

            new_val = -new_val

            if new_val > best_value:
                best_move = move
                best_value = new_val

            self.choices.append(move)

            alpha = max(alpha, best_value)
            if alpha >= beta:
                self.pruned += 1
                break

        return best_value, best_move




    def _make_dummy_move(self, move, colour):
        self.choices.remove(move)

        ### code to update the local board!

        return self.choices ###  should also return local board

    def _get_moves(self):
        return self.choices

    def _create_moves(self):
        for i in range(self.board_size):
            for j in range(self.board_size):
                self._choices_copy.append((i, j))









if (__name__ == "__main__"):
    agent = NaiveAgent()
    agent.run()
