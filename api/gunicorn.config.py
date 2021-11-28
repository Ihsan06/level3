import multiprocessing

bind = "0.0.0.0:5000"

# Additional server settings
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 10000
timeout = 240
