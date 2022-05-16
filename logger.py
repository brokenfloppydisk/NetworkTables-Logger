import asyncio
import argparse
from networktables import NetworkTables
import pandas as pd
import time
import keyboard

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
            self.current_values["Timestamp"] = (time.perf_counter() - self.start_time,)

    def parse_args(self) -> argparse.Namespace:
        """ Parse command-line arguments
        """
        parser = argparse.ArgumentParser(
            description="Log the SmartDashboard entries on a NetworkTables server.")

        parser.add_argument("IP", metavar="i", type=str, nargs=1,
                            help="The IP or team number of the NetworkTables server.")
        
        parser.add_argument("directory", metavar="D", type=str, nargs="?", default="./",
                            help="The directory where the csv file should be outputted. \
                            Defaults to the current open directory.")
        
        parser.add_argument("check_time", metavar="T", type=int, nargs="?", default=50,
                            help="The number of milliseconds between each log update. \
                            Defaults to 50 milliseconds.")

        return parser.parse_args()

    async def main(self):
        """ Main function of the logger. 

        Initializes the NetworkTables client and gets values every 50 ms,
        and then outputs the data to "SDlog_DATETIME.csv".
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
            self.current_values[key] = (self.smart_dash.getEntry[key],)
        
        self.log()

        self.smart_dash.addEntryListener(self.value_changed)

        frame_time: float = args.check_time / 1000

        async def check_key():
            for i in range(frame_time//20):
                await asyncio.sleep(20)
                if keyboard.is_pressed(" "):
                    return True
            return False

        while True:
            self.update_keys()
            self.log()

            # TODO: check every 20 ms instead of every frame_time
            if keyboard.is_pressed(" "):
                break

            await asyncio.sleep(frame_time)
        
        output_directory: str = args.directory

        if output_directory[-1] != "/":
            output_directory += "/"

        output_file = output_directory + "SDlog_" + time.strftime("%Y-%m-%d_%H:%M:%S") + ".csv"

        print(f"Saving output to {output_file}.")

        self.data_frame.to_csv(output_file)
    
    def update_keys(self):
        """ Adds new keys to the key index if detected.
        """
        keys = self.smart_dash.getKeys(0)
        for key in keys:
            if key not in self.current_values:
                self.current_values[key] = (self.smart_dash.getEntry[key],)

    def value_changed(self, table, key, value, isNew):
        """ Modify the current value of a key when it is changed.
        """
        self.current_values[key] = value

    def log(self):
        """ Append all current values to the log dataframe.
        """
        self.update_timestamp()
        curr_df = pd.DataFrame.from_dict(self.current_values, orient="columns")
        print("\n"*20
            + "Now logging SmartDashboard values. Press SPACE to stop.\n"
            +f"Data on current frame:\n{curr_df}")
        self.data_frame = pd.concat([self.data_frame, curr_df], ignore_index=True)

if __name__ == "__main__":
    logger = TableLogger()
    asyncio.run(logger.main())