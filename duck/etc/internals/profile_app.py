"""
Module for profiling a Duck application
"""
import cProfile
import pstats


def save_stats(profiler, stats_filepath: str):
    """
    Save profile statistics to the file.
    """
    profiler.disable()
    with open(stats_filepath, "w") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumulative")  # Sort by cumulative time
        stats.print_stats() # save stats to file.


def profile_app(app, stats_filepath: str = "profile_app_stats.prof"):
    """
    Profile a Duck application and write statistics to the stats_filepath.
    
    This is possible when CTRL-C is used to stop server.
    """
    profiler = cProfile.Profile()
    old_pre_stop = app.on_pre_stop
    app.on_pre_stop = lambda: (old_pre_stop(), save_stats(profiler, stats_filepath))
    profiler.enable()
    app.run()
    