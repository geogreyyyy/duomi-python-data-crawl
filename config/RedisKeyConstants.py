# coding:utf-8

redis_key_name = "python_data_crawl"
# redis异常状态
affiliate_center_crawl_status = redis_key_name+"_affiliate_center_crawl_status:"
redis_key_error_num = redis_key_name + "_error_num"
redis_key_response_num = redis_key_name + "_response_num"
redis_key_tik_tok_request_error_num = redis_key_name + "_tik_tok_request_error_num"
redis_key_tik_tok_request_wait_num = redis_key_name + "_tik_tok_request_wait_num"
# redis请求状态
redis_key_tiktok_shop_num = redis_key_name + "_tiktok_num"

redis_user_info_key = "tiktok_user_info:"

# -----------------redis lock -----------------------
redis_lock_name = redis_key_name + "_redis_lock:"
redis_lock_create_table = redis_lock_name+"create_table"
lock_insert_data = redis_lock_name+"lock_insert_data"
