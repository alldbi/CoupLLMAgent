from typing import List, Optional, Tuple
import random
import time
import itertools
import os
from openai import OpenAI

from src.models.action import (Action,
                               ActionType,
                               AssassinateAction,
                               CounterAction,
                               CoupAction,
                               ExchangeAction,
                               ForeignAidAction,
                               IncomeAction,
                               StealAction,
                               TaxAction,
                               CounterActionType,
                               get_counter_action, )

from src.models.players.base import BasePlayer
from src.models.action import Action, ActionType
from src.models.card import Card, CardType
from src.models.players.base import BasePlayer
from src.utils.print import print_text, print_texts

from src.models.players.prompts import (choose_action_chain,
                                        challenge_chain,
                                        remove_chain,
                                        exchange_chain, counter_chain)

# from src.models.players.chains import (llm_determine_challenge,
#                                        llm_determine_counter,
#                                        llm_remove_card,
#                                        llm_choose_exchange_cards, )


class LLMAgent(BasePlayer):
    is_ai: bool = True
    is_agent: bool = True

    def choose_action(self, other_players: List[BasePlayer],
                      revealed_cards: List[Card], deck_len: int, treasury: int) -> Tuple[Action, Optional[BasePlayer]]:
        """Choose the next action to perform"""

        available_actions = self.available_actions()

        print_text(f"[bold magenta]{self}[/] is thinking...", with_markup=True)
        # time.sleep(1)

        # Coup is only option
        # if len(available_actions) == 1:
        #     # TODO write another prompt for coup action 
        #     player = random.choice(other_players)
        #     return available_actions[0], player

        # # Pick any other random choice (might be a bluff)
        # target_action = random.choice(available_actions)
        # target_player = None

        # if target_action.requires_target:
        #     target_player = random.choice(other_players)
        target_action, target_player = choose_action(self, available_actions, other_players,
                                                     revealed_cards, deck_len, treasury)

        # Make sure we have a valid action/player combination
        while not self._validate_action(target_action, target_player):
            target_action, target_player = choose_action(self, available_actions, other_players,
                                                         revealed_cards, deck_len, treasury)

        return target_action, target_player

    def determine_challenge(self, player: BasePlayer, game) -> bool:
        """Choose whether to challenge the current player"""

        should_challenge = determine_challenge(player, self, game)
        return should_challenge

    def determine_counter(self, player: BasePlayer, game) -> bool:
        """Choose whether to counter the current player's action"""
        should_counter = determine_counter(player, self, game)
        # 10% chance of countering
        return should_counter

    def remove_card(self, game) -> Card:
        """Choose a card and remove it from your hand"""

        # discarded_card = llm_remove_card(self, game)
        discarded_card = remove_card(self, game)
        self.cards.remove(discarded_card)
        return discarded_card

    def choose_exchange_cards(self, exchange_cards: list[Card], game) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""
        first_len = len(self.cards)
        old_cards = self.cards

        self.cards += exchange_cards
        out_cards, in_cards = choose_exchange_cards(self, game)

        if len(out_cards) == 2 and len(in_cards) == first_len:
            self.cards = in_cards
            return out_cards[0], out_cards[1]

        else:
            self.cards = old_cards
            return exchange_cards[0], exchange_cards[1]


def choose_action(player: BasePlayer, available_actions: List[Action],
                  other_players: List[BasePlayer], revealed_cards: List[Card],
                  deck_len: int, treasury: int):
    """decide what action should be taken"""
    cards = player.cards
    card_types = [card.card_type for card in cards]
    action_count = itertools.count()
    actions = []

    available_honest_actions = []
    available_bluffing_actions = []

    for action in available_actions:
        if action.associated_card_type in card_types or action.associated_card_type is None:
            if action.requires_target:
                for i, p in enumerate(other_players):
                    actions.append({'action': action,
                                    'target': p,
                                    'action_str': f"{next(action_count)} - {str(action)} on Opponent Player {i}"})
            else:
                actions.append({'action': action,
                                'target': None,
                                'action_str': f"{next(action_count)} - {str(action)}"})

            available_honest_actions.append(action)
        else:
            if action.requires_target:
                for i, p in enumerate(other_players):
                    actions.append({'action': action,
                                    'target': p,
                                    'action_str': f"{next(action_count)} - Bluff {str(action)} on Opponent Player {i}"})
            else:
                actions.append({'action': action,
                                'target': None,
                                'action_str': f"{next(action_count)} - Bluff {str(action)}"})

            available_bluffing_actions.append(action)

    available_actions_str = '\n'.join([a['action_str'] for a in actions])

    other_players_str = ""
    for i, p in enumerate(other_players):
        other_players_str += f"Opponent Player {i}\nNumber of Influences (Cards):{len(p.cards)}\nNumber of Coins:{p.coins}\n"
        other_players_str += "--------------\n"

    game_state_str = f""""Your influences(Cards): {','.join(card_types)},
Your coins: {player.coins}
--------- other players ------
{other_players_str}   

Number of Treasury Coins: {treasury}
Remained Cards in the Deck: {deck_len}
-------- revealed cards --------
{[str(card) for card in revealed_cards]}
"""

    select_action_result = choose_action_chain.invoke(input={'number_of_active_players': len(other_players),
                                                             'state': game_state_str,
                                                             'available_actions': available_actions_str})['text']
    try:
        select_action_result = eval(select_action_result)
    except Exception as e:
        select_action_result = eval(
            select_action_result[select_action_result.find('('):select_action_result.find(')') + 1])

    selected_action_index = select_action_result[0] if type(select_action_result[0]) == int else int(
        select_action_result[0].strip(' ./-abcdefghijklmnopqrstuvwxyz'))
    # print('LLM chosen action:', str(actions[selected_action_index]['action']),
    #       '\nReason:', select_action_result[1], 
    #       '\nRisk:', select_action_result[2])

    return actions[selected_action_index]['action'], actions[selected_action_index]['target']


def determine_challenge(player_under_challenge: BasePlayer, challenger_player: BasePlayer, game):
    revealed_cards = game._revealed_cards + challenger_player.cards
    revealed_cards = [card.card_type for card in revealed_cards]
    player_cards = [card.card_type for card in challenger_player.cards]

    action = player_under_challenge.last_action
    if revealed_cards.count(action.associated_card_type) == 3:
        return True

    if type(action) == ActionType:
        counterAction = get_counter_action(action.action_type)
        if (counterAction is not None) and player_under_challenge.last_target == challenger_player:
            if counterAction.associated_card_type in player_cards:
                return False

    state = f"""Your Cards: {[card.card_type.value for card in challenger_player.cards]}
Your coins: {challenger_player.coins}
----
Opponent's Cards: {[card.card_type.value for card in player_under_challenge.cards]}
Opponent's coins: {player_under_challenge.coins}
----
Revealed Cards: {[card.card_type.value for card in game._revealed_cards]}
"""
    action_str = f"{player_under_challenge} "
    target_player = player_under_challenge.last_target
    if type(action) == 'Action':
        match action.action_type:
            case ActionType.tax:
                action_str += "take tax because they have influence over a Duke."

            case ActionType.assassinate:
                action_str += f"assassinate {target_player.name}."

            case ActionType.steal:
                action_str += f"steal coin from {target_player.name}"

            case ActionType.exchange:
                action_str += (
                    "perform an exchange, because they have influence over an Ambassador."
                )
    elif type(action) == CounterAction:
        match action.counter_type:
            case CounterActionType.block_foreign_aid:
                action_str += f"block {target_player}'s attempt to take foreign aid."
            case CounterActionType.block_assassination:
                action_str += f"block {target_player}'s assassination attempt."
            case CounterActionType.block_steal:
                action_str += f"block {target_player} from stealing."

    result = challenge_chain.invoke(input={'state': state, 'action': action_str})['text']

    # print(result)
    # input()

    if 'y' in result.strip().lower()[-3:]:
        return True
    else:
        return False


def determine_counter(player_under_countering: BasePlayer, player_countering: BasePlayer, game):
    counterAction = get_counter_action(player_under_countering.last_action.action_type)

    if counterAction.associated_card_type in [card.card_type for card in player_countering.cards]:
        return True

    if player_under_countering.last_target != player_countering:
        return False

    cards = player_countering.cards
    card_types = [card.card_type for card in cards]

    game_state_str = f""""Your influences(Cards): {','.join(card_types)},
Your coins: {player_countering.coins}
Opponent's coins: {player_under_countering.coins}
Opponent's influences(Cards): {len(player_under_countering.cards)} 
-------- revealed cards --------
{[str(card) for card in game._revealed_cards]}
"""
    action_str = f"{player_under_countering} "
    action = player_under_countering.last_action
    target_player = player_under_countering.last_target
    target_str = ""
    if target_player is not None and target_player.name == player_countering.name:
        target_str = "you"
    else:
        target_str = "one of your opponent players"

    match action.action_type:
        case ActionType.foreign_aid:
            action_str += "take foreign aid."

        case ActionType.assassinate:
            action_str += f"assassinate {target_str}."

        case ActionType.steal:
            action_str += f"steal coin from {target_str}"

    result = counter_chain.invoke(input={'state': game_state_str, 'action': action})['text']

    if 'y' in result.strip().lower()[-3:]:
        return True
    else:
        return False


def remove_card(player: BasePlayer, game) -> Card:
    """Choose a card and remove it from your hand"""
    if len(player.cards) == 1:
        return player.cards[0]

    state = f"""Your Cards: {[card.card_type.value for card in player.cards]}
Your coins: {player.coins}
{'''
'''.join([f"{player.name} coins: {player.coins}, cards: {len(player.cards)}" for playerr in game._players if playerr.name != player.name])}"""

    cards_index = [f"{str(i)}- {player.cards[i].card_type.value}" for i in range(len(player.cards))]
    result = remove_chain.invoke(input={'state': state,
                                        'cards_index': '\n'.join(cards_index)
                                        })['text']

    # print(result)
    # input()
    if str(0) in result.strip().lower()[-5:]:
        return player.cards[0]
    else:
        return player.cards[1]


def choose_exchange_cards(player: BasePlayer, game) -> Tuple[Card, Card]:
    state = f"""Your Cards: {[card.card_type.value for card in player.cards]}
Your coins: {player.coins}
{'''
'''.join([f"{player.name} coins: {player.coins}, cards: {len(player.cards)}" for playerr in game._players if playerr.name != player.name])}"""
    cards_index = [f"{str(i)}- {player.cards[i].card_type.value}" for i in range(len(player.cards))]

    result = exchange_chain.invoke(input={'state': state,
                                          'cards_index': '\n'.join(cards_index)
                                          })['text']

    result = result.strip().lower()[-7:]

    out_cards = []
    in_cards = []
    for i in range(len(player.cards)):
        if str(i) in result:
            out_cards.append(player.cards[i])
        else:
            in_cards.append(player.cards[i])

    # print(cards_index)
    # print(result)
    # print(out_cards)
    # input()

    return out_cards, in_cards
