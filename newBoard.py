# encoding: utf-8

import ipdb

class InvalidMove(Exception):
    def __init__(self, msg=""):
        self.msg = msg
    def __str__(self):
        return self.msg

class Space(object):
    #~ Parts of the board that make up the piece location.  The space is needed
    #~ for the linking_spaces method in Board
    letters_numbers = ("abcdefgh  ", "12345678  ")

    #~ These are the direction on how to find the neighboring squares. Origin is
    #~ at "a1", letters are along x,  numbers are along y
    #~ Increasing in letters/numbers gives +delta
    #~ Decreasing in letters/numbers gives -delta
    #~ The leading "_" is to help clean up namespace when working from cmdline
    compus_deltas = dict(
        _N  = ( 0,  1), _S  = ( 0, -1), _E  = ( 1,  0), _W  = (-1,  0),
        _NE = ( 1,  1), _NW = (-1,  1), _SE = ( 1, -1), _SW = (-1, -1),
        #~ _L's are knight moves from the square
        _L1 = ( 1,  2), _L2 = ( 1, -2), _L3 = ( 2,  1), _L4 = ( 2, -1),
        _L5 = (-1,  2), _L6 = (-1, -2), _L7 = (-2,  1), _L8 = (-2, -1))

    #~ Translate the compus direction into the geometric direction.
    #~ H: Horizontal
    #~ V: Vertical
    #~ L: Knight
    compus_translations = dict(
        _N  = "V", _S  = "V", _E  = "H", _W  = "H", _NE = "D", _NW = "D", _SE = "D", _SW = "D",
        _L1 = "L", _L2 = "L", _L3 = "L", _L4 = "L", _L5 = "L", _L6 = "L", _L7 = "L", _L8 = "L")

    #~ Geographical direction around the square.  List to loop over when finding
    #~ neighbors.
    compus_directions = ["_N" , "_S" , "_E" , "_W" , "_NE", "_NW", "_SE", "_SW",
                         "_L1", "_L2", "_L3", "_L4", "_L5", "_L6", "_L7", "_L8"]

    def __init__(self, location):
        self.location = location
        self.piece = Empty(location)

    def __str__(self):
        return self.location

    def init(self, board):
        self.board = board
        self._link_spaces(board)

    def move(self, to):
        try:
            self.piece.move(self.get_paths(), to)
        except InvalidMove:
            return False
        else:
            self.piece.square = self.board.__getattr__(to)
            self.board.__getattr__(to).piece = self.piece
            self.piece = Empty(self.location)
            self.board.show()

    def get_paths(self):
        """Get all the squares that have access to attack this square."""
        paths = {"H": set(), "V": set(), "D": set(), "L": set()}
        origin = self
        for direction in self.compus_directions:
            path = paths[self.compus_translations[direction]]
            path = self._get_path(direction, path)
            self = origin
            paths[self.compus_translations[direction]] = path
        return paths

    def _get_path(self, direction, path):
        """Get all the squares that have access to attack this square with the
        direction passed."""
        current_color = self.piece.color
        while True:
            space = getattr(self, direction)
            #~ None implies we're at the edge of the board
            if space is None:
                break

            #~ colors match meaning we're attacking our own piece.  Only save up to the
            #~ piece and not the piece as we can't capture.
            if (current_color != "wb".replace(space.piece.color, "")) and space.piece.color:
                return path

            #~ colors are different meaning we're attaching a valid piece. Save up to and
            #~ including the piece first encountered.
            elif (current_color == "wb".replace(space.piece.color, "")) and space.piece.color:
                path.add(space)
                return path

            path.add(space)
            #~ L shape moves only propagate one space for every direction.
            if direction.startswith("_L"):
                return path

            #~ Set the neighbor as the current square.
            self = space
        return path

    def _link_spaces(self, board):
        """Finds all the neighboring squares to this square and sets an attr
        to the neighboring object."""
        for direction in self.compus_directions:
            setattr(self, direction, self._find_neighbors(board, direction))

    def _find_neighbors(self, board, direction):
        """Finds neighbor's object in the board given compus direction."""
        neighbor = []
        for part, delta, variables in zip(self.location, self.compus_deltas[direction], self.letters_numbers):
            try:
                position = variables.find(part)
                neighbor.append(variables[position + delta])
            except (ValueError, IndexError):
                return None
        try:
            return board[neighbor[0]][neighbor[1]]
        except KeyError:
            return None


class Piece(object):

    pieces = {"King"  : {"b": "♔", "w": "♚"},
              "Queen" : {"b": "♕", "w": "♛"},
              "Rook"  : {"b": "♖", "w": "♜"},
              "Bishop": {"b": "♗", "w": "♝"},
              "Knight": {"b": "♘", "w": "♞"},
              "Pawn"  : {"b": "♙", "w": "♟"},
              "Empty" : {"" : " "}}

    def __init__(self, square, color=""):
        self.move_count = 0
        self.square     = square
        self.color      = color
        self.name       = self.__class__.__name__
        self.piece      = self.pieces[self.name][self.color]

    def __str__(self):
        return self.piece

    def move(self, paths, to):
        from_letter, from_number = self.square.location
        to_letter, to_number = to

        dx = "abcdefgh".find(to_letter) - "abcdefgh".find(from_letter)
        dy = "12345678".find(to_number) - "12345678".find(from_number)

        return self._move(paths, to, dx, dy)


class Empty(Piece):
    def __init__(self, square):
        Piece.__init__(self, square)

    def _move(self, *args):
        raise InvalidMove("Must select a square with a piece on it")


class Pawn(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

        #~ The direction that the piece must move, only needed with Pawns
        if self.color == "w":
            #~ Must move up the board
            self.must_move = 1
        else:
            #~ Must move down the board
            self.must_move = -1

    def _move(self, paths, to, dx, dy):
        valid_V_locations = map(lambda x: x.location, paths["V"])
        valid_D_locations = map(lambda x: x.location, paths["D"])

        valid_moves = [
        #~ Normal attack
        ((dy * self.must_move) == 1) and (to in valid_D_locations) and (self.square.board.__getattr__(to).piece.name is not "Empty"),
        #~ Move one square
        ((dy * self.must_move) == 1) and (to in valid_V_locations) and (self.square.piece.name is "Empty"),
        #~ Move two squares on first move
        ((dy * self.must_move) == 2) and (to in valid_V_locations) and (self.move_count == 0),
        #~ Enpassant
        False]

        if any(valid_moves):
            return True
        raise InvalidMove("Invalid Pawn Move")


class Rook(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

    def _move(self, paths, to, dx, dy):
        valid_V_locatoins = map(lambda x: x.location, paths["V"])
        valid_H_locations = map(lambda x: x.location, paths["H"])

        valid_moves = [
        (abs(dy) > 1) and (dx == 0) and (to in valid_V_locations),
        (abs(dx) > 1) and (dy == 0) and (to in valid_H_locations)]

        if any(valid_moves):
            return True
        raise InvalidMove("Invalid Rook Move")


class Knight(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

    def _move(self, paths, to, dx, dy):
        valid_L_locations = map(lambda x: x.location, paths["L"])

        if to in valid_L_locations:
            return True
        raise InvalidMove("Invalid Knight Move")


class Bishop(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

    def _move(self, paths, to, dx, dy):
        valid_D_locations = map(lambda x: x.location, paths["D"])

        if to in valid_D_locations:
            return True
        raise InvalidMove("Invalid Bishop Move")


class King(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

    def _move(self, paths, to, dx, dy):
        valid_V_locations = map(lambda x: x.location, paths["V"])
        valid_D_locations = map(lambda x: x.location, paths["D"])
        valid_H_locations = map(lambda x: x.location, paths["H"])

        valid_moves = [
            ((abs(dx) == 1) or (abs(dy) == 1)) and ((to in valid_V_locations) or
            (to in valid_H_locations) or (to in valid_D_locations)),]

        if any(valid_moves):
            return True
        raise InvalidMove("Invalid King Move")


class Queen(Piece):
    def __init__(self, square, color):
        Piece.__init__(self, square, color)

    def _move(self, paths, to, dx, dy):
        valid_V_locations = map(lambda x: x.location, paths["V"])
        valid_D_locations = map(lambda x: x.location, paths["D"])
        valid_H_locations = map(lambda x: x.location, paths["H"])

        if (to in valid_H_locations) or (to in valid_H_locations) or (to in valid_H_locations):
            return True
        raise InvalidMove("InvalidQueenMove")


class Board(dict):
    #~ Makes a dict of all the free spaces for the board
    free_spaces = {letter:{number:Space(letter+number) for number in "12345678"} for letter in "abcdefgh"}

    def __init__(self, sub_dict=False):

        if sub_dict:
            self.sub = sub_dict
        else:
            self.sub = self.free_spaces

        #~ Handle the nested dicts
        for key in self.sub.keys():
            if (type(self.sub[key]) is dict):
                self[key] = Board(self.sub[key])
            else:
                self[key] = self.sub[key]

        #~ We're at the last file, we can now link our squares together.
        if key == "h":
            self._link_spaces()
            self._setup_pieces()

    def show(self):
        #~ "┌ ┐ └ ┘ ┬ ┴ ├ ┤ ─ │ ┼"
        print " ┌───┬───┬───┬───┬───┬───┬───┬───┐"
        for number in "87654321":
            row = []
            for letter in "abcdefgh":
                row.append(self.get(letter + number).piece)
            print number + "│ {} │ {} │ {} │ {} │ {} │ {} │ {} │ {} │".format(*row)
            if number == "1": break
            print " ├───┼───┼───┼───┼───┼───┼───┼───┤"
        print " └───┴───┴───┴───┴───┴───┴───┴───┘"
        print "   a   b   c   d   e   f   g   h"

    def __getattr__(self, location):
        letter, number = location
        return self[letter][number]

    def get(self, location):
        letter, number = location
        return self[letter][number]

    def _link_spaces(self):
        for letter in self.keys():
            for number in self[letter].keys():
                self[letter][number].init(self)

    def _setup_pieces(self):
        lineup = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for piece, letter in zip(lineup, "abcdefgh"):
            for number, color in zip("18", "wb"):
                square = self.get(letter+number)
                square.piece = piece(square, color)
            for number, color in zip("27", "wb"):
                square = self.get(letter+number)
                square.piece = Pawn(square, color)


if __name__ == "__main__":
    b = Board()
    b.a2.piece = Pawn(b.a2, 'w')

    b.a2.move("a4")
    b.b7.move("b5")

