bind = "unix:/my_tg_bots/bboard/bboard.sock"
workers = 3
accesslog = "-"
timeout = 120
graceful_timeout = 30

limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

max_requests = 1000
max_requests_jitter = 50
preload_app = True