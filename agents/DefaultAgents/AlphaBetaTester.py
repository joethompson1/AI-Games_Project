import socket
import random
from random import choice
from time import sleep

INF = 9999

class NaiveAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234



    def run(self):
        """A finite-state machine that cycles through waiting for input
        and sending moves.
        """
        
        self._board_size = 0
        self._board = []
        self._colour = ""
        self._turn_count = 1
        self._choices = []
        self._choices_copy = []
        
        states = {
            1: NaiveAgent._connect,
            2: NaiveAgent._wait_start,
            3: NaiveAgent._make_move,
            4: NaiveAgent._wait_message,
            5: NaiveAgent._close
        }

        res = states[1](self)
        while (res != 0):
            res = states[res](self)

    def _connect(self):
        """Connects to the socket and jumps to waiting for the start
        message.
        """
        
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((NaiveAgent.HOST, NaiveAgent.PORT))

        self.create_moves()

        return 2

    def _wait_start(self):
        """Initialises itself when receiving the start message, then
        answers if it is Red or waits if it is Blue.
        """
        
        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "START"):
            self._board_size = int(data[1])
            for i in range(self._board_size):
                for j in range(self._board_size):
                    self._choices.append((i, j))
            self._colour = data[2]

            if (self._colour == "R"):
                return 3
            else:
                return 4

        else:
            print("ERROR: No START message received.")
            return 0

    def _make_move(self):
        """Makes a random valid move. It will choose to swap with
        a coinflip.
        """
        
        if (self._turn_count == 2 and choice([0, 1]) == 1):
            msg = "SWAP\n"
        else:
            self.pruned = 0
            move = choice(self._choices)
            msg = f"{move[0]},{move[1]}\n"
        
        self._s.sendall(bytes(msg, "utf-8"))

        return 4

    def _alpha_beta(self, colour, alpha, beta, depth=3):

        if colour == 'R':
            opp_colour = 'B'
        else:
            opp_colour = 'R'

        best_move = None
        best_value = -INF

        ## check if at max depth or if game is over

        if depth <= 0:
            best_value = self.random_evaluation(colour)
            best_move = None
            self._choices_copy = self._choices
            return best_value, best_move
        else:
            self.no_nodes_searched += 1
            moves = self._get_moves()
        
        for move in moves:

            self._make_dummy_move(move, colour)

            new_val, _ = self.alphabeta(opp_colour, -beta, -alpha, depth-1)

            new_val = -new_val

            if new_val > best_value:
                best_move = move
                best_value = new_val

            self._choices_copy.append(move)

            alpha = max(alpha, best_value)
            if alpha >= beta:
                self.pruned += 1
                break

        return best_value, best_move


    def _random_evaluation(self, colour):
        """ Evaluate board using a randomly generated number
        """
        self.eval_count += 1
        return self.local_random.randint(0, self.board.size*2)

    def _make_dummy_move(self, move, colour):
        
        #self._choices_dict = self._choices_dict.pop(move)
        self._choices_copy.remove(move)

        ### code to update the local board!

        return self._choices_copy ###  should also return local board

    def _get_moves(self):
        return self._choices_copy

    def _create_moves(self):
        for i in range(self._board_size):
            for j in range(self._board_size):
                self._choices_dict[(i, j)] = random.randint(0, 100)
                self._choices_copy.append([i, j])

    def _wait_message(self):
        """Waits for a new change message when it is not its turn."""

        self._turn_count += 1

        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "END" or data[-1] == "END"):
            return 5
        else:

            if (data[1] == "SWAP"):
                self._colour = self.opp_colour()
            else:
                x, y = data[1].split(",")
                self._choices.remove((int(x), int(y)))

            if (data[-1] == self._colour):
                return 3

        return 4

    def _close(self):
        """Closes the socket."""

        self._s.close()
        return 0

    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        
        if self._colour == "R":
            return "B"
        elif self._colour == "B":
            return "R"
        else:
            return "None"



if (__name__ == "__main__"):
    agent = NaiveAgent()
    agent.run()
