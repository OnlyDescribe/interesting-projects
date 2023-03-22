# -*- coding: utf-8 -*-
from __future__ import print_function
from enum import IntEnum, unique
import math
import random as rnd
import matplotlib.pyplot as plt
import time
from cube import Cube

from simanneal import Annealer  # from pypi

rnd.seed(24)


@unique
class Evolution(IntEnum):
    PERMUTATION_WITH_SETUP = 1
    PERMUTATION_WITH_DOUBLE_SETUP = 2

    COMMUCATOR = 3
    DOUBLE_COMMUCATOR = 4
    PERMUTATION = 5

    CONJAGATES_COMMUCATOR_WITH_SETUP = 6


SINGLE_MOVES = SETUP = [["U"], ["U'"], ["U2"],
                        ["D"], ["D'"], ["D2"],
                        ["R"], ["R'"], ["R2"],
                        ["L"], ["L'"], ["L2"],
                        ["F"], ["F'"], ["F2"],
                        ["B"], ["B'"], ["B2"],
                        ["E"], ["E'"], ["E2"],
                        ["M"], ["M'"], ["M2"],
                        ["S"], ["S'"], ["S2"],
                        [" "], [" "], [" "],
                        [" "], [" "], [" "],
                        [" "], [" "], [" "]]

SINGLE_MOVES_COMMUCATOR = [["U"], ["U'"], ["U2"],
                           ["D"], ["D'"], ["D2"],
                           ["R"], ["R'"], ["R2"],
                           ["L"], ["L'"], ["L2"],
                           ["F"], ["F'"], ["F2"],
                           ["B"], ["B'"], ["B2"],
                           ["E"], ["E'"], ["E2"],
                           ["M"], ["M'"], ["M2"],
                           ["S"], ["S'"], ["S2"],
                           ]

ROTATIONS = ["x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2", " ", " ", " "]

OLL = [
    # "R U2 R' U' R U' R'".split(" "),
    # "R U R' U R U' R' U R U2 R'".split(" "),
    # "F R' F' L x U R U' x' L'".split(" "),  # "F R' F' r U R U' r'".split(" "),
    # "R U2 R2 U' R2 U' R2 U2 R".split(" "),
    # "R U R' U R U2 R'".split(" "),
    # "L x U R' U' x' L' F R F'".split(" "),  # "r U R' U' r' F R F'".split(" "),
    # "R2 D R' U2 R D' R' U2 R'".split(" "),
    # # "F R U R' U' F' f R U R' U' f'".split(" "),
    # "F R U R' U' F' B z R U R' U' z' B'".split(" "),
    # "F R U R' U' F'".split(" "),
    # "B z R U R' U' z' B'".split(" "),  # "f R U R' U' f'".split(" "),
]

PLL = [
    "F R U' R' U' R U R' F' R U R' U' R' F R F'".split(" "),
    "R U R' U' R' F R2 U' R' U' R U R' F'".split(" "),
    "M2 U M2 U2 M2 U M2".split(" "),
    "R U' R U R U R U' R' U' R2".split(" "),
    "R2 U R U R' U' R' U' R' U R'".split(" "),
    "M' U M2 U M2 U M' U2 M2".split(" "),
]

PERMUTATIONS = OLL+PLL


class CubeSolver(Annealer):

    def __init__(self, state):
        self.Tmax = 0.37
        self.Tmin = 0.34

        self.steps = 500000
        self.updates = 1000

        self.progressFitness = []
        self.total_time = -1

        super(CubeSolver, self).__init__(state)

    def energy(self):
        """Calculates the fitness of the cube."""
        misplaced_stickers = 0
        for k, face in self.state.faces.items():
            # centers are fixed in a Rubik cube
            center = face[1, 1]

            for i in range(0, 3):
                for j in range(0, 3):
                    if face[i, j] != center:
                        misplaced_stickers += 1

        return misplaced_stickers
        # self.state.calculate_fitness()
        # self.state.calculate_fitness_euclidean()
        # self.state.calculate_fitness_hausdorff()
        # self.state.calculate_fitness_hausdorff_02()
        # return self.state.fitness

    def move(self, evolution_type):
        """Add permutations to the cube."""
        initial_energy = self.energy()

        if(evolution_type == Evolution.PERMUTATION_WITH_SETUP):
            self.state.execute(self.__rnd_rotation())
            self.state.execute(
                self.__rnd_permutation_with_setup())
        elif(evolution_type == Evolution.PERMUTATION_WITH_DOUBLE_SETUP):
            self.state.execute(self.__rnd_rotation())
            self.state.execute(
                self.__rnd_permutation_with_double_setup())

        elif(evolution_type == Evolution.PERMUTATION):
            self.state.execute(self.__rnd_rotation())
            self.state.execute(
                self.__rnd_permutation())

        elif(evolution_type == Evolution.DOUBLE_COMMUCATOR):
            # 生成公式蕴含了对称性, 不需要__rnd_rotation()
            self.state.execute(self.__rnd_double_commucator_with_setup())

        elif(evolution_type == Evolution.CONJAGATES_COMMUCATOR_WITH_SETUP):
            self.state.execute(
                self.__rnd_conjagates_commucator_with_setup())

        return self.energy() - initial_energy

    def copy_state(self, cube_state_from):
        cube_to = Cube()
        for f in cube_state_from.faces:
            for i in range(0, 3):
                for j in range(0, 3):
                    cube_to.faces[f][i, j] = cube_state_from.faces[f][i, j]

        cube_to.move_history = [item for item in cube_state_from.move_history]
        return cube_to

    def anneal(self):
        """Minimizes the energy of a system by simulated annealing."""
        step = 0
        self.start = time.time()

        # Precompute factor for exponential cooling from Tmax to Tmin
        if self.Tmin <= 0.0:
            raise Exception('Exponential cooling requires a minimum "\
                "temperature greater than zero.')
        Tfactor = -math.log(self.Tmax / self.Tmin)

        # Note initial state
        T = self.Tmax
        E = self.energy()
        prevState = self.copy_state(self.state)
        prevEnergy = E
        self.best_state = self.copy_state(self.state)
        self.best_energy = E
        trials = accepts = improves = 0
        if self.updates > 0:
            updateWavelength = self.steps / self.updates
            self.update(step, T, E, None, None)

        # Attempt moves to new states
        while step < self.steps and not self.user_exit:
            step += 1
            T = self.Tmax * math.exp(Tfactor * step / self.steps)

            rand = rnd.random()

            # evolution_type = Evolution.PERMUTATION  # Comparison 01

            # Algorithm 01
            if rand < 0.4:
                evolution_type = Evolution.PERMUTATION_WITH_SETUP
            elif rand < 1:
                evolution_type = Evolution.PERMUTATION_WITH_DOUBLE_SETUP

            # Algorithm 02
            # if rand < 0:
            #     evolution_type = Evolution.COMMUCATOR
            # elif rand < 1:
            #     evolution_type = Evolution.CONJAGATES_COMMUCATOR_WITH_SETUP

            dE = self.move(evolution_type)

            E += dE
            trials += 1

            # if dE = 0, it will add a lot of permutations to the cube.
            if dE == 0:
                dE = 1
            elif dE > 0.0 and math.exp(-dE / T) < rand:
                # if dE > 0.0 and math.exp(-dE / T) < rand:
                # Restore previous state
                self.state = self.copy_state(prevState)
                E = prevEnergy
                self.progressFitness.append(E)
            else:
                # Accept new state and compare to best state
                accepts += 1
                if dE < 0.0:
                    improves += 1
                prevState = self.copy_state(self.state)
                prevEnergy = E

                self.progressFitness.append(E)

                if E < self.best_energy:
                    self.best_state = self.copy_state(self.state)
                    self.best_energy = E

            if self.updates > 1:
                if (step // updateWavelength) > ((step - 1) // updateWavelength):
                    self.update(
                        step, T, E, accepts / trials, improves / trials)
                    trials = accepts = improves = 0
                if(E == 0):
                    self.update(
                        step, T, E, accepts / trials, improves / trials)
                    trials = accepts = improves = 0
                    break
        self.total_time = time.time() - self.start
        self.state = self.copy_state(self.best_state)
        if self.save_state_on_exit:
            self.save_state()

        # Return best state and energy
        return self.best_state, self.best_energy

    def __rnd_permutation(self):
        r = rnd.randint(0, len(PERMUTATIONS) - 1)
        return PERMUTATIONS[r]

    def __rnd_rotation(self):
        r = rnd.randint(0, len(ROTATIONS) - 1)
        return [ROTATIONS[r]]

    def __rnd_commucator(self):
        r_s = rnd.randint(0, len(SINGLE_MOVES_COMMUCATOR) - 1)
        r_p = rnd.randint(0, len(SINGLE_MOVES_COMMUCATOR) - 1)
        return [item
                for subset in [SINGLE_MOVES_COMMUCATOR[r_p], SINGLE_MOVES_COMMUCATOR[r_s],
                               inv_permutation(SINGLE_MOVES_COMMUCATOR[r_p]), inv_permutation(SINGLE_MOVES_COMMUCATOR[r_s])]
                for item in subset]

    def __rnd_conjugates(self):
        r_s_1 = rnd.randint(0, len(SETUP) - 1)
        r_s_2 = rnd.randint(0, len(SETUP) - 1)
        r_c = rnd.randint(0, len(SINGLE_MOVES_COMMUCATOR) - 1)
        return [item
                for subset in [SETUP[r_s_1], SETUP[r_s_2], SINGLE_MOVES_COMMUCATOR[r_c],
                               inv_permutation(SETUP[r_s_1]), inv_permutation(SETUP[r_s_2])]
                for item in subset]

    def ___rnd_double_conjugates(self):
        r_s_1 = rnd.randint(0, len(SETUP) - 1)
        r_s_2 = rnd.randint(0, len(SETUP) - 1)
        r_c_1 = rnd.randint(0, len(SINGLE_MOVES_COMMUCATOR) - 1)
        r_c_2 = rnd.randint(0, len(SINGLE_MOVES_COMMUCATOR) - 1)
        return [item
                for subset in [SETUP[r_s_1], SETUP[r_s_2], SINGLE_MOVES_COMMUCATOR[r_c_1], SINGLE_MOVES_COMMUCATOR[r_c_2],
                               inv_permutation(SETUP[r_s_1]), inv_permutation(SETUP[r_s_2])]
                for item in subset]

    def __rnd_double_commucator_with_setup(self):
        r_s_1 = rnd.randint(0, len(SETUP) - 1)
        r_s_2 = rnd.randint(0, len(SETUP) - 1)

        r = rnd.random()
        if r < 0.5:
            permutation_02 = self.__rnd_conjugates()
        elif r < 1:
            permutation_02 = self.__rnd_commucator()
        r = rnd.random()
        if r < 0.5:
            permutation_01 = self.__rnd_commucator()
        elif r < 1:
            permutation_01 = self.__rnd_conjugates()

        return [item
                for subset in [SETUP[r_s_1], SETUP[r_s_2], permutation_01, permutation_02,
                               inv_permutation(permutation_01), inv_permutation(
                                   permutation_02),
                               inv_permutation(SETUP[r_s_1]), inv_permutation(SETUP[r_s_2])]
                for item in subset]

    def __rnd_conjagates_commucator_with_setup(self):
        r_s_1 = rnd.randint(0, len(SETUP) - 1)
        r_s_2 = rnd.randint(0, len(SETUP) - 1)

        r = rnd.random()
        if r < 0.3:
            permutation_02 = self.__rnd_conjugates()
        elif r < 6:
            permutation_02 = self.__rnd_commucator()
        elif r < 1:
            permutation_02 = self.___rnd_double_conjugates()
        r = rnd.random()
        if r < 0.3:
            permutation_01 = self.__rnd_conjugates()
        elif r < 6:
            permutation_01 = self.__rnd_commucator()
        elif r < 1:
            permutation_01 = self.___rnd_double_conjugates()

        return [item
                for subset in [SETUP[r_s_1], SETUP[r_s_2], permutation_01, permutation_02,
                               inv_permutation(permutation_01), inv_permutation(
                                   permutation_02),
                               inv_permutation(SETUP[r_s_1]), inv_permutation(SETUP[r_s_2])]
                for item in subset]

    def __rnd_permutation_with_setup(self):
        r_p = rnd.randint(0, len(PERMUTATIONS) - 1)
        r_s = rnd.randint(0, len(SETUP) - 1)
        return [item
                for subset in [SETUP[r_s],
                               PERMUTATIONS[r_p], inv_permutation(SETUP[r_s])]
                for item in subset]

    def __rnd_permutation_with_double_setup(self):
        r_p = rnd.randint(0, len(PERMUTATIONS) - 1)
        r_s = rnd.randint(0, len(SETUP) - 1)
        r_s_2 = rnd.randint(0, len(SETUP) - 1)
        return [item
                for subset in [SETUP[r_s], SETUP[r_s_2],
                               PERMUTATIONS[r_p], inv_permutation(SETUP[r_s]), inv_permutation(SETUP[r_s_2])]
                for item in subset]

def inv_permutation(permutation):
    def func(x):
        if(x[-1] == "'"):
            return x[:-1]
        elif(x[-1] == "2"):
            return x
        elif(x == " "):
            return x
        else:
            return x+"'"

    return list(map(func,
                    permutation))[::-1]


def main():

    scramble_str_array = [
        "U2 B' F L B' F2 D' U B2 R' U B' F U F' R' U2 L' R' D F2 R' F' D2 L' R2 B' D L U2",
        "R' U' L2 B2 U2 F L2 B' L' B D R B F2 L F R' B2 F' L B' D B2 R2 D' U B2 F' D R2",
        "B' R' U2 B' F D2 R2 B F' L2 R' B2 D2 L2 F' U L B2 D F L' F R B2 D' U' B' L' B' F2",
        "F2 D2 U L' R' B2 L2 R2 B F L D' L2 D U' L' D' B2 D2 R' U L R' D' U L' R2 U F' L'",
        "D' B2 D2 L2 U' L R' F L2 R2 U' L2 B' L D' B2 R2 B' R F U2 R B2 F' L' B2 L2 R F2 L'",
        "L' U2 R' B2 L' F2 U2 D L U' L2 D2 U2 R' D' U R2 D' F2 L F R' B L2 U'",
        "L' F U2 B' R' L' U2 R L' D2 F B2 R' U2 B' L' U2 F2 U2 L F2 D2 B' U2 F2",
        "B2 U B D B2 L' D2 R L2 D2 R D L' F' L R F2 B' D2 R D' R2 L' U D2",
        "R2 D' L2 B' L' R B' F R' U2 F' R' U' D F2 D' U' B2 D2 B2 U2 L' U B' D2",
        "D' L2 F' U2 L2 R F' R2 L2 U' L B2 R B U B2 R2 L2 U2 R B' F R' F' L2", 

        # "D2 F2 D U' L D' L U2 L U D L2 U2 L' D' R D2 U F2 L D U2 B' L2 B'", 
        # "U2 R L' U D' R' F' L' D L R' B' D2 R U' F' L D2 L2 D' B' L' B' F L2", 
        # "R' D2 B' L F B U' R' D F2 R' B2 U' D2 R U2 L B' F D2 B2 F U2 D2 F", 

    ]
    progressFitness_all = []
    total_time_all = []
    algorithms_len_all = []
    for scramble_str in scramble_str_array:
        scramble = scramble_str.split(" ")
        state = Cube()
        state.execute(scramble)
        solver = CubeSolver(state)

        state, _ = solver.anneal()
        progressFitness_all.append(solver.progressFitness)
        total_time_all.append(solver.total_time)
        algorithms_len_all.append(
            len([i for i in state.get_algorithm() if i != ' ']))
        print('\n', state)

    _, ax = plt.subplots(1, 1, figsize=(18, 12))

    for i, progressFitness in enumerate(progressFitness_all):
        ax.plot([i for i in range(len(progressFitness))],
                progressFitness,
                label="scramble {}, time: {:.2f}, length: {}".format(
                    i, total_time_all[i], algorithms_len_all[i]),
                alpha=0.5,
                marker='o',
                markersize=8)
        ax.grid()
        ax.axis(xmin=0, ymin=0, xmax=max([len(i)
                for i in progressFitness_all])+20)
        plt.xlabel('step')
        plt.ylabel('Energy')
        ax.legend(fontsize=14)

    plt.savefig('PERMUTATION.png',
                dpi=300, bbox_inches='tight')

    plt.show()


if __name__ == '__main__':
    main()
