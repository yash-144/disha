file_path = r'backend\app\modules\pulse\intervention_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '            self.peer_mentor_pool[m["id"]] = m'
replacement = '            mentor_id = str(m["id"])\n            self.peer_mentor_pool[mentor_id] = m'

if target in text:
    text = text.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully!")
else:
    print("Target not found!")

