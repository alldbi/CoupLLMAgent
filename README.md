# CoupLLMAgent
LLM agent to play the Coup game

## How to run the code

1. Add OpenAI api key to the env variables

`export OPENAI_API_KEY='your API key'`

2. Install the dependencies

`pip3 install requirements.txt`

3. Run the code

`python3 coup.py`

## Win rate against random bots (computed over >10 rounds)

| # of players | win rate of random bot | win rate of LLM Agent |
|--------------|------------------------|-----------------------|
| 5            |  20%                   |  75.0%                |
| 4            | 25%                    |  72.2%                     |
|3             | 33.3%                  |  63.6%                     |
| 2            | 50%                    |  80.0%                      |
