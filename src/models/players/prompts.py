from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

llm: ChatOpenAI = ChatOpenAI(temperature=0, model_name='gpt-4', verbose='True')
#     9. Re-shuffling: If the deck runs out of cards, shuffle the discard pile to create a new deck.

# 10. Game End: The game ends when there is only one player left with any influence. That player is the winner.
best_action_template = """You are an experienced player in a bluffing game with {number_of_active_players} other players.
game rules, current state of the game, available actions and your goal in the game is provided. 
Read them carefully, think about each action's consequence and choose the best available action you can take in this turn, to reach your goal.
Write the reason of your choice and it's risk rate too (in a python tuple: (chosen action, reason, risk))

% GOAL:
Maximize coins and eliminate opponents to be the last player with influence.

% GAME RULES:
    1. Setup: The game is designed for 2-6 players. Each player starts with 2 coins. The deck consists of 15 cards: 3 Dukes, 3 Assassins, 3 Ambassadors, 3 Captains, and 3 Contessas.

    2. Role Distribution: Shuffle the deck and deal two cards to each player. These cards represent the player's influence and role in the game. Players keep their cards face down and secret from other players.

    3. Game Play: Players take turns in clockwise order. On their turn, a player must perform exactly one action from the possible actions.

    4. Possible Actions: 
        - Income: Take 1 coin from the treasury.
        - Foreign Aid: Take 2 coins from the treasury. This action can be blocked by a player claiming to have the Duke.
        - Coup: Pay 7 coins to the treasury and choose a player to lose an influence. This action cannot be blocked.
        - Taxes: Claim to be the Duke and take 3 coins from the treasury.
        - Assassinate: Claim to be the Assassin and pay 3 coins to the treasury to force another player to lose an influence. This action can be blocked by a player claiming to have the Contessa.
        - Exchange: Claim to be the Ambassador to exchange cards with the Court. Draw two cards from the deck, choose which (if any) to exchange with your face-down cards, then return two cards to the deck.
        - Steal: Claim to be the Captain and take 2 coins from another player. This action can be blocked by a player claiming to have the Captain or Ambassador.

    5. Bluffing: Players can bluff by performing an action that requires a role they do not have. If challenged, the player must show the card of the role they claimed. If they cannot, they lose an influence. If they can, the challenger loses an influence. Bluffing is a high risk action if player have 1 influence.

    6. Challenges: Any action or counteraction can be challenged. The player who is challenged must prove their role by showing the appropriate card. If they cannot, they lose an influence. If they can, the challenger loses an influence.

    7. Losing Influence: When a player loses an influence, they turn one of their cards face up for all to see. Once a player has lost both their influences, they are out of the game.

    8. Winning the Game: The last player to still have influence - that is, at least one face-down card - is the winner.


% GAME STATE:
{state} 

% AVAILABLE ACTIONS:
{available_actions}

(index of the best action, reason, risk):"""

best_action_prompt = PromptTemplate(template=best_action_template,
                                    input_variables=['number_of_active_players', 'state', 'available_actions'])
choose_action_chain: LLMChain = LLMChain(llm=llm, prompt=best_action_prompt)

consequence_template = """Rules of The Resistance: Coup game is provided. 
Current state of an ongoing game and an action chosen to be taken is also provided. 
Generate all possible consequences of the action.

% GAME RULES:

% EXAMPLE:
income: add 1 coin to player's coins
foreign aid: 1- be blocked: nothing happens to the player
             2- not blocked: add 2 coins the the player's coins
bluff duke: 1- be challenged: loses one influence
           2- unchallenged: adds 3 coins to player's coins (from treasury)
duke: 1- be challenged: the opponent player lose an influence
      2- unchallenged: adds 3 coins to player's coins (from treasury)
ambassador: 1- ...

bluff ambassador: 1- ...

% GAME HISTORY:
{history}
% CHOSEN ACTION BY THIS PLAYER:
{action}
"""

# TODO: ask about consequence on the game for each action
# TODO: ask to choose the best player to target
# % GOAL:
# Maximize coins and eliminate opponents to be the last player with influence.

challenge_template = """You are an experienced player in a bluffing game, Coup.
game rules, current state of the game, available actions and your goal in the game is provided. 
Read them carefully, think about each action's consequence and choose to challenge your opponent action or not.

If you are not the target of the action. don't risk.

% GAME RULES:
    1. Setup: The game is designed for 2-6 players. Each player starts with 2 coins. The deck consists of 15 cards: 3 Dukes, 3 Assassins, 3 Ambassadors, 3 Captains, and 3 Contessas.

    2. Role Distribution: Shuffle the deck and deal two cards to each player. These cards represent the player's influence and role in the game. Players keep their cards face down and secret from other players.

    3. Game Play: Players take turns in clockwise order. On their turn, a player must perform exactly one action from the possible actions.

    4. Possible Actions: 
        - Income: Take 1 coin from the treasury.
        - Foreign Aid: Take 2 coins from the treasury. This action can be blocked by a player claiming to have the Duke.
        - Coup: Pay 7 coins to the treasury and choose a player to lose an influence. This action cannot be blocked.
        - Taxes: Claim to be the Duke and take 3 coins from the treasury.
        - Assassinate: Claim to be the Assassin and pay 3 coins to the treasury to force another player to lose an influence. This action can be blocked by a player claiming to have the Contessa.
        - Exchange: Claim to be the Ambassador to exchange cards with the Court. Draw two cards from the deck, choose which (if any) to exchange with your face-down cards, then return two cards to the deck.
        - Steal: Claim to be the Captain and take 2 coins from another player. This action can be blocked by a player claiming to have the Captain or Ambassador.

    5. Bluffing: Players can bluff by performing an action that requires a role they do not have. If challenged, the player must show the card of the role they claimed. If they cannot, they lose an influence. If they can, the challenger loses an influence. Bluffing is a high risk action if player have 1 influence.

    6. Challenges: Any action or counteraction can be challenged. The player who is challenged must prove their role by showing the appropriate card. If they cannot, they lose an influence. If they can, the challenger loses an influence.

    7. Losing Influence: When a player loses an influence, they turn one of their cards face up for all to see. Once a player has lost both their influences, they are out of the game.

    8. Winning the Game: The last player to still have influence - that is, at least one face-down card - is the winner.


% GAME STATE:
{state} 

% Your Opponent Action:
{action}

Do you think your opponent is bluffing and you want to challenge him? Explain why you think he is bluffing or not and calculate the risk of challenging him with respect to the consequences. Then type y. or n. at the end of the line without any extra characters.
"""
challenge_prompt = PromptTemplate(template=challenge_template, input_variables=['state', 'action'])
challenge_chain: LLMChain = LLMChain(llm=llm, prompt=challenge_prompt)

counter_template = """You are an experienced player in a bluffing game, Coup.
game rules, current state of the game, and your goal in the game is provided. 
current action of one your opponent players is also provided.
Read them carefully, think about consequences of blocking the action and decide whether block your opponent action or not.
Write the reason of your choice and it's risk rate too.

IMPORTANT: Avoid high risk blocking!

% GAME RULES:
    1. Setup: The game is designed for 2-6 players. Each player starts with 2 coins. The deck consists of 15 cards: 3 Dukes, 3 Assassins, 3 Ambassadors, 3 Captains, and 3 Contessas.

    2. Role Distribution: Shuffle the deck and deal two cards to each player. These cards represent the player's influence and role in the game. Players keep their cards face down and secret from other players.

    3. Game Play: Players take turns in clockwise order. On their turn, a player must perform exactly one action from the possible actions.

    4. Possible Actions: 
        - Income: Take 1 coin from the treasury.
        - Foreign Aid: Take 2 coins from the treasury. This action can be blocked by a player claiming to have the Duke.
        - Coup: Pay 7 coins to the treasury and choose a player to lose an influence. This action cannot be blocked.
        - Taxes: Claim to be the Duke and take 3 coins from the treasury.
        - Assassinate: Claim to be the Assassin and pay 3 coins to the treasury to force another player to lose an influence. This action can be blocked by a player claiming to have the Contessa.
        - Exchange: Claim to be the Ambassador to exchange cards with the Court. Draw two cards from the deck, choose which (if any) to exchange with your face-down cards, then return two cards to the deck.
        - Steal: Claim to be the Captain and take 2 coins from another player. This action can be blocked by a player claiming to have the Captain or Ambassador.

    5. Bluffing: Players can bluff by performing an action that requires a role they do not have. If challenged, the player must show the card of the role they claimed. If they cannot, they lose an influence. If they can, the challenger loses an influence. Bluffing is a high risk action if player have 1 influence.

    6. Challenges: Any action or counteraction can be challenged. The player who is challenged must prove their role by showing the appropriate card. If they cannot, they lose an influence. If they can, the challenger loses an influence.

    7. Losing Influence: When a player loses an influence, they turn one of their cards face up for all to see. Once a player has lost both their influences, they are out of the game.

    8. Winning the Game: The last player to still have influence - that is, at least one face-down card - is the winner.


% GAME STATE:
{state} 

% Your Opponent Current Action:
{action}

Considering the risk, Is blocking a good idea? Explain why? Then type y. or n. at the end of the line without any extra characters.
"""
counter_prompt = PromptTemplate(template=counter_template, input_variables=['state', 'action'])
counter_chain: LLMChain = LLMChain(llm=llm, prompt=counter_prompt)

remove_template = """You are an experienced player in a bluffing game, Coup.
game rules, current state of the game, available actions and your goal in the game is provided. 
Read them carefully, think about each action's consequence and choose to remove one of your cards.

If you are not the target of the action. don't risk.

% GAME RULES:
    1. Setup: The game is designed for 2-6 players. Each player starts with 2 coins. The deck consists of 15 cards: 3 Dukes, 3 Assassins, 3 Ambassadors, 3 Captains, and 3 Contessas.

    2. Role Distribution: Shuffle the deck and deal two cards to each player. These cards represent the player's influence and role in the game. Players keep their cards face down and secret from other players.

    3. Game Play: Players take turns in clockwise order. On their turn, a player must perform exactly one action from the possible actions.

    4. Possible Actions: 
        - Income: Take 1 coin from the treasury.
        - Foreign Aid: Take 2 coins from the treasury. This action can be blocked by a player claiming to have the Duke.
        - Coup: Pay 7 coins to the treasury and choose a player to lose an influence. This action cannot be blocked.
        - Taxes: Claim to be the Duke and take 3 coins from the treasury.
        - Assassinate: Claim to be the Assassin and pay 3 coins to the treasury to force another player to lose an influence. This action can be blocked by a player claiming to have the Contessa.
        - Exchange: Claim to be the Ambassador to exchange cards with the Court. Draw two cards from the deck, choose which (if any) to exchange with your face-down cards, then return two cards to the deck.
        - Steal: Claim to be the Captain and take 2 coins from another player. This action can be blocked by a player claiming to have the Captain or Ambassador.

    5. Bluffing: Players can bluff by performing an action that requires a role they do not have. If challenged, the player must show the card of the role they claimed. If they cannot, they lose an influence. If they can, the challenger loses an influence. Bluffing is a high risk action if player have 1 influence.

    6. Challenges: Any action or counteraction can be challenged. The player who is challenged must prove their role by showing the appropriate card. If they cannot, they lose an influence. If they can, the challenger loses an influence.

    7. Losing Influence: When a player loses an influence, they turn one of their cards face up for all to see. Once a player has lost both their influences, they are out of the game.

    8. Winning the Game: The last player to still have influence - that is, at least one face-down card - is the winner.


% GAME STATE:
{state} 

{cards_index}
Which card do you want to remove? Explain your answer and return the card index you want to remove at the end of the line without any extra characters."""

remove_prompt = PromptTemplate(template=remove_template, input_variables=['state', 'cards_index'])
remove_chain: LLMChain = LLMChain(llm=llm, prompt=remove_prompt)

exchange_template = """You are an experienced player in a bluffing game, Coup.
game rules, current state of the game, available actions and your goal in the game is provided. 
Read them carefully, think about each action's consequence and choose to remove two cards from your hand.

If you are not the target of the action. don't risk.

% GAME RULES:
    1. Setup: The game is designed for 2-6 players. Each player starts with 2 coins. The deck consists of 15 cards: 3 Dukes, 3 Assassins, 3 Ambassadors, 3 Captains, and 3 Contessas.

    2. Role Distribution: Shuffle the deck and deal two cards to each player. These cards represent the player's influence and role in the game. Players keep their cards face down and secret from other players.

    3. Game Play: Players take turns in clockwise order. On their turn, a player must perform exactly one action from the possible actions.

    4. Possible Actions: 
        - Income: Take 1 coin from the treasury.
        - Foreign Aid: Take 2 coins from the treasury. This action can be blocked by a player claiming to have the Duke.
        - Coup: Pay 7 coins to the treasury and choose a player to lose an influence. This action cannot be blocked.
        - Taxes: Claim to be the Duke and take 3 coins from the treasury.
        - Assassinate: Claim to be the Assassin and pay 3 coins to the treasury to force another player to lose an influence. This action can be blocked by a player claiming to have the Contessa.
        - Exchange: Claim to be the Ambassador to exchange cards with the Court. Draw two cards from the deck, choose which (if any) to exchange with your face-down cards, then return two cards to the deck.
        - Steal: Claim to be the Captain and take 2 coins from another player. This action can be blocked by a player claiming to have the Captain or Ambassador.

    5. Bluffing: Players can bluff by performing an action that requires a role they do not have. If challenged, the player must show the card of the role they claimed. If they cannot, they lose an influence. If they can, the challenger loses an influence. Bluffing is a high risk action if player have 1 influence.

    6. Challenges: Any action or counteraction can be challenged. The player who is challenged must prove their role by showing the appropriate card. If they cannot, they lose an influence. If they can, the challenger loses an influence.

    7. Losing Influence: When a player loses an influence, they turn one of their cards face up for all to see. Once a player has lost both their influences, they are out of the game.

    8. Winning the Game: The last player to still have influence - that is, at least one face-down card - is the winner.


% GAME STATE:
{state} 

{cards_index}
Which two cards do you want to remove? Explain your answer and return just index of the two cards you want to remove at the end of the line in comma separated format."""

exchange_prompt = PromptTemplate(template=exchange_template, input_variables=['state', 'cards_index'])
exchange_chain: LLMChain = LLMChain(llm=llm, prompt=exchange_prompt)
