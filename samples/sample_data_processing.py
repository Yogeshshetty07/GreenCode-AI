# Inefficient Data Processing Sample (O(N^2) Lookup & Str Concatenation)
def process_user_data(user_ids, active_ids):
    result_log = ""
    # Inefficient list search inside loop -> O(N^2)
    for uid in user_ids:
        if uid in active_ids:  # Hidden O(N) lookup per iteration
            # Inefficient string concatenation in loop
            result_log += "Active user ID: " + str(uid) + "\n"
    return result_log

# Execution trigger for profiler
users = list(range(1, 1500))
active = list(range(500, 2500, 2))
output = process_user_data(users, active)
