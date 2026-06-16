from devassist.agent import ask

questions = [
    "how are files indexed?",
    "what file extensions are supported?",
    "how does chunking work?"
]

for q in questions:
    print(f"\n❓ {q}")
    print("─" * 50)
    answer = ask(q)
    print(answer)
    print()