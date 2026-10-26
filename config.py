"""Bake-off settings. Edit this file to add, remove or re-tune models.

IMPORTANT - model IDs:
  Only "openai/gpt-oss-120b" is confirmed from Baseten's documentation.
  Every other `id` below is a best guess at Baseten's naming.
  Before anything else, run:   python run_bakeoff.py list-models
  and copy the exact IDs from your account into this file.

Prices ($ per 1M tokens) and requests-per-minute limits come from your
Baseten dashboard screenshot taken Oct 26, 2026.

`family` = the company that trained the model. The simulated user must never
share a family with the interviewer it is talking to (the LLM-vs-LLM bias
control from the Milestone 1 feedback). The scripts enforce this.
"""

BASE_URL = "https://inference.baseten.co/v1"

# How Baseten controls "thinking" (from Baseten integration docs):
#   chat_template_args.enable_thinking  -> turns thinking on or off
#   reasoning_effort                    -> low / medium / high on some models
# Not every model honours both. `python run_bakeoff.py check` shows which work.
REASONING_SETTINGS = {
    "off": {"chat_template_args": {"enable_thinking": False}},
    "low": {"reasoning_effort": "low"},
    "default": {},  # whatever the provider does by default
}

MODELS = {
    # ---- interviewer candidates (stage 1) ----
    "glm-5.3": dict(
        id="zai-org/GLM-5.3", family="zhipu",
        price_in=1.40, price_out=4.40, rpm=120),
    "deepseek-v4.1-flash": dict(
        id="deepseek-ai/DeepSeek-V4.1-Flash", family="deepseek",
        price_in=0.30, price_out=1.20, rpm=120),
    "nemotron-ultra": dict(
        id="nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B", family="nvidia",
        price_in=0.60, price_out=2.40, rpm=120),
    "muse-spark-open": dict(
        id="meta-models/muse-spark-open", family="meta",
        price_in=1.25, price_out=4.25, rpm=120),
    "beam": dict(
        id="reflection/Beam-1.0", family="reflection",
        price_in=0.40, price_out=1.20, rpm=15,
        # Beam rejects history without its earlier reasoning. We drop reasoning
        # for every model, so skip the check to keep the comparison equal.
        # The flag only works inside chat_template_args (tested Oct 26).
        reasoning={
            "off": {"chat_template_args": {"enable_thinking": False, "allow_missing_thinking": True}},
            "low": {"reasoning_effort": "low", "chat_template_args": {"allow_missing_thinking": True}},
            "default": {"chat_template_args": {"allow_missing_thinking": True}}},
        note="15 requests/min: fine for the bake-off, ~22 h for the full run"),
    "kimi-k3": dict(
        id="moonshotai/Kimi-K3", family="moonshot",
        price_in=3.00, price_out=15.00, rpm=15,
        # Kimi K3 only offers maximum thinking, so "off"/"low" send nothing.
        reasoning={"off": {}, "low": {}},
        note="ceiling reference only: max thinking, priciest, 15 requests/min"),

    # ---- simulated-user candidates (stage 2) ----
    "nemotron-3.5-super": dict(
        id="nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B", family="nvidia",
        price_in=0.20, price_out=0.50, rpm=120),
    "deepseek-v4-flash-0731": dict(
        id="deepseek-ai/DeepSeek-V4-Flash-0731", family="deepseek",
        price_in=0.13, price_out=0.26, rpm=120),

    # ---- stage 1 simulated user (different company from every interviewer) ----
    "gpt-oss-120b": dict(
        id="openai/gpt-oss-120b", family="openai",
        price_in=0.10, price_out=0.50, rpm=15, verified=True,
        # gpt-oss has no "off" switch; its lowest setting is low effort.
        reasoning={"off": {"reasoning_effort": "low"}}),
}

# ---------------- Stage 1: compare interviewers ----------------
STAGE1_INTERVIEWERS = [
    "glm-5.3", "deepseek-v4.1-flash", "nemotron-ultra",
    "muse-spark-open", "beam", "kimi-k3",
]
STAGE1_INTERVIEWER_REASONING = "low"
STAGE1_USER = "gpt-oss-120b"
STAGE1_USER_REASONING = "low"

# ---------------- Stage 2: compare simulated users ----------------
# Run with the stage 1 winner. Any candidate from the same company as the
# interviewer is skipped automatically.
STAGE2_USER_CANDIDATES = [
    "nemotron-3.5-super", "deepseek-v4.1-flash",
    "deepseek-v4-flash-0731", "nemotron-ultra",
]
STAGE2_USER_REASONING = ["off", "low"]   # decision: test both
STAGE2_INTERVIEWER_REASONING = "low"

# ---------------- Main experiment (locked by the Oct 26 bake-off) ----------------
EXPERIMENT_INTERVIEWER = "glm-5.3"            # method D, and the answer mapper for method B
EXPERIMENT_INTERVIEWER_REASONING = "low"
EXPERIMENT_USER = "deepseek-v4-flash-0731"    # simulated users for every method
EXPERIMENT_USER_REASONING = "off"

# ---------------- Interview settings ----------------
BUDGET = 10                 # the middle budget from the shared contract
INTERVIEWER_MAX_TOKENS = 4000   # room for thinking + the JSON reply
USER_MAX_TOKENS = 1500
INTERVIEWER_TEMPERATURE = 0.7   # set to None to use each provider's default
USER_TEMPERATURE = 0.9
MAX_WORKERS = 6             # interviews run in parallel

# ---------------- Full-run projection (for cost/time estimates) ----------------
# 100 users x 3 budgets x 3 repeats x 2 conversational methods (B and D),
# average 10 questions -> same length as a bake-off interview.
FULL_RUN_INTERVIEWS = 100 * 3 * 3 * 2
# 100 users x 3 budgets x 3 repeats x 4 methods x ~10 answers each.
FULL_RUN_USER_ANSWERS = 100 * 3 * 3 * 4 * 10
