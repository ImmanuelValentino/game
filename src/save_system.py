"""
Sistem Save & Load Game untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menyimpan level, exp, gold, ash, inventory, dan quest pemain ke dalam file savegame.json.
"""
import os
import json

SAVE_FILE = "savegame.json"

class SaveSystem:
    @staticmethod
    def save_game(player, inventory, quest_mgr):
        try:
            # Serialisasi inventory
            inv_data = []
            for slot in inventory.slots:
                if slot and slot["item"]:
                    inv_data.append({
                        "id": slot["item"].id,
                        "count": slot["count"]
                    })
                else:
                    inv_data.append(None)

            # Serialisasi quest
            quest_data = {
                "active_index": quest_mgr.active_index,
                "quests": [
                    {
                        "id": q.id,
                        "current_count": q.current_count,
                        "is_completed": q.is_completed
                    } for q in quest_mgr.quests
                ]
            }

            data = {
                "level": player.level,
                "exp": player.exp,
                "exp_to_next": player.exp_to_next,
                "max_hp": player.max_hp,
                "hp": player.hp,
                "max_stamina": player.max_stamina,
                "stamina": player.stamina,
                "gold": player.gold,
                "monster_ash": player.monster_ash,
                "base_damage": player.base_damage,
                "bonus_damage": player.bonus_damage,
                "armor": player.armor,
                "speed_bonus": player.speed_bonus,
                "x": player.x,
                "y": player.y,
                "inventory": inv_data,
                "quest": quest_data
            }

            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("[SaveSystem] Game berhasil disimpan ke savegame.json!")
            return True
        except Exception as e:
            print(f"[SaveSystem] Gagal menyimpan game: {e}")
            return False

    @staticmethod
    def load_game(player, inventory, quest_mgr):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            player.level = data.get("level", 1)
            player.exp = data.get("exp", 0)
            player.exp_to_next = data.get("exp_to_next", 100)
            player.max_hp = data.get("max_hp", 100)
            player.hp = data.get("hp", player.max_hp)
            player.hp_trail = float(player.hp)
            player.max_stamina = data.get("max_stamina", 100)
            player.stamina = float(data.get("stamina", player.max_stamina))
            player.gold = data.get("gold", 50)
            player.monster_ash = data.get("monster_ash", 15)
            player.base_damage = data.get("base_damage", 22)
            player.bonus_damage = data.get("bonus_damage", 0)
            player.armor = data.get("armor", 0)
            player.speed_bonus = data.get("speed_bonus", 0.0)
            player.x = float(data.get("x", 544.0))
            player.y = float(data.get("y", 288.0))

            # Load inventory
            inv_data = data.get("inventory", [])
            for idx in range(min(len(inventory.slots), len(inv_data))):
                item_entry = inv_data[idx]
                if item_entry and "id" in item_entry:
                    inventory.slots[idx] = {
                        "item": inventory.ITEM_DATABASE.get(item_entry["id"]),
                        "count": item_entry.get("count", 1)
                    }
                else:
                    inventory.slots[idx] = None

            # Load quest
            q_data = data.get("quest", {})
            quest_mgr.active_index = q_data.get("active_index", 0)
            saved_quests = {q["id"]: q for q in q_data.get("quests", [])}
            for q in quest_mgr.quests:
                if q.id in saved_quests:
                    sq = saved_quests[q.id]
                    q.current_count = sq.get("current_count", 0)
                    q.is_completed = sq.get("is_completed", False)

            print("[SaveSystem] Game berhasil dimuat dari savegame.json!")
            return True
        except Exception as e:
            print(f"[SaveSystem] Gagal memuat game: {e}")
            return False
