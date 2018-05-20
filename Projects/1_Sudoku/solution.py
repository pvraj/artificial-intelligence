
from utils import *


row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]

# because we need to solve diagonal, we add the 2 units for the left and right diagonals
diagonal_left = [(row + cols[index]) for index, row in enumerate(rows)]
diagonal_right = [(rows[index] + col) for index, col in enumerate(reversed(cols))]
diagonal_units = [diagonal_left, diagonal_right]

unitlist = row_units + column_units + square_units + diagonal_units
# print("row units: %s" % row_units)
# print("column units: %s" % column_units)
# print("square units: %s" % square_units)
# print("diagonal left: %s" % diagonal_left)
# print("diagonal right: %s" % diagonal_right)
# print("the length: %s " % len(unitlist))

# Must be called after all units (including diagonals) are added to the unitlist
units = extract_units(unitlist, boxes)
peers = extract_peers(units, boxes)


def naked_twins(values):
    """Eliminate values using the naked twins strategy.

    The naked twins strategy says that if you have two or more unallocated boxes
    in a unit and there are only two digits that can go in those two boxes, then
    those two digits can be eliminated from the possible assignments of all other
    boxes in the same unit.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the naked twins eliminated from peers

    Notes
    -----
    Your solution can either process all pairs of naked twins from the input once,
    or it can continue processing pairs of naked twins until there are no such
    pairs remaining -- the project assistant test suite will accept either
    convention. However, it will not accept code that does not process all pairs
    of naked twins from the original input. (For example, if you start processing
    pairs of twins and eliminate another pair of twins before the second pair
    is processed then your code will fail the PA test suite.)

    The first convention is preferred for consistency with the other strategies,
    and because it is simpler (since the reduce_puzzle function already calls this
    strategy repeatedly).
    """
    # High Level Logic:
    # for each unit in unitlist
    # for each pair of naked twins in the unit
    # remove the naked twins values from all other boxes in that unit

    for unit in unitlist:
        # 1. make a dictionary for the unit, unit_sets, where each item is: box ---> {digit, digits} (set).
        # {'A1': { '1', '2'}, 'A2': {'3', '4', '1', '2'}...}
        unit_sets = {}
        for box in unit:
            unit_sets[box] = set(values[box])

            # 2. make another set, naked_sets; contains all frozen_sets that appear exactly twice (twins)
            # {{'1', '2'}, {'3', '4'}}

            # (2a) First, make a dictionary, set_frequency that maps unit_sets --> frequency in the unit.
            # { {'1', '2'} : 2, {'3', '4'} : 3, .... }
        set_frequency = {}
        for box_set in unit_sets:
            if frozenset(unit_sets[box_set]) in set_frequency:
                set_frequency[frozenset(unit_sets[box_set])] += 1
            else:
                set_frequency[frozenset(unit_sets[box_set])] = 1

                # (2b) Second, make a set, naked_sets, that contain all items from set_frequency that have a frequency of 2 and have exactly 2 items (naked_twins).
                # { {'1', '2' } : 2, {'3', '4'} : 2, ...}
        naked_sets = set()
        for freq_set in set_frequency:
            if (len(freq_set) == 2) and (set_frequency[freq_set] == 2):
                naked_sets.add(freq_set)

                # 3. For each naked_set (naked_twin) in naked_sets, for each box in unit_sets
                # if the length of the naked_set is smaller (to ensure we reduce a box that has at least 3 items (ruling out boxes that already have single values, boxes already have been reduced to twins, or boxes with 2 items) OR if the length is the same (both 2) and the sets are not equal (ruling out twins)
                # take the set difference, update the unit_sets[box] value and the values dictionary.
        for naked_set in naked_sets:
            for box in unit_sets:
                if ((len(naked_set) < len(unit_sets[box])) or (
                        len(naked_set) == len(unit_sets[box]) and (naked_set != unit_sets[box]))):
                    unit_sets[box] = (unit_sets[box] - naked_set)
                    new_box_value = ""
                    for item in sorted(list(unit_sets[box])):
                        new_box_value += item
                    assign_value(values, box, new_box_value)
    return values


def eliminate(values):
    """Apply the eliminate strategy to a Sudoku puzzle

    The eliminate strategy says that if a box has a value assigned, then none
    of the peers of that box can have the same value.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the assigned values eliminated from peers
    """
    for box in boxes:
        if len(values[box]) == 1:
            for peer in peers[box]:
                assign_value(values, peer, values[peer].replace(values[box], ''))
    return values


def only_choice(values):
    """Apply the only choice strategy to a Sudoku puzzle

    The only choice strategy says that if only one box in a unit allows a certain
    digit, then that box must be assigned that digit.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with all single-valued boxes assigned

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    """
    for unit in unitlist:  # [A1, A2] , [A1, B1], etc.
        unit_frequency_map = {}
        unit_frequency_map_once = {}
        unsolved_boxes = []
        for box in unit:  # A1, A2, etc.
            if len(values[box]) > 1:
                unsolved_boxes.append(box)
            for box_value in values[box]:  # get the frequency of all of them
                if box_value in unit_frequency_map:
                    unit_frequency_map[box_value] += 1
                else:
                    unit_frequency_map[box_value] = 1

        for item in unit_frequency_map:
            if unit_frequency_map[item] == 1:
                unit_frequency_map_once[item] = 1

        for single_item in unit_frequency_map_once:  # if something occurs once,
            for unsolved_box in unsolved_boxes:
                if single_item in values[unsolved_box]:  # and an unsolved box contains it
                    assign_value(values, unsolved_box, single_item)
    return values


def reduce_puzzle(values):
    """Reduce a Sudoku puzzle by repeatedly applying all constraint strategies

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary after continued application of the constraint strategies
        no longer produces any changes, or False if the puzzle is unsolvable 
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])

        # Your code here: Use the Eliminate Strategy
        values = eliminate(values)

        # Your code here: Use the Only Choice Strategy
        values = only_choice(values)

        # put in call to naked twins here?
        values = naked_twins(values)

        # Check how many boxes have a determined value, to compare
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])
        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after
        # Sanity check, return False if there is a box with zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values

def get_unsolved_boxes_by_num_possibilities(values):
    ''' Take as input the dictionary

        Return an ordered list of boxes. The boxes should be ordered in ascending order of number of possibilities
        (for example, if A1 has 2 possible values, and A5 has 6 possible values, the order would be A1, A5, etc.

    '''
    unsolved_boxes_map = {}
    for box in values:
        if len(values[box]) > 1:
            unsolved_boxes_map[box] = values[box]
    unsolved_boxes_ordered = [box for box in
                              sorted(unsolved_boxes_map, key=lambda box: len(values[box]), reverse=False)]
    return unsolved_boxes_ordered

def search(values):
    """Apply depth first search to solve Sudoku puzzles in order to solve puzzles
    that cannot be solved by repeated reduction alone.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary with all boxes assigned or False

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    and extending it to call the naked twins strategy.
    """
    "Using depth-first search and propagation, create a search tree and solve the sudoku."
    values = reduce_puzzle(values)  # First, reduce the puzzle using the previous function
    if values is False:
        return False

    if len([box for box in values.keys() if len(values[box]) == 1]) == 81:
        return values
    else:
        unsolved_boxes_ordered = get_unsolved_boxes_by_num_possibilities(values)
        unsolved_box = unsolved_boxes_ordered[0]
        for possibility in values[unsolved_box]:  # for each possible value in the unsolved box
            temp_values = values.copy()  # create a temporary version of the values dictionary,
            temp_values[unsolved_box] = possibility  # with our conjecture
            # print("conjecture %s --> %s" % (unsolved_box, possibility))
            temp_search_result = search(temp_values)  # Now use recursion to solve each one of the resulting sudokus,
            if temp_search_result:  # and if one returns a value (not False), return that answer!
                return temp_search_result


def solve(grid):
    """Find the solution to a Sudoku puzzle using search and constraint propagation

    Parameters
    ----------
    grid(string)
        a string representing a sudoku grid.
        
        Ex. '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'

    Returns
    -------
    dict or False
        The dictionary representation of the final sudoku grid or False if no solution exists.
    """
    values = grid2values(grid)
    values = search(values)
    return values


if __name__ == "__main__":
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(grid2values(diag_sudoku_grid))
    result = solve(diag_sudoku_grid)
    display(result)

    try:
        import PySudoku
        PySudoku.play(grid2values(diag_sudoku_grid), result, history)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
