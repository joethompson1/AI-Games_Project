import socket
from random import choice
from time import sleep
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


        self.left_x_displacement =  [-5,-4,-3,-2,-1,0,1,2,3,4,5]
        self.left_y_displacement =  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.top_x_displacement =  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.top_y_displacement = [-5,-4,-3,-2,-1,0,1,2,3,4,5]

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
        return choice(difference)


    # Need to make it so that if opponent switches moves then firstPos needs to change to the next players move
    def get_bridge_move(self, turn_count):
        # depends if we are moving top to bottom or left to right
        # top to bottom: x + 2 = bridge below
        x_n = self.firstPos[0]
        y_n = self.firstPos[1]

        print("turn count: ", turn_count)
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

            else:
                y_n -= 2

        pos = (x_n, y_n)

        # Makes sure move is valid else choose random from options
        if not(pos in self.choices):
            choices_set = set(self.choices)
            outside_set = set(self.invalid_swaps)
            inside_set = choices_set.difference(outside_set)
            choices_inside_set = list(inside_set)
            pos = choice(choices_inside_set)

        return pos



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
            if choice([0, 1]) == 1:
                self.s.sendall(bytes("SWAP\n", "utf-8"))
            else:
                # same as below
                pos = starting_move()
                # pos = choice(self.choices)
                if pos in self.choices:
                    self.choices.remove(pos)
                if pos in self._choices_copy:
                    self._choices_copy.remove(pos)

                
                self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
                self.board[pos[0]][pos[1]] = self.colour

        elif self.turn_count == 0:
            self.do_invalid_swaps()
            pos = self.starting_move()
            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)

            self.firstPos = pos
            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour

        elif self.turn_count < 4:
            pos = self.get_bridge_move(self.turn_count)
            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)

            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour

        
        else:
            self.no_nodes_searched = 0
            best_val, pos = self._alpha_beta(self.colour, -INF, INF)
            if pos in self.choices:
                self.choices.remove(pos)
            if pos in self._choices_copy:
                self._choices_copy.remove(pos)
            self.s.sendall(bytes(f"{pos[0]},{pos[1]}\n", "utf-8"))
            self.board[pos[0]][pos[1]] = self.colour
        self.turn_count += 1


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
        # Initialise visited and unvisited lists

        unvisited  = {} # Declare unvisted list as empty dictionary
        visited = {} # Declare visited list as empty dictionary

        # Add every node to the unvisited list
        for x in range(self.board_size):
            for y in range(self.board_size):
                unvisited[(x,y)] = [math.inf, None] # [costFromStart, previousNodeCoordinates]

        
        (playerStartPosition, playerEndPosition, 
        start_x_displacement, start_y_displacement) = self.startFinishPosition(playerColour)
        
        unvisited[playerStartPosition] = [math.inf, None]
        unvisited[playerEndPosition] = [math.inf, None]
        # Set the cost of the start node to 0
        unvisited[playerStartPosition][0] = 0 # set costFromStart to 0

        # Repeat the following steps until unvisted list is empty
        finished = False
        while not (finished):
            if not (unvisited): # If unvisted dictionary is empty then
                finished = True

            else:
                # Gets unvisited node with lowest cost as current node
                current_node = min(unvisited, key=unvisited.get(0))
                x = current_node[0]
                y = current_node[1]
                neighbour_count = 0

                # If at the starting node (outer most node)
                if (current_node == playerStartPosition):
                    neighbour_count = 11
                    x_displacement = start_x_displacement
                    y_displacement = start_y_displacement

                elif (playerEndPosition == self.redEndPosition):
                    if (x == self.board_size-1):
                        neighbour_count = 7
                        # Keep neighbour displacement the same
                        x_displacement = Tile.I_DISPLACEMENTS
                        # But add an extra displacement for the 7th neighbour (outermost node)
                        x_displacement.append(1) 
                        y_displacement = Tile.J_DISPLACEMENTS
                        # Add the displacement to get to the outerMostNode based on current node y value
                        y_displacement.append(playerEndPosition[1] - y)

                elif (playerEndPosition == self.blueEndPosition):
                    if (y == self.board_size-1):
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
                        
                        if not((x_n == playerEndPosition[0] and y_n == playerEndPosition[1]) or (x_n == playerStartPosition and y_n == playerEndPosition)):
                            neighbour = self._tiles[x_n][y_n]
                        # print("neighbour: ", neighbour.get_x(), neighbour.get_y())

                        neighbourTuple = (x_n,y_n)
                        if (not (x_n,y_n) in visited): # checks to see what neighbours value is and assigns weight based on value
                            if (neighbour.get_colour() == self.colour or neighbourTuple == playerEndPosition):
                                weight = 0

                            elif neighbour.get_colour() == self.opp_colour():
                                weight = math.inf


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
        # print("Move about to remove")
        # print(self._choices_copy)
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
