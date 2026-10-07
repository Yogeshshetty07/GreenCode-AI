import time
import tracemalloc
import psutil
import sys
import io

# Energy & Carbon Constants
AVERAGE_CPU_TDP_WATTS = 45.0  # Typical laptop/workstation CPU thermal design power
IDLE_CPU_POWER_WATTS = 5.0    # Baseline idle power consumption
CARBON_INTENSITY_GCO2_PER_JOULE = 0.000132  # Global grid avg (475 g CO2e / kWh)

class GreenCodeProfiler:
    @staticmethod
    def profile_code(code_string, exec_globals=None):
        if exec_globals is None:
            exec_globals = {}
        
        # Prepare unified execution scope so functions & recursive calls resolution succeeds
        safe_scope = {
            "__builtins__": __builtins__,
            "time": time,
            "sys": sys
        }
        safe_scope.update(exec_globals)

        # Capture output stdout to prevent cluttering console
        stdout_trap = io.StringIO()
        original_stdout = sys.stdout

        # Pre-execution hardware metrics
        cpu_percent_start = psutil.cpu_percent(interval=None)
        tracemalloc.start()
        start_time = time.perf_counter()

        exec_error = None
        try:
            sys.stdout = stdout_trap
            exec(code_string, safe_scope, safe_scope)
        except Exception as e:
            exec_error = str(e)
        finally:
            end_time = time.perf_counter()
            current_mem, peak_mem_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            sys.stdout = original_stdout
            cpu_percent_end = psutil.cpu_percent(interval=None)

        # Calculations
        execution_time_sec = max(end_time - start_time, 0.00001)  # floor at 10 microseconds
        peak_memory_mb = peak_mem_bytes / (1024 * 1024)

        # Calculate estimated active CPU power consumption (Watts)
        avg_cpu_percent = max((cpu_percent_start + cpu_percent_end) / 2.0, 10.0)
        estimated_watts = IDLE_CPU_POWER_WATTS + ((AVERAGE_CPU_TDP_WATTS - IDLE_CPU_POWER_WATTS) * (avg_cpu_percent / 100.0))

        # Energy in Joules = Power (Watts) * Time (seconds)
        energy_joules = estimated_watts * execution_time_sec

        # Carbon footprint in grams of CO2 equivalent
        carbon_gco2e = energy_joules * CARBON_INTENSITY_GCO2_PER_JOULE

        # Eco Grade mapping based on energy consumption per run
        eco_grade = GreenCodeProfiler._calculate_grade(energy_joules, peak_memory_mb)

        return {
            "execution_time_ms": round(execution_time_sec * 1000, 3),
            "execution_time_sec": round(execution_time_sec, 6),
            "peak_memory_mb": round(peak_memory_mb, 4),
            "estimated_watts": round(estimated_watts, 2),
            "energy_joules": round(energy_joules, 6),
            "carbon_gco2e": round(carbon_gco2e, 6),
            "eco_grade": eco_grade,
            "error": exec_error,
            "stdout": stdout_trap.getvalue()[:300]
        }

    @staticmethod
    def _calculate_grade(joules, memory_mb):
        if joules < 0.01 and memory_mb < 1.0:
            return "A+ (Ultra Eco-Friendly)"
        elif joules < 0.1 and memory_mb < 5.0:
            return "A (Eco Efficient)"
        elif joules < 0.5:
            return "B (Moderate Energy Usage)"
        elif joules < 2.0:
            return "C (Elevated Energy Footprint)"
        elif joules < 5.0:
            return "D (High Power Consumption)"
        else:
            return "F (Severe Carbon Intensive)"

    @staticmethod
    def compare_profiles(original_profile, optimized_profile):
        orig_j = original_profile["energy_joules"]
        opt_j = optimized_profile["energy_joules"]
        orig_t = original_profile["execution_time_ms"]
        opt_t = optimized_profile["execution_time_ms"]
        orig_c = original_profile["carbon_gco2e"]
        opt_c = optimized_profile["carbon_gco2e"]

        joules_saved = max(orig_j - opt_j, 0.0)
        carbon_reduced_pct = round(((orig_c - opt_c) / orig_c) * 100, 2) if orig_c > 0 else 0.0
        speedup_factor = round(orig_t / opt_t, 2) if opt_t > 0 else 1.0

        return {
            "joules_saved": round(joules_saved, 6),
            "carbon_reduced_pct": max(carbon_reduced_pct, 0.0),
            "speedup_factor": speedup_factor,
            "is_improved": opt_j <= orig_j
        }
