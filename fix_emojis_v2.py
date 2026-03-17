
import os
import re

file_path = r'c:\Users\grend\Desktop\Новая папка\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Мы просто ищем строку f"<b>Spins</b>\n👤 {user_name}\n"
# А затем строку f" и какой-то символ \n"
# И заменяем этот символ на правильный эмодзи, глядя на следующую строку.

lines = content.split('\n')
for i in range(len(lines)):
    if 'f"<b>Spins</b>\\n👤 {user_name}\\n"' in lines[i]:
        # Смотрим на i+1 (это должен быть эмодзи)
        if 'f"' in lines[i+1] and '\\n"' in lines[i+1]:
            # Смотрим на i+2 (там написано во что играли)
            if 'Проигрыш в игре 🗼' in lines[i+2]:
                lines[i+1] = lines[i+1].split('f"')[0] + 'f"🗼\\n"'
            elif 'Проигрыш в игре 💣' in lines[i+2]:
                lines[i+1] = lines[i+1].split('f"')[0] + 'f"💣\\n"'
            elif 'Победа в игре 💣' in lines[i+2]:
                lines[i+1] = lines[i+1].split('f"')[0] + 'f"💣\\n"'
            elif 'Победа в игре 🗼' in lines[i+2]:
                lines[i+1] = lines[i+1].split('f"')[0] + 'f"🗼\\n"'

new_content = '\n'.join(lines)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Emoji fixes done via line analysis.")
