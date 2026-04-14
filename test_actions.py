from core.actions import clear_temp_files, kill_high_cpu_process, get_top_processes

print("Top Processes:", get_top_processes())

print("\nClearing temp...")
print(clear_temp_files())

print("\nKilling process...")
print(kill_high_cpu_process())