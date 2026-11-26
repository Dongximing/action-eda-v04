"""ALFWorld TextWorld episode adapter and a reproducible scripted valid_seen probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from importlib.metadata import version
from pathlib import Path

FAMILIES = {
    "pick_and_place_simple", "look_at_obj_in_light", "pick_clean_then_place_in_recep",
    "pick_heat_then_place_in_recep", "pick_cool_then_place_in_recep", "pick_two_obj_and_place",
}
PROBE_GAME = Path(
    "pick_clean_then_place_in_recep-ButterKnife-None-CounterTop-8/"
    "trial_T20190909_105559_983897/game.tw-pddl"
)


def select_games(split_dir: Path, limit: int, seed: int) -> list[Path]:
    """Sample distinct solvable released games without replacement."""
    if limit < 1:
        raise ValueError("episode count must be positive")
    candidates = []
    for path in sorted(Path(split_dir).glob("*/*/game.tw-pddl")):
        family_spec = path.parent.parent.name
        if family_spec.partition("-")[0] not in FAMILIES or "Sliced" in family_spec:
            continue
        # As in upstream ALFWorld, only select declared-solvable games. The
        # game file and its path are never part of any model-visible object.
        if json.loads(path.read_bytes()).get("solvable") is True:
            candidates.append(path)
    if len(candidates) < limit:
        raise ValueError(f"requested {limit} games but found {len(candidates)} in {split_dir}")
    return random.Random(seed).sample(candidates, limit)


class Episode:
    """Expose only public feedback and optionally admissible commands before execution."""

    def __init__(self, game: Path, *, show_admissible: bool = False):
        import textworld
        from alfworld.agents.environment.alfred_tw_env import AlfredDemangler

        self._show_admissible = show_admissible
        infos = textworld.EnvInfos(won=True, admissible_commands=show_admissible)
        self._env = textworld.start(str(game), infos, wrappers=[AlfredDemangler])
        self._history: list[dict] = []
        self._commands: list[str] = []
        self.task = ""
        self.won = self.done = False
        self.steps = 0

    def _observe(self, state, action: str, observation: str) -> dict:
        self._history.append({"id": f"r{self.steps}", "action": action, "observation": observation})
        self._commands = list(state.admissible_commands) if self._show_admissible else []
        self.won = bool(state.won)
        return self.view()

    def reset(self) -> dict:
        state = self._env.reset()
        parts = re.split(r"Your task is to\s*:\s*", state.feedback, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) != 2 or not parts[1].strip():
            raise ValueError("ALFWorld reset did not publish a task in the initial observation")
        self.task = parts[1].strip()
        self._history.clear()
        self.steps = 0
        self.done = False
        return self._observe(state, "reset", parts[0].strip())

    def view(self) -> dict:
        if not self._history:
            raise RuntimeError("reset the episode first")
        public = {
            "task": self.task,
            "observation": self._history[-1]["observation"],
            "history": [dict(row) for row in self._history],
        }
        if self._show_admissible:
            public["admissible_commands"] = list(self._commands)
        return public

    def step(self, action: str) -> dict:
        if not self._history or self.done:
            raise RuntimeError("reset before stepping a new or finished episode")
        if not isinstance(action, str) or not action.strip() or len(action.splitlines()) != 1:
            raise ValueError("an environment action must be one nonempty line")
        action = action.strip()
        state, _, done = self._env.step(action)
        self.steps += 1
        self.done = bool(done) or bool(state.won)
        return self._observe(state, action, state.feedback.strip())

    def close(self) -> None:
        self._env.close()


def probe(split_dir: Path, output: Path) -> None:
    """Repeated resets allow separate replay checks before executing the proposed clean."""
    game = split_dir / PROBE_GAME
    if split_dir.resolve().name != "valid_seen" or not game.is_file():
        raise ValueError("this scripted probe requires the released valid_seen split")
    go_sink = "go to sinkbasin 1"
    go_counter = "go to countertop 2"
    setup = [go_counter, "take butterknife 1 from countertop 2"]
    proposal = "clean butterknife 1 with sinkbasin 1"
    prefixes, outcomes = [], []
    for i, extra in enumerate(([], [go_sink], [go_sink, go_counter], [go_sink, go_counter, go_sink]), 1):
        branch = []
        for _ in range(2):
            env = Episode(game)
            try:
                before = env.reset()
                for action in setup + extra:
                    before = env.step(action)
                    if before["observation"] == "Nothing happens.":
                        raise RuntimeError(f"probe setup failed for action {action!r}")
                after = env.step(proposal)
                branch.append((before, after["observation"]))
            finally:
                env.close()
        if branch[0] != branch[1]:
            raise RuntimeError(f"reset/replay changed public observations for branch {i}")
        before, feedback = branch[0]
        unchanged = feedback.casefold().strip() == "nothing happens."
        cleaned = bool(re.search(r"\bclean\b.*\bbutterknife 1\b", feedback, flags=re.IGNORECASE))
        if not ((i % 2 and unchanged) or (i % 2 == 0 and cleaned)):
            raise RuntimeError(f"unexpected clean observation for branch {i}: {feedback!r}")
        case_id = f"scripted-dev-{i:02d}"
        prefixes.append({"id": case_id, "proposed_action": proposal, "prefix": before})
        outcomes.append({"id": case_id, "post_action_observation": feedback,
                         "observed_effect": "no_effect" if unchanged else "cleaned",
                         "identical_prefix_and_outcome_across_two_resets": True})

    output.mkdir(parents=True, exist_ok=False)
    with (output / "prefixes.jsonl").open("x", encoding="utf-8") as f:
        for row in prefixes:
            print(json.dumps(row, ensure_ascii=False), file=f)
    metadata = {
        "source": "scripted integration probe; four branches of one released valid_seen game",
        "game": str(PROBE_GAME), "game_sha256": hashlib.sha256(game.read_bytes()).hexdigest(),
        "alfworld": version("alfworld"), "textworld": version("textworld"),
        "policy": "fixed setup and identical clean action; no Qwen or Jev calls",
        "admissible_commands_to_model": False, "outcomes": outcomes,
    }
    (output / "outcomes.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-dir", type=Path, required=True, help="path ending in valid_seen")
    parser.add_argument("--output", type=Path, required=True, help="fresh output directory for scripted probe")
    args = parser.parse_args()
    probe(args.split_dir, args.output)
