import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

from understanding_engine import Understand
from memory_engine import setup_database, Remember

setup_database()

# Record some context first
Remember({"text": "Founder A: We are discussing cognitive-os-paper/03_memory.md as our storage draft."}, "Episodic", 0.99, "test")

# Now query Understand with a pronoun
raw_text = "We should update it before the next meeting."
print(f"Input: {raw_text}")
model = Understand(raw_text)
print("Situational Mental Model:")
print(json.dumps(model, indent=2))
