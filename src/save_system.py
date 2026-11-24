"""
Sistem Save & Load Game untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menyimpan progres lengkap ke savegame.json (stat, senjata, skill, karma, bioma terbuka, inventory, quest).
"""
import os
import json
from src.inventory import ITEM_DATABASE

SAVE_FILE = "savegame.json"


class SaveSystem:
    @staticmethod
    def has_save(filepath=SAVE_FILE):
        return os.path.exists(filepath)

    @staticmethod
    def save_game(player, inventory, quest_mgr, current_map="map1safeworld.tmx", filepath=SAVE_FILE):
        try:
            inv_data = []
            for slot in inventory.slots:
                if slot and slot.get("item"):
                    inv_data.append({
                        "id": slot["item"].id,
                        "count": slot["count"]
                    })
                else:
                    inv_data.append(None)

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
                "current_map": current_map,
                "level": player.level,
                "exp": player.exp,
                "exp_to_next": player.exp_to_next,
                "max_hp": player.max_hp,
                "hp": player.hp,
                "max_stamina": player.max_stamina,
                "stamina": player.stamina,
                "gold": player.gold,
                "monster_ash": player.monster_ash,
                "karma": getattr(player, "karma", 0),
                "weapon_id": getattr(player, "weapon_id", "ancestral_blade"),
                "skill_points": getattr(player, "skill_points", 0),
                "skill_levels": getattr(player, "skill_levels", {"power": 0, "stamina": 0, "defense": 0, "blade": 0}),
                "beacons_cleared": sorted(list(getattr(player, "beacons_cleared", set()))),
                "base_damage": player.base_damage,
                "bonus_damage": player.bonus_damage,
                "armor": getattr(player, "_armor", 10),
                "bonus_def": getattr(player, "bonus_def", 0),
                "speed_bonus": player.speed_bonus,
                "x": player.x,
                "y": player.y,
                "inventory": inv_data,
                "hotbar_ids": list(getattr(inventory, "hotbar_ids", [None] * 4)),
                "quest": quest_data
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[SaveSystem] Game berhasil disimpan ke {filepath}!")
            return True
        except Exception as e:
            print(f"[SaveSystem] Gagal menyimpan game: {e}")
            return False

    @staticmethod
    def load_game(player, inventory, quest_mgr, filepath=SAVE_FILE):
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            new_slots = [None] * inventory.capacity
            inv_data = data.get("inventory", [])
            for idx in range(min(inventory.capacity, len(inv_data))):
                item_entry = inv_data[idx]
                if item_entry and "id" in item_entry:
                    item_obj = ITEM_DATABASE.get(item_entry["id"])
                    cnt = int(item_entry.get("count", 1))
                    if item_obj is not None and cnt > 0:
                        new_slots[idx] = {"item": item_obj, "count": cnt}

            max_hp = max(1, int(data.get("max_hp", 100)))
            hp = int(data.get("hp", max_hp))
            if hp <= 0:
                hp = max_hp
            max_stamina = max(1, int(data.get("max_stamina", 50)))
            stamina = min(float(max_stamina), max(0.0, float(data.get("stamina", max_stamina))))

            player.level = max(1, int(data.get("level", 1)))
            player.exp = max(0, int(data.get("exp", 0)))
            player.exp_to_next = max(1, int(data.get("exp_to_next", 120)))
            player.max_hp = max_hp
            player.hp = min(max_hp, hp)
            player.hp_trail = float(player.hp)
            player.max_stamina = max_stamina
            player.stamina = stamina
            player.gold = max(0, int(data.get("gold", 50)))
            player.monster_ash = max(0, int(data.get("monster_ash", 15)))
            player.karma = int(data.get("karma", 0))
            player.equip_weapon(data.get("weapon_id", "ancestral_blade"))
            player.skill_points = max(0, int(data.get("skill_points", 0)))

            saved_skl = data.get("skill_levels", {})
            for k in ("power", "stamina", "defense", "blade"):
                player.skill_levels[k] = max(0, int(saved_skl.get(k, 0)))

            player.beacons_cleared = set(data.get("beacons_cleared", []))
            player.base_damage = int(data.get("base_damage", 15))
            player.bonus_damage = int(data.get("bonus_damage", 0))
            player._armor = int(data.get("armor", 10))
            player.bonus_def = int(data.get("bonus_def", 0))
            player.speed_bonus = float(data.get("speed_bonus", 0.0))
            player.x = float(data.get("x", 584.0))
            player.y = float(data.get("y", 232.0))
            player.is_dead = False
            player.saved_map = data.get("current_map", "map1safeworld.tmx")

            inventory.slots = new_slots
            saved_hb = data.get("hotbar_ids")
            if isinstance(saved_hb, list):
                inventory.hotbar_ids = [
                    hid if hid in ITEM_DATABASE else None
                    for hid in saved_hb[:inventory.HOTBAR_SIZE]
                ]
                while len(inventory.hotbar_ids) < inventory.HOTBAR_SIZE:
                    inventory.hotbar_ids.append(None)
            else:
                inventory.hotbar_ids = [None] * inventory.HOTBAR_SIZE
            inventory.sync_hotbar_from_inventory()

            q_data = data.get("quest", {})
            saved_quests = {q["id"]: q for q in q_data.get("quests", []) if "id" in q}
            for q in quest_mgr.quests:
                if q.id in saved_quests:
                    sq = saved_quests[q.id]
                    q.current_count = min(q.target_count, max(0, int(sq.get("current_count", 0))))
                    q.is_completed = bool(sq.get("is_completed", False)) or (q.current_count >= q.target_count)
            quest_mgr.sync_active_index()

            print(f"[SaveSystem] Game berhasil dimuat dari {filepath}!")
            return True
        except Exception as e:
            print(f"[SaveSystem] Gagal memuat game: {e}")
            return False
