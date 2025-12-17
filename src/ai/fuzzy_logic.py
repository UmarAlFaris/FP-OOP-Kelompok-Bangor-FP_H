"""
Fuzzy AI — tambah 3 metode inferensi (Mamdani, Sugeno, Tsukamoto-approx)
- Tetap kompatibel API sebelumnya
- Tambah fungsi untuk mengembalikan ketiga skor (untuk perbandingan di main)
"""
try:
    import numpy as np
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    SKFUZZY = True
except Exception:
    SKFUZZY = False

# Universes
x_hp = np.arange(0, 101, 1)
x_mana = np.arange(0, 101, 1)
x_cd = np.arange(0, 11, 1)
x_action = np.arange(0, 101, 1)

# Build FIS (Mamdani) same seperti sebelumnya
if SKFUZZY:
    # membership arrays (same as cb.ipynb)
    hp_p_low = fuzz.trapmf(x_hp, [0, 0, 20, 50])
    hp_p_med = fuzz.trapmf(x_hp, [20, 40, 60, 80])
    hp_p_high = fuzz.trapmf(x_hp, [50, 80, 100, 100])
    hp_b_low = fuzz.trapmf(x_hp, [0, 0, 30, 60])
    hp_b_med = fuzz.trapmf(x_hp, [30, 50, 70, 90])
    hp_b_high = fuzz.trapmf(x_hp, [70, 90, 100, 100])

    mana_p_low = fuzz.trimf(x_mana, [0, 0, 40])
    mana_p_med = fuzz.trimf(x_mana, [20, 50, 80])
    mana_p_high = fuzz.trimf(x_mana, [60, 100, 100])
    mana_b_low = fuzz.trimf(x_mana, [0, 0, 30])
    mana_b_med = fuzz.trimf(x_mana, [30, 50, 70])
    mana_b_high = fuzz.trimf(x_mana, [70, 100, 100])

    cd_ready = fuzz.trapmf(x_cd, [0, 0, 1, 3])
    cd_mid = fuzz.trapmf(x_cd, [2, 4, 6, 8])
    cd_long = fuzz.trapmf(x_cd, [6, 9, 10, 10])

    act_weak = fuzz.trapmf(x_action, [0, 0, 20, 40])
    act_mid = fuzz.trapmf(x_action, [20, 40, 60, 80])
    act_strong = fuzz.trapmf(x_action, [60, 80, 100, 100])

    # Antecedents / Consequents (with-mana)
    hp_p = ctrl.Antecedent(x_hp, 'HP_Player')
    hp_bot = ctrl.Antecedent(x_hp, 'HP_Bot')
    mana_p = ctrl.Antecedent(x_mana, 'Mana_Player')
    mana_b = ctrl.Antecedent(x_mana, 'Mana_Bot')
    cd_p = ctrl.Antecedent(x_cd, 'CD_Player')
    action = ctrl.Consequent(x_action, 'Action_Strength')

    hp_p['low'], hp_p['med'], hp_p['high'] = hp_p_low, hp_p_med, hp_p_high
    hp_bot['low'], hp_bot['med'], hp_bot['high'] = hp_b_low, hp_b_med, hp_b_high
    mana_p['low'], mana_p['med'], mana_p['high'] = mana_p_low, mana_p_med, mana_p_high
    mana_b['low'], mana_b['med'], mana_b['high'] = mana_b_low, mana_b_med, mana_b_high
    cd_p['ready'], cd_p['mid'], cd_p['long'] = cd_ready, cd_mid, cd_long
    action['weak'], action['mid'], action['strong'] = act_weak, act_mid, act_strong

    # rule specs (mirror cb.ipynb rules) as condition labels for Sugeno/Tsukamoto
    rule_specs = [
        (['hp_bot_low','hp_p_high'], 'weak'),
        (['hp_bot_high','hp_p_low'], 'strong'),
        (['hp_bot_low','mana_b_low'], 'weak'),
        (['mana_b_high','hp_p_low'], 'strong'),
        (['cd_ready','hp_bot_med'], 'weak'),

        (['cd_long','hp_bot_high'], 'strong'),
        (['hp_bot_med','hp_p_med'], 'mid'),
        (['mana_p_low','cd_mid'], 'strong'),
        (['mana_b_low','hp_bot_med'], 'weak'),
        (['hp_p_high','mana_b_low'], 'weak'),

        (['hp_bot_high','mana_p_high'], 'mid'),
        (['hp_bot_low','mana_p_high'], 'weak'),
        (['mana_b_high','mana_p_low'], 'strong'),
        (['cd_ready','hp_p_high'], 'mid'),
        (['cd_long','mana_b_med'], 'mid'),

        (['hp_bot_high','hp_p_med'], 'strong'),
        (['hp_bot_med','hp_p_low'], 'strong'),
        (['mana_p_high','mana_b_low'], 'weak'),
        (['cd_long','hp_p_med'], 'mid'),
        (['hp_bot_high','mana_b_high'], 'strong'),
    ]

    # Build Mamdani ControlSystem (existing)
    rules = [
        ctrl.Rule(hp_bot['low'] & hp_p['high'], action['weak']),
        ctrl.Rule(hp_bot['high'] & hp_p['low'], action['strong']),
        ctrl.Rule(hp_bot['low'] & mana_b['low'], action['weak']),
        ctrl.Rule(mana_b['high'] & hp_p['low'], action['strong']),
        ctrl.Rule(cd_p['ready'] & hp_bot['med'], action['weak']),

        ctrl.Rule(cd_p['long'] & hp_bot['high'], action['strong']),
        ctrl.Rule(hp_bot['med'] & hp_p['med'], action['mid']),
        ctrl.Rule(mana_p['low'] & cd_p['mid'], action['strong']),
        ctrl.Rule(mana_b['low'] & hp_bot['med'], action['weak']),
        ctrl.Rule(hp_p['high'] & mana_b['low'], action['weak']),

        ctrl.Rule(hp_bot['high'] & mana_p['high'], action['mid']),
        ctrl.Rule(hp_bot['low'] & mana_p['high'], action['weak']),
        ctrl.Rule(mana_b['high'] & mana_p['low'], action['strong']),
        ctrl.Rule(cd_p['ready'] & hp_p['high'], action['mid']),
        ctrl.Rule(cd_p['long'] & mana_b['med'], action['mid']),

        ctrl.Rule(hp_bot['high'] & hp_p['med'], action['strong']),
        ctrl.Rule(hp_bot['med'] & hp_p['low'], action['strong']),
        ctrl.Rule(mana_p['high'] & mana_b['low'], action['weak']),
        ctrl.Rule(cd_p['long'] & hp_p['med'], action['mid']),
        ctrl.Rule(hp_bot['high'] & mana_b['high'], action['strong']),
    ]
    bot_ctrl = ctrl.ControlSystem(rules)
    bot_simulasi = ctrl.ControlSystemSimulation(bot_ctrl)

    # No-mana FIS (Mamdani) for Zombie/Skeleton
    HP_P_z = ctrl.Antecedent(x_hp, 'HP_Player_Z')
    HP_B_z = ctrl.Antecedent(x_hp, 'HP_Bot_Z')
    CD_P_z = ctrl.Antecedent(x_cd, 'CD_Player_Z')
    ACTION_z = ctrl.Consequent(x_action, 'Action_Strength_Z')

    hp_l = fuzz.trapmf(x_hp, [0, 0, 20, 50])
    hp_m = fuzz.trapmf(x_hp, [20, 40, 60, 80])
    hp_h = fuzz.trapmf(x_hp, [50, 80, 100, 100])
    cd_r = fuzz.trapmf(x_cd, [0, 0, 1, 3])
    cd_m = fuzz.trapmf(x_cd, [2, 4, 6, 8])
    cd_l = fuzz.trapmf(x_cd, [6, 9, 10, 10])

    ACTION_z['weak'], ACTION_z['mid'], ACTION_z['strong'] = act_weak, act_mid, act_strong
    HP_P_z['low'], HP_P_z['med'], HP_P_z['high'] = hp_l, hp_m, hp_h
    HP_B_z['low'], HP_B_z['med'], HP_B_z['high'] = hp_l, hp_m, hp_h
    CD_P_z['ready'], CD_P_z['mid'], CD_P_z['long'] = cd_r, cd_m, cd_l

    rules_z = [
        ctrl.Rule(HP_B_z['high'] & CD_P_z['long'], ACTION_z['strong']),
        ctrl.Rule(HP_P_z['low'], ACTION_z['strong']),
        ctrl.Rule(HP_B_z['low'], ACTION_z['weak']),
        ctrl.Rule(CD_P_z['ready'] & HP_B_z['med'], ACTION_z['mid']),
    ]
    system_z = ctrl.ControlSystem(rules_z)
    sim_z = ctrl.ControlSystemSimulation(system_z)

# Fallback scorers (simple heuristics)
def fallback_score_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p):
    score = 50.0
    score += (100 - hp_p) * 0.2
    score += (hp_b - 50) * 0.2
    score += (mana_b - 50) * 0.1
    score += (cd_p) * 1.2
    if hp_b < 30:
        score -= 35
    return max(0, min(100, score))

def fallback_score_no_mana(hp_p, hp_b, cd_p):
    score = 50.0
    score += (100 - hp_p) * 0.25
    score += (hp_b - 50) * 0.25
    score += (cd_p) * 1.5
    if hp_b < 30:
        score -= 40
    return max(0, min(100, score))

# -------------------- three inference implementations --------------------

def _compute_degrees_with_mana(hp_p_val, hp_b_val, mana_p_val, mana_b_val, cd_p_val):
    """Return dict of membership degrees for antecedents (requires SKFUZZY)."""
    if not SKFUZZY:
        return None
    deg = {}
    deg['hp_p_low'] = fuzz.interp_membership(x_hp, hp_p_low, hp_p_val)
    deg['hp_p_med'] = fuzz.interp_membership(x_hp, hp_p_med, hp_p_val)
    deg['hp_p_high'] = fuzz.interp_membership(x_hp, hp_p_high, hp_p_val)
    deg['hp_b_low'] = fuzz.interp_membership(x_hp, hp_b_low, hp_b_val)
    deg['hp_b_med'] = fuzz.interp_membership(x_hp, hp_b_med, hp_b_val)
    deg['hp_b_high'] = fuzz.interp_membership(x_hp, hp_b_high, hp_b_val)
    deg['mana_p_low'] = fuzz.interp_membership(x_mana, mana_p_low, mana_p_val)
    deg['mana_p_med'] = fuzz.interp_membership(x_mana, mana_p_med, mana_p_val)
    deg['mana_p_high'] = fuzz.interp_membership(x_mana, mana_p_high, mana_p_val)
    deg['mana_b_low'] = fuzz.interp_membership(x_mana, mana_b_low, mana_b_val)
    deg['mana_b_med'] = fuzz.interp_membership(x_mana, mana_b_med, mana_b_val)
    deg['mana_b_high'] = fuzz.interp_membership(x_mana, mana_b_high, mana_b_val)
    deg['cd_ready'] = fuzz.interp_membership(x_cd, cd_ready, cd_p_val)
    deg['cd_mid'] = fuzz.interp_membership(x_cd, cd_mid, cd_p_val)
    deg['cd_long'] = fuzz.interp_membership(x_cd, cd_long, cd_p_val)
    return deg

def _compute_degrees_no_mana(hp_p_val, hp_b_val, cd_p_val):
    if not SKFUZZY:
        return None
    deg = {}
    deg['hp_p_low'] = fuzz.interp_membership(x_hp, hp_l, hp_p_val)
    deg['hp_p_med'] = fuzz.interp_membership(x_hp, hp_m, hp_p_val)
    deg['hp_p_high'] = fuzz.interp_membership(x_hp, hp_h, hp_p_val)
    deg['hp_b_low'] = fuzz.interp_membership(x_hp, hp_l, hp_b_val)
    deg['hp_b_med'] = fuzz.interp_membership(x_hp, hp_m, hp_b_val)
    deg['hp_b_high'] = fuzz.interp_membership(x_hp, hp_h, hp_b_val)
    deg['cd_ready'] = fuzz.interp_membership(x_cd, cd_r, cd_p_val)
    deg['cd_mid'] = fuzz.interp_membership(x_cd, cd_m, cd_p_val)
    deg['cd_long'] = fuzz.interp_membership(x_cd, cd_l, cd_p_val)
    return deg

# Mamdani scorers (existing behavior)
def mamdani_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p):
    if SKFUZZY:
        try:
            bot_simulasi.input['HP_Player'] = hp_p
            bot_simulasi.input['HP_Bot'] = hp_b
            bot_simulasi.input['Mana_Player'] = mana_p
            bot_simulasi.input['Mana_Bot'] = mana_b
            bot_simulasi.input['CD_Player'] = cd_p
            bot_simulasi.compute()
            return float(bot_simulasi.output['Action_Strength'])
        except Exception:
            return fallback_score_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)
    else:
        return fallback_score_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)

def mamdani_no_mana(hp_p, hp_b, cd_p):
    if SKFUZZY:
        try:
            sim_z.input['HP_Player_Z'] = hp_p
            sim_z.input['HP_Bot_Z'] = hp_b
            sim_z.input['CD_Player_Z'] = cd_p
            sim_z.compute()
            return float(sim_z.output['Action_Strength_Z'])
        except Exception:
            return fallback_score_no_mana(hp_p, hp_b, cd_p)
    else:
        return fallback_score_no_mana(hp_p, hp_b, cd_p)

# Sugeno approximator: weighted average of rule consequents (centroid singletons)
def sugeno_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p):
    if not SKFUZZY:
        # fallback: perturb fallback_score to simulate different inference
        base = fallback_score_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)
        return max(0, min(100, base * 0.95))  # slightly different
    deg = _compute_degrees_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)
    # singleton centroids for outputs
    centroids = {'weak': 20.0, 'mid': 50.0, 'strong': 80.0}
    num = 0.0; den = 0.0
    for conds, out in rule_specs:
        # compute firing strength = min of involved antecedents
        vals = [deg.get(c, 0.0) for c in conds]
        firing = min(vals) if vals else 0.0
        num += firing * centroids[out]
        den += firing
    return float(num/den) if den > 1e-9 else float(fallback_score_with_mana(hp_p,hp_b,mana_p,mana_b,cd_p))

def sugeno_no_mana(hp_p, hp_b, cd_p):
    if not SKFUZZY:
        base = fallback_score_no_mana(hp_p, hp_b, cd_p)
        return max(0, min(100, base * 0.95))
    deg = _compute_degrees_no_mana(hp_p, hp_b, cd_p)
    centroids = {'weak': 20.0, 'mid': 50.0, 'strong': 80.0}
    # use subset of rules_z approximated as rule_specs_z
    rule_specs_z = [
        (['hp_b_high','cd_long'], 'strong'),
        (['hp_p_low'], 'strong'),
        (['hp_b_low'], 'weak'),
        (['cd_ready','hp_b_med'], 'mid'),
    ]
    num = 0.0; den = 0.0
    for conds, out in rule_specs_z:
        vals = [deg.get(c, 0.0) for c in conds]
        firing = min(vals) if vals else 0.0
        num += firing * centroids[out]
        den += firing
    return float(num/den) if den > 1e-9 else float(fallback_score_no_mana(hp_p,hp_b,cd_p))

# Tsukamoto approximator: invert monotonic consequents to get z per rule then weighted average
def tsukamoto_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p):
    if not SKFUZZY:
        base = fallback_score_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)
        return max(0, min(100, base * 1.05))
    deg = _compute_degrees_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)
    num = 0.0; den = 0.0
    for conds, out in rule_specs:
        vals = [deg.get(c, 0.0) for c in conds]
        firing = min(vals) if vals else 0.0
        # invert monotonic consequent approx:
        if out == 'weak':
            z = 40.0 * (1.0 - firing)       # range 0..40
        elif out == 'mid':
            z = 40.0 + 20.0 * firing       # range 40..60
        else:  # 'strong'
            z = 60.0 + 40.0 * firing       # range 60..100
        num += firing * z
        den += firing
    return float(num/den) if den > 1e-9 else float(mamdani_with_mana(hp_p,hp_b,mana_p,mana_b,cd_p))

def tsukamoto_no_mana(hp_p, hp_b, cd_p):
    if not SKFUZZY:
        base = fallback_score_no_mana(hp_p, hp_b, cd_p)
        return max(0, min(100, base * 1.05))
    deg = _compute_degrees_no_mana(hp_p, hp_b, cd_p)
    rule_specs_z = [
        (['hp_b_high','cd_long'], 'strong'),
        (['hp_p_low'], 'strong'),
        (['hp_b_low'], 'weak'),
        (['cd_ready','hp_b_med'], 'mid'),
    ]
    num = 0.0; den = 0.0
    for conds, out in rule_specs_z:
        vals = [deg.get(c, 0.0) for c in conds]
        firing = min(vals) if vals else 0.0
        if out == 'weak':
            z = 40.0 * (1.0 - firing)
        elif out == 'mid':
            z = 40.0 + 20.0 * firing
        else:
            z = 60.0 + 40.0 * firing
        num += firing * z
        den += firing
    return float(num/den) if den > 1e-9 else float(mamdani_no_mana(hp_p,hp_b,cd_p))

# -------------------- aggregator helpers --------------------

def get_all_scores(bot_type, hp_p, hp_b, mana_p, mana_b, cd_p):
    """
    Return dict with three inference scores: {'mamdani':..,'sugeno':..,'tsukamoto':..}
    Use no-mana versions for Zombie/Skeleton; with-mana for Enderman/Boss.
    """
    if bot_type in ('Zombie','Skeleton'):
        m = mamdani_no_mana(hp_p,hp_b,cd_p)
        s = sugeno_no_mana(hp_p,hp_b,cd_p)
        t = tsukamoto_no_mana(hp_p,hp_b,cd_p)
    else:
        m = mamdani_with_mana(hp_p,hp_b,mana_p,mana_b,cd_p)
        s = sugeno_with_mana(hp_p,hp_b,mana_p,mana_b,cd_p)
        t = tsukamoto_with_mana(hp_p,hp_b,mana_p,mana_b,cd_p)
    return {'mamdani': float(m), 'sugeno': float(s), 'tsukamoto': float(t)}

# Backwards-compatible wrappers (keep default behaviour using Mamdani scorers)
def get_bot_action_score(hp_p_val, hp_b_val, mana_p_val, mana_b_val, cd_p_val):
    return mamdani_with_mana(hp_p_val, hp_b_val, mana_p_val, mana_b_val, cd_p_val)

def get_zombie_action_score(hp_p_val, hp_b_val, cd_p_val):
    return mamdani_no_mana(hp_p_val, hp_b_val, cd_p_val)

# existing high-level API unchanged: map -> behavior + actions
def map_fuzzy_score_to_behavior(score, bot_type):
    if score < 40:
        strength = "Weak"
    elif score < 70:
        strength = "Mid"
    else:
        strength = "Strong"

    if bot_type == "Zombie":
        if strength == "Weak":   return "MOVE_RETREAT"
        if strength == "Mid":    return "MOVE_CLOSE"
        if strength == "Strong": return "MOVE_CLOSE"
    if bot_type == "Skeleton":
        if strength == "Weak":   return "MOVE_RETREAT"
        if strength == "Mid":    return "RANGED_ATTACK"
        if strength == "Strong": return "RANGED_ATTACK"
    if bot_type == "Enderman":
        if strength == "Weak":   return "TELEPORT_FAR"
        if strength == "Mid":    return "TELEPORT_CLOSE"
        if strength == "Strong": return "TELEPORT_CLOSE"
    if bot_type == "Boss":
        if strength == "Weak":   return "MOVE_RETREAT"
        if strength == "Mid":    return "RANGED_ATTACK"
        if strength == "Strong": return "MOVE_CLOSE"
    return "WAIT"

# --- Movement & utility helpers (dipakai oleh get_final_action) ---
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def pick_adjacent_for_closer(zpos, ppos, occupied, grid_w, grid_h):
    zx, zy = zpos
    best = None
    best_d = manhattan(zpos, ppos)
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = zx + dx, zy + dy
        if 0 <= nx < grid_w and 0 <= ny < grid_h and (nx, ny) not in occupied:
            d = manhattan((nx, ny), ppos)
            if d < best_d:
                best_d = d
                best = (nx, ny)
    return best

def pick_adjacent_for_farther(zpos, ppos, occupied, grid_w, grid_h):
    zx, zy = zpos
    best = None
    best_d = manhattan(zpos, ppos)
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = zx + dx, zy + dy
        if 0 <= nx < grid_w and 0 <= ny < grid_h and (nx, ny) not in occupied:
            d = manhattan((nx, ny), ppos)
            if d > best_d:
                best_d = d
                best = (nx, ny)
    return best

# --- Heal-priority interrupt (Enderman / Boss) ---
def heal_priority_check(bot_type, hp_b_val, mana_b_val):
    if bot_type == "Enderman":
        if hp_b_val <= 40 and mana_b_val >= 30:
            return ("HEAL", True)
    if bot_type == "Boss":
        if hp_b_val <= 50 and mana_b_val >= 40:
            return ("HEAL", True)
    return (None, False)

# keep get_final_action / wrappers from previous file (unchanged)
def get_final_action(bot_type, hp_p, hp_b, mana_p, mana_b, cd_p,
                     pos, player_pos, occupied, grid_w=8, grid_h=6):
    if hp_b <= 0:
        return ("WAIT", None)
    heal_act, do_heal = heal_priority_check(bot_type, hp_b, mana_b)
    if do_heal:
        tgt = pick_adjacent_for_farther(pos, player_pos, occupied, grid_w, grid_h)
        return ("HEAL", tgt)
    if manhattan(pos, player_pos) == 1:
        return ("ATTACK", player_pos)

    # default uses Mamdani mapping (keeps previous behavior)
    if bot_type in ('Zombie','Skeleton'):
        score = mamdani_no_mana(hp_p, hp_b, cd_p)
    else:
        score = mamdani_with_mana(hp_p, hp_b, mana_p, mana_b, cd_p)

    behavior = map_fuzzy_score_to_behavior(score, bot_type)

    if behavior == "RANGED_ATTACK":
        if manhattan(pos, player_pos) <= 2:
            return ("RANGED_ATTACK", player_pos)
        tgt = pick_adjacent_for_closer(pos, player_pos, occupied, grid_w, grid_h)
        return ("MOVE_CLOSE", tgt) if tgt else ("WAIT", None)

    if behavior == "TELEPORT_CLOSE":
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            tx,ty = player_pos[0]+dx, player_pos[1]+dy
            if 0 <= tx < grid_w and 0 <= ty < grid_h and (tx,ty) not in occupied:
                return ("TELEPORT", (tx,ty))
        return ("WAIT", None)

    if behavior == "TELEPORT_FAR":
        tgt = pick_adjacent_for_farther(pos, player_pos, occupied, grid_w, grid_h)
        return ("TELEPORT", tgt) if tgt else ("WAIT", None)

    if behavior == "MOVE_CLOSE":
        tgt = pick_adjacent_for_closer(pos, player_pos, occupied, grid_w, grid_h)
        return ("MOVE_CLOSE", tgt) if tgt else ("WAIT", None)

    if behavior == "MOVE_RETREAT":
        tgt = pick_adjacent_for_farther(pos, player_pos, occupied, grid_w, grid_h)
        return ("MOVE_RETREAT", tgt) if tgt else ("WAIT", None)

    return ("WAIT", None)

def get_zombie_action(hp_player, hp_zombie, mana_player, mana_zombie, cd_player,
                      zombie_pos, player_pos, occupied_positions,
                      grid_w=8, grid_h=6):
    return get_final_action('Zombie', hp_player, hp_zombie, 0, 0, cd_player,
                            zombie_pos, player_pos, occupied_positions, grid_w, grid_h)

def get_bot_action(bot_type, hp_player, hp_bot, mana_player, mana_bot, cd_player,
                   bot_pos, player_pos, occupied_positions, grid_w=8, grid_h=6):
    return get_final_action(bot_type, hp_player, hp_bot, mana_player, mana_bot, cd_player,
                            bot_pos, player_pos, occupied_positions, grid_w, grid_h)