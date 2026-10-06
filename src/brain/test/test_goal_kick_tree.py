from pathlib import Path
import re
import xml.etree.ElementTree as ET


tree = ET.parse(
    Path(__file__).parents[1]
    / "behavior_trees/subtrees/subtree_goal_kick.xml"
)
goal_kick = tree.getroot().find("./BehaviorTree[@ID='GoalKick']")
assert goal_kick is not None

branches = goal_kick.findall("./ReactiveSequence/ReactiveSequence")
own = next(b for b in branches if "gc_game_sub_state_type=='NONE'" in b.get("_while", "")
           and "!gc_is_sub_state_kickoff_side" not in b.get("_while", ""))
opponent = next(b for b in branches if "!gc_is_sub_state_kickoff_side" in b.get("_while", ""))
for branch in (own, opponent):
    field_player = branch.find("./SubTree[@ID='StrikerPlay']")
    assert field_player is not None
    assert "striker" in field_player.get("_while", "")
    assert "supporter" in field_player.get("_while", "")
    assert branch.find("./SubTree[@ID='GoalKeeperPlay']") is not None

assert goal_kick.find("./ReactiveSequence/SetVelocity") is not None

game = ET.parse(Path(__file__).parents[1] / "behavior_trees/game.xml")
entry = next(node for node in game.getroot().iter("SubTree")
             if node.get("ID") == "GoalKick")
parent = next(node for node in game.getroot().iter("ReactiveSequence")
              if entry in list(node))
condition = parent.get("_while", "")


def routed(kind, real, playing=True, penalty=False):
    expression = condition.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression)
    return eval(expression, {"__builtins__": {}}, {
        "gc_game_state": "PLAY" if playing else "SET",
        "penalty_kick_active": penalty,
        "gc_game_sub_state_type": kind,
        "gc_real_game_sub_state": real,
    })


assert routed("NONE", "GOAL_KICK")  # v20 own kick after release
assert routed("FREE_KICK", "GOAL_KICK")  # legacy set play
assert not routed("NONE", "NONE")
assert not routed("NONE", "GOAL_KICK", playing=False)
assert not routed("NONE", "GOAL_KICK", penalty=True)
print("GoalKick subtree guards and role paths OK")
