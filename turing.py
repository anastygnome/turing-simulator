#!/usr/bin/env python3
"""
Lit la description d'une machine de Turing depuis un fichier et la simule.
Lors de l'exécution, renvoie le code d'erreur 1 en cas d'erreur de syntaxe,
dans la description de la machine et 74 en cas d'erreur d'entrée/sortie.
"""
import argparse
from collections import deque
from pathlib import Path
import re
from sys import stderr, exit as sys_exit  # exit ne s'utilise que dans l'interpréteur
from typing import Deque, Dict, Set, Tuple


def simulate_turing_machine(
    tape: Deque[str],
    initial_state: str,
    transitions: Dict[Tuple[str, str], Tuple[str, str, str]],
    debug: bool = True,
) -> Tuple[str, Deque[str]]:
    """
    Simule une machine de Turing.

    :param tape: Le ruban de la machine de Turing.
    :param etat_initial: L'état initial de la machine de Turing.
    :param transitions: Les transitions de la machine de Turing.
    :param debug: Si True, affiche des informations de débogage pendant la simulation.
    :return: L'état final et le ruban à la fin du calcul par la machine de Turing.
    """
    if not tape:
        return initial_state, []

    current_state = initial_state
    current_index = 0
    if debug:
        print(
            (
                f"DEBUG:initial state: {current_state}\nDEBUG:tape: {tape}\nDEBUG:head"
                f" = {tape[current_index]if tape[current_index] != ' ' else '␣'} at"
                f" position {current_index+1}\n"
            ),
            file=stderr,
        )

    while (current_state, tape[current_index]) in transitions:
        # Met à jour le ruban avec le symbole de sortie
        # de la transition courante
        next_transition = transitions[(current_state, tape[current_index])]
        output_symbol, movement_direction, next_state = next_transition
        tape[current_index] = output_symbol

        # Met à jour l'index de la tête de lecture/écriture et gère les dépassements
        if movement_direction == ">":
            current_index += 1
        elif movement_direction == "<":
            current_index -= 1

        if current_index < 0:
            tape.appendleft(" ")
            current_index = 0

        elif current_index == len(tape):
            tape.append(" ")

        current_state = next_state

        if debug:
            print(
                (
                    f"DEBUG:next state: {current_state}\nDEBUG:tape: {tape}\nDEBUG:head"
                    f" = {tape[current_index]if tape[current_index] != ' ' else '␣'} at"
                    f" position {current_index+1}\n"
                ),
                file=stderr,
            )

    # Retire les blancs surnuméraires de la bande avant le renvoi.
    while tape and tape[-1] == " ":
        tape.pop()

    while tape and tape[0] == " ":
        tape.popleft()

    return current_state, tape


def parse_turing_machine(
    tape: Deque[str], file_path: str, debug: bool = True
) -> Tuple[Set[str], Set[str], str, Dict[Tuple[str, str], Tuple[str, str, str]]]:
    """
    Initialise une machine de Turing à partir d'un fichier de description.
    L'espace sert de caractère blanc.

    :param debug: Si True, affiche des informations de débogage pendant la simulation.
    :type debug: Bool
    :param tape: Le ruban initial de la machine de Turing.
    :type tape: List[str]
    :param file_path: Le chemin du fichier de description.
    :type file_path: str
    :return: Un tuple contenant la description de la machine de Turing.
    :rtype: Tuple[Set[str], Set[str], str, Dict[Tuple[str, str], Tuple[str, str, str]]]
    """
    regex = re.compile(
        r"([^#]+),(.):(?:([^<>]|[<>](?=,[<>])),)?(?:([<>]),)?(?!\s*$)([^#]+)",
        re.IGNORECASE,
    )

    states = set()
    alphabet = set()
    transitions = {}
    try:
        with file_path.open() as f:
            for lineno, line in enumerate(f):
                # Ignore les caractères espaces au début en à la fin des lignes,
                # et filtre les commentaires et les lignes vides.²
                lin = line.strip()
                if not lin or lin[0] == "#":
                    continue
                try:
                    if debug:
                        print(
                            (
                                "DEBUG: result of parsing line"
                                f" {lineno+1}: {regex.match(lin).groups()}"
                            ),
                            file=stderr,
                        )
                    # Lit chaque ligne pour extraire les informations des transitions
                    state_in, symbol_in, symbol_out, movement, state_out = regex.match(
                        lin
                    ).groups()

                    # Gère les espaces en fin de ligne
                    # La regex impose que cette chaine sera non-vide.
                    state_out = state_out.rstrip()

                except AttributeError:
                    print(f"ERROR: Syntax error at line {lineno+1}", file=stderr)
                    sys_exit(1)

                if not states:
                    initial_state = state_in
                if symbol_out is None:
                    symbol_out = symbol_in

                states.update([state_in, state_out])
                alphabet.update([symbol_in, symbol_out])
                if (state_in, symbol_in) in transitions:
                    print(
                        (
                            f"WARNING: Duplicated transition found at line {lineno+1} :"
                            f" {(state_in,symbol_in)}. Overwriting"
                        ),
                        file=stderr,
                    )

                transitions[(state_in, symbol_in)] = (symbol_out, movement, state_out)

    except IOError as e:
        # En cas d'erreur d'entrée/sortie, on affiche l'erreur à l'utilisateur
        # et on interrompt le script en renvoyant 74 (convention de sysexits.h)
        print(f"ERROR: Error while reading from {file_path}: {e.args[1]}", file=stderr)
        sys_exit(74)

    # Le symbole blanc n'est pas dans l'alphabet.
    alphabet.discard(" ")

    # Affiche les informations de la machine de Turing
    print(
        f"Turing machine represented by {file_path}\n\nAlphabet : {alphabet}\nPossible"
        f" states : {states}\nStart state: {initial_state}\nTransition"
        f" table:\n{transitions}\nTape : {list(tape)}"
    )

    return alphabet, states, initial_state, transitions


if __name__ == "__main__":
    # Lit les arguments de la ligne de commande
    parser = argparse.ArgumentParser(
        description="Turing Machine Simulator",
        epilog=(
            "For more information, please refer to https://zanotti.univ-tln.fr/turing/"
        ),
    )

    parser.add_argument(
        "file_path", type=Path, help="file describing the Turing machine to simulate"
    )
    parser.add_argument(
        "input",
        nargs="+",
        type=str,
        help="input to be written on the tape",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        default=0,
        help=(
            "show each execution step if set once, also show each parsing step if set"
            " twice."
        ),
    )
    args = parser.parse_args()

    # Pré-traite les symboles de la bande pour obtenir une liste (doublement chaînée) de caractères
    # On utilise ces listes pour pouvoir ajouter et retirer des case en temps constant.
    m_tape = deque("".join(args.input))

    m_alphabet, m_states, m_initial_state, m_transitions = parse_turing_machine(
        m_tape, args.file_path, debug=args.debug >= 2
    )

    print("\nSimulation results:")
    m_final_state, m_tape = simulate_turing_machine(
        m_tape, m_initial_state, m_transitions, debug=args.debug
    )
    print(f"Machine halted in state: {m_final_state}\nTape: {list(m_tape)}")
