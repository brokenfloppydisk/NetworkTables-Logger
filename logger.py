import asyncio
import argparse
from networktables import NetworkTables
import pandas as pd
import time
import keyboard

class TableLogger:
    __slots__ = "start_time", "current_values", "data_frame", "has_timestamp",\
                "smart_dash", "logging_finished", "start_timestamp", "output_file"

    def __init__(self):
        self.start_time = time.perf_counter()
        self.current_values = {}
        self.data_frame = pd.DataFrame()
        self.has_timestamp = False
        self.smart_dash = None
        self.logging_finished = False
        self.output_file = ""
    
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
        
        parser.add_argument("flush_time", metavar="F", type=float, nargs="?", default=3,
                            help="The number of seconds between each log flush. \
                            Defaults to 3 seconds.")
        
        return parser.parse_args()

    def main(self):
        """ Main function of the logger. 

        Initializes the NetworkTables client and gets values every 50 ms,
        and then outputs the data to "SDlog_DATETIME.csv".
        """
        args = self.parse_args()

        self.initialize_logger(args.IP, args.directory)    

        frame_time: float = args.check_time / 1000

        asyncio.run(self.log(frame_time, args.flush_time))

        self.output_to_csv()
    
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

    def initialize_logger(self, ip: str, directory: str):
        """ Initialize the NetworkTables client and update the initial current_values.
        """
        if len(ip) <= 4:
            ip = f"roborio-{ip}-frc.local"

        NetworkTables.initialize(server=ip)
        self.smart_dash = NetworkTables.getTable("SmartDashboard")

        keys = self.smart_dash.getKeys(0)

        if "Timestamp" in keys:
            self.has_timestamp = True

        for key in keys:
            self.current_values[key] = (self.smart_dash.getEntry[key],)
        
        self.append_to_df()
        
        self.smart_dash.addEntryListener(self.value_changed)

        output_directory: str = directory

        if output_directory[-1] != "/":
            output_directory += "/"
        
        self.output_file = output_directory + "SDlog_" + time.strftime("%Y-%m-%d_%H:%M:%S") + ".csv"

    def append_to_df(self) -> None:
        """ Append all current values to the log dataframe and print status to the user.
        """
        self.update_timestamp()
        curr_df = pd.DataFrame.from_dict(self.current_values, orient="columns")
        print("\n"*20
            + "Now logging SmartDashboard values. Press SPACE to stop.\n"
            +f"Data on current frame:\n{curr_df}")
        self.data_frame = pd.concat([self.data_frame, curr_df], ignore_index=True)
    
    async def log(self, frame_time: float, flush_time: float) -> None:
        """ Append values to the dataframe and print the status to the user.
        """
        async def check_keyboard() -> None:
            """ Check keyboard inputs every 20 ms.
                Exit if the user presses space, and flush the log if the user presses f.
            """
            flush_cooldown = 0.0
            while not self.logging_finished:
                if keyboard.is_pressed(" "):
                    self.logging_finished = True
                if keyboard.is_pressed("f") and flush_cooldown == 0:
                    self.output_to_csv()
                    flush_cooldown = 0.5
                if flush_cooldown > 0:
                    flush_cooldown -= 0.02
                await asyncio.sleep(0.02)

        async def flush_log() -> None:
            """ Flush the contents of the dataframe to a csv.
            """
            while not self.logging_finished:
                self.output_to_csv()
                await asyncio.sleep(flush_time)
        
        async def update_dataframe() -> None:
            """ Update the keys and log value every frame_time
            """
            while not self.logging_finished:
                self.update_keys()
                self.append_to_df()
                await asyncio.sleep(frame_time)

        # Asynchronously run the two coroutines
        await asyncio.gather(
            check_keyboard(),
            update_dataframe(),
            flush_log()
        )

        # Block until logging is done
        while not self.logging_finished :
            pass

    def output_to_csv(self) -> None:
        """ Output the dataframe to a csv file (SDlog_TIMESTAMP.csv)
        """
        print(f"Saving output to {self.output_file}.")
        self.data_frame.to_csv(self.output_file)

if __name__ == "__main__":
    logger = TableLogger()
    logger.main()