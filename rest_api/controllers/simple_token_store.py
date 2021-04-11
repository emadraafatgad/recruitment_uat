# -*- coding: utf-8 -*-

import time
import logging

_logger = logging.getLogger(__name__)


class SimpleTokenStore(object):
    
    def __init__(self):
        self.ss = {}
    
    def save_all_tokens(self, access_token, expires_in,
                refresh_token, refresh_expires_in, user_id):
        current_time = time.time()
        # access_token
        self.ss['access_' + access_token] = {
            'user_id':      user_id,
            'expiry_time':  current_time + expires_in,
        }
        # refresh_token
        self.ss['refresh_' + refresh_token] = {
            'access_token': access_token,
            'user_id':      user_id,
            'expiry_time':  current_time + refresh_expires_in,
        }
    
    def fetch_by_key(self, key):
        res = None
        existing_token = self.ss.get(key)
        if existing_token:
            # Check expiry time
            current_time = time.time()
            if existing_token['expiry_time'] < current_time:
                # token is expired - delete it
                del self.ss[key]
            else:
                res = existing_token
        return res
    
    def fetch_by_access_token(self, access_token):
        return self.fetch_by_key('access_' + access_token)
    
    def fetch_by_refresh_token(self, refresh_token):
        return self.fetch_by_key('refresh_' + refresh_token)
    
    def delete_by_key(self, key):
        if self.ss.get(key):
            del self.ss[key]
    
    def delete_access_token(self, access_token):
        self.delete_by_key('access_' + access_token)
    
    def delete_refresh_token(self, refresh_token):
        self.delete_by_key('refresh_' + refresh_token)
    
    def update_access_token(self, old_access_token,
                            new_access_token, expires_in,
                            refresh_token, user_id):
        current_time = time.time()
        # Delete old access token
        self.delete_access_token(old_access_token)
        # Write new access token
        self.ss['access_' + new_access_token] = {
            'user_id':      user_id,
            'expiry_time':  current_time + expires_in,
        }
        # Update refresh token
        self.ss['refresh_' + refresh_token]['access_token'] = new_access_token
    
    def delete_all_tokens_by_refresh_token(self, refresh_token):
        refresh_token_data = self.fetch_by_refresh_token(refresh_token)
        if refresh_token_data:
            access_token = refresh_token_data['access_token']
            # Delete tokens
            self.delete_access_token(access_token)
            self.delete_refresh_token(refresh_token)
