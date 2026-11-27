# MPO ALFWorld prompt files (copy)

From https://github.com/WeiminXiong/MPO at commit 5529eca70ab352eb7e56533ca44cb60fbf34bef1 (Apache-2.0, LICENSE here):
- `alfworld_icl.json` (prompt/icl_examples): per task type, ReAct trajectories as chat turns; the first one of a
  type is the one-shot example (icl_num 1). They are ReAct's react_<type>_0 games (ReAct, MIT).
- `alfworld_inst.txt` (prompt/instructions): MPO's instruction. The ReAct baseline of VBL (arXiv 2610.41564, App. F.3)
  follows ReflAct (arXiv 2505.15182, App. K.1, Figure 14), whose ReAct instruction differs from this file in: the
  ReAct sentence ("You should first think about the current condition and plan for your future actions, and then
  output your action in this turn. ..."), action 6 "use obj", placeholders without braces, and one reminder line.
  run_online.py (REACT_STD_INSTRUCTION) uses the ReflAct version.
