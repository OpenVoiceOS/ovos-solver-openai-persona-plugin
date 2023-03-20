# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> ChatGPT
 
Give Mycroft some sass with ChatGPT!

Leverages [ChatGPT](chat.openai.com/) to create some fun interactions.  Phrases not explicitly handled by other skills will be run by the ChatGPT, so nearly every interaction will have _some_ response.  But be warned, Mycroft might become a bit obnoxious...


## Usage

Spoken answers api with ChatGPT backend

```python
from ovos_solver_chatgpt_plugin import OpenAICompletionsSolver

d = ChatGPTSolver()
sentence = d.spoken_answer("explain general relativity in simple terms")
print(sentence)
```
