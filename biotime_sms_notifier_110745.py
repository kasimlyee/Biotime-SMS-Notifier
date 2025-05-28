#!/usr/bin/env python3
"""
BioTime SMS Notification System
Automatically sends SMS alerts to parents when students check in/out using BioTime logs

Author: Kasim Lyee
Email: kasiimlyee@gmail.com
Phone: +256784071324, +256701521269
Version: 0.1.1 
"""

import os
import sys
import time
import logging
import pandas as pd
import glob
import csv
from pathlib import Path
from datetime import datetime, timedelta
import json
import requests
import html
import configparser
import argparse
from typing import Optional, Tuple, Dict, Any
import re

# Constants
DEFAULT_CONFIG = {
    'general': {
        'log_folder': "C:/BioTimeLogs",
        'sent_log_file': "sent_sms_tracker.txt",
        'polling_interval': "60",
        'max_retries': "3",
        'retry_delay': "10"
    },
    'sms_gateway': {
        'url': 'your sms provider url',
        'username': 'username',
        'password': 'password',
        'senderid': 'senderid',
        'timeout': '5'
    },
    'messages': {
        'check_in': 'Dear parent, {name} has reached school at {time}',
        'check_out': 'Dear parent, {name} has left school at {time}',
        'error_message': 'System error occurred. Contact school IT'
    }
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biotime_sms_notifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Handles configuration loading and management"""
    
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(self.config_path):
            self._create_default_config()
        
        self._load_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist"""
        self.config.read_dict(DEFAULT_CONFIG)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        logger.info(f"Created new config file at {self.config_path}")
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            self.config.read(self.config_path)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default  #Return the default value if specified
    
    def getint(self, section: str, key: str, default: Any = None) -> int:
        """Get integer configuration value with optional default"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if default is not None:
                return int(default)
            raise
    
    def validate_config(self) -> bool:
        """Validate required configuration values"""
        required_sections = {
            'general': ['log_folder', 'sent_log_file'],
            'sms_gateway': ['url', 'username', 'password', 'senderid']
        }
        
        for section, keys in required_sections.items():
            if not self.config.has_section(section):
                logger.error(f"Missing config section: {section}")
                return False
            for key in keys:
                if not self.config.has_option(section, key):
                    logger.error(f"Missing config option: {section}.{key}")
                    return False
        
        return True

class SMSGateway:
    """Handles SMS sending operations"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.timeout = config.getint('sms_gateway', 'timeout', 5)
        self.max_retries = config.getint('general', 'max_retries', 3)
        self.retry_delay = config.getint('general', 'retry_delay', 10)
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS to the specified phone number
        
        Args:
            phone_number: Recipient phone number
            message: SMS content
            
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        url = self.config.get('sms_gateway', 'url')
        password = self.config.get('sms_gateway', 'password')
        username = self.config.get('sms_gateway', 'username')
        senderid = self.config.get('sms_gateway', 'senderid')
        
        data = {
            "method": "SendSms",
            "userdata": {
                "username": html.escape(username),
                "password": html.escape(password)
            },
            "msgdata": [{
                "number":html.escape(phone_number),
                "message":html.escape(message),
                "senderid":html.escape(senderid),
                "priority":"0"
            }]
        }
        
        data_in_json = json.dumps(data)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, data=data_in_json, timeout=self.timeout)
                response.raise_for_status()
                
                logger.info(f"SMS sent to {phone_number}. Response: {response.text}")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {phone_number}: {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
        
        logger.error(f"Failed to send SMS to {phone_number} after {self.max_retries} attempts")
        return False

class LogProcessor:
    """Processes BioTime log files and manages sent message tracking"""
    
    def __init__(self, config: ConfigManager, sms_gateway: SMSGateway):
        self.config = config
        self.sms_gateway = sms_gateway
        self.log_folder = config.get('general', 'log_folder')
        self.sent_log_file = config.get('general', 'sent_log_file')
        self.csv_file = os.path.join(self.log_folder, "parent_contact.csv")
        
        # Ensure required directories exist
        os.makedirs(self.log_folder, exist_ok=True)
        
        # Initialize sent log file if it doesn't exist
        if not os.path.exists(self.sent_log_file):
            with open(self.sent_log_file, 'w') as f:
                pass
    
    def get_latest_csv(self) -> Optional[str]:
        """Get the most recent CSV file in the log folder"""
        try:
            list_of_files = glob.glob(os.path.join(self.log_folder, '*.csv'))
            if not list_of_files:
                return None
            return max(list_of_files, key=os.path.getctime)
        except Exception as e:
            logger.error(f"Error finding latest CSV: {str(e)}")
            return None
    
    def read_last_line(self, csv_file: str) -> Optional[dict]:
        """Read the last line of a CSV file and return relevant data as dict"""
        try:
            with open(csv_file, 'r', newline='') as f:
                # Read all non-empty lines
                lines = [line for line in csv.reader(f, delimiter='\t') if line]
                if not lines:
                    return None
                
                last_line = lines[-1]
                
                # Find emp_code - first non-empty field
                emp_code = next((field for field in last_line if field.strip()), None)
                
                # Find date - looks like YYYY-MM-DD
                date_str = next((field for field in last_line if re.match(r'\d{4}-\d{2}-\d{2}', field)), None)
                
                # Time should be right after date
                time_index = last_line.index(date_str) + 1 if date_str else -1
                time_str = last_line[time_index] if time_index < len(last_line) else None
                
                if not all([emp_code, date_str, time_str]):
                    return None
                    
                return {
                    'emp_code': emp_code.strip(),
                    'date': date_str.strip(),
                    'time': time_str.strip()
                }
                
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_file}: {str(e)}")
            return None    
    def already_sent(self, emp_code: str, msg_type: str) -> bool:
        """Check if message was already sent today"""
        today_key = f"{time.strftime('%Y-%m-%d')}_{emp_code}_{msg_type}"
        try:
            if os.path.exists(self.sent_log_file):
                with open(self.sent_log_file, 'r') as f:
                    return today_key in f.read()
            return False
        except Exception as e:
            logger.error(f"Error checking sent log: {str(e)}")
            return True  # Assume sent to prevent duplicate messages
    
    def mark_as_sent(self, emp_code: str, msg_type: str) -> None:
        """Record that a message was sent"""
        today_key = f"{time.strftime('%Y-%m-%d')}_{emp_code}_{msg_type}"
        try:
            with open(self.sent_log_file, 'a') as f:
                f.write(today_key + '\n')
        except Exception as e:
            logger.error(f"Error updating sent log: {str(e)}")
    
    def process_log(self) -> bool:
        """Process the latest log file and send appropriate SMS"""
        latest_file = self.get_latest_csv()
        if not latest_file:
            logger.warning("No CSV file found in log folder")
            return False
        
        log_data = self.read_last_line(latest_file)
        if not log_data:
            logger.warning(f"Could not extract valid data from {latest_file}")
            return False
        
        try:
            emp_code = log_data['emp_code']
            date_str = log_data['date']
            time_str = log_data['time']
            timestamp_str = f"{date_str} {time_str}"
            
            logger.info(f"Processing log for EmpCode: {emp_code}, Time: {timestamp_str}")
            # Load and validate CSV data
            try:
                df = pd.read_csv(self.csv_file)
                required_columns = {'EmpCode', 'ParentNumber', 'Name'}
                if not required_columns.issubset(df.columns):
                    logger.error(
                        f"CSV file missing required columns. Needs: {required_columns}"
                    )
                    return False
                
                matched = df[df["EmpCode"] == emp_code]
                
                if not matched.empty:
                    phone_number = str(matched.iloc[0]["ParentNumber"]).strip()
                    name = matched.iloc[0]["Name"].strip()
                    
                    try:
                        check_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                    except ValueError:
                        logger.error(f"Invalid timestamp format: {timestamp_str}")
                        return False
                    
                    hour = check_time.hour
                    msg_type = "in" if hour < 12 else "out"
                    
                    if msg_type == "in":
                        message_template = self.config.get(
                            'messages', 'check_in' 
                            #fallback=DEFAULT_CONFIG['messages']['check_in']
                        )
                    else:
                        message_template = self.config.get(
                            'messages', 'check_out'
                            #fallback=DEFAULT_CONFIG['messages']['check_out']
                        )
                    
                    message = message_template.format(
                        name=name,
                        time=check_time.strftime('%Y-%m-%d %H:%M')
                    )
                    
                    if not self.already_sent(emp_code, msg_type):
                        if self.sms_gateway.send_sms(phone_number, message):
                            self.mark_as_sent(emp_code, msg_type)
                            logger.info(f"Successfully processed {msg_type} message for {emp_code}")
                            return True
                        else:
                            logger.error(f"Failed to send SMS for {emp_code}")
                            return False
                    else:
                        logger.info(
                            f"Already sent {msg_type} SMS for {emp_code} today. Skipping."
                        )
                        return True
                else:
                    logger.warning(f"EmpCode {emp_code} not found in CSV. Skipping.")
                    return False
                
            except Exception as e:
                logger.error(f"Error processing CSV data: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error processing log: {str(e)}")
            return False

def main():
    """Main application entry point"""
    while True:  # Infinite loop to auto-restart
        try:
            # Parse command line arguments
            parser = argparse.ArgumentParser(
                description='BioTime SMS Notification System',
                epilog='Author: Kasim Lyee (kasiimlyee@gmail.com)'
            )
            parser.add_argument(
                '--config', 
                default='config.ini',
                help='Path to configuration file'
            )
            parser.add_argument(
                '--simulate',
                action='store_true',
                help='Run in simulation mode (no actual SMS sent)'
            )
            args = parser.parse_args()
            
            # Initialize configuration
            config = ConfigManager(args.config)
            if not config.validate_config():
                logger.error("Invalid configuration. Please check config.ini")
                time.sleep(10)  # Wait before retrying
                continue
            
            # Initialize SMS gateway and log processor
            sms_gateway = SMSGateway(config)
            log_processor = LogProcessor(config, sms_gateway)
            
            # Main monitoring loop
            polling_interval = config.getint('general', 'polling_interval', 60)
            last_seen = ""
            
            logger.info("Starting BioTime SMS Notifier monitoring...")
            logger.info(f"Watching folder: {log_processor.log_folder}")
            logger.info(f"Polling interval: {polling_interval} seconds")
            
            while True:
                try:
                    latest = log_processor.get_latest_csv()
                    if latest and latest != last_seen:
                        last_seen = latest
                        logger.info(f"Detected new log file: {latest}")
                        if not log_processor.process_log():
                            logger.warning("Failed to process log file")
                    
                    time.sleep(polling_interval)
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {str(e)}")
                    time.sleep(10)  # Wait before retrying
                    break  # Restart outer loop
        
        except Exception as e:
            logger.error(f"Script crashed: {str(e)}. Restarting in 10 seconds...")
            time.sleep(10)
        

if __name__ == "__main__":
    main()
