import asyncio
import argparse
from networktables import NetworkTables
import pandas as pd
import time
import msvcrt

class TableLogger:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.current_values = {}
        self.data_frame = pd.DataFrame()
        self.has_timestamp = False
        self.smart_dash = None

    def update_timestamp(self):
        """ Update the current timestamp using perf_counter()
        """
        if not self.has_timestamp:
            self.current_values["timestamp"] = self.start_time - time.perf_counter()

    def parse_args() -> argparse.Namespace:
        """ Parse command-line arguments
        """
        parser = argparse.ArgumentParser(
            description="Log the SmartDashboard entries on a NetworkTables server.")

        parser.add_argument("IP", metavar="i", type=str, nargs="1",
                            help="The IP or team number of the NetworkTables server.")
        
        parser.add_argument("directory", metavar="D", type=str, nargs="?", default="",
                            help="The directory where the csv file should be outputted. \
                            Defaults to the current open directory.")

        return parser.parse_args()

    def main(self):
        """ Main function. Initializes the NetworkTables client and gets values every 50 ms.
        Then outputs to SmartDashboard_log_DATETIME
        """
        args = self.parse_args()
        
        ip: str = args.IP
        if len(ip) <= 4:
            ip = f"roborio-{ip}-frc.local"

        NetworkTables.initialize(server=ip)
        self.smart_dash = NetworkTables.getTable("SmartDashboard")

        keys = self.smart_dash.getKeys(0)

        if "Timestamp" in keys:
            self.has_timestamp = True

        for key in keys:
            self.current_values[key] = self.smart_dash.getEntry[key]
        
        self.log()

        self.smart_dash.addEntryListener(self.value_changed)

        while True:
            print("Now logging SmartDashboard values. Press SPACE to stop.")

            self.update_keys()
            self.log()

            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 32:
                    break
            
            asyncio.sleep(0.05)
        
        output_directory: str = args.directory

        if output_directory[-1] == "/":
            output_directory = output_directory[0:-1:]

        output_file = output_directory + "SmartDashboard_log_" + "-".join([time.localtime()][0:6:]) + ".csv"

        print(f"Printing output to {output_file}.")

        self.data_frame.to_csv(output_file)
    
    def update_keys(self):
        """ Adds new keys to the key index if detected.
        """
        keys = self.smart_dash.getKeys(0)
        for key in keys:
            if key not in self.current_values:
                self.current_values[key] = self.smart_dash.getEntry[key]

    def value_changed(self, table, key, value, isNew):
        """ Modify the current value of a key when it is changed.
        """
        self.current_values[key] = value

    def log(self):
        """ Append all current values to the log dataframe.
        """
        self.update_timestamp()
        self.data_frame = pd.concat([self.data_frame, self.current_values], ignore_index=True)
